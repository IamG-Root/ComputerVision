import json
import time
import utils
from munkres import Munkres, print_matrix

MAX_ID = 999
RANGE = 0.5
DELETE_DELTA_TIME = 5

# "persona": [{"id": 280, "class": "persona", "position": (180000, 250000),"last_update": 1761656444}]
entities = {}
processing_buffer = []
raw_data = {}

def message_parser(topic, msg):
    if "MODULE" not in topic:
        return
    module_id = topic.split("MODULE")[1]
    module_snapshot = json.loads(msg)
    for obj in module_snapshot:
        obj["module"] = module_id
    raw_data[module_id] = module_snapshot

def insert_misure():
    misure = [
        {"id":0, "class":"persona", "position":(4.2,2.8)},
        {"id":1, "class":"persona", "position":(6.0,3.0)},
        {"id":2, "class":"persona", "position":(17,24)},
        {"id":3, "class":"macchina", "position":(2.5,1.25)}
    ]
    message_parser("CV/MODULE1", json.dumps(misure))
    misure = [
        {"id":0, "class":"persona", "position":(18,25)},
        {"id":1, "class":"persona", "position":(4.3,2.8)},
        {"id":2, "class":"persona", "position":(6.0,2.7)},
        {"id":3, "class":"macchina", "position":(2.5,1.25)},
        {"id":4, "class":"persona", "position":(170,214)},
    ]
    message_parser("CV/MODULE2", json.dumps(misure))
    misure = [
        {"id":3, "class":"macchina", "position":(2.2,1.01)},
        {"id":4, "class":"persona", "position":(160,230)},
        {"id":5, "class":"persona", "position":(23,0)},
        {"id":1, "class":"persona", "position":(170.3,213.7)}
    ]
    message_parser("CV/MODULE3", json.dumps(misure))

def main():
    next_id = -1
    hungarian = Munkres()
    # Inserimento manuale delle telemetrie come con MQTT.
    insert_misure()

    # Raggruppamento delle telemetrie per classe.
    data_by_class = utils.group_by_class(raw_data)

    for _class, objs in data_by_class.items():
        # Eliminare questo if messo solo per debug.
        # if _class != "persona":
        #     break
        class_by_module = utils.group_by_module(objs)
        modules_ids = list(class_by_module.keys())
        m_rows = class_by_module[modules_ids[0]]
        for id in modules_ids[1:]:
            m_cols = class_by_module[id]
            # Inizializzazione della matrice dei costi con eventuale padding per far si che sia quadrata.
            cost_matrix = utils.square_matrix(len(m_rows), len(m_cols))
            # Inserimento costi nella matrice.
            for i, obj_row in enumerate(m_rows):
                for j, obj_col in enumerate(m_cols):
                    cost_matrix[i, j] = utils.distance(obj_row["position"], obj_col["position"])
            indexes = hungarian.compute(cost_matrix)

            # Inizio iterazione tra oggetti di camere diverse.
            temp_rows = []
            for i in indexes:
                rowval = m_rows[i[0]] if len(m_rows) > i[0] else m_cols[i[1]] # Se è accoppiato con un entità "padding", quindi indice > lunghezza, mantiene il valore non mediato. 
                colval = m_cols[i[1]] if len(m_cols) > i[1] else m_rows[i[0]]
                # Se la distanza tra le entità è nel range faccio una media, altrimenti le mantengo entrambe nella lista in maniera indipendente.
                if utils.distance(rowval["position"], colval["position"]) <= RANGE:
                    temp_rows.append({"class": _class, "position": utils.mean_position(rowval["position"], colval["position"])})
                else:
                    temp_rows.append({"class": _class, "position": rowval["position"]})
                    temp_rows.append({"class": _class, "position": colval["position"]})
            m_rows = temp_rows
        for obj in temp_rows:
            processing_buffer.append(obj)
    #print(processing_buffer)

    # Confronto delle entità processate con le entità gia presenti.

    # Divido le entità processate raggruppandole per classe.
    processed_by_class = {}
    for obj in processing_buffer:
        processed_by_class.setdefault(obj["class"], []).append(obj)
    #print(processed_by_class)

    # Inizio a cercare le associazioni per ogni classe.
    for _class, objs in processed_by_class.items():
        if _class not in entities:
            for obj in objs:
                next_id = utils.progress_id(next_id, MAX_ID)
                entities.setdefault(_class, []).append({"id": next_id, "class": _class, "position": obj["position"], "last_update": int(time.time())})
            continue
        # Calcolo la matrice dei costi.
        association_matrix = utils.square_matrix(len(objs), len(entities[_class]))
        for i, obj in enumerate(objs):
            for j, entity in enumerate(entities[_class]):
                association_matrix[i, j] = utils.distance(obj["position"], entity["position"])
        indexes = hungarian.compute(association_matrix)

        class_entities = entities[_class].copy()
        for i in indexes:
            _rowval = objs[i[0]] if len(objs) > i[0] else None
            _colval = entities[_class][i[1]] if len(entities[_class]) > i[1] else None
            if _rowval is None:
                next_id = utils.progress_id(next_id, MAX_ID)
                class_entities.append({"id": next_id, "class": _class, "position": _colval["position"], "last_update": int(time.time())})
                continue
            if _colval is None:
                next_id = utils.progress_id(next_id, MAX_ID)
                class_entities.append({"id": next_id, "class": _class, "position": _rowval["position"], "last_update": int(time.time())})
                continue
            if utils.distance(_rowval["position"], _colval["position"]) <= RANGE:
                class_entities[i[1]]["position"] = _rowval["position"]
                class_entities[i[1]]["last_update"] = int(time.time())
            else:
                next_id = utils.progress_id(next_id, MAX_ID)
                class_entities.append({"id":next_id, "class": _class, "position": _rowval["position"], "last_update": int(time.time())})
        entities[_class] = class_entities

        # Eliminare le entità non aggiornate da troppo tempo
        for __class, _objs in entities.items():
            entities[__class] = [
                valid for valid in _objs
                if abs(time.time() - valid["last_update"]) <= DELETE_DELTA_TIME
            ]
    return

if __name__ == "__main__":
    main()
    print(entities)