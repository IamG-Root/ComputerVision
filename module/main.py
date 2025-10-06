import time
import signal
import config as cfg
from args import parser
from inference import Inference
from connection import MQTTClient
from camera_stream import CameraStream
from drawing import Drawing, NullDrawing
from debug import Debugger, NullDebugger

def on_quit():
	print("Closing...")
	conn.stop()
	cam.stop()
	drawing.stop()
	exit(0)

if __name__ == "__main__":
	frame_number = 0
	args = parser()
	conn = MQTTClient()
	cam = CameraStream()
	drawing = Drawing() if args.draw else NullDrawing()
	debugger = Debugger() if args.debug else NullDebugger()
	inference = Inference()
	
	signal.signal(signal.SIGINT, lambda signum, frame: on_quit())
	
	entities = {}
	
	while True:
		frame = cam.capture_frame()
		
		entities = inference.extract_entities(frame, frame_number)
		
		drawing.draw(frame, entities)
		
		debugger.log(frame_number, entities)
		
		conn.send(inference.to_json(entities))
		
		if (drawing.exit()):
			break
		
		frame_number = (frame_number + 1) % (cfg.FLUSH_TIME + 1)
		if frame_number == 0:
			inference.entities.clear()
		
		time.sleep(0.2)
	on_quit()
		
	
