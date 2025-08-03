from flask import Blueprint, request, jsonify
import arrow
from src.db.queries import (
    get_spot_by_id,
    get_user_surf_level,
    get_spot_preferences,
    get_forecasts_from_db,
    get_tides_forecast_from_db
)
from src.recommendation.data_fetcher import determine_tide_phase, get_cardinal_direction
from src.recommendation.recommendation_logic import calculate_suitability_score
from src.utils.utils import convert_to_localtime_string # Assuming this utility exists

"""
Exemplo de requisição para http://127.0.0.1:5000/recommendations
{
    "user_id": 1,
    "spot_ids": [1],
    "day_offset": 1,
    "start_time": "08:00",
    "end_time": "20:00"
}

Esta requisição busca recomendações para o usuário com ID 1, para o spot com ID 1,
no dia seguinte (day_offset = 1), entre 08:00 e 20:00 UTC.
"""

# Cria uma Blueprint para as rotas de recomendação
recommendation_bp = Blueprint('recommendations', __name__)


# A lógica principal de recomendação, adaptada para ser chamada pela API
def generate_recommendations_logic(user_id, spot_ids_list, day_offset, start_time_str, end_time_str):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")

    surf_level = get_user_surf_level(user_id)
    if not surf_level:
        return {"error": f"Não foi possível determinar o nível de surf para o usuário {user_id}."}, 400

    base_date = arrow.utcnow().shift(days=day_offset).floor('day')

    try:
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))
    except ValueError:
        return {"error": "Formato de hora inválido. Use HH:MM."}, 400

    start_utc = base_date.replace(hour=start_hour, minute=start_minute).to('utc').datetime
    end_utc = base_date.replace(hour=end_hour, minute=end_minute, second=59, microsecond=999999).to('utc').datetime
    day_start = base_date.replace(hour=0, minute=0, second=0, microsecond=0).to('utc').datetime
    day_end = base_date.replace(hour=23, minute=59, second=59, microsecond=999999).to('utc').datetime

    flat_recommendations = []

    for spot_id in spot_ids_list:
        spot = get_spot_by_id(spot_id)
        if not spot:
            print(f"Spot ID {spot_id} não encontrado.")
            continue

        spot_name = spot['spot_name']
        timezone = spot['timezone']

        preferences = get_spot_preferences(spot_id, user_id, surf_level) or {}

        forecast_data = get_forecasts_from_db(spot_id, start_utc, end_utc)
        tide_extremes = get_tides_forecast_from_db(spot_id, day_start, day_end)

        if not forecast_data:
            print(f"Nenhum dado de previsão para o spot {spot_name} (ID {spot_id}).")
            continue

        for entry in forecast_data:
            timestamp = entry['timestamp_utc']
            sea_level = entry.get('sea_level_sg')

            tide_phase = determine_tide_phase(timestamp, sea_level, tide_extremes)
            entry['tide_phase'] = tide_phase

            score = calculate_suitability_score(entry, preferences)

            flat_recommendations.append({
                "suitability_score": round(score, 2),
                "spot_id": spot_id,
                "spot_name": spot_name,
                "timestamp_utc": timestamp.isoformat(),
                "local_time": arrow.get(timestamp).to(timezone).format('YYYY-MM-DD HH:mm:ss ZZZ'),

                # Parâmetros completos da previsão
                "wave_height_sg": entry.get("wave_height_sg"),
                "wave_direction_sg": entry.get("wave_direction_sg"),
                "wave_period_sg": entry.get("wave_period_sg"),
                
                "swell_height_sg": entry.get("swell_height_sg"),
                "swell_direction_sg": entry.get("swell_direction_sg"),
                "swell_period_sg": entry.get("swell_period_sg"),

                "secondary_swell_height_sg": entry.get("secondary_swell_height_sg"),
                "secondary_swell_direction_sg": entry.get("secondary_swell_direction_sg"),
                "secondary_swell_period_sg": entry.get("secondary_swell_period_sg"),

                "wind_speed_sg": entry.get("wind_speed_sg"),
                "wind_direction_sg": entry.get("wind_direction_sg"),

                "water_temperature_sg": entry.get("water_temperature_sg"),
                "air_temperature_sg": entry.get("air_temperature_sg"),

                "current_speed_sg": entry.get("current_speed_sg"),
                "current_direction_sg": entry.get("current_direction_sg"),

                "sea_level_sg": sea_level,
                "tide_phase": tide_phase
            })

    flat_recommendations.sort(key=lambda x: -x["suitability_score"])

    return {"recommendations": flat_recommendations}, 200



@recommendation_bp.route('/recommendations', methods=['POST'])
def get_recommendations_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Requisição inválida: JSON esperado no corpo da requisição."}), 400

    required_fields = ['user_id', 'spot_ids', 'day_offset', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400

    try:
        user_id = int(data['user_id'])
        spot_ids = [int(s_id) for s_id in data['spot_ids']]
        day_offset = int(data['day_offset'])
        start_time = data['start_time']
        end_time = data['end_time']
    except ValueError as e:
        return jsonify({"error": f"Erro de tipo de dado nos parâmetros: {e}"}), 400
    except TypeError as e:
        return jsonify({"error": f"Erro de tipo de dado ou formato: {e}. Verifique os tipos de dados fornecidos."}), 400

    # Chamar a lógica principal
    recommendations, status_code = generate_recommendations_logic(user_id, spot_ids, day_offset, start_time, end_time)
    return jsonify(recommendations), status_code