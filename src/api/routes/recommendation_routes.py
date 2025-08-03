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

"""
Exemplo de requisição para http://127.0.0.1:5000/recommendations
{
    "userId": 1,
    "spotIds": [1],
    "dayOffset": 1,
    "startTime": "08:00",
    "endTime": "20:00"
}

Esta requisição busca recomendações para o usuário com ID 1, para o spot com ID 1,
no dia seguinte (dayOffset = 1), entre 08:00 e 20:00 UTC. 
"""

# Cria uma Blueprint para as rotas de recomendação
recommendation_bp = Blueprint('recommendations', __name__)


# A lógica principal de recomendação, adaptada para ser chamada pela API
def generate_recommendations_logic(user_id, spot_ids_list, day_offset, start_time_str, end_time_str):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")

    # get_user_surf_level já retorna o surf_level em camelCase ou None.
    # No caso de surf_level, é um único valor, então a conversão camelCase não se aplica a ele.
    surf_level = get_user_surf_level(user_id)
    if not surf_level:
        print(f"Não foi possível determinar o nível de surf para o usuário {user_id}.")
        return {"error": f"Não foi possível determinar o nível de surf para o usuário {user_id}."}, 400

    print(f"Usuário {user_id} é um surfista '{surf_level}'.")

    spots_to_process = []
    for s_id in spot_ids_list:
        # spot_details já virá em camelCase do queries.py
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
        # Acessando spotId e spotName em camelCase
        spot_id = spot['spotId']
        spot_name = spot['spotName'] 
        spot_timezone = spot.get('timezone', 'UTC') # Obter fuso horário do spot
        print(f"\n--- Processando spot: {spot_name} (ID: {spot_id}) ---")

        # raw_preferences já virá em camelCase do queries.py
        raw_preferences = get_spot_preferences(spot_id, user_id, surf_level)
        preferences = raw_preferences if raw_preferences is not None else {}

        if not preferences:
            print(f"Usando preferências padrão (não específicas) para o spot {spot_name}, pois nenhuma foi encontrada.")

        # Buscar dados de previsão usando a nova função (camelCase na saída)
        forecast_data = get_forecasts_from_db(spot_id, start_time_utc.datetime, end_time_utc.datetime)

        print(f"Dados de previsão para {spot_name} ({spot_id}): {forecast_data}")

        # Buscar extremos de maré para o dia inteiro (camelCase na saída)
        day_start_utc_datetime = start_time_utc.replace(hour=0, minute=0, second=0, microsecond=0).datetime
        day_end_utc_datetime = start_time_utc.replace(hour=23, minute=59, second=59, microsecond=999999).datetime
        tide_extremes = get_tides_forecast_from_db(spot_id, day_start_utc_datetime, day_end_utc_datetime)

        if not forecast_data:
            print(f"Nenhum dado de previsão disponível para {spot_name} no período especificado.")
            continue

        for entry in forecast_data:
            # Acessando timestampUtc e seaLevel em camelCase
            timestamp_utc = entry['timestampUtc']
            current_sea_level = entry.get('seaLevel') 

            # determine_tide_phase espera camelCase para tide_extremes
            tide_phase = determine_tide_phase(
                current_time_utc=timestamp_utc,
                current_sea_level=current_sea_level,
                tide_extremes=tide_extremes
            )
            # Adiciona currentTidePhase em camelCase
            entry['currentTidePhase'] = tide_phase

            # calculate_suitability_score também precisará ser adaptada para esperar camelCase
            # tanto em 'entry' quanto em 'preferences' (já vêm assim para cá)
            score = calculate_suitability_score(entry, preferences)

            recommendations.append({
                'spotId': spot_id, # camelCase
                'spotName': spot_name, # camelCase
                'spotTimezone': spot_timezone, # Novo campo em camelCase
                'timestampUtc': timestamp_utc.isoformat(), # camelCase
                'waveHeight': entry.get('waveHeight'), # Removido _sg, camelCase
                'wavePeriod': entry.get('wavePeriod'), # Removido _sg, camelCase
                'waveDirection': get_cardinal_direction(entry.get('waveDirection')), # Removido _sg, camelCase
                'swellDirection': entry.get('swellDirection'), # Removido _sg, camelCase
                'windSpeed': entry.get('windSpeed'), # Removido _sg, camelCase
                'windDirection': entry.get('windDirection'), # Removido _sg, camelCase
                'tidePhase': tide_phase, # camelCase
                'seaLevel': entry.get('seaLevel'), # Removido _sg, camelCase
                'waterTemperature': entry.get('waterTemperature'), # Removido _sg, camelCase
                'airTemperature': entry.get('airTemperature'), # Removido _sg, camelCase
                'currentSpeed': entry.get('currentSpeed'), # Removido _sg, camelCase
                'currentDirection': entry.get('currentDirection'), # Removido _sg, camelCase
                'suitabilityScore': round(score, 2) # camelCase
            })

    if recommendations:
        # Ordena por suitabilityScore (decrescente) e timestampUtc (crescente)
        recommendations.sort(key=lambda x: (-x['suitabilityScore'], x['timestampUtc']))
        return {"recommendations": recommendations}, 200
    else:
        print("Nenhuma recomendação pôde ser gerada (por exemplo, nenhum spot ou nenhum dado de previsão após a filtragem).")
        return {"message": "Nenhuma recomendação pôde ser gerada (verifique os parâmetros ou dados disponíveis)."}, 200


@recommendation_bp.route('/recommendations', methods=['POST'])
def get_recommendations_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Requisição inválida: JSON esperado no corpo da requisição."}), 400

    # Campos esperados na requisição POST, agora em camelCase
    required_fields = ['userId', 'spotIds', 'dayOffset', 'startTime', 'endTime']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400

    try:
        user_id = int(data['userId'])
        spot_ids = [int(s_id) for s_id in data['spotIds']]
        day_offset = int(data['dayOffset'])
        start_time = data['startTime']
        end_time = data['endTime']
    except ValueError as e:
        return jsonify({"error": f"Erro de tipo de dado nos parâmetros: {e}"}), 400
    except TypeError as e:
        return jsonify({"error": f"Erro de tipo de dado ou formato em spotIds: {e}. Certifique-se de que é uma lista de inteiros."}), 400

    # Chama a função de recomendação
    result, status_code = generate_recommendations_logic(user_id, spot_ids, day_offset, start_time, end_time)

    # Retorna o resultado como JSON
    return jsonify(result), status_code