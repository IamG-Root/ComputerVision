class Debug:
	def log(self, frame_number, entities):
		pass

class Debugger(Debug):
	def log(self, frame_number, entities):
		print(f"---- FRAME: {frame_number}\n")
		for id, entity in entities.items():
			print(entity.to_json(id) + "\n")
		print("---- \n")

class NullDebugger(Debug):
	pass
