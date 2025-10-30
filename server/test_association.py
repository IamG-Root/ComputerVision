import json
import time
import utils
import signal
import threading
import config as cfg
import paho.mqtt.client as mqtt
from munkres import Munkres, print_matrix

MAX_ID = 999
RANGE = 0.5
DELETE_DELTA_TIME = 5

lock = threading.Lock()
entities = {}
processing_buffer = []
raw_data = {}
hungarian = Munkres()
next_id = -1

def signal_handler(sig, frame):
    print("Interrupt received, stopping MQTT client...")
    client.loop_stop()
    client.disconnect()
    exit(0)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(cfg.TOPIC)
        print(f"Subscribed to: '{cfg.TOPIC}'")
    else:
        print(f"Connection failed with error code: {rc}")

# Storing last received data from each module and sign every object with module_id
def on_message(client, userdata, msg):
    module_id = msg.topic.split("MODULE")[1]
    data = json.loads(msg.payload.decode('utf-8'))
    with lock:
        for obj in data:
            obj["module"] = module_id
        raw_data[module_id] = data

def init_receiver():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(cfg.BROKER_IP_ADDRESS, cfg.BROKER_PORT, keepalive=60)
        print("Connection to broker...")
    except Exception as e:
        print(f"Error occurred during connection: {e}")
        exit(1)

    client.loop_start()

def compute():
    global next_id

    # Raggruppamento delle telemetrie per classe.
    data_by_class = utils.group_by_class(raw_data)

    for _class, objs in data_by_class.items():
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

def main():
    signal.signal(signal.SIGINT, signal_handler)
    init_receiver()
    while True:
        with lock:
            compute()
            print("---------- ENTITIES ----------")
            print(entities)

if __name__ == "__main__":
    main()