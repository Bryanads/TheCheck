import numpy as np # Importe numpy aqui
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
from src.recommendation.recommendation_logic import calculate_suitability_score
from src.utils.utils import convert_to_localtime_string, determine_tide_phase

# Adicione a função auxiliar para converter tipos NumPy
def convert_numpy_to_python_types(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python_types(elem) for elem in obj]
    # Se for um tipo NumPy escalar, converte para tipo Python nativo
    elif isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    return obj


recommendation_bp = Blueprint('recommendations', __name__)

def generate_recommendations_logic(user_id, spot_ids_list, day_offsets, start_time_str, end_time_str):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")
    print(f"DEBUG LOGIC: day_offsets type: {type(day_offsets)}, value: {day_offsets}")
    print(f"DEBUG LOGIC: start_time_str type: {type(start_time_str)}, value: {start_time_str}")
    print(f"DEBUG LOGIC: end_time_str type: {type(end_time_str)}, value: {end_time_str}")


    user = get_user_by_id(user_id) # Buscar o objeto usuário completo
    if not user:
        print(f"DEBUG LOGIC ERROR: Usuário com ID {user_id} não encontrado (404).")
        return {"error": f"Usuário com ID {user_id} não encontrado."}, 404
    
    surf_level = user.get('surf_level')
    print(f"DEBUG LOGIC: Surf level for user {user_id}: {surf_level}")
    if not surf_level:
        print(f"DEBUG LOGIC ERROR: Nível de surf não definido para o usuário {user_id} (400).")
        return {"error": f"Nível de surf não definido para o usuário {user_id}. Por favor, atualize seu perfil."}, 400

    try:
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))
        print(f"DEBUG LOGIC: Times parsed successfully. Start: {start_hour}:{start_minute}, End: {end_hour}:{end_minute}")
    except ValueError as e:
        print(f"DEBUG LOGIC ERROR: Formato de hora inválido: {e} (400).")
        return {"error": f"Formato de hora inválido. Use HH:MM: {e}"}, 400 # Adicione 'e' para mais detalhes do erro.

    all_spot_recommendations = [] 

    for spot_id in spot_ids_list:
        spot = get_spot_by_id(spot_id)
        if not spot:
            print(f"Aviso: Spot com ID {spot_id} não encontrado, pulando.")
            # ... (adiciona erro ao resultado e continua) ...
            spot_daily_recommendations = [{"spot_name": f"Spot ID {spot_id}", "spot_id": spot_id, "error": f"Spot com ID {spot_id} não encontrado."}]
            all_spot_recommendations.append(spot_daily_recommendations)
            continue

        spot_daily_recommendations = []
        
        spot_preferences = get_spot_preferences(user_id, spot_id, preference_type='user')
        if not spot_preferences:
            spot_preferences = get_spot_preferences(user_id, spot_id, preference_type='model')
        if not spot_preferences:
            spot_preferences = get_level_spot_preferences(surf_level, spot_id)
            if not spot_preferences:
                print(f"Aviso: Preferências não encontradas para o nível '{surf_level}' no spot {spot_id}, pulando.")
                spot_daily_recommendations.append({
                    "spot_name": spot['spot_name'],
                    "spot_id": spot_id,
                    "error": f"Nenhuma preferência configurada para o spot {spot['spot_name']} para este usuário/nível."
                })
                all_spot_recommendations.append(spot_daily_recommendations)
                continue
        
        for day_offset_single in day_offsets:
            base_date_for_offset = datetime.datetime.utcnow().date() + datetime.timedelta(days=day_offset_single)

            start_utc = datetime.datetime.combine(base_date_for_offset, datetime.time(start_hour, start_minute)).replace(tzinfo=datetime.timezone.utc)
            end_utc = datetime.datetime.combine(base_date_for_offset, datetime.time(end_hour, end_minute, 59, 999999)).replace(tzinfo=datetime.timezone.utc)
            day_start = datetime.datetime.combine(base_date_for_offset, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
            day_end = datetime.datetime.combine(base_date_for_offset, datetime.time.max).replace(tzinfo=datetime.timezone.utc)

            forecasts = get_forecasts_from_db(spot_id, day_start, day_end)
            tides_extremes = get_tides_forecast_from_db(spot_id, day_start, day_end)

            if not forecasts:
                print(f"Aviso: Previsões não encontradas para o spot {spot_id} no dia {base_date_for_offset.isoformat()}, pulando este dia.")
                spot_daily_recommendations.append({
                    "day_offset": day_offset_single,
                    "spot_name": spot['spot_name'],
                    "error": f"Previsões não encontradas para o spot {spot['spot_name']} para o dia {day_offset_single}."
                })
                continue
            
            filtered_forecasts = [
                f for f in forecasts
                if start_utc <= f['timestamp_utc'] <= end_utc
            ]

            if not filtered_forecasts:
                print(f"Aviso: Nenhuma previsão encontrada para o spot {spot_id} entre {start_time_str} e {end_time_str} para o dia {day_offset_single}, pulando este dia.")
                spot_daily_recommendations.append({
                    "day_offset": day_offset_single,
                    "spot_name": spot['spot_name'],
                    "error": f"Nenhuma previsão encontrada para o spot {spot['spot_name']} entre {start_time_str} e {end_time_str} para o dia {day_offset_single}."
                })
                continue

            hourly_recommendations_for_day = []
            for forecast_entry in filtered_forecasts:
                tide_phase = determine_tide_phase(forecast_entry['timestamp_utc'], tides_extremes)
                suitability_score, detailed_scores = calculate_suitability_score(forecast_entry, spot_preferences, spot, tide_phase, user)

                recommendation_entry = {
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
                        "sea_level_sg": forecast_entry.get('sea_level_sg')
                    },
                    "spot_characteristics": {
                        "bottom_type": spot.get('bottom_type'),
                        "coast_orientation": spot.get('coast_orientation'),
                        "general_characteristics": spot.get('general_characteristics')
                    },
                    "preferences_used": spot_preferences
                }
                hourly_recommendations_for_day.append(recommendation_entry)
            
            spot_daily_recommendations.append({
                "day_offset": day_offset_single,
                "spot_name": spot['spot_name'],
                "recommendations": hourly_recommendations_for_day,
                "preferences_used_for_spot": spot_preferences
            })
        
        all_spot_recommendations.append(spot_daily_recommendations)
            
    # Converta para lista Python, se a saída for um np.ndarray
    return convert_numpy_to_python_types({"recommendations_by_spot": all_spot_recommendations}), 200


@recommendation_bp.route('/recommendations', methods=['POST'])
def get_recommendations_endpoint():
    data = request.get_json()
    print(f"DEBUG ENDPOINT: Raw received data: {data}")

    required_fields = ['user_id', 'spot_ids', 'day_offset', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            print(f"DEBUG ENDPOINT ERROR: Missing required field '{field}' (400).")
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400
    
    user_id = data.get('user_id')
    spot_ids = data.get('spot_ids')
    day_offsets = data.get('day_offset')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    try:
        spot_ids = [int(s_id) for s_id in spot_ids]
        print(f"DEBUG ENDPOINT: Processed spot_ids: {spot_ids}")
    except (ValueError, TypeError) as e:
        print(f"DEBUG ENDPOINT ERROR: spot_ids format error: {e} (400).")
        return jsonify({"error": "spot_ids deve ser uma lista de IDs de spots inteiros."}), 400

    try:
        if not isinstance(day_offsets, list):
            day_offsets = [int(day_offsets)]
        else:
            day_offsets = [int(do) for do in day_offsets]
        print(f"DEBUG ENDPOINT: Processed day_offsets: {day_offsets}")
    except (ValueError, TypeError) as e:
        print(f"DEBUG ENDPOINT ERROR: day_offset format error: {e} (400).")
        return jsonify({"error": "day_offset deve ser um número inteiro ou uma lista de números inteiros."}), 400

    recommendations_data, status_code = generate_recommendations_logic(
        user_id, spot_ids, day_offsets, start_time, end_time
    )

    if status_code != 200:
        print(f"DEBUG ENDPOINT: generate_recommendations_logic returned status {status_code}.")
        return jsonify(recommendations_data), status_code
    
    return jsonify(recommendations_data), 200