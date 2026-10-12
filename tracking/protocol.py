"""Strict, atomic validation of complete snapshots. No image fields."""
from dataclasses import dataclass
import math


@dataclass
class Snapshot:
    module: str
    session: str
    frame: int
    capture: float
    received: float
    observations: list
    synchronized: bool
    legacy: bool = False


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Expected finite numeric value')
    return float(value)


def decode(data, module, received, wall, max_age=1.0, max_entities=256):
    legacy = isinstance(data, list)
    if legacy:
        rows, session, frame, capture, sync = data, 'legacy', -1, wall, False
    else:
        if not isinstance(data, dict) or data.get('version') != 2 or data.get('module_id') != module:
            raise ValueError('Invalid version or module/topic mismatch')
        session = data['session_id']
        frame = data['frame_id']
        if not isinstance(session, str) or not 1 <= len(session) <= 128:
            raise ValueError('Invalid session')
        if type(frame) is not int or frame < 0:
            raise ValueError('Invalid frame')
        capture = number(data['capture_timestamp'])
        sync = data.get('clock_synchronized', False)
        if type(sync) is not bool:
            raise ValueError('Invalid clock status')
        if sync and not -0.25 <= wall - capture <= max_age:
            raise ValueError('Stale snapshot or clock skew')
        processing_age = number(data.get('processing_age', 0))
        if not 0 <= processing_age <= max_age:
            raise ValueError('Stale edge processing')
        if not sync:
            capture = wall-processing_age
        rows = data['entities']
    if not isinstance(rows, list) or len(rows) > max_entities:
        raise ValueError('Invalid entity list')
    observations, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid entity')
        ident = row.get('id') if legacy else row.get('local_track_id')
        if type(ident) is not int or ident < 0 or ident in seen:
            raise ValueError('Invalid or duplicated local ID')
        seen.add(ident)
        cls = row['class']
        if not isinstance(cls, str) or not 1 <= len(cls) <= 128:
            raise ValueError('Invalid class')
        pos = row['position']
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            raise ValueError('Invalid position')
        pos = [number(v) for v in pos]
        conf = number(row.get('confidence', 0.5))
        age = number(row.get('observation_age', 0))
        quality = number(row.get('quality', 1))
        if not 0 <= conf <= 1 or not 0 < quality <= 1 or age < 0:
            raise ValueError('Invalid confidence, quality or age')
        state = row.get('track_state', 'observed')
        if state not in ('observed', 'predicted', 'tentative', 'occluded'):
            raise ValueError('Invalid observation state')
        if state != 'observed' or age > 0:
            continue
        observations.append(dict(key=(module, session, ident), cls=cls, position=pos,
                                 confidence=conf, quality=quality, age=age))
    return Snapshot(module, session, frame, capture, received, observations, sync, legacy)
