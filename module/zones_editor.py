import cv2
import json
import utils
from enum import Enum
from camera_stream import CameraStream
from shapely.geometry import Point, Polygon

INFO = "+: Draw polygon | -: Delete polygon | S: Save | Q: Quit"

class Functions(Enum):
    NULL = 0
    DRAW = 1
    DELETE = 2

activefunction = Functions.NULL
active_polygon = []
polygons = []

def setactivefunction(function):
    global activefunction
    if activefunction == Functions.DRAW:
        createpolygon()
    activefunction = function
    return

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if activefunction == Functions.DRAW:
            active_polygon.append((x,y))
        elif activefunction == Functions.DELETE:
            erasepolygon((x,y))

def createpolygon():
    global polygons
    if len(active_polygon) > 2:
        polygons.append(active_polygon.copy())
    active_polygon.clear()

def erasepolygon(point):
    global polygons
    for poly in polygons:
        testpoly = Polygon(poly)
        testpoint = Point(point)
        if testpoly.contains(testpoint):
            polygons.remove(poly)
            break

def exportpolygons():
    to_export = []
    if polygons is not None and len(polygons) > 0:
        for poly in polygons:
            export_poly = []
            for point in poly:
                wx, wz = utils.pixel_to_world(point[0], point[1])
                wx, wz = utils.relative_to_absolute_position(wx, wz)
                export_poly.append([float(wx), float(wz)])
            to_export.append(export_poly)
        with open("output.json", "w") as f:
            json.dump(to_export, f)
        print("Exported polygons in output.json")

def importpolygons():
    try:
        with open("output.json", "r") as f:
            absolute_polygons = json.load(f)
    except FileNotFoundError:
        print("Polygon file not found.")
        return []
    imported_polygons = []
    for poly in absolute_polygons:
        pixel_poly = []
        for point in poly:
            wx, wz = utils.absolute_to_relative_position(point[0], point[1])
            pixelx, pixely = utils.world_to_pixel(wx, wz)
            pixel_poly.append([pixelx, pixely])
        imported_polygons.append(pixel_poly)
    return imported_polygons

def draw_polygon(frame, polygon, color):
    for i in range(len(polygon) - 1):
        cv2.line(frame, tuple(polygon[i]), tuple(polygon[i + 1]), color, 2)
    if len(polygon) > 2:
        cv2.line(frame, tuple(polygon[0]), tuple(polygon[-1]), color, 2)
    return frame

if __name__ == "__main__":
    cv2.namedWindow("Zone editor")
    cv2.setMouseCallback("Zone editor", on_click)
    polygons = importpolygons()
    cam = CameraStream()
    while True:
        frame = cam.capture_frame()
        frame = draw_polygon(frame, active_polygon,  (255, 0, 0))
        for poly in polygons:
            frame = draw_polygon(frame, poly, (0, 0, 255))
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            exportpolygons()
        elif key == ord('+'):
            setactivefunction(Functions.DRAW)
        elif key == ord('-'):
            setactivefunction(Functions.DELETE)
        elif key == ord('n'):
            setactivefunction(Functions.NULL)
        
        cv2.putText(frame, f"FUNCTION: {activefunction.name}", (1024 - 300, 768 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
        cv2.putText(frame, INFO, (25, 768 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
        cv2.imshow("Zone editor", frame)
    cv2.destroyAllWindows()