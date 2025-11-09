# ======= Processing parameters =======

# Maximum distance between two entities to be considered the same (Meters, m)
RANGE = 0.5
# Time threshold after which non-updated entities are deleted (Seconds, s)
DELETE_DELTA_TIME = 5
# Maximum number of trackable entities
MAX_ID = 999
# Maximum number of frames. After this restart from 0.
FLUSH_TIME = 100000

# ======= MQTT Parameters =======

# Module name
MODULE_NAME = "SERVER"

# MQTT Broker IPv4 Address
BROKER_IP_ADDRESS = "192.168.1.33"
# MQTT Broker Port
BROKER_PORT = 1883
# MQTT Publish Topic name
PUB_TOPIC = "POS"
# MQTT Subscription Topic name
SUB_TOPIC = "CV/#"