import json
import time
import signal
import config as cfg
from args import parser
from subprocess import Popen
from sys import executable
from connection import MQTTClient, ConnectionInfo
from processing import DataProcessing

def on_quit():
    print("Closing...")
    local_conn.stop()
    fiware_conn.stop()
    draw and draw.terminate()
    exit(0)

if __name__ == "__main__":
    frame_number = 0
    args = parser()
    processor = DataProcessing()

    infoLocalConnection = ConnectionInfo(
        client_id=cfg.SERVER_MODULE_NAME,
        broker_ip=cfg.LOCAL_BROKER_IP_ADDRESS,
        broker_port=cfg.LOCAL_BROKER_PORT,
        sub_topic=cfg.LOCAL_SUB_TOPIC,
        pub_topic=cfg.LOCAL_PUB_TOPIC
        )
    infoFiwareConnection = ConnectionInfo(
        client_id=cfg.FIWARE_MODULE_NAME,
        broker_ip=cfg.FIWARE_BROKER_IP_ADDRESS,
        broker_port=cfg.FIWARE_BROKER_PORT,
        sub_topic=cfg.FIWARE_SUB_TOPIC,
        pub_topic=cfg.FIWARE_PUB_TOPIC
        )
    
    local_conn = MQTTClient(info=infoLocalConnection, on_message=processor.on_message)
    fiware_conn = MQTTClient(info=infoFiwareConnection)

    signal.signal(signal.SIGINT, lambda signum, frame: on_quit())
    
    draw = Popen([executable, cfg.VISUALIZER_NAME]) if args.draw else None

    while True:
        frame_number = (frame_number + 1) % (cfg.FLUSH_TIME)
        entities = processor.compute(frame_number, verbose=args.debug)
        entities_array = []
        for _class, _objs in entities.items():
            for _obj in _objs:
                entities_array.append(_obj)
        unity_array = processor.format_array_for_unity(entities_array)
        local_conn.send(json.dumps(unity_array))
        fiware_array = processor.format_array_for_fiware(entities_array)
        for _item in fiware_array:
            fiware_conn.send(json.dumps(_item))
        time.sleep(0.2)