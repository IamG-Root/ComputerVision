import json
import math
from utils import pixel_to_world, relative_to_absolute_position

class Entity:
	def __init__(self, class_name, box, seen_count = -1, last_seen = -1):
		self.class_name = class_name
		self.box = box
		x1, y1, x2, y2 = box
		self.center = int((x1 + x2) / 2), int((y1 + y2) / 2)
		self.ground = (int(x1 + ((x2 - x1)/2)), y2)
		wx, wz = pixel_to_world(self.ground[0], self.ground[1])
		self.position = relative_to_absolute_position(wx, wz)
		self.seen_count = seen_count
		self.last_seen = last_seen
	
	def to_dict(self, id):
		return {
			"id": id,
			"class": self.class_name,
			"position": self.position
		}
		
	def to_json(self, id):
		return json.dumps(self.to_dict(id))
	
	@staticmethod
	def distance(e1, e2):
		return math.hypot(e1.center[0] - e2.center[0], e1.center[1] - e2.center[1])
