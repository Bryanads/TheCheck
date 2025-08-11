import numpy as np

def calcular_score_vento(
    wind_speed,
    wind_dir,
    preferred_wind_dir,
    ideal_wind=6.0,
    max_wind=20.0
):
    DIRECTION_BONUS_WEIGHT = 0.4

    wind_speed = np.asarray(wind_speed, dtype=float)
    wind_dir = np.asarray(wind_dir, dtype=float)
    preferred_wind_dir = np.asarray(preferred_wind_dir, dtype=float)

    wind_speed, wind_dir, preferred_wind_dir = np.broadcast_arrays(
        wind_speed, wind_dir, preferred_wind_dir
    )

    score = np.zeros_like(wind_speed, dtype=float)
    mask_allowed = wind_speed < max_wind
    if not np.any(mask_allowed):
        return score

    fator_escala = 3.0  # controla suavidade da queda
    baseline = 1 - np.tanh((wind_speed / max_wind) * fator_escala)
    baseline = np.clip(baseline, 0, 1)
    score[mask_allowed] = baseline[mask_allowed]

    # Alinhamento direcional (cosseno)
    angle_diff = np.abs(wind_dir - preferred_wind_dir) % 360
    angle_diff = np.minimum(angle_diff, 360 - angle_diff)
    dir_align = np.cos(np.radians(angle_diff))
    dir_align = np.clip(dir_align, 0, 1)

    # Fator velocidade para bônus, suavizado com tanh
    speed_ratio = np.minimum(wind_speed / ideal_wind, 1.0)
    bonus_speed_factor = np.tanh(speed_ratio * fator_escala)

    direction_bonus = dir_align * bonus_speed_factor * DIRECTION_BONUS_WEIGHT
    score[mask_allowed] = np.clip(score[mask_allowed] + direction_bonus[mask_allowed], 0, 1)

    return score