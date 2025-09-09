import config as cfg
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

class Sender:
	def __init__(self):
		self.client = mqtt.Client(client_id=cfg.MODULE_NAME, callback_api_version=CallbackAPIVersion.VERSION2)
		self.client.on_connect = self.on_connect
		self.client.connect(cfg.BROKER_IP_ADDRESS)
	
	def on_connect(self, client, userdata, flags, reason_code, properties):
		if reason_code == "Success":
			print(f"Connected to: {cfg.BROKER_IP_ADDRESS}")
		else:
			print(f"Connection failed to: {cfg.BROKER_IP_ADDRESS}")
	
	def send(self, content):
		self.client.publish(cfg.TOPIC, content)
		
	def stop(self):
		self.client.disconnect()
	
	
