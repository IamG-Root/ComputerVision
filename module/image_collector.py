import cv2
import sys
import time
import signal
import subprocess
from os import mkdir
from os.path import exists
from camera_stream import CameraStream

COLLECTION_FOLDER = "Collection"

def on_quit():
     print("Closing...")
     cam.stop()
     try:
         subprocess.run(["zip", "-r", "-0", f"{COLLECTION_FOLDER}.zip", COLLECTION_FOLDER], check=True)
         print(f"Images exported in {COLLECTION_FOLDER}.zip")
     except subprocess.CalledProcessError as e:
         print("Error during compression: ", e)
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

    if not exists(COLLECTION_FOLDER):
         mkdir(COLLECTION_FOLDER)

    while True:
        frame = cam.capture_frame()
        frame = cv2.resize(frame, (640, 640))
        ts = int(time.time())
        cv2.imwrite(f"{COLLECTION_FOLDER}/{ts}.jpg", frame)
        print(f"Saved {ts}.jpg")
        time.sleep(capture_delta_time)