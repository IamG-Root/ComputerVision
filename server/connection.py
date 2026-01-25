import config as cfg
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

class ConnectionInfo:
	def __init__(self, client_id, broker_ip, broker_port, sub_topic, pub_topic):
		self.client_id = client_id
		self.broker_ip = broker_ip
		self.broker_port = broker_port
		self.sub_topic = sub_topic
		self.pub_topic = pub_topic

class MQTTClient:
	def __init__(self, info:ConnectionInfo, on_message = None):
		self.isConnected = False
		self.should_stop = False
		self.info = info
		self.client = mqtt.Client(client_id=info.client_id, callback_api_version=CallbackAPIVersion.VERSION2)
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		self.client.on_message = on_message
		self.client.reconnect_delay_set(min_delay=2, max_delay=30)
		self.try_connection()
	
	def try_connection(self):
		try:
			print("[...] Connection to broker...")
			self.client.connect(self.info.broker_ip, self.info.broker_port, keepalive=60)
			self.client.loop_start()
		except Exception as e:
			print(f"[ERROR] Error while attempting to connect to broker: {e}")

	def on_connect(self, client, userdata, flags, reason_code, properties):
		if reason_code == "Success":
			print(f"[OK] Connected to: {self.info.broker_ip}:{self.info.broker_port}")
			self.isConnected = True
			self.client.subscribe(self.info.sub_topic)
			print(f"[OK] Subscribed to: '{self.info.sub_topic}'")
		else:
			print(f"[ERROR] Connection failed to: {self.info.broker_ip}")
	
	def on_disconnect(self, client, userdata, flags, reason_code, properties):
		if self.isConnected:
			self.isConnected = False
		if not self.should_stop:
			self.try_connection()
	
	def send(self, content):
		self.client.publish(self.info.pub_topic, content)
		
	def stop(self):
		if self.isConnected:
			self.should_stop = True
			self.client.loop_stop()
			self.client.disconnect()
			self.isConnected = False