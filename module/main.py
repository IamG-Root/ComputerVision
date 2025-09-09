import cv2
import time
import argparse
from inference import Inference
from camera_stream import CameraStream
from drawing import Drawing
from sender import Sender
import utils

def parser():
    parser = argparse.ArgumentParser(description="Computer vision module")
    parser.add_argument('--debug', action='store_true', help='Print detection log messages')
    parser.add_argument('--draw', action='store_true', help='Display debug window')
    parser.add_argument('--send', action='store_true', help='Send detections to server')
    args = parser.parse_args()
    return args

def on_click(event, x, y, flags, param):
    global mouseX, mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        mouseX,mouseY = x,y
        wx, wz, dist = utils.pixel_to_world(mouseX, mouseY)
        print(f"Cliccato in X = {wx:.2f}m, Z = {wz:.2f}m, distanza = {dist:.2f}m")
    
if __name__ == "__main__":
    frame_number = 0
    args = parser()
    cam = CameraStream()
    inference = Inference()
    drawing = Drawing()
    sender = Sender()
    tracked = {}
    cv2.setMouseCallback("Cattura", on_click)
    while True:
        frame = cam.capture_frame()
        results = inference.predict(frame, 0.5, False)
        detections = inference.detect(results)
        if detections is not None:
            tracked = inference.track(frame_number, tracked, detections)
            valid_tracked = inference.valid(tracked)
        if args.debug:
            print(str(valid_tracked))
        if args.draw:
            drawing.draw(frame, valid_tracked)
        if args.send:
            formatted = inference.format(valid_tracked)
            sender.send(str(formatted))
        if (drawing.exit()):
            break
        frame_number = frame_number + 1 if frame_number < 1000 else 0
        time.sleep(0.2)
    cam.stop()
    drawing.stop()
    sender.stop()
