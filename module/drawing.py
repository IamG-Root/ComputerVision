import cv2
import config as cfg
from utils import import_exclusions, pixel_to_world, relative_to_absolute_position

class Graphic:
    def draw(self, frame, entities):
        pass
    def exit(self):
        return False
    def stop(self):
        pass

class Drawing(Graphic):
    def __init__(self):
        cv2.namedWindow(cfg.MODULE_NAME)
        cv2.setMouseCallback(cfg.MODULE_NAME, self.on_click)
        self.exclusions = import_exclusions()

    def draw(self, frame, entities):
        for id, entity in entities.items():
            x1, y1, x2, y2 = map(int, entity.box)
            cx, cy = entity.center
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            class_name = entity.class_name
            cv2.putText(frame, f"CLASS: {class_name}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(frame, f"ID: {id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        for exclusion in self.exclusions:
            self.draw_polygon(frame, exclusion, (0, 0, 255))
        cv2.imshow(cfg.MODULE_NAME, frame)

    def exit(self):
        return (cv2.waitKey(1) & 0xFF == ord('q'))

    def stop(self):
        cv2.destroyAllWindows()
    
    def on_click(self, event, x, y, flags, param):
        global mouseX, mouseY
        if event == cv2.EVENT_LBUTTONDOWN:
            mouseX,mouseY = x,y
            wx, wz = pixel_to_world(mouseX, mouseY)
            print(f"CAMERA: X = {wx:.2f}m, Z = {wz:.2f}m")
            wx, wz = relative_to_absolute_position(wx, wz)
            print(f"ABSOLUTE: X = {wx:.2f}m, Z = {wz:.2f}m")
    
    @staticmethod
    def draw_polygon(frame, polygon, color):
        for i in range(len(polygon) - 1):
            cv2.line(frame, tuple(polygon[i]), tuple(polygon[i + 1]), color, 2)
        if len(polygon) > 2:
            cv2.line(frame, tuple(polygon[0]), tuple(polygon[-1]), color, 2)
        return frame

class NullDrawing(Graphic):
    pass
    
