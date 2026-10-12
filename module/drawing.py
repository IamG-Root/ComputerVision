import cv2
import os
import sys
import subprocess
import logging
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
        self.active = False
        if sys.platform.startswith('linux') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            logging.warning('--draw unavailable: no graphical display; tracking continues')
            return
        # Qt can abort rather than raise when a display is unusable. Probe in a child.
        try:
            probe = subprocess.run([sys.executable, '-c',
                'import cv2; cv2.namedWindow("Display check"); cv2.destroyAllWindows()'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if probe.returncode:
                raise RuntimeError('OpenCV display probe failed')
            cv2.namedWindow(cfg.MODULE_NAME)
            cv2.setMouseCallback(cfg.MODULE_NAME, self.on_click)
            self.exclusions = import_exclusions()
            self.active = True
        except (Exception, cv2.error) as exc:
            logging.warning('--draw unavailable: %s; tracking continues', exc)

    def draw(self, frame, entities):
        if not self.active:
            return
        frame = frame.copy()
        try:
            for ident, entity in entities.items():
                x1,y1,x2,y2 = map(int,entity.box)
                state = getattr(entity, 'track_state', 'observed')
                color = (0,255,0) if state == 'observed' else (0,165,255)
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                cv2.circle(frame,tuple(map(int,entity.ground)),4,color,-1)
                label = f'{ident} {entity.class_name} {getattr(entity,"confidence",0):.2f} {state}'
                coords = f'X={entity.position[0]:.2f} Z={entity.position[1]:.2f}'
                cv2.putText(frame,label,(x1,max(20,y1-25)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
                cv2.putText(frame,coords,(x1,max(40,y1-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
            for exclusion in self.exclusions:
                self.draw_polygon(frame,exclusion,(0,0,255))
            cv2.imshow(cfg.MODULE_NAME,frame)
        except cv2.error:
            logging.warning('Diagnostic window unavailable; tracking continues')
            self.stop()

    def exit(self):
        if self.active:
            try:
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(cfg.MODULE_NAME,cv2.WND_PROP_VISIBLE) < 1:
                    self.stop()
            except cv2.error:
                self.stop()
        return False

    def stop(self):
        if self.active:
            self.active = False
            try:
                cv2.destroyWindow(cfg.MODULE_NAME)
            except cv2.error:
                pass

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
    
