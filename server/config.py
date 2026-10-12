# ======= Processing parameters =======

# Maximum distance between two entities to be considered the same (Meters, m)
RANGE = 0.5
# Time threshold after which non-updated entities are deleted (Seconds, s)
DELETE_DELTA_TIME = 5
# Maximum number of trackable entities
MAX_ID = 999
# Maximum number of frames. After this restart from 0.
FLUSH_TIME = 100000

# ======= Visualizer Parameters =======

# Visualizer script name
VISUALIZER_NAME = "server/visualizer.py"
# Width of the window (Pixels)
WIDTH = 720
# Height of the window (Pixels)
HEIGHT = 720
# Padding of the rectangle of the window (Pixels)
PADDING = 20
# Width of the dot representing an entity
DOT_WIDTH = 5

# ======= MQTT Parameters =======

# Local Server Module name
SERVER_MODULE_NAME = "SERVER"
# Local Visualizer Module name
VISUALIZER_MODULE_NAME = "VISUALIZER"
# FIWARE Module name
FIWARE_MODULE_NAME = "FIWARE"

# Local MQTT Broker IPv4 Address
LOCAL_BROKER_IP_ADDRESS = "localhost"
# Local MQTT Broker Port
LOCAL_BROKER_PORT = 1883
# Local MQTT Publish Topic name
LOCAL_PUB_TOPIC = "POS"
# Local MQTT Subscription Topic name
LOCAL_SUB_TOPIC = "CV/#"

# Fiware MQTT Broker IPv4 Address
FIWARE_BROKER_IP_ADDRESS = "localhost"
# Fiware MQTT Broker Port
FIWARE_BROKER_PORT = 1883
# Fiware MQTT Publish Topic name
FIWARE_PUB_TOPIC = "/secret_key_cam/cam_1/attrs"
# Fiware MQTT Subscription Topic name
FIWARE_SUB_TOPIC = "$SYS/#"

# Internal MC-MOT settings (seconds, meters); public MQTT settings above unchanged.
TRACK_POLICY = dict(confirm_hits=2, publish_age=0.6, lost_age=1.5, delete_age=4.0,
                    max_distance=1.2, max_speed=3.0, measurement_sigma=0.15,
                    acceleration=1.5, gate=9.21)
# Keys must match model class names exactly. Example: {"pallet": {"acceleration": 0.3}}
CLASS_POLICIES = {}
REORDER_WINDOW = 0.08
FUSION_WINDOW = 0.06
MAX_SNAPSHOT_AGE = 1.0
MAX_PENDING_SNAPSHOTS = 256
MAX_PAYLOAD_BYTES = 262144
MAX_ENTITIES_PER_SNAPSHOT = 256
MAX_MODULES = 128
# Optional surveyed visibility polygons; empty means no geometry restriction.
CAMERA_VISIBILITY = {}
