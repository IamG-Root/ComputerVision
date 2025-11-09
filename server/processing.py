import time
import json
import debug
import utils
import threading
import config as cfg

class DataProcessing:
    def __init__(self):
        self.lock = threading.Lock()
        self.next_id = 0
        self.entities = {}
        self.raw_data = {}
    
    def on_message(self, client, userdata, msg):
        module_id = msg.topic.split("MODULE")[1]
        data = json.loads(msg.payload.decode('utf-8'))
        with self.lock:
            for obj in data:
                obj["module"] = module_id
            self.raw_data[module_id] = {
                "entities": data,
                "last_update": int(time.time())
            }
    
    def increment(self):
        self.next_id = self.next_id + 1 if self.next_id < cfg.MAX_ID else 0
        return self.next_id
    
    def compute(self, frame_number = 0, verbose = False):
        if not self.raw_data: return {}
        processing_buffer = {}
        with self.lock:
            raw_data_by_class = utils.group_by_class(self.raw_data)
            # Asscociazioni tra entità del frame corrente.
            for _class, _objs in raw_data_by_class.items():
                processing_buffer[_class] = self.compute_class(_class = _class, _entities_in_class = _objs)
            # Associazioni tra entità processate del frame corrente ed entità del frame precedente.
            for _class, _objs in processing_buffer.items():
                if _class not in self.entities:
                    self.entities[_class] = self.init_class(_class = _class, _objs = _objs)
                else:
                    self.entities[_class] = self.compute_frame_class(_class = _class, _frame_entities = _objs, _entities_in_class = self.entities[_class])
            # Cancellazione delle entità non aggiornate da un certo lasso di tempo.
            self.entities = self.remove_obsolete_entities(self.entities)
            # Cancellazione dei dati provenienti dai moduli non aggiornati da un certo lasso di tempo.
            self.raw_data = self.remove_obsolete_modules(self.raw_data)
            if verbose:
                debug.log_frame(frame_number=frame_number, raw_data=self.raw_data, processing_buffer=processing_buffer, entities=self.entities)
            return self.entities

    
    def init_class(self, _class, _objs):
        buffer = []
        for _obj in _objs:
            buffer.append({"id": self.increment(), "class": _class, "position": _obj["position"], "last_update": int(time.time())})
        return buffer

    @staticmethod
    def compute_class(_class, _entities_in_class):
        buffer = []
        class_by_module = utils.group_by_module(_entities_in_class)
        modules_ids = list(class_by_module.keys())

        _rows = class_by_module[modules_ids[0]]

        # Se c'è un modulo solo che rileva la classe di oggetti, aggiungo indipendentemente ogni oggetto.
        if len(modules_ids) == 1:
            for _obj in _rows:
                buffer.append({"class": _class, "position": _obj["position"]})

        for id in modules_ids[1:]:
            _cols = class_by_module[id]
            matches = utils.calculate_matches(_rows, _cols)
            # Inizio iterazione tra oggetti di camere diverse.
            for i in matches:
                # Se è accoppiato con un entità "padding", quindi indice > lunghezza, mantiene il valore non mediato.
                _rowval = _rows[i[0]] if len(_rows) > i[0] else _cols[i[1]]
                _colval = _cols[i[1]] if len(_cols) > i[1] else _rows[i[0]]
                if utils.distance(_rowval["position"], _colval["position"]) <= cfg.RANGE:
                    buffer.append({"class": _class, "position": utils.mean_position(_rowval["position"], _colval["position"])})
                else:
                    buffer.append({"class": _class, "position": _rowval["position"]})
                    buffer.append({"class": _class, "position": _colval["position"]})
            _rows = buffer
        return buffer

    def compute_frame_class(self, _class, _frame_entities, _entities_in_class):
        buffer = []

        matches = utils.calculate_matches(_frame_entities, _entities_in_class)
        for i in matches:
            _rowval = _frame_entities[i[0]] if len(_frame_entities) > i[0] else None
            _colval = _entities_in_class[i[1]] if len(_entities_in_class) > i[1] else None
            if _rowval is None: continue
            if _colval is None:
                buffer.append({"id": self.increment(), "class": _class, "position": _rowval["position"], "last_update": int(time.time())})
                continue
            if utils.distance(_rowval["position"], _colval["position"]) <= cfg.RANGE:
                buffer.append({"id": _colval["id"], "class": _colval["class"], "position": _rowval["position"], "last_update": int(time.time())})
            else:
                buffer.append({"id": self.increment(), "class": _class, "position": _rowval["position"], "last_update": int(time.time())})
        return buffer
    
    @staticmethod
    def remove_obsolete_entities(_entities):
        current_time = int(time.time())
        filtered_entities = {}
        for _class, _objs in _entities.items():
            filtered_entities[_class] = [
                valid for valid in _objs
                if abs(current_time - valid["last_update"]) <= cfg.DELETE_DELTA_TIME
            ]
        return filtered_entities
    
    @staticmethod
    def remove_obsolete_modules(_raw_data):
        current_time = int(time.time())
        return {
            module: data
            for module, data in _raw_data.items()
            if current_time - data["last_update"] <= cfg.DELETE_DELTA_TIME
        }