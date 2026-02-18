# ======= Camera parameters =======

# X Resolution of camera native capture (Pixel)
CAPTURE_RES_X = 1640
# Y Resolution of camera native capture (Pixel)
CAPTURE_RES_Y = 1232
# X Resolution of frame (Pixel)
FRAME_RES_X = 1024
# Y Resolution of frame (Pixel)
FRAME_RES_Y = 768
# Camera Horizontal FOV angle (Degrees, °)
FOV_H_DEG = 53
# Camera Vertical FOV angle (Degrees, °)
FOV_V_DEG = 41
# Camera height (Meters, m)
CAMERA_H = 2.545
# Camera pitch angle (Degrees, °)
CAMERA_PITCH_DEG = 35
# Absolute position x (Meters, m)
CAMERA_POS_X = 4.5
# Absolute position y (Meters, m)
CAMERA_POS_Z = 0.8

# Orientation [1 - 4]
#
#
#     ╔═══════════════╗
#     ║       3       ║
#     ║       ˄       ║
#  ↑  ║               ║
#  Z  ║ 2<          >4║
#  ↓  ║               ║
#     ║       ˅       ║
#     ║       1       ║
#   0 ╚═══════════════╝
#           ← X →             

# 1: x = wx + CAMERA_POS_X | z = wz + CAMERA_POS_Z
# 2: x = wz + CAMERA_POS_X | z = -wx + CAMERA_POS_Z
# 3: x = -wx + CAMERA_POS_X | z = -wz + CAMERA_POS_Z
# 4: x = -wz + CAMERA_POS_X | z = wx + CAMERA_POS_Z
ORIENTATION = 1

# Excluded areas represented as polygons with absolute vertex coordinates.
EXCLUSIONS = []


# ======= Model parameters =======

# Model path to use
MODEL_PATH = "models/extinguisher_ncnn_model"
# Confidence of the detected entity
CONFIDENCE = 0.5


# ======= Tracking parameters =======

# Max distance between center of box (Pixel)
MAX_DISTANCE = 50
# Max frame difference from last appearance (Frame)
MAX_FRAME_DIFF = 10
# Consecutive frame number to valid a box (Frame)
MIN_VALID_SEEN_COUNT = 4
# Max number of entities detected at the same time
MAX_IDS = 1000
# Amount of frames to flush and restart entities
FLUSH_TIME = 1000


# ======= MQTT Parameters =======

# Module name
MODULE_NAME = "MODULEX"

# MQTT Broker IPv4 Address
BROKER_IP_ADDRESS = "10.1.64.130"
# MQTT Broker port
BROKER_PORT = 1883
# MQTT Publishing Topic name
TOPIC = "CV/" + MODULE_NAME
