import cv2
from camera_stream import CameraStream

if __name__ == "__main__":
    cam = CameraStream()
    while True:
        frame = cam.capture_frame()
        height, width, ch = frame.shape
        cv2.line(frame, (0, height//2), (width, height//2), (0, 255, 0), 1)
        cv2.line(frame, (width//2, 0), (width//2, height), (0, 255, 0), 1)
        cv2.imshow("Calibration", frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            break
    cv2.destroyAllWindows()
