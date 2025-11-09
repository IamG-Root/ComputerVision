import config as cfg
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

class MQTTClient:
	def __init__(self, on_message = None):
		self.isConnected = False
		self.client = mqtt.Client(client_id=cfg.MODULE_NAME, callback_api_version=CallbackAPIVersion.VERSION2)
		self.client.on_connect = self.on_connect
		self.client.on_message = on_message
		try:
			print("[...] Connection to broker...")
			self.client.connect(cfg.BROKER_IP_ADDRESS, cfg.BROKER_PORT, keepalive=60)
			self.client.loop_start()
		except Exception as e:
			print(f"[ERROR] Error while attempting to connect to broker: {e}")
	
	def on_connect(self, client, userdata, flags, reason_code, properties):
		if reason_code == "Success":
			print(f"[OK] Connected to: {cfg.BROKER_IP_ADDRESS}:{cfg.BROKER_PORT}")
			self.isConnected = True
			self.client.subscribe(cfg.SUB_TOPIC)
			print(f"[OK] Subscribed to: '{cfg.SUB_TOPIC}'")
		else:
			print(f"[ERROR] Connection failed to: {cfg.BROKER_IP_ADDRESS}")
	
	def send(self, content):
		self.client.publish(cfg.TOPIC, content)
		
	def stop(self):
		if self.isConnected:
			self.client.loop_stop()
			self.client.disconnect()
			self.isConnected = False