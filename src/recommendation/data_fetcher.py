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
                                      do dia, com chaves 'timestamp_utc', 'tide_type' ('low' ou 'high') e 'height'
                                      (agora em snake_case).

    Returns:
        str: A fase da maré (low, high, rising, falling, mid, unknown).
    """
    if not tide_extremes or current_sea_level is None:
        return "unknown"

    # Garante que os extremos de maré estejam ordenados por timestamp_utc (snake_case)
    tide_extremes.sort(key=lambda x: x['timestamp_utc'])

    # Encontra o extremo de maré anterior e o próximo ao current_time_utc
    prev_extreme = None
    next_extreme = None

    for i, extreme in enumerate(tide_extremes):
        extreme_time_utc = extreme['timestamp_utc'] # Acessa 'timestamp_utc' (snake_case)
        if extreme_time_utc <= current_time_utc:
            prev_extreme = extreme
        else:
            next_extreme = extreme
            break

    if prev_extreme is None and next_extreme is None:
        return "unknown"
    elif prev_extreme is None: # current_time_utc é anterior ao primeiro extremo do dia
        # Se o primeiro extremo é uma maré baixa, a maré está subindo (ou está baixa no início do dia)
        # Se o primeiro extremo é uma maré alta, a maré está caindo (ou está alta no início do dia)
        if next_extreme['tide_type'] == 'low':
            return "falling" # Assumindo que estava alta antes e está caindo para a baixa
        else: # next_extreme['tide_type'] == 'high'
            return "rising" # Assumindo que estava baixa antes e está subindo para a alta
    elif next_extreme is None: # current_time_utc é posterior ao último extremo do dia
        # Se o último extremo foi uma maré baixa, a maré está subindo
        # Se o último extremo foi uma maré alta, a maré está caindo
        if prev_extreme['tide_type'] == 'low':
            return "rising" # Assumindo que estava baixa e está subindo
        else: # prev_extreme['tide_type'] == 'high'
            return "falling" # Assumindo que estava alta e está caindo
    else:
        # Ambos os extremos existem, e o current_time_utc está entre eles
        prev_type = prev_extreme['tide_type']
        next_type = next_extreme['tide_type']

        if prev_type == 'low' and next_type == 'high':
            return "rising"
        elif prev_type == 'high' and next_type == 'low':
            return "falling"
        # Casos onde o tipo se repete (e.g., high -> high, low -> low, o que não deveria acontecer se os extremos fossem apenas high/low)
        # Isso pode indicar que o current_time_utc está muito próximo de um extremo.
        elif prev_type == 'low' and next_type == 'low':
             # Se o nível atual é próximo ao nível de prev_extreme, é "low". Caso contrário, "rising" para a próxima maré alta (fora do escopo dos extremos fornecidos)
            if abs(current_sea_level - prev_extreme['height']) < 0.1: # Margem de erro de 10cm
                return "low"
            else:
                return "rising" # Assumindo que está subindo após a maré baixa anterior
        elif prev_type == 'high' and next_type == 'high':
            # Similarmente, se o nível atual é próximo ao nível de prev_extreme, é "high". Caso contrário, "falling"
            if abs(current_sea_level - prev_extreme['height']) < 0.1:
                return "high"
            else:
                return "falling" # Assumindo que está caindo após a maré alta anterior

    # Para os próprios extremos ou muito próximo a eles
    if prev_extreme and abs(current_time_utc - prev_extreme['timestamp_utc']).total_seconds() < 3600: # Dentro de 1 hora do extremo anterior
        return prev_extreme['tide_type']
    if next_extreme and abs(current_time_utc - next_extreme['timestamp_utc']).total_seconds() < 3600: # Dentro de 1 hora do próximo extremo
        return next_extreme['tide_type']

    # Se não for rising/falling/low/high, assume-se "mid"
    return "mid"


def get_cardinal_direction(degrees):
    """
    Converte graus decimais (0-360) para uma direção cardeal (N, NE, E, SE, S, SW, W, NW).
    """
    if degrees is None:
        return "N/A" # Ou algum outro valor padrão

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    # Adiciona 22.5 para centralizar os ranges: N de 337.5 a 22.5, NE de 22.5 a 67.5, etc.
    index = round((degrees % 360) / 45) % 8
    return directions[index]