"""Paho manages reconnects in its network loop, including initial broker outage."""
import logging
import paho.mqtt.client as mqtt
log = logging.getLogger(__name__)

class MQTTBase:
    def configure(self, client_id, host, port, topic, subscription=None, on_message=None):
        self.topic, self.subscription = topic, subscription
        self.isConnected, self.should_stop = False, False
        self.client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = on_message
        self.client.reconnect_delay_set(min_delay=2, max_delay=30)
        self.client.max_queued_messages_set(1)
        self.client.connect_async(host, port, keepalive=60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        self.isConnected = reason_code == 0
        if self.isConnected:
            log.info('MQTT connected')
            if self.subscription:
                client.subscribe(self.subscription)
        else:
            log.warning('MQTT connect failed: %s', reason_code)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.isConnected = False
        if not self.should_stop:
            log.warning('MQTT disconnected: %s; automatic reconnect', reason_code)

    def send(self, content):
        if not self.isConnected:
            log.debug('MQTT offline; current snapshot dropped')
            return False
        result = self.client.publish(self.topic, content, qos=0, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning('MQTT publish failed rc=%s',result.rc)
            return False
        log.debug('MQTT published topic=%s bytes=%s',self.topic,len(content))
        return True

    def stop(self):
        self.should_stop = True
        self.client.disconnect()
        self.client.loop_stop()
        self.isConnected = False
