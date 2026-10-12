import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tracking.mqtt import MQTTBase

class ConnectionInfo:
    def __init__(self, client_id, broker_ip, broker_port, sub_topic, pub_topic):
        self.client_id, self.broker_ip, self.broker_port = client_id, broker_ip, broker_port
        self.sub_topic, self.pub_topic = sub_topic, pub_topic

class MQTTClient(MQTTBase):
    def __init__(self, info, on_message=None):
        self.info = info
        self.configure(info.client_id, info.broker_ip, info.broker_port,
                       info.pub_topic, info.sub_topic, on_message)
