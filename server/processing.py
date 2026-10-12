"""MQTT ingress and bounded event-time buffering; public output is legacy."""
import json
import logging
import time
import threading
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg
from legacy_output import LegacyOutput
from tracking.protocol import decode
from tracking.visibility import quality
from tracking.global_tracker import GlobalTracker, Policy

log = logging.getLogger(__name__)

class DataProcessing(LegacyOutput):
    def __init__(self, clock=time.monotonic, wall=time.time):
        self.lock = threading.Lock()
        self.clock, self.wall = clock, wall
        self.pending = []
        self.modules = {}
        self.tracker = GlobalTracker(Policy(**cfg.TRACK_POLICY),
            {k: Policy(**dict(cfg.TRACK_POLICY, **v)) for k,v in cfg.CLASS_POLICIES.items()}, cfg.MAX_ID)
        self.entities = {}
        self.rejected = 0

    def on_message(self, client, userdata, msg):
        try:
            if not msg.topic.startswith('CV/MODULE') or getattr(msg, 'retain', False):
                raise ValueError('Unexpected topic or retained snapshot')
            if len(msg.payload) > cfg.MAX_PAYLOAD_BYTES:
                raise ValueError('Snapshot exceeds size limit')
            now, wall = self.clock(), self.wall()
            module = msg.topic.split('/')[-1]
            snap = decode(json.loads(msg.payload.decode('utf-8')), module, now, wall,
                          cfg.MAX_SNAPSHOT_AGE, cfg.MAX_ENTITIES_PER_SNAPSHOT)
            when = now - max(0., wall-snap.capture)
            # observation_age is extra age relative to capture, not network latency.
            snap.observations = [o for o in snap.observations
                                 if now-when+o['age'] <= cfg.MAX_SNAPSHOT_AGE]
            for o in snap.observations:
                o['quality'] *= quality(o['position'], cfg.CAMERA_VISIBILITY.get(module))
            with self.lock:
                old = self.modules.get(module)
                if old:
                    session, seq, retired, _ = old
                    if snap.session in retired or (session == snap.session and not snap.legacy and snap.frame <= seq):
                        raise ValueError('Duplicate, retired session or out-of-order frame')
                    if session != snap.session:
                        retired = (retired + [session])[-32:]
                        self.pending = [item for item in self.pending if item[2].module != module]
                else:
                    if len(self.modules) >= cfg.MAX_MODULES:
                        raise ValueError('Module capacity reached')
                    retired = []
                self.modules[module] = (snap.session, snap.frame, retired, now)
                if len(self.pending) >= cfg.MAX_PENDING_SNAPSHOTS:
                    self.pending.pop(0)
                    log.warning('Input queue full; oldest snapshot dropped')
                self.pending.append((when, snap.capture, snap))
                log.debug('Snapshot module=%s frame=%s count=%s synchronized=%s', module, snap.frame, len(snap.observations), snap.synchronized)
        except (ValueError, KeyError, TypeError, UnicodeError, IndexError) as exc:
            self.rejected += 1
            log.warning('Rejected MQTT snapshot: %s', exc)

    def compute(self, frame_number=0, verbose=False):
        now = self.clock()
        with self.lock:
            ready = sorted((x for x in self.pending if now-x[2].received >= cfg.REORDER_WINDOW),
                           key=lambda x: (x[0], x[2].module, x[2].frame))
            self.pending = [x for x in self.pending if now-x[2].received < cfg.REORDER_WINDOW]
        # Group close observations once per camera; repeated camera frames form next group.
        groups = []
        for item in ready:
            if now-item[0] > cfg.MAX_SNAPSHOT_AGE:
                continue
            if not groups or item[0]-groups[-1][0][0] > cfg.FUSION_WINDOW or any(x[2].module == item[2].module for x in groups[-1]):
                groups.append([])
            groups[-1].append(item)
        for group in groups:
            when = max(x[0] for x in group)
            obs = [o for x in group for o in x[2].observations]
            self.tracker.ingest(obs, when, max(x[1] for x in group))
        self.entities = self.tracker.output(now)
        if verbose:
            log.debug('Frame=%s tracks=%s published=%s rejected=%s', frame_number,
                      len(self.tracker.tracks), sum(map(len,self.entities.values())), self.rejected)
        return self.entities
