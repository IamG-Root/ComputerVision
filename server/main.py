import json
import time
import signal
import threading
import config as cfg
import paho.mqtt.client as mqtt

modules_data = {}
lock = threading.Lock()

def signal_handler(sig, frame):
    print("Interrupt received, stopping MQTT client...")
    client.loop_stop()
    client.disconnect()
    exit(0)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(cfg.TOPIC)
        print(f"Subscribed to: '{cfg.TOPIC}'")
    else:
        print(f"Connection failed with error code: {rc}")


# Storing last received data from each module and sign every object with module_id
def on_message(client, userdata, msg):
    module_id = msg.topic.split("MODULE")[1]
    data = json.loads(msg.payload.decode('utf-8'))
    with lock:
        for obj in data:
            obj["module"] = module_id
        modules_data[module_id] = data


def init_receiver():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(cfg.BROKER_IP_ADDRESS, cfg.BROKER_PORT, keepalive=60)
        print("Connection to broker...")
    except Exception as e:
        print(f"Error occurred during connection: {e}")
        exit(1)

    client.loop_start()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    init_receiver()
    while True:
        with lock:
            # Group by class.
            data_by_class = {}
            for module_id, objs in modules_data.items():
                for obj in objs:
                    data_by_class.setdefault(obj["class"], []).append(obj)
            # Print for debug.
            for classe, objs in data_by_class.items():
                print(f"{classe} --- {data_by_class[classe]}\n")
        
        time.sleep(1)


if __name__ == "__main__":
    main()