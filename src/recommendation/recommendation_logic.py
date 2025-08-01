# src/recommendation/recommendation_logic.py
import math
from src.recommendation.data_fetcher import get_cardinal_direction # Importa a função de data_fetcher

def calculate_suitability_score(forecast_entry, preferences):
    """
    Calculates a suitability score for a given forecast entry based on user/level preferences.
    Guarantees a score >= 0, applying penalties for unsuitable conditions.

    Args:
        forecast_entry (dict): Um dicionário contendo os dados de previsão para um timestamp.
        preferences (dict): Um dicionário contendo as preferências do surfista/nível para o spot.

    Returns:
        float: Um score de adequação (quanto maior, melhor).
               Retorna um score baixo (próximo de zero) se as condições são muito inadequadas,
               mas não zero, a menos que dados críticos estejam faltando completamente.
    """
    score = 50.0 # Score base arbitrário.
    # Definindo pesos e penalidades para maior controle
    WEIGHT_MAJOR = 30
    WEIGHT_MINOR = 15
    WEIGHT_TERTIARY = 10
    PENALTY_CRITICAL = 50 # Penalidade para condições que tornam o surfe impossível/perigoso
    PENALTY_HIGH = 20
    PENALTY_MEDIUM = 10
    PENALTY_LOW = 5
    PENALTY_VERY_LOW = 2 # Nova penalidade para pequenas desvantagens
    BONUS_IDEAL = 15 # Bônus por estar próximo ao ideal
    BONUS_GOOD = 5 # Bônus por estar na faixa aceitável
    BONUS_VERY_LOW = 2 # Novo bônus para pequenas vantagens

    # Função auxiliar para obter o valor da preferência e converter para float se necessário
    def get_pref_float(key):
        val = preferences.get(key)
        return float(val) if val is not None else None

    # NOVO: Função auxiliar para pontuar quando apenas o "ideal" é fornecido
    def score_proximity_to_single_ideal(current_value, ideal_val,
                                        ideal_bonus=BONUS_GOOD, medium_penalty=PENALTY_LOW, high_penalty=PENALTY_MEDIUM):
        if current_value is None or ideal_val is None:
            return 0
        current_value = float(current_value)
        ideal_val = float(ideal_val)

        # Dentro de uma margem aceitável do ideal (ex: +/- 10%)
        if ideal_val * 0.9 <= current_value <= ideal_val * 1.1:
            return ideal_bonus
        # Um pouco mais longe (ex: +/- 20%)
        elif ideal_val * 0.8 <= current_value <= ideal_val * 1.2:
            return -medium_penalty
        # Muito longe
        else:
            return -high_penalty


    # Função auxiliar para pontuar proximidade ao ideal (min, max, ideal)
    def score_proximity_to_range_ideal(current_value, min_val, max_val, ideal_val,
                                 ideal_bonus=BONUS_IDEAL, good_bonus=BONUS_GOOD,
                                 high_penalty=PENALTY_HIGH, medium_penalty=PENALTY_MEDIUM, very_low_penalty=PENALTY_VERY_LOW):
        if current_value is None:
            return 0

        current_value = float(current_value)

        # Prioriza o ideal_val se definido
        if ideal_val is not None:
            ideal_val = float(ideal_val)
            # Se MUITO próximo do ideal
            if ideal_val * 0.9 <= current_value <= ideal_val * 1.1:
                return ideal_bonus
            # Se dentro da faixa aceitável min/max (se existirem e forem válidos)
            elif min_val is not None and max_val is not None and float(min_val) <= current_value <= float(max_val):
                return good_bonus
            # Fora da faixa min/max, mas não muito
            elif (min_val is not None and current_value < float(min_val)) or \
                 (max_val is not None and current_value > float(max_val)):
                return -medium_penalty
            # Muito fora da faixa min/max ou muito longe do ideal (se min/max não definidos)
            elif (min_val is not None and current_value < float(min_val) * 0.8) or \
                 (max_val is not None and current_value > float(max_val) * 1.2) or \
                 (min_val is None and max_val is None and (current_value < ideal_val * 0.8 or current_value > ideal_val * 1.2)):
                return -high_penalty
            else: # Está fora do ideal, mas não atinge nenhuma penalidade severa
                return -very_low_penalty
        # Se NÃO há ideal, mas há min/max
        elif min_val is not None and max_val is not None:
            min_val = float(min_val)
            max_val = float(max_val)
            if min_val <= current_value <= max_val:
                return good_bonus
            elif current_value < min_val * 0.8 or current_value > max_val * 1.2:
                return -high_penalty
            elif current_value < min_val or current_value > max_val:
                return -medium_penalty
        return 0 # Nenhuma preferência definida para o parâmetro

    # Condições críticas: se dados básicos estão faltando, o score é 0 pois não há como avaliar.
    if forecast_entry.get('waveHeight_sg') is None:
        return 0.0 # Se não há altura de onda, não há surfe.

    # --- 1. Onda Principal (waveHeight_sg, waveDirection_sg, wavePeriod_sg) ---
    wave_height = forecast_entry.get('waveHeight_sg')
    wave_direction = forecast_entry.get('waveDirection_sg')
    wave_period = forecast_entry.get('wavePeriod_sg')

    # Preferências de altura da onda
    min_wh = get_pref_float('min_wave_height')
    max_wh = get_pref_float('max_wave_height')
    ideal_wh = get_pref_float('ideal_wave_height')
    score += score_proximity_to_range_ideal(wave_height, min_wh, max_wh, ideal_wh, ideal_bonus=WEIGHT_MAJOR, good_bonus=BONUS_GOOD, high_penalty=PENALTY_CRITICAL)

    # Preferências de período da onda - AGORA COM MIN/MAX/IDEAL
    min_wp = get_pref_float('min_wave_period')
    max_wp = get_pref_float('max_wave_period')
    ideal_wp = get_pref_float('ideal_wave_period')
    score += score_proximity_to_range_ideal(wave_period, min_wp, max_wp, ideal_wp, ideal_bonus=BONUS_GOOD, high_penalty=PENALTY_HIGH)

    # Preferências de direção da onda
    preferred_wave_directions_str = preferences.get('preferred_wave_direction')
    if wave_direction is not None and preferred_wave_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_wave_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(wave_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # --- 2. Swell Principal (swellHeight_sg, swellDirection_sg, swellPeriod_sg) ---
    swell_height = forecast_entry.get('swellHeight_sg')
    swell_direction = forecast_entry.get('swellDirection_sg')
    swell_period = forecast_entry.get('swellPeriod_sg')

    # Preferências de altura do swell
    min_sh = get_pref_float('min_swell_height')
    max_sh = get_pref_float('max_swell_height')
    ideal_sh = get_pref_float('ideal_swell_height')
    score += score_proximity_to_range_ideal(swell_height, min_sh, max_sh, ideal_sh, ideal_bonus=WEIGHT_MAJOR, high_penalty=PENALTY_CRITICAL)

    # Preferências de direção do swell
    preferred_swell_directions_str = preferences.get('preferred_swell_direction')
    if swell_direction is not None and preferred_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(swell_direction)
        if current_cardinal_direction in preferred_dirs:
            score += WEIGHT_MAJOR # Mais peso para swell primário
        else:
            score -= PENALTY_HIGH

    # Preferências de período do swell
    min_sp = get_pref_float('min_swell_period')
    max_sp = get_pref_float('max_swell_period')
    ideal_sp = get_pref_float('ideal_swell_period')
    score += score_proximity_to_range_ideal(swell_period, min_sp, max_sp, ideal_sp, ideal_bonus=BONUS_IDEAL, high_penalty=PENALTY_HIGH)

    # --- 3. Swell Secundário (secondarySwellHeight_sg, secondarySwellDirection_sg, secondarySwellPeriod_sg) ---
    secondary_swell_height = forecast_entry.get('secondarySwellHeight_sg')
    secondary_swell_direction = forecast_entry.get('secondarySwellDirection_sg')
    secondary_swell_period = forecast_entry.get('secondarySwellPeriod_sg')

    # Preferências de altura do swell secundário - AGORA SÓ IDEAL
    ideal_ssh = get_pref_float('ideal_secondary_swell_height')
    score += score_proximity_to_single_ideal(secondary_swell_height, ideal_ssh, ideal_bonus=BONUS_VERY_LOW)

    # Preferências de direção do swell secundário
    preferred_secondary_swell_directions_str = preferences.get('preferred_secondary_swell_direction')
    if secondary_swell_direction is not None and preferred_secondary_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_secondary_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(secondary_swell_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_VERY_LOW # Bônus pequeno
        else:
            score -= PENALTY_VERY_LOW # Penalidade muito leve

    # Preferências de período do swell secundário - AGORA SÓ IDEAL
    ideal_ssp = get_pref_float('ideal_secondary_swell_period')
    score += score_proximity_to_single_ideal(secondary_swell_period, ideal_ssp, ideal_bonus=BONUS_VERY_LOW)


    # --- 4. Vento (windSpeed_sg, windDirection_sg) ---
    wind_speed = forecast_entry.get('windSpeed_sg')
    wind_direction = forecast_entry.get('windDirection_sg')

    # Preferências de velocidade do vento - AGORA COM MIN/MAX/IDEAL
    min_ws = get_pref_float('min_wind_speed')
    max_ws = get_pref_float('max_wind_speed')
    ideal_ws = get_pref_float('ideal_wind_speed')
    # Para vento, geralmente o ideal é baixo, então o min_val pode ser 0 ou muito pequeno
    score += score_proximity_to_range_ideal(wind_speed, min_ws, max_ws, ideal_ws,
                                     ideal_bonus=WEIGHT_MINOR, good_bonus=BONUS_GOOD,
                                     high_penalty=PENALTY_HIGH, medium_penalty=PENALTY_MEDIUM)

    preferred_wind_directions_str = preferences.get('preferred_wind_direction')
    if wind_speed is not None and preferred_wind_directions_str: # Só importa a direção se houver preferência
        preferred_dirs = [d.strip().upper() for d in preferred_wind_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(wind_direction)
        if current_cardinal_direction in preferred_dirs:
            score += WEIGHT_MINOR # Bônus para direção de vento ideal (terral ou fraco lateral)
        else:
            score -= PENALTY_MEDIUM # Penalidade se a direção não for a preferida, mas o vento for aceitável


    # --- 5. Maré (current_tide_phase no forecast_entry & sea_level_sg) ---
    ideal_tide_type = preferences.get('ideal_tide_type')
    current_tide_phase = forecast_entry.get('current_tide_phase')
    if ideal_tide_type and current_tide_phase and current_tide_phase != 'unknown':
        preferred_tides = [t.strip().lower() for t in ideal_tide_type.split(',')]
        if current_tide_phase.lower() in preferred_tides:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # Preferência de Nível do Mar (quantificado) - AGORA COM MIN/MAX/IDEAL
    sea_level = forecast_entry.get('seaLevel_sg')
    min_sl = get_pref_float('min_sea_level')
    max_sl = get_pref_float('max_sea_level')
    ideal_sl = get_pref_float('ideal_sea_level')
    score += score_proximity_to_range_ideal(sea_level, min_sl, max_sl, ideal_sl, ideal_bonus=BONUS_GOOD)


    # --- 6. Temperaturas (water_temperature_sg, air_temperature_sg) ---
    water_temperature = forecast_entry.get('waterTemperature_sg')
    air_temperature = forecast_entry.get('airTemperature_sg')

    # Temperatura da Água - AGORA SÓ IDEAL
    ideal_wt = get_pref_float('ideal_water_temperature')
    score += score_proximity_to_single_ideal(water_temperature, ideal_wt, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)

    # Temperatura do Ar - AGORA SÓ IDEAL
    ideal_at = get_pref_float('ideal_air_temperature')
    score += score_proximity_to_single_ideal(air_temperature, ideal_at, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)


    # --- 7. Correntes (current_speed_sg, current_direction_sg) ---
    current_speed = forecast_entry.get('currentSpeed_sg')
    current_direction = forecast_entry.get('currentDirection_sg')

    # Velocidade da Corrente - AGORA SÓ IDEAL
    ideal_cs = get_pref_float('ideal_current_speed')
    score += score_proximity_to_single_ideal(current_speed, ideal_cs, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)

    preferred_current_directions_str = preferences.get('preferred_current_direction')
    if current_direction is not None and preferred_current_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_current_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(current_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_VERY_LOW # Bônus pequeno
        else:
            score -= PENALTY_VERY_LOW # Penalidade muito leve


    # Garantir que o score mínimo seja 0, mesmo após penalidades
    return max(0.0, score)