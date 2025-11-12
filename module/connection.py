import time
import config as cfg
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

class MQTTClient:
	def __init__(self):
		self.isConnected = False
		self.should_stop = False
		self.client = mqtt.Client(client_id=cfg.MODULE_NAME, callback_api_version=CallbackAPIVersion.VERSION2)
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		self.try_connection()
	
	def try_connection(self):
		attempt = 0
		while not self.isConnected:
			attempt += 1
			try:
				print(f"[...] Connection to broker attempt n.{attempt}...")
				self.client.connect(cfg.BROKER_IP_ADDRESS, cfg.BROKER_PORT, keepalive=60)
				self.client.loop_start()
				time.sleep(1)
				if self.isConnected:
					break
			except Exception as e:
				print(f"[ERROR] Error while attempting to connect to broker: {e}")

	def on_connect(self, client, userdata, flags, reason_code, properties):
		if reason_code == "Success":
			print(f"[OK] Connected to: {cfg.BROKER_IP_ADDRESS}")
			self.isConnected = True
		else:
			print(f"[ERROR] Connection failed to: {cfg.BROKER_IP_ADDRESS}")
	
	def on_disconnect(self, client, userdata, flags, reason_code, properties):
		if not self.should_stop:
			self.try_connection()
	
	def send(self, content):
		self.client.publish(cfg.TOPIC, content)
		
	def stop(self):
		if self.isConnected:
			self.should_stop = True
			self.client.loop_stop()
			self.client.disconnect()
			self.isConnected = False
	
	
