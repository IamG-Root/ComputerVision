import numpy as np

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

# Raggruppamento entità per classe.
def group_by_class(entities):
    data_by_class = {}
    for module_id, objs in entities.items():
        for obj in objs:
            data_by_class.setdefault(obj["class"], []).append(obj)
    return data_by_class

# Raggruppamento entità per sensore all'interno di una classe.
def group_by_module(objs):
    class_by_sensor = {}
    for obj in objs:
        class_by_sensor.setdefault(obj["module"], []).append(obj)
    return class_by_sensor

def square_matrix(rows, cols):
    dim = max(rows, cols)
    matrix = np.zeros((dim, dim))
    return matrix

def mean_position(pos1, pos2):
    x_med = (pos1[0] + pos2[0]) / 2
    z_med = (pos1[1] + pos2[1]) / 2
    return((x_med, z_med))

def progress_id(id, MAX):
    return id+1 if id < MAX else 0