import json
import time
import signal
import config as cfg
from args import parser
from subprocess import Popen
from sys import executable
from connection import MQTTClient
from processing import DataProcessing

def on_quit():
    print("Closing...")
    conn.stop()
    draw and draw.terminate()
    exit(0)

if __name__ == "__main__":
    frame_number = 0
    args = parser()
    processor = DataProcessing()
    conn = MQTTClient(name=cfg.SERVER_MODULE_NAME, on_message=processor.on_message)

    signal.signal(signal.SIGINT, lambda signum, frame: on_quit())
    
    draw = Popen([executable, cfg.VISUALIZER_NAME]) if args.draw else None

    while True:
        frame_number = (frame_number + 1) % (cfg.FLUSH_TIME)
        entities = processor.compute(frame_number, verbose=args.debug)
        entities_array = []
        for _class, _objs in entities.items():
            for _obj in _objs:
                entities_array.append(_obj)
        conn.send(json.dumps(entities_array))
        time.sleep(0.2)