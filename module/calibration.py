import cv2
import config as cfg
from camera_stream import CameraStream
from utils import pixel_to_world, relative_to_absolute_position

def on_click(event, x, y, flags, param):
    global mouseX, mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        mouseX,mouseY = x,y
        wx, wz = pixel_to_world(mouseX, mouseY)
        print(f"CAMERA: X = {wx:.2f}m, Z = {wz:.2f}m")
        wx, wz = relative_to_absolute_position(wx, wz)
        print(f"ABSOLUTE: X = {wx:.2f}m, Z = {wz:.2f}m")
            
if __name__ == "__main__":
    cam = CameraStream()
    cv2.namedWindow("Calibration")
    cv2.setMouseCallback("Calibration", on_click)
    while True:
        frame = cam.capture_frame()
        height, width, ch = frame.shape
        cv2.line(frame, (0, height//2), (width, height//2), (0, 255, 0), 1)
        cv2.line(frame, (width//2, 0), (width//2, height), (0, 255, 0), 1)
        cv2.imshow("Calibration", frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            break
    cv2.destroyAllWindows()
