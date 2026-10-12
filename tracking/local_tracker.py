"""One-to-one image-space association, with short constant-velocity prediction."""
import logging
import numpy as np
from .assignment import assign
log = logging.getLogger(__name__)

class LocalTracker:
    def __init__(self, max_distance=50, max_missed=10, min_hits=5):
        self.entities = {}
        self.next_id = 0
        self.max_distance, self.max_missed, self.min_hits = max_distance, max_missed, min_hits

    def update(self, detections, frame):
        old = [(k,e) for k,e in self.entities.items() if 0 <= frame-e.last_seen < self.max_missed]
        costs = np.full((len(detections),len(old)), np.inf)
        for i,d in enumerate(detections):
            for j,(_,e) in enumerate(old):
                if d.class_name == e.class_name:
                    predicted = np.asarray(e.center) + np.asarray(getattr(e,'velocity',(0.,0.))) * (frame-e.last_seen)
                    costs[i,j] = np.linalg.norm(np.asarray(d.center)-predicted)
        matches = assign(costs, self.max_distance)
        result = dict(old)
        for e in result.values():
            e.track_state = 'occluded'
        used = set()
        for i,j in matches:
            ident,e = old[j]; d = detections[i]; used.add(i)
            dt = max(1,frame-e.last_seen)
            d.velocity = tuple((np.asarray(d.center)-np.asarray(e.center))/dt)
            d.seen_count = e.seen_count + 1 if dt == 1 else 1
            # Confirmed tracks survive short occlusion without repeated warm-up.
            d.confirmed = getattr(e,'confirmed',False) or d.seen_count >= self.min_hits
            d.last_seen = frame; d.track_state = 'observed' if d.confirmed else 'tentative'
            result[ident] = d
            log.debug('Local association id=%s frame=%s', ident, frame)
        for i,d in enumerate(detections):
            if i not in used:
                d.seen_count=1; d.last_seen=frame; d.velocity=(0.,0.)
                d.confirmed=self.min_hits<=1
                d.track_state='observed' if d.confirmed else 'tentative'
                result[self.next_id]=d
                log.debug('Local birth id=%s',self.next_id)
                self.next_id+=1
        for ident in self.entities.keys()-result.keys():
            log.debug('Local deleted id=%s',ident)
        self.entities=result
        return result
