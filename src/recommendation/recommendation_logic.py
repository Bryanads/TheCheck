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

    # Função auxiliar para pontuar proximidade ao ideal
    # (Adicionei flexibilidade para bônus/penalidades customizadas por chamada)
    def score_proximity_to_ideal(current_value, min_val, max_val, ideal_val,
                                 ideal_bonus=BONUS_IDEAL, good_bonus=BONUS_GOOD,
                                 high_penalty=PENALTY_HIGH, medium_penalty=PENALTY_MEDIUM):
        if current_value is None:
            return 0

        current_value = float(current_value) # Garante que o valor da previsão é float

        # Se há um ideal definido
        if ideal_val is not None:
            ideal_val = float(ideal_val)
            # Verifica se está MUITO próximo do ideal
            if ideal_val * 0.9 <= current_value <= ideal_val * 1.1:
                return ideal_bonus
            # Verifica se está dentro da faixa MIN/MAX (se definida)
            elif min_val is not None and max_val is not None and float(min_val) <= current_value <= float(max_val):
                return good_bonus
            # Verifica se está MUITO fora da faixa (com margem de erro)
            elif (min_val is not None and current_value < float(min_val) * 0.8) or \
                 (max_val is not None and current_value > float(max_val) * 1.2):
                return -high_penalty
            # Verifica se está fora da faixa MIN/MAX, mas não muito
            elif (min_val is not None and current_value < float(min_val)) or \
                 (max_val is not None and current_value > float(max_val)):
                return -medium_penalty
            else: # Se não há min/max mas há ideal, e está longe dele
                # Penaliza se estiver muito longe do ideal e sem faixa definida
                if current_value < ideal_val * 0.8 or current_value > ideal_val * 1.2:
                    return -medium_penalty
        # Se não há ideal, mas há min/max
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
    score += score_proximity_to_ideal(wave_height, min_wh, max_wh, ideal_wh)

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
    score += score_proximity_to_ideal(swell_height, min_sh, max_sh, ideal_sh)

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
    score += score_proximity_to_ideal(swell_period, min_sp, max_sp, ideal_sp)

    # --- 3. Swell Secundário (secondarySwellHeight_sg, secondarySwellDirection_sg, secondarySwellPeriod_sg) ---
    secondary_swell_height = forecast_entry.get('secondarySwellHeight_sg')
    secondary_swell_direction = forecast_entry.get('secondarySwellDirection_sg')
    secondary_swell_period = forecast_entry.get('secondarySwellPeriod_sg')

    # Preferências de altura do swell secundário (geralmente menos impactante, mas pode ajudar ou atrapalhar)
    min_ssh = get_pref_float('min_secondary_swell_height')
    max_ssh = get_pref_float('max_secondary_swell_height')
    if secondary_swell_height is not None:
        score += score_proximity_to_ideal(secondary_swell_height, min_ssh, max_ssh, None, # Sem ideal específico, só min/max
                                         ideal_bonus=0, good_bonus=BONUS_GOOD, # Bônus menor
                                         high_penalty=PENALTY_LOW, medium_penalty=PENALTY_VERY_LOW)


    # Preferências de direção do swell secundário
    preferred_secondary_swell_directions_str = preferences.get('preferred_secondary_swell_direction')
    if secondary_swell_direction is not None and preferred_secondary_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_secondary_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(secondary_swell_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_VERY_LOW # Bônus pequeno
        else:
            score -= PENALTY_VERY_LOW # Penalidade muito leve

    # Preferências de período do swell secundário (geralmente menos impactante)
    min_ssp = get_pref_float('min_secondary_swell_period')
    max_ssp = get_pref_float('max_secondary_swell_period')
    if secondary_swell_period is not None:
        score += score_proximity_to_ideal(secondary_swell_period, min_ssp, max_ssp, None,
                                         ideal_bonus=0, good_bonus=BONUS_VERY_LOW,
                                         high_penalty=PENALTY_VERY_LOW, medium_penalty=PENALTY_VERY_LOW)

    # --- 4. Vento (windSpeed_sg, windDirection_sg) ---
    wind_speed = forecast_entry.get('windSpeed_sg')
    wind_direction = forecast_entry.get('windDirection_sg')

    max_ws = get_pref_float('max_wind_speed')
    ideal_ws = get_pref_float('ideal_wind_speed')
    # Para vento, geralmente o ideal é baixo, então o min_val pode ser 0 ou muito pequeno
    score += score_proximity_to_ideal(wind_speed, 0, max_ws, ideal_ws, # Min wind speed is generally 0 or very low
                                     ideal_bonus=WEIGHT_MINOR, good_bonus=BONUS_GOOD,
                                     high_penalty=PENALTY_HIGH, medium_penalty=PENALTY_MEDIUM)

    preferred_wind_directions_str = preferences.get('preferred_wind_direction')
    if wind_speed is not None and preferred_wind_directions_str and max_ws is not None and wind_speed <= max_ws: # Só importa a direção se o vento for aceitável
        preferred_dirs = [d.strip().upper() for d in preferred_wind_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(wind_direction)
        if current_cardinal_direction in preferred_dirs:
            score += WEIGHT_MINOR # Bônus para direção de vento ideal (terral ou fraco lateral)
        else:
            score -= PENALTY_MEDIUM # Penalidade se a direção não for a preferida, mas o vento for aceitável
    elif wind_speed is not None and max_ws is not None and wind_speed > max_ws: # Se o vento está acima do máximo preferido, penaliza
        score -= PENALTY_HIGH


    # --- 5. Maré (current_tide_phase no forecast_entry & sea_level_sg) ---
    ideal_tide_type = preferences.get('ideal_tide_type')
    current_tide_phase = forecast_entry.get('current_tide_phase')
    if ideal_tide_type and current_tide_phase and current_tide_phase != 'unknown':
        preferred_tides = [t.strip().lower() for t in ideal_tide_type.split(',')]
        if current_tide_phase.lower() in preferred_tides:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # Preferência de Nível do Mar (quantificado)
    sea_level = forecast_entry.get('seaLevel_sg')
    min_sl = get_pref_float('min_sea_level')
    max_sl = get_pref_float('max_sea_level')
    ideal_sl = get_pref_float('ideal_sea_level')
    score += score_proximity_to_ideal(sea_level, min_sl, max_sl, ideal_sl)


    # --- 6. Temperaturas (water_temperature_sg, air_temperature_sg) ---
    water_temperature = forecast_entry.get('waterTemperature_sg')
    air_temperature = forecast_entry.get('airTemperature_sg')

    # Temperatura da Água
    min_wt = get_pref_float('min_water_temperature')
    max_wt = get_pref_float('max_water_temperature')
    ideal_wt = get_pref_float('ideal_water_temperature')
    score += score_proximity_to_ideal(water_temperature, min_wt, max_wt, ideal_wt,
                                     ideal_bonus=BONUS_GOOD, good_bonus=BONUS_VERY_LOW,
                                     high_penalty=PENALTY_MEDIUM, medium_penalty=PENALTY_LOW) # Menos peso para temperatura

    # Temperatura do Ar
    min_at = get_pref_float('min_air_temperature')
    max_at = get_pref_float('max_air_temperature')
    ideal_at = get_pref_float('ideal_air_temperature')
    score += score_proximity_to_ideal(air_temperature, min_at, max_at, ideal_at,
                                     ideal_bonus=BONUS_GOOD, good_bonus=BONUS_VERY_LOW,
                                     high_penalty=PENALTY_MEDIUM, medium_penalty=PENALTY_LOW) # Menos peso para temperatura


    # --- 7. Correntes (current_speed_sg, current_direction_sg) ---
    current_speed = forecast_entry.get('currentSpeed_sg')
    current_direction = forecast_entry.get('currentDirection_sg')

    max_cs = get_pref_float('max_current_speed')
    if current_speed is not None and max_cs is not None:
        if current_speed <= max_cs * 0.5: # Corrente fraca é ideal
            score += BONUS_VERY_LOW
        elif current_speed <= max_cs: # Corrente aceitável
            pass # Sem bônus, sem penalidade
        else: # Corrente acima do máximo preferido
            score -= PENALTY_LOW # Penalidade leve por corrente forte

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