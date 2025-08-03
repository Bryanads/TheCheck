# src/recommendation/data_fetcher.py
import datetime
import arrow # Para lidar com timestamps

def determine_tide_phase(current_time_utc, current_sea_level, tide_extremes):
    """
    Determina a fase da maré (low, high, rising, falling, mid, unknown) para um determinado ponto no tempo
    e nível do mar, com base nos extremos de maré (altas e baixas) do dia.

    Args:
        current_time_utc (datetime.datetime): O timestamp UTC atual para o qual determinar a fase.
        current_sea_level (float): O nível do mar atual (altura da maré em metros) para o current_time_utc.
        tide_extremes (list of dict): Uma lista de dicionários, cada um representando um extremo de maré
                                      do dia, com chaves 'timestampUtc', 'tideType' ('low' ou 'high') e 'height'.
                                      Esses dados já vêm em camelCase do queries.py.

    Returns:
        str: A fase da maré (low, high, rising, falling, mid, unknown).
    """
    if not tide_extremes or current_sea_level is None:
        return "unknown"

    # Garante que os extremos de maré estejam ordenados por timestampUtc
    # CORREÇÃO AQUI: Acessa 'timestampUtc' (camelCase)
    tide_extremes.sort(key=lambda x: x['timestampUtc'])

    # Encontra o extremo de maré anterior e o próximo ao current_time_utc
    prev_extreme = None
    next_extreme = None

    for i, extreme in enumerate(tide_extremes):
        # CORREÇÃO AQUI: Acessa 'timestampUtc' (camelCase)
        extreme_time_utc = extreme['timestampUtc']

        if extreme_time_utc <= current_time_utc:
            prev_extreme = extreme
        elif extreme_time_utc > current_time_utc:
            next_extreme = extreme
            break

    # Se estamos exatamente em um extremo
    if prev_extreme and prev_extreme['timestampUtc'] == current_time_utc:
        # CORREÇÃO AQUI: Acessa 'tideType' (camelCase)
        return prev_extreme['tideType']

    # Se não há extremo anterior ou próximo, não podemos determinar
    if not prev_extreme or not next_extreme:
        return "unknown" # Ou "mid" se houver apenas um extremo antes ou depois, mas não ambos

    # CORREÇÃO AQUI: Acessa 'tideType' e 'height' (camelCase)
    prev_type = prev_extreme['tideType']
    prev_height = prev_extreme['height']
    next_type = next_extreme['tideType']
    next_height = next_extreme['height']

    # Determina se a maré está subindo ou descendo
    if prev_type == 'low' and next_type == 'high':
        # Maré subindo
        if current_sea_level > prev_height and current_sea_level < next_height:
            return "rising"
        elif current_sea_level <= prev_height: # Caso esteja muito próximo do low anterior
            return "low"
        elif current_sea_level >= next_height: # Caso esteja muito próximo do high seguinte
            return "high"
        else: # Pode ser erro ou dado inconsistente
            return "unknown"
    elif prev_type == 'high' and next_type == 'low':
        # Maré descendo
        if current_sea_level < prev_height and current_sea_level > next_height:
            return "falling"
        elif current_sea_level >= prev_height: # Caso esteja muito próximo do high anterior
            return "high"
        elif current_sea_level <= next_height: # Caso esteja muito próximo do low seguinte
            return "low"
        else: # Pode ser erro ou dado inconsistente
            return "unknown"
    
    # Se chegamos aqui, é um cenário inesperado ou a maré está no meio entre dois extremos do mesmo tipo
    # (o que não deveria acontecer se os extremos forem Low e High alternados).
    # Ou se for um ponto exato onde a maré está estável ou em transição.
    # Por segurança, podemos classificar como "mid" se estiver entre dois extremos válidos, mas sem direção clara.
    return "mid"

def get_cardinal_direction(degrees):
    """Converts degrees to cardinal direction (e.g., 180 -> 'S')."""
    if degrees is None: return None
    # Adjusting ranges slightly to ensure no gaps and full coverage
    if (degrees >= 337.5 and degrees <= 360) or (degrees >= 0 and degrees < 22.5): return 'N'
    if 22.5 <= degrees < 67.5: return 'NE'
    if 67.5 <= degrees < 112.5: return 'E'
    if 112.5 <= degrees < 157.5: return 'SE'
    if 157.5 <= degrees < 202.5: return 'S'
    if 202.5 <= degrees < 247.5: return 'SW'
    if 247.5 <= degrees < 292.5: return 'W'
    if 292.5 <= degrees < 337.5: return 'NW'
    return None