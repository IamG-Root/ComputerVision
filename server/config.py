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
VISUALIZER_NAME = "visualizer.py"
# Width of the window (Pixels)
WIDTH = 720
# Height of the window (Pixels)
HEIGHT = 720
# Padding of the rectangle of the window (Pixels)
PADDING = 20
# Width of the dot representing an entity
DOT_WIDTH = 5

# ======= MQTT Parameters =======

# Server Module name
SERVER_MODULE_NAME = "SERVER"
# Visualizer Module name
VISUALIZER_MODULE_NAME = "VISUALIZER"

# MQTT Broker IPv4 Address
BROKER_IP_ADDRESS = "192.168.1.33"
# MQTT Broker Port
BROKER_PORT = 1883
# MQTT Publish Topic name
PUB_TOPIC = "POS"
# MQTT Subscription Topic name
SUB_TOPIC = "CV/#"