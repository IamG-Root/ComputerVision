"""Versioned internal wire format; only real detections leave the edge."""
import uuid
import time
import config as cfg

class Telemetry:
    def __init__(self):
        self.session = str(uuid.uuid4())

    def snapshot(self, entities, frame, capture):
        return {'version': 2, 'module_id': cfg.MODULE_NAME, 'session_id': self.session,
                'frame_id': frame, 'capture_timestamp': capture,
                'clock_synchronized': cfg.CLOCK_SYNCHRONIZED,
                'processing_age': max(0., time.time()-capture),
                'entities': [{'local_track_id': int(ident), 'class': e.class_name,
                    'position': [float(x) for x in e.position], 'confidence': e.confidence,
                    'bbox': [int(x) for x in e.box], 'track_state': 'observed',
                    'observation_age': 0.0, 'quality': 1.0} for ident,e in entities.items()]}
