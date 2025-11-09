import numpy as np
import config as cfg

ray_origin = (0.0, cfg.CAMERA_H, 0.0)

def relative_to_absolute_position(wx, wz):
    if cfg.ORIENTATION == 1:
        return (round(wx + cfg.CAMERA_POS_X, 3), round(wz + cfg.CAMERA_POS_Z, 3))
    elif cfg.ORIENTATION == 2:
        return (round(wz + cfg.CAMERA_POS_X, 3), round((-wx) + cfg.CAMERA_POS_Z, 3))
    elif cfg.ORIENTATION == 3:
        return (round((-wx) + cfg.CAMERA_POS_X, 3), round((-wz) + cfg.CAMERA_POS_Z, 3))
    elif cfg.ORIENTATION == 4:
        return (round((-wz) + cfg.CAMERA_POS_X, 3), round(wx + cfg.CAMERA_POS_Z, 3))
    else:
        return (0,0)

def absolute_to_relative_position(ax, az):
    if cfg.ORIENTATION == 1:
        return (round(ax - cfg.CAMERA_POS_X, 3), round(az - cfg.CAMERA_POS_Z, 3))
    elif cfg.ORIENTATION == 2:
        return (round(- (az - cfg.CAMERA_POS_Z), 3), round(ax - cfg.CAMERA_POS_X, 3))
    elif cfg.ORIENTATION == 3:
        return (round(- (ax - cfg.CAMERA_POS_X), 3), round(- (az - cfg.CAMERA_POS_Z), 3))
    elif cfg.ORIENTATION == 4:
        return (round(az - cfg.CAMERA_POS_Z, 3), round(- (ax - cfg.CAMERA_POS_X), 3))
    else:
        return (0, 0)

def _pixel_to_direction(x, y, res_x, res_y, fov_h_deg, fov_v_deg):
    fov_h = np.radians(fov_h_deg)
    fov_v = np.radians(fov_v_deg)
    
    nx = (x - res_x / 2) / (res_x / 2)
    ny = (y - res_y / 2) / (res_y / 2)
    
    theta_x = nx * (fov_h / 2)
    theta_y = ny * (fov_v / 2)

    dir_cam = np.array([
        np.tan(theta_x),         # X Axis
        -np.tan(theta_y),        # Y Axis (-1 = down)
        1.0                      # Z Axis forward
    ])
    return dir_cam / np.linalg.norm(dir_cam)

def _rotate_vector(v, pitch_deg):
    # Rotation on X (pitch)
    pitch = np.radians(pitch_deg)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch),  np.cos(pitch)],
    ])
    return Rx @ v

def _intersect_with_floor(ray_origin, ray_dir):
    # Horizontal plane intersection y = 0 (floor)
    if ray_dir[1] == 0:
        return np.array([np.nan, np.nan, np.nan])
    t = -ray_origin[1] / ray_dir[1]
    if t < 0:
        return np.array([np.nan, np.nan, np.nan])
    return ray_origin + t * ray_dir

# Converts pixel point to camera-relative world point
def pixel_to_world(x, y):
    dir_cam = _pixel_to_direction(x, y, cfg.FRAME_RES_X, cfg.FRAME_RES_Y, cfg.FOV_H_DEG, cfg.FOV_V_DEG)
    dir_world = _rotate_vector(dir_cam, cfg.CAMERA_PITCH_DEG)
    point_on_floor = _intersect_with_floor(ray_origin, dir_world)
    world_x = point_on_floor[0]
    world_z = point_on_floor[2]
    #dist_from_camera = np.sqrt(world_x**2 + world_z**2)
    return world_x, world_z#, dist_from_camera

def _norm(v):
    n = np.linalg.norm(v)
    return v/n if n > 0 else v

def _Rx(deg):
    r = np.radians(deg)
    return np.array([
        [1, 0,            0           ],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r),  np.cos(r)],
    ])

def rotate_vector_world_to_cam(v_world, pitch_deg):
    # Inversa: mondo -> camera (applica -pitch)
    return _Rx(-cfg.CAMERA_PITCH_DEG) @ v_world

# Converts camera-relative world point to pixel
def world_to_pixel(X, Z):
    # Direzione dal centro camera al punto
    p_world = np.array([X, 0.0, Z])
    dir_world = p_world - ray_origin
    if np.linalg.norm(dir_world) == 0:
        return np.nan, np.nan, False

    # Porta nel sistema camera (inversa della rotazione di pitch)
    dir_cam = rotate_vector_world_to_cam(_norm(dir_world), cfg.CAMERA_PITCH_DEG)

    # Se z_cam <= 0 il punto è dietro il piano immagine → non visibile
    if dir_cam[2] <= 0:
        return np.nan, np.nan, False

    # Angoli rispetto all'asse ottico (coerenti con la convenzione usata)
    theta_x = np.arctan2(dir_cam[0], dir_cam[2])     # x vs z
    theta_y = np.arctan2(-dir_cam[1], dir_cam[2])    # -y vs z (per coerenza col segno usato prima)

    # Normalizza sugli FOV
    fov_h = np.radians(cfg.FOV_H_DEG)
    fov_v = np.radians(cfg.FOV_V_DEG)
    nx = theta_x / (fov_h/2)
    ny = theta_y / (fov_v/2)

    # Mappa a pixel
    x_px = (nx * (cfg.FRAME_RES_X/2)) + (cfg.FRAME_RES_X/2)
    y_px = (ny * (cfg.FRAME_RES_Y/2)) + (cfg.FRAME_RES_Y/2)

    return int(x_px), int(y_px)