import json
import logging
import signal
import time
import config as cfg
from args import parser
from inference import Inference
from connection import MQTTClient
from camera_stream import CameraStream
from drawing import Drawing, NullDrawing
from debug import Debugger, NullDebugger
from telemetry import Telemetry


def main():
    args = parser()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    conn = cam = drawing = None
    try:
        conn = MQTTClient()
        drawing = Drawing() if args.draw else NullDrawing()
        debugger = Debugger() if args.debug else NullDebugger()
        inference, telemetry = Inference(), Telemetry()
        frame_number = 0
        while running:
            start = time.monotonic()
            try:
                if cam is None:
                    cam = CameraStream()
                    logging.info('Camera ready')
                frame = cam.capture_frame()
                capture = cam.capture_timestamp
            except Exception:
                logging.exception('Camera unavailable; retrying')
                if cam is not None:
                    cam.stop(); cam = None
                time.sleep(1)
                continue
            entities = inference.extract_entities(frame, frame_number)
            drawing.draw(frame, inference.entities)
            debugger.log(frame_number, inference.entities)
            payload = (inference.to_json(entities) if cfg.PROTOCOL_VERSION == 1 else
                       json.dumps(telemetry.snapshot(entities, frame_number, capture), allow_nan=False))
            conn.send(payload)
            # Closing diagnostics does not terminate tracking or reset identities.
            drawing.exit()
            frame_number += 1
            elapsed = time.monotonic()-start
            logging.debug('Frame=%s capture=%.6f processing=%.3f fps=%.2f published=%s',
                          frame_number, capture, elapsed, 1/max(.001,elapsed+.2), len(entities))
            time.sleep(.2)
    finally:
        for resource in (drawing, cam, conn):
            if resource is not None:
                resource.stop()

if __name__ == '__main__':
    main()
