@staticmethod
def log_class(raw_data):
    print("------- RAW DATA -------")
    for _module, _content in raw_data.items():
        print(f"\nMODULE {_module}:")
        for _obj in _content["entities"]:
            print(f"\t-> Class: {_obj['class']} - Position: {_obj['position']}")

@staticmethod
def log_frame_entities(processing_buffer):
    print("\n------- FRAME ENTITIES -------\n")
    for _class, _objs in processing_buffer.items():
        print(f"CLASS {_class}:")
        for _obj in _objs:
            print(f"\t-> Class: {_obj['class']} - Position: {_obj['position']}")

@staticmethod
def log_entities(entities):
    print("\n------- ENTITIES -------\n")
    for _class, _objs in entities.items():
        print(f"CLASS {_class}:")
        for _obj in _objs:
            print(f"\t-> ID: {_obj['id']} - Class: {_obj['class']} - Position: {_obj['position']} - Last update: {_obj['last_update']}")

@staticmethod
def log_frame(frame_number: int, raw_data: dict, processing_buffer: dict, entities: dict):
    print("\033c", end="")
    print("\t\t\t---------- ENTITIES ----------\n")
    print(f"FRAME: {frame_number}\n")
    log_class(raw_data)
    log_frame_entities(processing_buffer)
    log_entities(entities)