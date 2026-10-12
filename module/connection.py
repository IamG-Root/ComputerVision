import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg
from tracking.mqtt import MQTTBase

class MQTTClient(MQTTBase):
    def __init__(self):
        self.configure(cfg.MODULE_NAME, cfg.BROKER_IP_ADDRESS, cfg.BROKER_PORT, cfg.TOPIC)
