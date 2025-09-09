import math
import config as cfg
from ultralytics import YOLO
from utils import pixel_to_world

class Inference:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH)
        self.next_id = 0
    
    def predict(self, frame, conf, verbose):
        results = self.model.predict(source=frame, conf=conf, verbose=verbose)
        return results[0]

    def detect(self, results):
        detections = []
        for box in results.boxes:
            class_name = self.model.names[int(box.cls[0])]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            center = int((x1 + x2) / 2), int((y1 + y2) / 2)
            ground_origin = (int(x1 + ((x2 - x1)/2)), y2)
            wx, wz, wdist = pixel_to_world(ground_origin[0], ground_origin[1])
            detections.append({"box": (x1, y1, x2, y2), "ground": ground_origin, "center": center, "position": (round(wx + cfg.CAMERA_POS_X, 3), round(wz + cfg.CAMERA_POS_Y, 3)), "class": class_name})
        return detections

    def track(self, frame_number, tracked, detections):
        updated_tracked = tracked.copy()
        for det in detections:
            assigned = False
            for id, track in updated_tracked.items():
                dist = math.hypot(det["center"][0] - track["center"][0], det["center"][1] - track["center"][1])
                if dist < cfg.MAX_DISTANCE and det["class"] == track["class"]:
                    updated_tracked[id] = {
                            "box": det["box"],
                            "ground": det["ground"],
                            "center": det["center"],
                            "position": det["position"],
                            "class": det["class"],
                            "seen_count": (track["seen_count"] + 1) if track["seen_count"] <= cfg.MIN_VALID_SEEN_COUNT else track["seen_count"],
                            "last_seen": frame_number
                            }
                    assigned = True
                    break
            if not assigned:
                updated_tracked[self.next_id] = {"box": det["box"], "ground": det["ground"], "center": det["center"], "position": det["position"], "class": det["class"], "seen_count": 1, "last_seen": frame_number}
                self.next_id += 1
        updated_tracked = {
                id:track for id, track in updated_tracked.items()
                if frame_number - track["last_seen"] < cfg.MAX_FRAME_DIFF
                }
        return updated_tracked
        

    def valid(self, tracked):
        valid_tracked = {
                id:track for id, track in tracked.items()
                if track["seen_count"] > cfg.MIN_VALID_SEEN_COUNT
                }
        return valid_tracked
        
    def format(self, tracked):
        formatted = []
        for id, track in tracked.items():
            formatted.append({"id": id, "class": track["class"], "position": track["position"]})
        return formatted
