import cv2

class Drawing:
    def __init__(self):
        cv2.namedWindow("Cattura")

    def draw(self, frame, results):
        for id, track in results.items():
            x1, y1, x2, y2 = map(int, track["box"])
            cx, cy = track["center"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            class_name = track["class"]
            cv2.putText(frame, f"CLASS: {class_name}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(frame, f"ID: {id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.imshow("Cattura", frame)

    def exit(self):
        return (cv2.waitKey(1) & 0xFF == ord('q'))

    def stop(self):
        cv2.destroyAllWindows()
