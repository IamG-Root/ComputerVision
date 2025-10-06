import json
import math
import config as cfg
from entity import Entity
from ultralytics import YOLO

class Inference:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH, task="detect")
        self.next_id = 0
        self.entities = {}
    
    def detect(self, results):
        detections = []
        for box in results.boxes:
            class_name = self.model.names[int(box.cls[0])]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            detections.append(Entity(class_name, (x1, y1, x2, y2)))
        return detections

    def track(self, detections, frame_number):
        updated_entities = self.entities.copy()
        for detection in detections:
            assigned = False
            for id, entity in self.entities.items():
                if detection.class_name == entity.class_name:
                    distance = Entity.distance(detection, entity)
                    if distance < cfg.MAX_DISTANCE:
                        updated_entities[id] = Entity(detection.class_name, detection.box, (entity.seen_count + 1) if entity.seen_count <= cfg.MIN_VALID_SEEN_COUNT else entity.seen_count, frame_number)
                        assigned = True
                        break
            if not assigned:
                updated_entities[self.next_id] = Entity(detection.class_name, detection.box, 1, frame_number)
                self.next_id = self.next_id + 1 if self.next_id < cfg.MAX_IDS else 0
        
        updated_entities = {
                id:entity for id, entity in updated_entities.items()
                if frame_number - entity.last_seen < cfg.MAX_FRAME_DIFF
                }
        return updated_entities
        

    def valid(self):
        valid_entities = {
                id:entity for id, entity in self.entities.items()
                if entity.seen_count > cfg.MIN_VALID_SEEN_COUNT
                }
        return valid_entities
    
    @staticmethod
    def to_json(entities):
        json_data = []
        for id, entity in entities.items():
            json_data.append(entity.to_dict(id))
        return(json.dumps(json_data))
        
    def extract_entities(self, frame, frame_number):
        results = self.model.predict(source=frame, conf=cfg.CONFIDENCE, verbose=False)[0]
        detections = self.detect(results)
        self.entities = self.track(detections, frame_number)
        return self.valid()
