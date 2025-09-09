# ======= Camera parameters =======

# X Resolution of camera native capture (Pixel)
CAPTURE_RES_X = 1640
# Y Resolution of camera native capture (Pixel)
CAPTURE_RES_Y = 1232
# X Resolution of frame (Pixel)
FRAME_RES_X = 1024
# Y Resolution of frame (Pixel)
FRAME_RES_Y = 768
# Camera Horizontal FOV angle (Deg, �)
FOV_H_DEG = 51.4
# Camera Vertical FOV angle (Degrees, �)
FOV_V_DEG = 39.4
# Camera height (Meters, m)
CAMERA_H = 2.545
# Camera pitch angle (Degrees, �)
CAMERA_PITCH_DEG = 35
# Posizione assoluta x (Buttare)
CAMERA_POS_X = 4.5
# Posizione assoluta y (Buttare)
CAMERA_POS_Y = 0.8



# ======= Model parameters =======

# Model path to use
MODEL_PATH = "models/extinguisher_ncnn_model"


# ======= Tracking parameters =======

# Max distance between center of box (Pixel)
MAX_DISTANCE = 50
# Max frame difference from last appearance (Frame)
MAX_FRAME_DIFF = 10
# Consecutive frame number to valid a box (Frame)
MIN_VALID_SEEN_COUNT = 4


# ======= MQTT Parameters =======

# Module name
MODULE_NAME = "MODULE1"

# MQTT Broker IPv4 Address
BROKER_IP_ADDRESS = "192.168.1.33"
TOPIC = "CV/MODULE1"
