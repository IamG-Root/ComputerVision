"""Persistent CV Kalman tracker; per-camera constrained assignment in time order."""
from dataclasses import dataclass, field
import logging
import numpy as np
from .assignment import assign

log = logging.getLogger(__name__)

@dataclass
class Policy:
    confirm_hits: int = 2
    publish_age: float = 0.6
    lost_age: float = 1.5
    delete_age: float = 4.0
    max_distance: float = 1.2
    max_speed: float = 3.0
    measurement_sigma: float = 0.15
    acceleration: float = 1.5
    gate: float = 9.21

@dataclass
class Track:
    ident: int
    cls: str
    x: np.ndarray
    P: np.ndarray
    time: float
    last_real: float
    wall: float
    hits: int = 1
    state: str = 'Tentative'
    keys: set = field(default_factory=set)
    last_hit: float = 0.0

class GlobalTracker:
    def __init__(self, policy=None, classes=None, max_id=999):
        self.policy = policy or Policy()
        self.classes = classes or {}
        self.max_id = max_id
        self.tracks = {}
        self.next_id = 0
        self.last_time = float('-inf')

    def rules(self, cls):
        return self.classes.get(cls, self.policy)

    def predict(self, t, now):
        dt = max(0., now - t.time)
        if not dt:
            return
        F = np.eye(4); F[0, 2] = F[1, 3] = dt
        G = np.array([[dt*dt/2, 0], [0, dt*dt/2], [dt, 0], [0, dt]])
        t.x = F @ t.x
        t.P = F @ t.P @ F.T + G @ G.T * self.rules(t.cls).acceleration**2
        t.time = now

    def allocate(self):
        for _ in range(self.max_id + 1):
            self.next_id = self.next_id + 1 if self.next_id < self.max_id else 0
            if self.next_id not in self.tracks:
                return self.next_id
        log.warning('Global ID capacity reached; birth suppressed')
        return None

    def ingest(self, observations, when, wall):
        # Caller sorts short buffered batches; late measurements never refresh life.
        if when < self.last_time - 1e-6:
            return
        self.last_time = when
        for t in self.tracks.values():
            self.predict(t, when)
        by_camera = {}
        for o in observations:
            by_camera.setdefault(o['key'][0], []).append(o)
        for camera in sorted(by_camera):
            rows = sorted(by_camera[camera], key=lambda o: o['key'])
            tracks = sorted(self.tracks.values(), key=lambda t: t.ident)
            costs = np.full((len(rows), len(tracks)), np.inf)
            for i, o in enumerate(rows):
                p = self.rules(o['cls'])
                for j, t in enumerate(tracks):
                    if o['cls'] != t.cls or when - t.last_real > p.delete_age:
                        continue
                    delta = np.asarray(o['position']) - t.x[:2]
                    if np.linalg.norm(delta) > min(p.max_distance, 0.5 + p.max_speed * max(0., when-t.last_real)):
                        continue
                    R = np.eye(2) * p.measurement_sigma**2 / max(.1, o['confidence']*o['quality'])
                    mahal = float(delta @ np.linalg.solve(t.P[:2, :2]+R, delta))
                    if mahal <= p.gate:
                        costs[i,j] = mahal / p.gate + (0 if o['key'] in t.keys else .15)
            matches = assign(costs, 1.15)
            used = set()
            for i, j in matches:
                used.add(i)
                o, t = rows[i], tracks[j]
                p = self.rules(t.cls)
                R = np.eye(2) * p.measurement_sigma**2 / max(.1, o['confidence']*o['quality'])
                K = np.linalg.solve(t.P[:2,:2]+R, t.P[:,:2].T).T
                t.x += K @ (np.asarray(o['position'])-t.x[:2])
                A = np.eye(4); A[:,:2] -= K
                t.P = A @ t.P @ A.T + K @ R @ K.T
                # Correlated cameras must not imply arbitrary measurement precision.
                t.P[:2,:2] += np.eye(2) * .001
                t.last_real, t.wall = when, wall
                if when - t.last_hit >= .08:
                    t.hits += 1; t.last_hit = when
                # Bound aliases: only latest local key per camera/session.
                t.keys = {k for k in t.keys if k[0] != camera}
                t.keys.add(o['key'])
                if t.hits >= p.confirm_hits:
                    t.state = 'Confirmed'
            for i, o in enumerate(rows):
                if i in used:
                    continue
                ident = self.allocate()
                if ident is None:
                    continue
                p = self.rules(o['cls'])
                t = Track(ident, o['cls'], np.array([*o['position'],0.,0.]),
                          np.diag([.04,.04,1.,1.]), when, when, wall,
                          keys={o['key']}, last_hit=when)
                if p.confirm_hits <= 1:
                    t.state = 'Confirmed'
                self.tracks[ident] = t
                log.debug('Birth global=%s class=%s', ident, o['cls'])

    def output(self, now):
        result = {}
        for ident, t in list(self.tracks.items()):
            p = self.rules(t.cls)
            age = now - t.last_real
            if age > p.delete_age or (t.hits < p.confirm_hits and age > p.lost_age):
                t.state = 'Deleted'; del self.tracks[ident]
                log.debug('Deleted global=%s', ident)
                continue
            if age > p.lost_age:
                t.state = 'Lost'
            elif age > p.publish_age:
                t.state = 'Occluded'
            if t.hits >= p.confirm_hits and age <= p.publish_age:
                result.setdefault(t.cls, []).append({'id': t.ident, 'class': t.cls,
                    'position': [round(float(x),3) for x in t.x[:2]], 'last_update': int(t.wall)})
        return result
