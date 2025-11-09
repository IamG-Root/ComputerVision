import time
import signal
import config as cfg
from args import parser
from connection import MQTTClient
from processing import DataProcessing

def on_quit():
    print("Closing...")
    conn.stop()
    exit(0)

if __name__ == "__main__":
    frame_number = 0
    args = parser()
    processor = DataProcessing()
    conn = MQTTClient(on_message=processor.on_message)

    signal.signal(signal.SIGINT, lambda signum, frame: on_quit())

    while True:
        frame_number = (frame_number + 1) % (cfg.FLUSH_TIME)
        entities = processor.compute(frame_number, verbose=args.debug)
        # To add:
        # Send entities to MQTT pub topic
        time.sleep(0.2)