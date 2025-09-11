import numpy as np
import config as cfg

ray_origin = (0.0, cfg.CAMERA_H, 0.0)

def calculate_position(wx, wz):
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

# Converts pixel point to world point
def pixel_to_world(x, y):
    dir_cam = _pixel_to_direction(x, y, cfg.FRAME_RES_X, cfg.FRAME_RES_Y, cfg.FOV_H_DEG, cfg.FOV_V_DEG)
    dir_world = _rotate_vector(dir_cam, cfg.CAMERA_PITCH_DEG)
    point_on_floor = _intersect_with_floor(ray_origin, dir_world)
    world_x = point_on_floor[0]
    world_z = point_on_floor[2]
    dist_from_camera = np.sqrt(world_x**2 + world_z**2)
    return world_x, world_z, dist_from_camera
