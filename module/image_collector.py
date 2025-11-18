import cv2
import sys
import time
import signal
from os import mkdir
from os.path import exists
from camera_stream import CameraStream

def on_quit():
	print("Closing...")
	cam.stop()
	exit(0)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("[ERROR] Invalid capture delta time.")
        exit(1)
    
    try:
        capture_delta_time = int(sys.argv[1])
        print(f"Starting image collection with capture delta time: {capture_delta_time}s.")
    except ValueError:
        print("[ERROR] First argument must be an integer number.")
        exit(1)
    
    signal.signal(signal.SIGINT, lambda signum, frame: on_quit())
    cam = CameraStream()

    if exists("Collections"):
         mkdir("Collections")

    while True:
        frame = cam.capture_frame()
        frame = cv2.resize(frame, (640, 640))
        ts = int(time.time())
        cv2.imwrite(f"Collections/{ts}.jpg", frame)
        print("Saved {ts}.jpg")
        time.sleep(capture_delta_time)