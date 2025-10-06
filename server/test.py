import json
import numpy as np
from scipy.optimize import linear_sum_assignment
import networkx as nx

modules_data = {}

def distanza(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def test_message(topic, msg):
    module_id = topic.split("MODULE")[1]
    module_snapshot = json.loads(msg)
    for obj in module_snapshot:
        obj["module"] = module_id
    modules_data[module_id] = module_snapshot

def insert_misure():
    misure = [
        {"id":0, "classe":"persona", "posizione":(4.5,3.0)},
        {"id":1, "classe":"persona", "posizione":(4.2,2.8)},
        {"id":2, "classe":"macchina", "posizione":(2.5,1.25)}
    ]
    test_message("CV/MODULE1", json.dumps(misure))
    misure = [
        {"id":0, "classe":"persona", "posizione":(4.3,2.8)},
        {"id":1, "classe":"persona", "posizione":(4.3,2.7)},
        {"id":2, "classe":"macchina", "posizione":(2.5,1.25)}
    ]
    test_message("CV/MODULE2", json.dumps(misure))
    misure = [
    {"id": 0, "classe": "cane", "posizione": (5.0, 3.5)},
    {"id": 1, "classe": "libro", "posizione": (4.7, 3.3)},
    {"id": 2, "classe": "bicicletta", "posizione": (2.2, 1.0)}
    ]
    test_message("CV/MODULE3", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "bicicletta", "posizione": (3.5, 2.5)},
        {"id": 1, "classe": "albero", "posizione": (3.2, 2.3)},
        {"id": 2, "classe": "gatto", "posizione": (1.8, 1.0)}
    ]
    test_message("CV/MODULE4", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "gatto", "posizione": (4.6, 3.2)},
        {"id": 1, "classe": "carrello", "posizione": (4.4, 3.1)},
        {"id": 2, "classe": "aereo", "posizione": (3.0, 2.0)}
    ]
    test_message("CV/MODULE5", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "carrello", "posizione": (5.2, 3.7)},
        {"id": 1, "classe": "albero", "posizione": (5.0, 3.6)},
        {"id": 2, "classe": "bicicletta", "posizione": (2.8, 1.5)}
    ]
    test_message("CV/MODULE6", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "libro", "posizione": (4.0, 3.0)},
        {"id": 1, "classe": "gatto", "posizione": (3.8, 2.9)},
        {"id": 2, "classe": "aereo", "posizione": (2.3, 1.2)}
    ]
    test_message("CV/MODULE7", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "estintore", "posizione": (6.0, 4.0)},
        {"id": 1, "classe": "carrello", "posizione": (5.8, 3.9)},
        {"id": 2, "classe": "cane", "posizione": (1.5, 0.5)}
    ]
    test_message("CV/MODULE8", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "albero", "posizione": (3.0, 1.8)},
        {"id": 1, "classe": "libro", "posizione": (2.9, 1.7)},
        {"id": 2, "classe": "cane", "posizione": (2.1, 1.1)}
    ]
    test_message("CV/MODULE9", json.dumps(misure))

    misure = [
        {"id": 0, "classe": "cane", "posizione": (4.4, 3.0)},
        {"id": 1, "classe": "aereo", "posizione": (4.2, 2.8)},
        {"id": 2, "classe": "libro", "posizione": (3.5, 2.0)}
    ]
    test_message("CV/MODULE10", json.dumps(misure))

# Funziona ma fa la media delle posizizioni progressivamente e non tutta insieme.
def fusione_perfetta(data_by_class, distanzamax = 1.0):
    results = []
    for classe, objs in data_by_class.items():
        # Raggruppamento per sensore all'interno della classe.
        class_by_sensor = {}
        for obj in objs:
            class_by_sensor.setdefault(obj.get("module"), []).append(obj)
        
        # Caso in cui un entità è rilevata da un solo sensore.
        if len(class_by_sensor) == 1:
            assigned = []
            for id, objs in class_by_sensor.items():
                for obj in objs:
                    assigned.append({
                        "classe": classe,
                        "posizione": obj["posizione"]
                    })
            results.extend(assigned)
            continue

        sensor_ids = list(class_by_sensor.keys())
        base = class_by_sensor[sensor_ids[0]]
        
        fused = base
        for id in sensor_ids[1:]:
            current = class_by_sensor[id]

            # Calcolo distanze tra oggetti rilevati da sensori differenti.
            cost_matrix = np.zeros((len(fused), len(current)))
            for i, obj1 in enumerate(fused):
                for (j, obj2) in enumerate(current):
                    cost_matrix[i, j] = distanza(obj1["posizione"], obj2["posizione"])
            
            # Associazione di oggetti con le minori distanze.
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            # Oggetti associati o da associare.
            assigned = []
            # Oggetti attualmente associati con un proprio rispettivo in un altro sensore.
            currently_assigned = set()
            usati_fused = set()
            for i,j in zip(row_ind, col_ind):
                if cost_matrix[i,j] <= distanzamax:
                    o1, o2 = fused[i], current[j]
                    x_med = round((o1["posizione"][0] + o2["posizione"][0]) / 2, 3)
                    z_med = round((o1["posizione"][1] + o2["posizione"][1]) / 2, 3)
                    assigned.append({
                        "classe": classe,
                        "posizione": [x_med, z_med]
                    })
                    currently_assigned.add(j)
                    usati_fused.add(i)
                else:
                    assigned.append({
                        "classe": classe,
                        "posizione": fused[i]["posizione"]
                    })
                    assigned.append({
                        "classe":classe,
                        "posizione": current[j]["posizione"]
                    })
                    usati_fused.add(i)
                    currently_assigned.add(j)
            
            # Se ci sono oggetti rilevati, ma non associati con nessun rispettivo, vengono comunque mantenuti.
            for j, o2 in enumerate(current):
                if j not in currently_assigned:
                    assigned.append({
                        "classe": classe,
                        "posizione": o2["posizione"]
                    })
            
            for i, o1 in enumerate(fused):
                if i not in usati_fused:
                    assigned.append({
                        "classe": classe,
                        "posizione": o1["posizione"]
                    })
            fused = assigned
        
        results.extend(fused)

    print(f"Risultati fusione: {results}")
    return

def fusione_graph(data_by_class, max_dist = 1.0):
    fused_final = []

    for classe, items in data_by_class.items():
        # crea grafo
        G = nx.Graph()
        for i, r1 in enumerate(items):
            G.add_node(i, **r1)  # nodo con attributi
            for j, r2 in enumerate(items[i+1:], i+1):
                if r1["module"] != r2["module"]:  # evita auto-archi stesso sensore
                    if distanza(r1["posizione"], r2["posizione"]) <= max_dist:
                        G.add_edge(i, j)

        # trova componenti connesse
        for comp in nx.connected_components(G):
            posizioni = [G.nodes[n]["posizione"] for n in comp]
            #sensori = [G.nodes[n]["module"] for n in comp]
            x_media = round(sum(p[0] for p in posizioni) / len(posizioni), 3)
            y_media = round(sum(p[1] for p in posizioni) / len(posizioni), 3)

            fused_final.append({
                "classe": classe,
                "posizione": (x_media, y_media),
                #"origine_sensori": set(sensori)
            })
    
    print(f"Risultati fusione: {fused_final}")
    return
if __name__ == "__main__":
    insert_misure()
    data_by_class = {}
    for module_id, objs in modules_data.items():
        for obj in objs:
            data_by_class.setdefault(obj["classe"], []).append(obj)
    fusione_graph(data_by_class, 1.0)
    #fusione_perfetta(data_by_class, 1.0)
    # for classe, objs in data_by_class.items():
    #     print(f"{classe} --- {data_by_class[classe]}\n")