import numpy as np

from src.recommendation.wind_score import calcular_score_vento
from src.recommendation.tide_score import calcular_score_mare
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

    # --- 1. Score de Onda Principal ---
    # Tamanho da Onda
    previsao_onda_tamanho = forecast_entry.get('wave_height_sg')
    tamanho_minimo = float(spot_preferences.get('min_wave_height', 0.0)) # Converter para float
    tamanho_ideal = float(spot_preferences.get('ideal_wave_height', 1.0)) # Converter para float
    tamanho_maximo = float(spot_preferences.get('max_wave_height', 3.0)) # Converter para float

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

    # Direção da Onda/Swell Principal
    previsao_onda_direcao = forecast_entry.get('swell_direction_sg') # Usamos swell_direction_sg como a direção principal
    direcao_ideal = float(spot_preferences.get('ideal_swell_direction', 0.0)) # Converter para float

    score_direcao = 0.0
    if previsao_onda_direcao is not None and direcao_ideal is not None:
        score_direcao_result = calcular_score_direcao_onda(
            previsao_onda_direcao,
            direcao_ideal
        )
        score_direcao = float(score_direcao_result.item()) if isinstance(score_direcao_result, np.ndarray) else float(score_direcao_result)
    detailed_scores['swell_direction_score'] = score_direcao

    # Período da Onda/Swell Principal
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

    # --- 2. Score de Vento ---
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

    # --- 3. Score de Maré ---
    previsao_mare = forecast_entry.get('sea_level_sg') # Altura da maré
    mare_ideal = float(spot_preferences.get('ideal_tide_height', 0.0)) # Converter para float
    mare_tipo_ideal = spot_preferences.get('ideal_tide_type', 'qualquer') # 'qualquer', 'enchente', 'vazante', etc.

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

    # --- 4. Score de Temperaturas ---
    # Temperatura da Água
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

    # Temperatura do Ar
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

    # --- 5. Impacto do Swell Secundário ---
    # Converter para float, com default para 0.0 se não existir
    previsao_swell_secundario_tamanho = float(forecast_entry.get('secondary_swell_height_sg', 0.0))
    previsao_swell_secundario_periodo = float(forecast_entry.get('secondary_swell_period_sg', 0.0))
    previsao_swell_secundario_direcao = float(forecast_entry.get('secondary_swell_direction_sg', 0.0))

    # Reutiliza os dados do swell principal para comparação, convertendo para float
    previsao_onda_tamanho_principal = float(forecast_entry.get('swell_height_sg', 0.0))
    previsao_onda_periodo_principal = float(forecast_entry.get('swell_period_sg', 0.0))
    previsao_onda_direcao_principal = float(forecast_entry.get('swell_direction_sg', 0.0))

    impacto_swell_secundario = 0.0 # Score entre -1 e 1
    # Check if primary swell data is valid for comparison
    if all(v is not None for v in [previsao_onda_tamanho_principal, previsao_onda_periodo_principal, previsao_onda_direcao_principal]):
        impacto_swell_secundario_result = calcular_impacto_swell_secundario(
            previsao_swell_secundario_tamanho,
            previsao_swell_secundario_periodo,
            previsao_swell_secundario_direcao,
            previsao_onda_tamanho_principal,
            previsao_onda_periodo_principal,
            previsao_onda_direcao_principal
        )
        impacto_swell_secundario = float(impacto_swell_secundario_result.item()) if isinstance(impacto_swell_secundario_result, np.ndarray) else float(impacto_swell_secundario_result)
    detailed_scores['secondary_swell_impact'] = impacto_swell_secundario
    
    # --- 6. Combinação dos Scores e Pesos ---
    # Defina pesos para cada critério. Estes podem vir de:
    # 1. Preferências do usuário (configuráveis)
    # 2. Padrões por nível de surf
    # 3. Padrões globais/modelo default
    
    # É crucial que a soma dos pesos seja 1 (ou normalizável para 1) se você quiser
    # uma média ponderada direta que resulte em um score entre 0 e 1.
    # No entanto, a forma como o impacto do swell secundário é integrado pode variar.
    
    # Consideramos os scores calculados (0 a 1) e o impacto do swell secundário (-1 a 1).
    # Vamos primeiro calcular um score base para as condições principais.
    # Em seguida, ajustamos esse score base com o impacto do swell secundário.

    # Pesos para os critérios principais (ajuste conforme a importância de cada um)
    # Garante que os pesos sejam floats e tenham um valor padrão mínimo de 0.0, e um mínimo de 1.0 se for usado para divisão
    PESO_TAMANHO_ONDA = float(spot_preferences.get('weight_wave_height', 0.30))
    PESO_DIRECAO_ONDA = float(spot_preferences.get('weight_swell_direction', 0.25))
    PESO_PERIODO_ONDA = float(spot_preferences.get('weight_swell_period', 0.20))
    PESO_VENTO = float(spot_preferences.get('weight_wind', 0.15))
    PESO_MARE = float(spot_preferences.get('weight_tide', 0.05))
    PESO_TEMPERATURA_AGUA = float(spot_preferences.get('weight_water_temperature', 0.025))
    PESO_TEMPERATURA_AR = float(spot_preferences.get('weight_air_temperature', 0.025))
    
    # Soma dos pesos das condições principais para normalização
    soma_pesos_principais = (
        PESO_TAMANHO_ONDA + PESO_DIRECAO_ONDA + PESO_PERIODO_ONDA +
        PESO_VENTO + PESO_MARE + PESO_TEMPERATURA_AGUA + PESO_TEMPERATURA_AR
    )
    
    if soma_pesos_principais == 0:
        # Evita divisão por zero se todos os pesos forem 0
        score_base = 0.0
    else:
        score_base = (
            (detailed_scores.get('wave_height_score', 0.0) * PESO_TAMANHO_ONDA) +
            (detailed_scores.get('swell_direction_score', 0.0) * PESO_DIRECAO_ONDA) +
            (detailed_scores.get('swell_period_score', 0.0) * PESO_PERIODO_ONDA) +
            (detailed_scores.get('wind_score', 0.0) * PESO_VENTO) +
            (detailed_scores.get('tide_score', 0.0) * PESO_MARE) +
            (detailed_scores.get('water_temperature_score', 0.0) * PESO_TEMPERATURA_AGUA) +
            (detailed_scores.get('air_temperature_score', 0.0) * PESO_TEMPERATURA_AR)
        ) / soma_pesos_principais

    # Ajusta o score base com o impacto do swell secundário.
    # O impacto do swell secundário é um fator multiplicativo/aditivo.
    # Se impacto_swell_secundario for 1, melhora o score. Se for -1, piora.
    
    # Exemplo simples: um impacto de 1 significa que o score final pode ser até X% maior que o score base,
    # e -1 significa até X% menor.
    FATOR_AJUSTE_SWELL_SECUNDARIO = 0.2 # Permite um ajuste de até 20% no score base

    # Transforma o impacto de [-1, 1] para um multiplicador de [1 - FATOR, 1 + FATOR]
    # Se impacto = 1, multiplicador = 1 + FATOR_AJUSTE_SWELL_SECUNDARIO
    # Se impacto = 0, multiplicador = 1
    # Se impacto = -1, multiplicador = 1 - FATOR_AJUSTE_SWELL_SECUNDARIO
    multiplicador_swell_secundario = 1 + (detailed_scores.get('secondary_swell_impact', 0.0) * FATOR_AJUSTE_SWELL_SECUNDARIO)

    final_suitability_score = score_base * multiplicador_swell_secundario

    # Garante que o score final esteja dentro do intervalo [0, 1]
    final_suitability_score = np.clip(final_suitability_score, 0.0, 1.0)
    
    return float(final_suitability_score), detailed_scores