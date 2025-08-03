from flask import Blueprint, request, jsonify
import arrow

# Importa as funções da sua lógica de recomendação
# Ajuste os '..' para a navegação correta dentro do pacote 'src'
from src.utils.utils import convert_to_localtime_string
from src.db.queries import (
    get_spot_by_id,
    get_user_surf_level,
    get_spot_preferences,
    get_forecast_data_for_spot,
    get_tide_extremes_for_spot
)
from src.recommendation.data_fetcher import determine_tide_phase, get_cardinal_direction
from src.recommendation.recommendation_logic import calculate_suitability_score

# Cria uma Blueprint para as rotas de recomendação
recommendation_bp = Blueprint('recommendations', __name__)


# A lógica principal de recomendação, adaptada para ser chamada pela API
def generate_recommendations_logic(user_id, spot_ids_list, day_offset, start_time_str, end_time_str):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")

    surf_level = get_user_surf_level(user_id)
    if not surf_level:
        print(f"Não foi possível determinar o nível de surf para o usuário {user_id}.")
        return {"error": f"Não foi possível determinar o nível de surf para o usuário {user_id}."}, 400

    print(f"Usuário {user_id} é um surfista '{surf_level}'.")

    spots_to_process = []
    for s_id in spot_ids_list:
        spot_details = get_spot_by_id(s_id)
        if spot_details:
            spots_to_process.append(spot_details)
        else:
            print(f"Aviso: Spot com ID {s_id} não encontrado no banco de dados. Ignorando.")

    if not spots_to_process:
        print(f"Nenhum spot válido encontrado nos IDs fornecidos: {spot_ids_list}. Nenhuma recomendação pode ser feita.")
        return {"message": "Nenhum spot válido encontrado ou nenhum dado de previsão após a filtragem."}, 200

    # Calcular início e fim com base em day_offset + horários
    base_date = arrow.utcnow().shift(days=day_offset).floor('day')
    try:
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))
    except ValueError:
        return {"error": "Formato de hora inválido. Use HH:MM."}, 400

    start_time_utc = base_date.replace(hour=start_hour, minute=start_minute)
    end_time_utc = base_date.replace(hour=end_hour, minute=end_minute)

    recommendations = []

    for spot in spots_to_process:
        spot_id = spot['spot_id']
        spot_name = spot['name'] 
        print(f"\n--- Processando spot: {spot_name} (ID: {spot_id}) ---")

        raw_preferences = get_spot_preferences(spot_id, user_id, surf_level)
        preferences = raw_preferences if raw_preferences is not None else {}

        if not preferences:
            print(f"Usando preferências padrão (não específicas) para o spot {spot_name}, pois nenhuma foi encontrada.")

        forecast_data = get_forecast_data_for_spot(spot_id, start_time_utc.datetime, end_time_utc.datetime)

        print(f"Dados de previsão para {spot_name} ({spot_id}): {forecast_data}")

        day_start = start_time_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = start_time_utc.replace(hour=23, minute=59, second=59, microsecond=0)
        tide_extremes = get_tide_extremes_for_spot(spot_id, day_start.datetime, day_end.datetime)

        if not forecast_data:
            print(f"Nenhum dado de previsão disponível para {spot_name} no período especificado.")
            continue

        for entry in forecast_data:
            timestamp = entry['timestamp_utc']

            tide_phase = determine_tide_phase(
                timestamp,
                entry.get('sea_level_sg'),
                tide_extremes
            )
            entry['current_tide_phase'] = tide_phase

            score = calculate_suitability_score(entry, preferences)

            recommendations.append({
                'spot_id': spot_id,
                'spot_name': spot_name,
                'timestamp_utc': timestamp.isoformat(),
                'wave_height': entry.get('waveHeight_sg'),       
                'swell_direction': entry.get('swellDirection_sg'), 
                'wind_speed': entry.get('windSpeed_sg'),          
                'wind_direction': entry.get('windDirection_sg'), 
                'tide_phase': tide_phase,
                'sea_level': entry.get('seaLevel_sg'),           
                'water_temperature': entry.get('waterTemperature_sg'),
                'air_temperature': entry.get('airTemperature_sg'),   
                'current_speed': entry.get('currentSpeed_sg'),     
                'current_direction': entry.get('currentDirection_sg'),
                'suitability_score': round(score, 2)
            })

    if recommendations:
        recommendations.sort(key=lambda x: (-x['suitability_score'], x['timestamp_utc']))
        return {"recommendations": recommendations}, 200
    else:
        print("Nenhuma recomendação pôde ser gerada (por exemplo, nenhum spot ou nenhum dado de previsão após a filtragem).")
        return {"message": "Nenhuma recomendação pôde ser gerada (verifique os parâmetros ou dados disponíveis)."}, 200


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
        return jsonify({"error": f"Erro de tipo de dado ou formato em spot_ids: {e}. Certifique-se de que é uma lista de inteiros."}), 400

    # Chama a função de recomendação
    result, status_code = generate_recommendations_logic(user_id, spot_ids, day_offset, start_time, end_time)

    # Retorna o resultado como JSON
    return jsonify(result), status_code