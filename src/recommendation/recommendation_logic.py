import math
from src.recommendation.data_fetcher import get_cardinal_direction

def calculate_suitability_score(forecast_entry, spot_preferences, spot, tide_phase, user):
    """
    Calculates a suitability score for a given forecast entry at a specific spot,
    considering user preferences, spot characteristics, and tide conditions.

    Args:
        forecast_entry (dict): Dictionary containing detailed forecast data for a specific hour.
                               (e.g., 'wave_height_sg', 'sea_level_sg').
        spot_preferences (dict): Dictionary of preferences for the specific spot,
                                 either user-defined or model-generated/level-based.
                                 (e.g., 'min_wave_height', 'ideal_tide_type').
        spot (dict): Dictionary containing the spot's characteristics (e.g., bottom_type, coast_orientation).
        tide_phase (str): The calculated tide phase ('low', 'high', 'rising', 'falling').
                          Passado diretamente, não precisa ser extraído de forecast_entry.
        user (dict): Dictionary containing user profile information (e.g., surf_level, goofy_regular_stance).

    Returns:
        float: A suitability score (higher is better).
               Returns a low score (close to zero) if conditions are very unsuitable,
               but not zero unless critical data is completely missing.
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
    # As chaves de spot_preferences devem vir já em snake_case do banco de dados (get_spot_preferences)
    def get_pref_float(key):
        val = spot_preferences.get(key) # Agora usa spot_preferences
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


    # Onda (Wave)
    # As chaves agora são snake_case
    wave_height = forecast_entry.get('wave_height_sg')
    min_wh = get_pref_float('min_wave_height')
    max_wh = get_pref_float('max_wave_height')
    ideal_wh = get_pref_float('ideal_wave_height')
    score += score_proximity_to_range_ideal(wave_height, min_wh, max_wh, ideal_wh) * WEIGHT_MAJOR

    wave_period = forecast_entry.get('wave_period_sg')
    min_wp = get_pref_float('min_wave_period')
    max_wp = get_pref_float('max_wave_period')
    ideal_wp = get_pref_float('ideal_wave_period')
    score += score_proximity_to_range_ideal(wave_period, min_wp, max_wp, ideal_wp) * WEIGHT_MINOR

    wave_direction = forecast_entry.get('wave_direction_sg')
    pref_wd = spot_preferences.get('preferred_wave_direction') # Usando spot_preferences
    if wave_direction is not None and pref_wd is not None:
        current_cardinal_wd = get_cardinal_direction(wave_direction)
        if current_cardinal_wd == pref_wd:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW


    # Ondulação Primária (Swell)
    swell_height = forecast_entry.get('swell_height_sg')
    min_sh = get_pref_float('min_swell_height')
    max_sh = get_pref_float('max_swell_height')
    ideal_sh = get_pref_float('ideal_swell_height')
    score += score_proximity_to_range_ideal(swell_height, min_sh, max_sh, ideal_sh) * WEIGHT_MAJOR

    swell_period = forecast_entry.get('swell_period_sg')
    min_sp = get_pref_float('min_swell_period')
    max_sp = get_pref_float('max_swell_period')
    ideal_sp = get_pref_float('ideal_swell_period')
    score += score_proximity_to_range_ideal(swell_period, min_sp, max_sp, ideal_sp) * WEIGHT_MINOR

    swell_direction = forecast_entry.get('swell_direction_sg')
    pref_sd = spot_preferences.get('preferred_swell_direction') # Usando spot_preferences
    if swell_direction is not None and pref_sd is not None:
        current_cardinal_sd = get_cardinal_direction(swell_direction)
        if current_cardinal_sd == pref_sd:
            score += BONUS_GOOD
        else:
            score -= PENALTY_LOW

    # Ondulação Secundária (Secondary Swell) - Apenas Ideal
    secondary_swell_height = forecast_entry.get('secondary_swell_height_sg')
    ideal_ssh = get_pref_float('ideal_secondary_swell_height')
    score += score_proximity_to_single_ideal(secondary_swell_height, ideal_ssh) * WEIGHT_TERTIARY

    secondary_swell_period = forecast_entry.get('secondary_swell_period_sg')
    ideal_ssp = get_pref_float('ideal_secondary_swell_period')
    score += score_proximity_to_single_ideal(secondary_swell_period, ideal_ssp) * WEIGHT_TERTIARY

    secondary_swell_direction = forecast_entry.get('secondary_swell_direction_sg')
    pref_ssd = spot_preferences.get('preferred_secondary_swell_direction') # Usando spot_preferences
    if secondary_swell_direction is not None and pref_ssd is not None:
        current_cardinal_ssd = get_cardinal_direction(secondary_swell_direction)
        if current_cardinal_ssd == pref_ssd:
            score += BONUS_VERY_LOW
        else:
            score -= PENALTY_VERY_LOW


    # Vento (Wind)
    wind_speed = forecast_entry.get('wind_speed_sg')
    min_ws = get_pref_float('min_wind_speed')
    max_ws = get_pref_float('max_wind_speed')
    ideal_ws = get_pref_float('ideal_wind_speed')
    score += score_proximity_to_range_ideal(wind_speed, min_ws, max_ws, ideal_ws) * WEIGHT_MAJOR # Vento é crítico

    wind_direction = forecast_entry.get('wind_direction_sg')
    pref_wd_wind = spot_preferences.get('preferred_wind_direction') # Usando spot_preferences
    if wind_direction is not None and pref_wd_wind is not None:
        current_cardinal_wd_wind = get_cardinal_direction(wind_direction)
        # Prefere vento "offshore" ou "cross-offshore" para a maioria dos picos.
        # Isso pode ser mais complexo, dependendo da orientação do spot.
        # Por simplicidade, vamos verificar se a direção preferida corresponde.
        if current_cardinal_wd_wind == pref_wd_wind:
            score += BONUS_GOOD
        else:
            score -= PENALTY_HIGH # Vento ruim penaliza bastante


    # Maré (Tide)
    # 'tide_phase' já está a ser passado como um argumento separado, não precisa de ser extraído de forecast_entry
    ideal_tide_type = spot_preferences.get('ideal_tide_type') # Usando spot_preferences
    if tide_phase and ideal_tide_type: # Agora usa tide_phase diretamente
        if tide_phase.lower() == ideal_tide_type.lower():
            score += BONUS_GOOD
        elif tide_phase.lower() in ["low", "high"] and ideal_tide_type.lower() in ["rising", "falling"]:
            score -= PENALTY_LOW # Pequena penalidade se é um extremo quando prefere movimento
        else:
            score -= PENALTY_MEDIUM # Penalidade se a maré é totalmente diferente do ideal

    sea_level = forecast_entry.get('sea_level_sg')
    min_sl = get_pref_float('min_sea_level')
    max_sl = get_pref_float('max_sea_level')
    ideal_sl = get_pref_float('ideal_sea_level')
    score += score_proximity_to_range_ideal(sea_level, min_sl, max_sl, ideal_sl) * WEIGHT_MINOR

    # Temperatura da Água e do Ar
    water_temperature = forecast_entry.get('water_temperature_sg')
    ideal_wt = get_pref_float('ideal_water_temperature')
    score += score_proximity_to_single_ideal(water_temperature, ideal_wt) * WEIGHT_TERTIARY

    air_temperature = forecast_entry.get('air_temperature_sg')
    ideal_at = get_pref_float('ideal_air_temperature')
    score += score_proximity_to_single_ideal(air_temperature, ideal_at) * WEIGHT_TERTIARY

    # Corrente (Current)
    current_speed = forecast_entry.get('current_speed_sg')
    ideal_cs = get_pref_float('ideal_current_speed')
    score += score_proximity_to_single_ideal(current_speed, ideal_cs) * WEIGHT_TERTIARY

    current_direction = forecast_entry.get('current_direction_sg')
    pref_cd = spot_preferences.get('preferred_current_direction') # Usando spot_preferences
    if current_direction is not None and pref_cd is not None:
        current_cardinal_cd = get_cardinal_direction(current_direction)
        if current_cardinal_cd == pref_cd:
            score += BONUS_VERY_LOW
        else:
            score -= PENALTY_VERY_LOW

    # Nível do Utilizador (User Level)
    # `user` é um argumento agora, e `spot` também pode ter características relevantes
    user_surf_level = user.get('surf_level')
    spot_bottom_type = spot.get('bottom_type')
    spot_coast_orientation = spot.get('coast_orientation')

    # Exemplo: Penalizar se o nível do utilizador for "iniciante" e as ondas forem muito grandes,
    # mesmo que as preferências do spot permitam ondas grandes (o que é improvável, mas para ilustrar)
    if user_surf_level == 'beginner' and wave_height is not None and wave_height > 2.0: # Exemplo de threshold
        score -= PENALTY_HIGH # Penalidade extra para iniciantes em ondas grandes

    # Garante que o score não seja negativo
    final_score = max(0, score)
    
    # Você pode adicionar um dicionário 'detailed_scores' aqui, se quiser um breakdown
    # por exemplo: detailed_scores = {'wave_height': wave_height_score, 'wind': wind_score, ...}
    # Por enquanto, retorna apenas o score final, mas a função em recommendation_routes.py espera 2 retornos.
    # Vamos adicionar um placeholder para detailed_scores para evitar erros futuros.
    detailed_scores = {
        "wave_height_score": score_proximity_to_range_ideal(wave_height, min_wh, max_wh, ideal_wh),
        "swell_direction_score": BONUS_GOOD if current_cardinal_sd == pref_sd else -PENALTY_LOW,
        "wind_score": BONUS_GOOD if current_cardinal_wd_wind == pref_wd_wind else -PENALTY_HIGH,
        "tide_score": BONUS_GOOD if tide_phase == ideal_tide_type else -PENALTY_MEDIUM,
        # Adicione mais conforme a sua lógica de detalhamento
    }


    return final_score, detailed_scores