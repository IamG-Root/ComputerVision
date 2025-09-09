import cv2
import time
import config as cfg
from picamera2 import Picamera2

class CameraStream:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (cfg.CAPTURE_RES_X, cfg.CAPTURE_RES_Y)})
        self.picam2.configure(config)
        self.picam2.start(show_preview = False)
        time.sleep(2)
    
    def capture_frame(self):
        frame = self.picam2.capture_array()
        frame = cv2.resize(frame, (cfg.FRAME_RES_X, cfg.FRAME_RES_Y))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
        return frame

    def stop(self):
        self.picam2.stop()
