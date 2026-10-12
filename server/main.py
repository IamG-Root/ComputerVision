import json
import logging
import time
import signal
import config as cfg
from args import parser
from subprocess import Popen
from sys import executable
from connection import MQTTClient, ConnectionInfo
from processing import DataProcessing

def main():
    frame_number = 0
    args = parser()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    processor = DataProcessing()

    infoLocalConnection = ConnectionInfo(
        client_id=cfg.SERVER_MODULE_NAME + ('_SHADOW' if args.shadow else ''),
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
    fiware_conn = None if args.shadow else MQTTClient(info=infoFiwareConnection)

    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    draw = Popen([executable, cfg.VISUALIZER_NAME]) if args.draw else None

    try:
        while running:
            frame_number = (frame_number + 1) % (cfg.FLUSH_TIME)
            entities = processor.compute(frame_number, verbose=args.debug)
            if not args.shadow:
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
    finally:
        local_conn.stop()
        if fiware_conn is not None:
            fiware_conn.stop()
        if draw is not None:
            draw.terminate()
            draw.wait(timeout=5)

if __name__ == '__main__':
    main()
