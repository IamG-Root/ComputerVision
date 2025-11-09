
import numpy as np
from munkres import Munkres

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def group_by_class(entities):
    data_by_class = {}
    for module_id, content in entities.items():
        for obj in content["entities"]:
            data_by_class.setdefault(obj["class"], []).append(obj)
    return data_by_class

def group_by_module(objs):
    class_by_sensor = {}
    for obj in objs:
        class_by_sensor.setdefault(obj["module"], []).append(obj)
    return class_by_sensor

def square_matrix(rows, cols):
    dim = max(rows, cols)
    matrix = np.zeros((dim, dim))
    return matrix

def calculate_matches(rows, cols):
    hungarian = Munkres()
    # Inizializzazione della matrice dei costi con eventuale padding per far si che sia quadrata.
    cost_matrix = square_matrix(len(rows), len(cols))
    # Inserimento costi nella matrice.
    for i, obj_row in enumerate(rows):
        for j, obj_col in enumerate(cols):
            cost_matrix[i, j] = distance(obj_row["position"], obj_col["position"])
    indexes = hungarian.compute(cost_matrix)
    return indexes

def mean_position(pos1, pos2):
    x_med = (pos1[0] + pos2[0]) / 2
    z_med = (pos1[1] + pos2[1]) / 2
    return((round(x_med, 2), round(z_med, 2)))