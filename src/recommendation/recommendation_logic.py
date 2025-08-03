# src/recommendation/recommendation_logic.py
import math
# Garanta que get_cardinal_direction está disponível e esperando graus decimais
from src.recommendation.data_fetcher import get_cardinal_direction 

def calculate_suitability_score(forecast_entry, preferences):
    """
    Calculates a suitability score for a given forecast entry based on user/level preferences.
    Guarantees a score >= 0, applying penalties for unsuitable conditions.

    Args:
        forecast_entry (dict): Um dicionário contendo os dados de previsão para um timestamp,
                               com chaves em camelCase (ex: 'waveHeight', 'seaLevel').
        preferences (dict): Um dicionário contendo as preferências do surfista/nível para o spot,
                            com chaves em camelCase (ex: 'minWaveHeight', 'idealTideType').

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
    # As chaves de preferências devem vir já em camelCase do banco de dados (get_spot_preferences)
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
            # Se MUITO próximo do ideal (dentro de 10%)
            if ideal_val * 0.9 <= current_value <= ideal_val * 1.1:
                return ideal_bonus
            # Se dentro da faixa aceitável min/max (se existirem e forem válidos)
            elif min_val is not None and max_val is not None and float(min_val) <= current_value <= float(max_val):
                return good_bonus
            # Fora da faixa min/max, mas não muito (dentro de 20% do min/max ou ideal)
            elif (min_val is not None and current_value < float(min_val) * 0.8) or \
                 (max_val is not None and current_value > float(max_val) * 1.2) or \
                 (min_val is None and max_val is None and (current_value < ideal_val * 0.8 or current_value > ideal_val * 1.2)):
                return -high_penalty
            elif (min_val is not None and current_value < float(min_val)) or \
                 (max_val is not None and current_value > float(max_val)) or \
                 (min_val is None and max_val is None and (current_value < ideal_val or current_value > ideal_val)):
                return -medium_penalty
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
    # Usando 'waveHeight' (camelCase)
    if forecast_entry.get('waveHeight') is None:
        return 0.0 # Se não há altura de onda, não há surfe.

    # --- 1. Onda Principal (waveHeight, waveDirection, wavePeriod) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    wave_height = forecast_entry.get('waveHeight')
    wave_direction = forecast_entry.get('waveDirection')
    wave_period = forecast_entry.get('wavePeriod')

    # Preferências de altura da onda (minWaveHeight, maxWaveHeight, idealWaveHeight)
    min_wh = get_pref_float('minWaveHeight')
    max_wh = get_pref_float('maxWaveHeight')
    ideal_wh = get_pref_float('idealWaveHeight')
    score += score_proximity_to_range_ideal(wave_height, min_wh, max_wh, ideal_wh, ideal_bonus=WEIGHT_MAJOR, good_bonus=BONUS_GOOD, high_penalty=PENALTY_CRITICAL)

    # Preferências de período da onda (minWavePeriod, maxWavePeriod, idealWavePeriod)
    min_wp = get_pref_float('minWavePeriod')
    max_wp = get_pref_float('maxWavePeriod')
    ideal_wp = get_pref_float('idealWavePeriod')
    score += score_proximity_to_range_ideal(wave_period, min_wp, max_wp, ideal_wp, ideal_bonus=BONUS_GOOD, high_penalty=PENALTY_HIGH)

    # Preferências de direção da onda (preferredWaveDirection)
    preferred_wave_directions_str = preferences.get('preferredWaveDirection')
    if wave_direction is not None and preferred_wave_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_wave_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(wave_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # --- 2. Swell Principal (swellHeight, swellDirection, swellPeriod) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    swell_height = forecast_entry.get('swellHeight')
    swell_direction = forecast_entry.get('swellDirection')
    swell_period = forecast_entry.get('swellPeriod')

    # Preferências de altura do swell (minSwellHeight, maxSwellHeight, idealSwellHeight)
    min_sh = get_pref_float('minSwellHeight')
    max_sh = get_pref_float('maxSwellHeight')
    ideal_sh = get_pref_float('idealSwellHeight')
    score += score_proximity_to_range_ideal(swell_height, min_sh, max_sh, ideal_sh, ideal_bonus=WEIGHT_MAJOR, high_penalty=PENALTY_CRITICAL)

    # Preferências de direção do swell (preferredSwellDirection)
    preferred_swell_directions_str = preferences.get('preferredSwellDirection')
    if swell_direction is not None and preferred_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(swell_direction)
        if current_cardinal_direction in preferred_dirs:
            score += WEIGHT_MAJOR # Mais peso para swell primário
        else:
            score -= PENALTY_HIGH

    # Preferências de período do swell (minSwellPeriod, maxSwellPeriod, idealSwellPeriod)
    min_sp = get_pref_float('minSwellPeriod')
    max_sp = get_pref_float('maxSwellPeriod')
    ideal_sp = get_pref_float('idealSwellPeriod')
    score += score_proximity_to_range_ideal(swell_period, min_sp, max_sp, ideal_sp, ideal_bonus=BONUS_IDEAL, high_penalty=PENALTY_HIGH)

    # --- 3. Swell Secundário (secondarySwellHeight, secondarySwellDirection, secondarySwellPeriod) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    secondary_swell_height = forecast_entry.get('secondarySwellHeight')
    secondary_swell_direction = forecast_entry.get('secondarySwellDirection')
    secondary_swell_period = forecast_entry.get('secondarySwellPeriod')

    # Preferências de altura do swell secundário (idealSecondarySwellHeight)
    ideal_ssh = get_pref_float('idealSecondarySwellHeight')
    score += score_proximity_to_single_ideal(secondary_swell_height, ideal_ssh, ideal_bonus=BONUS_VERY_LOW)

    # Preferências de direção do swell secundário (preferredSecondarySwellDirection)
    preferred_secondary_swell_directions_str = preferences.get('preferredSecondarySwellDirection')
    if secondary_swell_direction is not None and preferred_secondary_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_secondary_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(secondary_swell_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_VERY_LOW # Bônus pequeno
        else:
            score -= PENALTY_VERY_LOW # Penalidade muito leve

    # Preferências de período do swell secundário (idealSecondarySwellPeriod)
    ideal_ssp = get_pref_float('idealSecondarySwellPeriod')
    score += score_proximity_to_single_ideal(secondary_swell_period, ideal_ssp, ideal_bonus=BONUS_VERY_LOW)


    # --- 4. Vento (windSpeed, windDirection) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    wind_speed = forecast_entry.get('windSpeed')
    wind_direction = forecast_entry.get('windDirection')

    # Preferências de velocidade do vento (minWindSpeed, maxWindSpeed, idealWindSpeed)
    min_ws = get_pref_float('minWindSpeed')
    max_ws = get_pref_float('maxWindSpeed')
    ideal_ws = get_pref_float('idealWindSpeed')
    # Para vento, geralmente o ideal é baixo, então o min_val pode ser 0 ou muito pequeno
    score += score_proximity_to_range_ideal(wind_speed, min_ws, max_ws, ideal_ws,
                                         ideal_bonus=WEIGHT_MINOR, good_bonus=BONUS_GOOD,
                                         high_penalty=PENALTY_HIGH, medium_penalty=PENALTY_MEDIUM)

    # Preferências de direção do vento (preferredWindDirection)
    preferred_wind_directions_str = preferences.get('preferredWindDirection')
    if wind_speed is not None and preferred_wind_directions_str: # Só importa a direção se houver preferência
        preferred_dirs = [d.strip().upper() for d in preferred_wind_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(wind_direction)
        if current_cardinal_direction in preferred_dirs:
            score += WEIGHT_MINOR # Bônus para direção de vento ideal (terral ou fraco lateral)
        else:
            score -= PENALTY_MEDIUM # Penalidade se a direção não for a preferida, mas o vento for aceitável


    # --- 5. Maré (currentTidePhase & seaLevel) ---
    # Acessando chaves em camelCase
    ideal_tide_type = preferences.get('idealTideType') # idealTideType (camelCase)
    current_tide_phase = forecast_entry.get('currentTidePhase') # currentTidePhase (camelCase)
    if ideal_tide_type and current_tide_phase and current_tide_phase != 'unknown':
        preferred_tides = [t.strip().lower() for t in ideal_tide_type.split(',')]
        if current_tide_phase.lower() in preferred_tides:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # Preferência de Nível do Mar (quantificado) (minSeaLevel, maxSeaLevel, idealSeaLevel)
    # Acessando 'seaLevel' (camelCase)
    sea_level = forecast_entry.get('seaLevel') 
    min_sl = get_pref_float('minSeaLevel')
    max_sl = get_pref_float('maxSeaLevel')
    ideal_sl = get_pref_float('idealSeaLevel')
    score += score_proximity_to_range_ideal(sea_level, min_sl, max_sl, ideal_sl, ideal_bonus=BONUS_GOOD)


    # --- 6. Temperaturas (waterTemperature, airTemperature) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    water_temperature = forecast_entry.get('waterTemperature')
    air_temperature = forecast_entry.get('airTemperature')

    # Temperatura da Água (idealWaterTemperature)
    ideal_wt = get_pref_float('idealWaterTemperature')
    score += score_proximity_to_single_ideal(water_temperature, ideal_wt, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)

    # Temperatura do Ar (idealAirTemperature)
    ideal_at = get_pref_float('idealAirTemperature')
    score += score_proximity_to_single_ideal(air_temperature, ideal_at, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)


    # --- 7. Correntes (currentSpeed, currentDirection) ---
    # Acessando chaves em camelCase, removendo sufixo '_sg'
    current_speed = forecast_entry.get('currentSpeed')
    current_direction = forecast_entry.get('currentDirection')

    # Velocidade da Corrente (idealCurrentSpeed)
    ideal_cs = get_pref_float('idealCurrentSpeed')
    score += score_proximity_to_single_ideal(current_speed, ideal_cs, ideal_bonus=BONUS_VERY_LOW, medium_penalty=PENALTY_LOW)

    # Direção da Corrente (preferredCurrentDirection)
    preferred_current_directions_str = preferences.get('preferredCurrentDirection')
    if current_direction is not None and preferred_current_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_current_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(current_direction)
        if current_cardinal_direction in preferred_dirs:
            score += BONUS_VERY_LOW # Bônus pequeno
        else:
            score -= PENALTY_VERY_LOW # Penalidade muito leve


    # Garantir que o score mínimo seja 0, mesmo após penalidades
    return max(0.0, score)