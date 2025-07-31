import math

def calculate_suitability_score(forecast_entry, preferences):
    """
    Calculates a suitability score for a given forecast entry based on user/level preferences.
    Guarantees a score >= 0, applying penalties for unsuitable conditions.

    Args:
        forecast_entry (dict): Um dicionário contendo os dados de previsão para um timestamp,
                               extraídos do StormGlass (ex: waveHeight_sg, swellDirection_sg, etc.).
        preferences (dict): Um dicionário contendo as preferências do surfista/nível para o spot,
                            obtido de level_spot_preferences ou user_spot_preferences.

    Returns:
        float: Um score de adequação (quanto maior, melhor).
               Retorna um score baixo (próximo de zero) se as condições são muito inadequadas,
               mas não zero, a menos que dados críticos estejam faltando completamente.
    """
    # Inicia com um score base positivo para garantir que sempre haverá um score.
    # Penalidades serão subtraídas deste valor.
    score = 50.0 # Score base arbitrário. Ajuste conforme a granularidade desejada.
    PENALTY_HIGH = 20
    PENALTY_MEDIUM = 10
    PENALTY_LOW = 5
    PENALTY_VERY_LOW = 2


    # Condições críticas: se dados básicos estão faltando, o score é 0 pois não há como avaliar.
    if forecast_entry.get('waveHeight_sg') is None:
        return 0.0 # Se não há altura de onda, não há surfe.

    # 1. Altura da Onda (waveHeight_sg)
    wave_height = forecast_entry.get('waveHeight_sg')
    # >>> ALTERAÇÃO AQUI: Converter para float se não for None <<<
    min_wh = float(preferences.get('min_wave_height')) if preferences.get('min_wave_height') is not None else None
    max_wh = float(preferences.get('max_wave_height')) if preferences.get('max_wave_height') is not None else None


    if min_wh is not None and max_wh is not None:
        if min_wh <= wave_height <= max_wh:
            score += 30 # Grande bônus para onda ideal
        elif wave_height < min_wh * 0.8 or wave_height > max_wh * 1.2: # Muito fora da faixa
            score -= PENALTY_HIGH # Penalidade severa
        elif wave_height < min_wh or wave_height > max_wh: # Fora da faixa ideal, mas aceitável
            score -= PENALTY_MEDIUM # Penalidade média
    elif wave_height is not None: # Se não há preferências de altura, não penaliza mas também não bonifica muito
        score += 5 # Bônus pequeno por ter onda, mas sem critério claro


    # 2. Direção do Swell (swellDirection_sg)
    swell_direction = forecast_entry.get('swellDirection_sg')
    preferred_swell_directions_str = preferences.get('preferred_swell_direction')
    if swell_direction is not None and preferred_swell_directions_str:
        preferred_dirs = [d.strip().upper() for d in preferred_swell_directions_str.split(',')]
        current_cardinal_direction = get_cardinal_direction(swell_direction)

        if current_cardinal_direction in preferred_dirs:
            score += 15 # Bônus para direção ideal
        elif current_cardinal_direction is not None and any(d in current_cardinal_direction for d in preferred_dirs):
            score += 5 # Bônus menor para direção próxima
        else:
            score -= PENALTY_LOW # Penalidade se a direção não for a preferida


    # 3. Período do Swell (swellPeriod_sg)
    swell_period = forecast_entry.get('swellPeriod_sg')
    # >>> ALTERAÇÃO AQUI: Converter para float se não for None <<<
    min_sp = float(preferences.get('min_swell_period')) if preferences.get('min_swell_period') is not None else None
    max_sp = float(preferences.get('max_swell_period')) if preferences.get('max_swell_period') is not None else None


    if min_sp is not None and max_sp is not None and swell_period is not None:
        if min_sp <= swell_period <= max_sp:
            score += 10 # Bônus para período ideal
        elif swell_period < min_sp * 0.9 or swell_period > max_sp * 1.1:
            score -= PENALTY_MEDIUM # Penalidade se muito fora do período ideal
        elif swell_period < min_sp or swell_period > max_sp:
            score -= PENALTY_LOW # Penalidade leve


    # 4. Velocidade e Direção do Vento (windSpeed_sg, windDirection_sg)
    wind_speed = forecast_entry.get('windSpeed_sg')
    # >>> ALTERAÇÃO AQUI: Converter para float se não for None <<<
    max_ws = float(preferences.get('max_wind_speed')) if preferences.get('max_wind_speed') is not None else None
    preferred_wind_directions_str = preferences.get('preferred_wind_direction')

    if wind_speed is not None and max_ws is not None:
        if wind_speed <= max_ws * 0.5: # Vento muito fraco (ideal para muitos)
            score += 10
        elif wind_speed <= max_ws: # Vento aceitável
            score += 5
        else: # Vento acima do máximo preferido
            score -= PENALTY_HIGH # Penalidade severa por vento forte demais

        if preferred_wind_directions_str and wind_speed <= max_ws: # Só importa a direção se o vento for aceitável
            preferred_dirs = [d.strip().upper() for d in preferred_wind_directions_str.split(',')]
            current_cardinal_direction = get_cardinal_direction(forecast_entry.get('windDirection_sg'))

            if current_cardinal_direction in preferred_dirs:
                score += 10 # Bônus para direção de vento ideal (terral ou fraco lateral)
            else:
                score -= PENALTY_LOW # Penalidade se a direção não for a preferida, mas o vento for aceitável
    elif wind_speed is not None: # Se não há preferência de vento, mas há vento
        if wind_speed <= 10: # Vento fraco é geralmente bom
            score += 5
        elif wind_speed > 25: # Vento muito forte é geralmente ruim
            score -= PENALTY_MEDIUM


    # 5. Maré (current_tide_phase no forecast_entry)
    ideal_tide_type = preferences.get('ideal_tide_type')
    current_tide_phase = forecast_entry.get('current_tide_phase') # Assumindo que esta é preenchida antes da chamada
    if ideal_tide_type and current_tide_phase and current_tide_phase != 'unknown':
        preferred_tides = [t.strip().lower() for t in ideal_tide_type.split(',')]
        if current_tide_phase.lower() in preferred_tides:
            score += 10 # Bônus para maré ideal
        else:
            score -= PENALTY_LOW # Penalidade leve se a maré não for a preferida


    # Garantir que o score mínimo seja 0, mesmo após penalidades
    return max(0.0, score)


# Função auxiliar para mapear direções (pode ser movida para src/utils/helpers.py se for usada em outros lugares)
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