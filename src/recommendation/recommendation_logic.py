import numpy as np

from src.recommendation.wind_score import calcular_score_vento
from src.recommendation.tide_score import calcular_score_mare
from src.recommendation.current_score import calcular_score_corrente
from src.recommendation.temperature_score import (
    calcular_score_temperatura_agua,
    calcular_score_temperatura_ar
)
from src.recommendation.wave_score import (
    calcular_score_direcao_onda,
    calcular_score_periodo_onda,
    calcular_score_tamanho_onda,
    calcular_impacto_swell_secundario
)
from src.utils.utils import cardinal_to_degrees

def calculate_suitability_score(forecast_entry, spot_preferences, spot_info, tide_phase, user_info):
    """
    Calcula um score de adequação geral para o surf com base nas previsões e preferências.

    Args:
        forecast_entry (dict): Dados de previsão para um determinado timestamp.
        spot_preferences (dict): Preferências de surf para o spot (do usuário ou padrão).
        spot_info (dict): Informações estáticas sobre o spot (tipo de fundo, orientação, etc.).
        tide_phase (str): Fase da maré determinada ('enchente', 'vazante', 'pico_alta', 'pico_baixa').
        user_info (dict): Informações do usuário (nível de surf, etc.).

    Returns:
        tuple: Um tuple contendo:
            - float: O score de adequação geral (0 a 1).
            - dict: Um dicionário com os scores detalhados de cada critério.
    """

    detailed_scores = {}

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Scores Onda------------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    #------------------------------------SCORE TAMANHO ONDA------------------------------------
    swell_height_sg = float(forecast_entry.get('swell_height_sg', 0.0))
    wave_height_sg = float(forecast_entry.get('wave_height_sg', 0.0))
    previsao_onda_tamanho = swell_height_sg * 0.6 + wave_height_sg * 0.4 # Peso 60% swell, 40% wave

    tamanho_minimo = float(spot_preferences.get('min_wave_height')) # Converter para float
    tamanho_ideal = float(spot_preferences.get('ideal_wave_height')) # Converter para float
    tamanho_maximo = float(spot_preferences.get('max_wave_height')) # Converter para float

    score_tamanho = 0.0

    if all(v is not None for v in [previsao_onda_tamanho, tamanho_minimo, tamanho_ideal, tamanho_maximo]):
        score_tamanho_result = calcular_score_tamanho_onda(
            previsao_onda_tamanho,
            tamanho_minimo,
            tamanho_ideal,
            tamanho_maximo
        )
        score_tamanho = float(score_tamanho_result.item()) if isinstance(score_tamanho_result, np.ndarray) else float(score_tamanho_result)
    detailed_scores['wave_height_score'] = score_tamanho


    #------------------------------------SCORE DIREÇÃO SWELL------------------------------------
    previsao_onda_direcao = float(forecast_entry.get('swell_direction_sg', 0.0)) # Direção do swell principal em graus

    ideal_swell_direction_cardinal = spot_preferences.get('preferred_swell_direction')
    direcao_ideal = cardinal_to_degrees(ideal_swell_direction_cardinal)
    
    if direcao_ideal is None:
        print(f"Aviso: Direção ideal do swell '{ideal_swell_direction_cardinal}' não reconhecida, usando 0.0 graus como default.")
        direcao_ideal = 0.0 


    score_direcao = 0.0

    if direcao_ideal is not None: # Verifica se direcao_ideal é um número válido (não None)
        score_direcao_result = calcular_score_direcao_onda(
            previsao_onda_direcao,
            direcao_ideal
        )
        score_direcao = float(score_direcao_result.item()) if isinstance(score_direcao_result, np.ndarray) else float(score_direcao_result)
    detailed_scores['swell_direction_score'] = score_direcao

    #------------------------------------SCORE PERIODO ONDA------------------------------------
    previsao_onda_periodo = forecast_entry.get('swell_period_sg') # Usamos swell_period_sg como o período principal
    periodo_ideal = float(spot_preferences.get('ideal_swell_period', 8.0)) # Converter para float

    score_periodo = 0.0

    if previsao_onda_periodo is not None and periodo_ideal is not None:
        score_periodo_result = calcular_score_periodo_onda(
            previsao_onda_periodo,
            periodo_ideal
        )
        score_periodo = float(score_periodo_result.item()) if isinstance(score_periodo_result, np.ndarray) else float(score_periodo_result)
    detailed_scores['swell_period_score'] = score_periodo

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Score Vento------------------------------------------
    -----------------------------------------------------------------------------------------------
    """

    wind_speed = forecast_entry.get('wind_speed_sg')
    wind_dir = forecast_entry.get('wind_direction_sg')
    preferred_wind_dir = float(spot_preferences.get('ideal_wind_direction', 0.0)) # Converter para float
    ideal_wind_speed = float(spot_preferences.get('ideal_wind_speed', 5.0)) # Converter para float
    max_wind_speed = float(spot_preferences.get('max_wind_speed', 20.0)) # Converter para float

    score_vento = 0.0

    if all(v is not None for v in [wind_speed, wind_dir, preferred_wind_dir, ideal_wind_speed, max_wind_speed]):
        score_vento_result = calcular_score_vento(
            wind_speed,
            wind_dir,
            preferred_wind_dir,
            ideal_wind_speed,
            max_wind_speed
        )
        score_vento = float(score_vento_result.item()) if isinstance(score_vento_result, np.ndarray) else float(score_vento_result)
    detailed_scores['wind_score'] = score_vento

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Score Maré------------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    previsao_mare = forecast_entry.get('sea_level_sg') # Altura da maré
    mare_ideal = float(spot_preferences.get('ideal_tide_height', 0.0)) # Converter para float
    mare_tipo_ideal = spot_preferences.get('ideal_tide_type') # 'qualquer', 'enchente', 'vazante', etc.

    score_mare = 0.0

    if all(v is not None for v in [previsao_mare, mare_ideal, tide_phase, mare_tipo_ideal]):
        score_mare_result = calcular_score_mare(
            previsao_mare,
            mare_ideal,
            tide_phase, # A fase da maré atual para comparação
            mare_tipo_ideal
        )
        score_mare = float(score_mare_result.item()) if isinstance(score_mare_result, np.ndarray) else float(score_mare_result)
    detailed_scores['tide_score'] = score_mare

    """
    -----------------------------------------------------------------------------------------------
    ---------------------------------------Scores Temperatura---------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    #------------------------------------SCORE TEMPERATURA ÁGUA------------------------------------
    water_temp = forecast_entry.get('water_temperature_sg')
    ideal_water_temp = float(spot_preferences.get('ideal_water_temperature', 22.0)) # Converter para float

    score_temperatura_agua = 0.0
    
    if water_temp is not None and ideal_water_temp is not None:
        score_temperatura_agua_result = calcular_score_temperatura_agua(
            water_temp,
            ideal_water_temp
        )
        score_temperatura_agua = float(score_temperatura_agua_result.item()) if isinstance(score_temperatura_agua_result, np.ndarray) else float(score_temperatura_agua_result)
    detailed_scores['water_temperature_score'] = score_temperatura_agua

    #------------------------------------SCORE TEMPERATURA AR------------------------------------
    air_temp = forecast_entry.get('air_temperature_sg')
    ideal_air_temp = float(spot_preferences.get('ideal_air_temperature', 25.0)) # Converter para float

    score_temperatura_ar = 0.0

    if air_temp is not None and ideal_air_temp is not None:
        score_temperatura_ar_result = calcular_score_temperatura_ar(
            air_temp,
            ideal_air_temp
        )
        score_temperatura_ar = float(score_temperatura_ar_result.item()) if isinstance(score_temperatura_ar_result, np.ndarray) else float(score_temperatura_ar_result)
    detailed_scores['air_temperature_score'] = score_temperatura_ar

    """
    -----------------------------------------------------------------------------------------------
    -----------------------------------------Scores Corrente-----------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    current_speed = forecast_entry.get('current_speed_sg')
    # O spot_preferences pode ter 'ideal_current_speed', mas um default de 0.0 é razoável
    ideal_current_speed = float(spot_preferences.get('ideal_current_speed', 0.0))

    score_corrente = 0.0

    if current_speed is not None and ideal_current_speed is not None:
        score_corrente_result = calcular_score_corrente(
            current_speed,
            ideal_current_speed
        )
        score_corrente = float(score_corrente_result.item()) if isinstance(score_corrente_result, np.ndarray) else float(score_corrente_result)
    detailed_scores['current_score'] = score_corrente

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------Scores impacto Swell Secundário----------------------------------
    -----------------------------------------------------------------------------------------------
    """
    # Converter para float, com default para 0.0 se não existir
    previsao_swell_secundario_tamanho = float(forecast_entry.get('secondary_swell_height_sg', 0.0))
    previsao_swell_secundario_periodo = float(forecast_entry.get('secondary_swell_period_sg', 0.0))
    previsao_swell_secundario_direcao = float(forecast_entry.get('secondary_swell_direction_sg', 0.0))

    # Reutiliza os dados do swell principal para comparação, convertendo para float
    previsao_onda_tamanho_principal = previsao_onda_tamanho
    previsao_onda_periodo_principal = previsao_onda_periodo
    previsao_onda_direcao_principal = previsao_onda_direcao

    impacto_swell_secundario = 0.0 

    if all(v is not None for v in [previsao_onda_tamanho, previsao_onda_periodo, previsao_onda_direcao]):
        # Estes são placeholders; assuma que eles vêm do seu forecast_entry
        sec_swell_height = float(forecast_entry.get('secondary_swell_height_sg', 0.0))
        sec_swell_period = float(forecast_entry.get('secondary_swell_period_sg', 0.0))
        sec_swell_direction = float(forecast_entry.get('secondary_swell_direction_sg', 0.0))

        impacto_swell_secundario_result = calcular_impacto_swell_secundario(
            sec_swell_height,
            sec_swell_period,
            sec_swell_direction,
            previsao_onda_tamanho,
            previsao_onda_periodo,
            previsao_onda_direcao
        )
        impacto_swell_secundario = float(impacto_swell_secundario_result.item()) if isinstance(impacto_swell_secundario_result, np.ndarray) else float(impacto_swell_secundario_result)
    detailed_scores['secondary_swell_impact'] = impacto_swell_secundario
    


    """
    -----------------------------------------------------------------------------------------------
    ---------------------------------------Cálculo Final-------------------------------------------
    -----------------------------------------------------------------------------------------------
    """

    FATOR_AJUSTE_ONDA_SWELL_SECUNDARIO = 0.10

    for score_key in ['wave_height_score', 'swell_direction_score', 'swell_period_score']:
        ajuste_percentual = 1 - FATOR_AJUSTE_ONDA_SWELL_SECUNDARIO
        detailed_scores[score_key] = detailed_scores[score_key] * ajuste_percentual
        detailed_scores[score_key] += detailed_scores['secondary_swell_impact'] * FATOR_AJUSTE_ONDA_SWELL_SECUNDARIO
        detailed_scores[score_key] = np.round(detailed_scores[score_key], 2)


    weights = {
        'wave_height_score': 0.29,
        'swell_direction_score': 0.10,
        'swell_period_score': 0.10,
        'wind_score': 0.29,
        'tide_score': 0.10,
        'water_temperature_score': 0.05,
        'air_temperature_score': 0.05,
        'current_score': 0.02 
    }

    # Calcula o score total ponderado
    weighted_sum = 0.0
    total_weights = 0.0

    for criterion, score in detailed_scores.items():
        if criterion in weights: # Verifica se o critério tem um peso definido para o cálculo final
            weighted_sum += score * weights[criterion]
            total_weights += weights[criterion]
            
    final_suitability_score = 0.0
    if total_weights > 0:
        final_suitability_score = weighted_sum / total_weights
    
    # Garante que o score final esteja dentro do intervalo [0, 1] antes de escalar para 0-100
    final_suitability_score = np.clip(final_suitability_score, 0.0, 100.0)

    final_suitability_score = np.round(final_suitability_score, 2)  # Arredonda para duas casas decimais
    
    return float(final_suitability_score), detailed_scores
