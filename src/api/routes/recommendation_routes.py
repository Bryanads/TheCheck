from flask import Blueprint, request, jsonify
import datetime 
from src.db.queries import (
    get_spot_by_id,
    get_user_by_id, 
    get_spot_preferences,
    get_forecasts_from_db,
    get_tides_forecast_from_db,
    get_level_spot_preferences 
)
from src.recommendation.data_fetcher import determine_tide_phase
from src.recommendation.recommendation_logic import calculate_suitability_score
from src.utils.utils import convert_to_localtime_string 
"""
Exemplo de requisição para http://127.0.0.1:5000/recommendations
{
    "user_id": "UUID_DO_USUARIO_AQUI",
    "spot_ids": [1],
    "day_offset": 1,
    "start_time": "08:00",
    "end_time": "20:00"
}

Esta requisição busca recomendações para o usuário com o UUID, para o spot com ID 1,
no dia seguinte (day_offset = 1), entre 08:00 e 20:00 UTC.
"""

# Cria uma Blueprint para as rotas de recomendação
recommendation_bp = Blueprint('recommendations', __name__)


# A lógica principal de recomendação, adaptada para ser chamada pela API
def generate_recommendations_logic(user_id, spot_ids_list, day_offset, start_time_str, end_time_str):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")

    user = get_user_by_id(user_id) # Buscar o objeto usuário completo
    if not user:
        return {"error": f"Usuário com ID {user_id} não encontrado."}, 404
    
    surf_level = user.get('surf_level')
    if not surf_level:
        return {"error": f"Nível de surf não definido para o usuário {user_id}. Por favor, atualize seu perfil."}, 400

    base_date = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=day_offset)

    try:
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))
    except ValueError:
        return {"error": "Formato de hora inválido. Use HH:MM."}, 400

    start_utc = datetime.datetime.combine(base_date, datetime.time(start_hour, start_minute)).replace(tzinfo=datetime.timezone.utc)
    end_utc = datetime.datetime.combine(base_date, datetime.time(end_hour, end_minute, 59, 999999)).replace(tzinfo=datetime.timezone.utc)
    day_start = datetime.datetime.combine(base_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
    day_end = datetime.datetime.combine(base_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)

    flat_recommendations = []

    for spot_id in spot_ids_list:
        spot = get_spot_by_id(spot_id)
        if not spot:
            print(f"Aviso: Spot com ID {spot_id} não encontrado, pulando.")
            continue
        
        # 1. Tentar pegar preferências do usuário (manuais)
        spot_preferences = get_spot_preferences(user_id, spot_id, preference_type='user')
        
        # 2. Se não houver, tentar pegar preferências do modelo
        if not spot_preferences:
            spot_preferences = get_spot_preferences(user_id, spot_id, preference_type='model')

        # 3. Se ainda não houver (primeiro acesso ou modelo não gerou), usar preferências baseadas no nível do surfista
        if not spot_preferences:
            spot_preferences = get_level_spot_preferences(surf_level, spot_id)
            if not spot_preferences:
                print(f"Aviso: Preferências não encontradas para o nível '{surf_level}' no spot {spot_id}, pulando.")
                continue


        forecasts = get_forecasts_from_db(spot_id, day_start, day_end)
        tides_extremes = get_tides_forecast_from_db(spot_id, day_start, day_end)

        if not forecasts:
            print(f"Aviso: Previsões não encontradas para o spot {spot_id} no dia {base_date.isoformat()}, pulando.")
            continue

        # Filtrar previsões para o período de tempo especificado pelo usuário (start_time, end_time)
        filtered_forecasts = [
            f for f in forecasts
            if start_utc <= f['timestamp_utc'] <= end_utc
        ]

        if not filtered_forecasts:
            print(f"Aviso: Nenhuma previsão encontrada para o spot {spot_id} entre {start_time_str} e {end_time_str}, pulando.")
            continue

        for forecast_entry in filtered_forecasts:
            tide_phase = determine_tide_phase(forecast_entry['timestamp_utc'], tides_extremes)
            
            # Calcular o score de adequação para cada entrada de previsão
            suitability_score, detailed_scores = calculate_suitability_score(forecast_entry, spot_preferences, spot, tide_phase, user)

            # Preparar a entrada de recomendação
            recommendation_entry = {
                "spot_id": spot_id,
                "spot_name": spot['spot_name'],
                "timestamp_utc": forecast_entry['timestamp_utc'].isoformat(),
                "local_time": convert_to_localtime_string(forecast_entry['timestamp_utc'].isoformat(), spot.get('timezone', 'UTC')),
                "suitability_score": suitability_score,
                "detailed_scores": detailed_scores,
                "forecast_conditions": {
                    "wave_height_sg": forecast_entry.get('wave_height_sg'),
                    "wave_direction_sg": forecast_entry.get('wave_direction_sg'),
                    "wave_period_sg": forecast_entry.get('wave_period_sg'),
                    "swell_height_sg": forecast_entry.get('swell_height_sg'),
                    "swell_direction_sg": forecast_entry.get('swell_direction_sg'),
                    "swell_period_sg": forecast_entry.get('swell_period_sg'),
                    "secondary_swell_height_sg": forecast_entry.get('secondary_swell_height_sg'),
                    "secondary_swell_direction_sg": forecast_entry.get('secondary_swell_direction_sg'),
                    "secondary_swell_period_sg": forecast_entry.get('secondary_swell_period_sg'),
                    "wind_speed_sg": forecast_entry.get('wind_speed_sg'),
                    "wind_direction_sg": forecast_entry.get('wind_direction_sg'),
                    "water_temperature_sg": forecast_entry.get('water_temperature_sg'),
                    "air_temperature_sg": forecast_entry.get('air_temperature_sg'),
                    "current_speed_sg": forecast_entry.get('current_speed_sg'),
                    "current_direction_sg": forecast_entry.get('current_direction_sg'),
                    "sea_level_sg": forecast_entry.get('sea_level_sg'),
                },
                "tide_info": {
                    "tide_phase": tide_phase,
                    "sea_level_sg": forecast_entry.get('sea_level_sg') # Replicando aqui para fácil acesso
                },
                "spot_characteristics": {
                    "bottom_type": spot.get('bottom_type'),
                    "coast_orientation": spot.get('coast_orientation'),
                    "general_characteristics": spot.get('general_characteristics')
                },
                "preferences_used": spot_preferences # Inclui as preferências que foram usadas
            }
            flat_recommendations.append(recommendation_entry)
            
    return {"recommendations": flat_recommendations}, 200 # Retorna um dicionário com a chave "recommendations"


@recommendation_bp.route('/recommendations', methods=['POST'])
def get_recommendations_endpoint():
    data = request.get_json()

    required_fields = ['user_id', 'spot_ids', 'day_offset', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400
    
    user_id = data.get('user_id')
    spot_ids = data.get('spot_ids')
    day_offset = data.get('day_offset')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    try:
        # Convert spot_ids to list of integers for validation
        spot_ids = [int(s_id) for s_id in spot_ids]
    except (ValueError, TypeError):
        return jsonify({"error": "spot_ids deve ser uma lista de IDs de spots inteiros."}), 400

    # Chamar a lógica principal
    recommendations, status_code = generate_recommendations_logic(
        user_id, spot_ids, day_offset, start_time, end_time
    )

    if status_code != 200:
        return jsonify(recommendations), status_code
    
    return jsonify(recommendations), 200