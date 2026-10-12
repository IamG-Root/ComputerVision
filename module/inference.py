import json
import math
import time
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tracking.local_tracker import LocalTracker
import config as cfg
from entity import Entity
from ultralytics import YOLO
from utils import is_inside_exclusions

class Inference:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH, task="detect")
        self.tracker = LocalTracker(cfg.MAX_DISTANCE, cfg.MAX_FRAME_DIFF, cfg.MIN_VALID_SEEN_COUNT+1)
        self.next_id = 0
        self.entities = {}
    
    def detect(self, results):
        detections = []
        for box in results.boxes:
            class_name = self.model.names[int(box.cls[0])]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            entity = Entity(class_name, (x1, y1, x2, y2))
            entity.confidence = float(box.conf[0])
            if all(math.isfinite(v) for v in entity.position):
                detections.append(entity)
            else:
                logging.warning("Non-finite projection rejected")
        return detections

    def track(self, detections, frame_number):
        return self.tracker.update(detections, frame_number)

    def valid(self):
        valid_entities = {
                id:entity for id, entity in self.entities.items()
                if getattr(entity, "confirmed", False) and entity.track_state == "observed" and not is_inside_exclusions(entity.position)
                }
        return valid_entities
    
    @staticmethod
    def to_json(entities):
        json_data = []
        for id, entity in entities.items():
            json_data.append(entity.to_dict(id))
        return(json.dumps(json_data))
        
    def extract_entities(self, frame, frame_number):
        start = time.monotonic()
        results = self.model.predict(source=frame, conf=cfg.CONFIDENCE, verbose=False)[0]
        detections = self.detect(results)
        logging.debug("Inference seconds=%.3f detections=%s", time.monotonic()-start, len(detections))
        self.entities = self.track(detections, frame_number)
        return self.valid()
