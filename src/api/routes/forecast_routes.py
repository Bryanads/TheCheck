from flask import Blueprint, request, jsonify
import arrow

# Importa as funções de banco de dados e utilitários
from src.db.queries import get_spot_by_id, get_forecast_data_for_spot
from src.utils.utils import convert_to_localtime_string

# Cria uma Blueprint específica para as previsões (puras)
forecast_bp = Blueprint('forecasts', __name__)

@forecast_bp.route('/forecasts', methods=['POST'])
def get_pure_forecasts_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Requisição inválida: JSON esperado no corpo da requisição."}), 400

    required_fields = ['spot_ids', 'day_offset']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400

    try:
        spot_ids = [int(s_id) for s_id in data['spot_ids']]
        day_offsets = [int(d_offset) for d_offset in data['day_offset']]
    except ValueError as e:
        return jsonify({"error": f"Erro de tipo de dado nos parâmetros: {e}"}), 400
    except TypeError as e:
        return jsonify({"error": f"Erro de tipo de dado ou formato em spot_ids/day_offset: {e}. Certifique-se de que são listas de inteiros."}), 400

    all_pure_forecasts = []
    has_errors = False
    error_messages = []

    # Definir o período do dia inteiro
    start_time_daily = "00:00"
    end_time_daily = "23:59"

    for day_offset in day_offsets:
        base_date = arrow.utcnow().shift(days=day_offset).floor('day')
        try:
            start_hour, start_minute = map(int, start_time_daily.split(":"))
            end_hour, end_minute = map(int, end_time_daily.split(":"))
        except ValueError:
            # Isso não deve acontecer com "00:00" e "23:59" mas é bom ter
            error_messages.append(f"Erro interno de formato de hora para day_offset {day_offset}.")
            has_errors = True
            continue # Pula para o próximo day_offset

        start_time_utc = base_date.replace(hour=start_hour, minute=start_minute)
        end_time_utc = base_date.replace(hour=end_hour, minute=end_minute)


        for spot_id in spot_ids:
            spot_details = get_spot_by_id(spot_id)
            if not spot_details:
                error_messages.append(f"Aviso: Spot com ID {spot_id} não encontrado no banco de dados. Ignorando para day_offset {day_offset}.")
                has_errors = True
                continue # Pula para o próximo spot_id

            spot_name = spot_details['name'] # Assumindo 'name' é a chave para o nome do spot

            forecast_data = get_forecast_data_for_spot(spot_id, start_time_utc.datetime, end_time_utc.datetime)

            if not forecast_data:
                error_messages.append(f"Nenhum dado de previsão disponível para {spot_name} (ID: {spot_id}) no período {start_time_daily}-{end_time_daily} do day_offset {day_offset}.")
                has_errors = True
                continue

            for entry in forecast_data:
                # Retorna os dados como eles vêm do DB, com timestamps formatados
                pure_forecast_entry = {
                    'spot_id': spot_id,
                    'spot_name': spot_name,
                    'requested_day_offset': day_offset,
                    'timestamp_utc': entry['timestamp_utc'].isoformat() if 'timestamp_utc' in entry else None,
                    'timestamp_local': convert_to_localtime_string(entry['timestamp_utc']) if 'timestamp_utc' in entry else None,
                    'waveHeight_sg': entry.get('waveHeight_sg'),
                    'waveDirection_sg': entry.get('waveDirection_sg'),
                    'wavePeriod_sg': entry.get('wavePeriod_sg'),
                    'swellHeight_sg': entry.get('swellHeight_sg'),
                    'swellDirection_sg': entry.get('swellDirection_sg'),
                    'swellPeriod_sg': entry.get('swellPeriod_sg'),
                    'secondarySwellHeight_sg': entry.get('secondarySwellHeight_sg'),
                    'secondarySwellDirection_sg': entry.get('secondarySwellDirection_sg'),
                    'secondarySwellPeriod_sg': entry.get('secondarySwellPeriod_sg'),
                    'windSpeed_sg': entry.get('windSpeed_sg'),
                    'windDirection_sg': entry.get('windDirection_sg'),
                    'waterTemperature_sg': entry.get('waterTemperature_sg'),
                    'airTemperature_sg': entry.get('airTemperature_sg'),
                    'currentSpeed_sg': entry.get('currentSpeed_sg'),
                    'currentDirection_sg': entry.get('currentDirection_sg'),
                    'seaLevel_sg': entry.get('seaLevel_sg')
                }
                all_pure_forecasts.append(pure_forecast_entry)

    # Ordenar as previsões por timestamp_utc, depois por spot_id para melhor legibilidade
    all_pure_forecasts.sort(key=lambda x: (x['timestamp_utc'] if x['timestamp_utc'] else '', x['spot_id']))

    if has_errors and not all_pure_forecasts:
        return jsonify({"error": "Ocorreram erros ao processar algumas requisições ou nenhum dado encontrado.", "details": error_messages}), 500
    elif has_errors:
        return jsonify({"message": "Algumas previsões foram obtidas, mas ocorreram erros em outras.", "partial_forecasts": all_pure_forecasts, "errors": error_messages}), 200
    elif not all_pure_forecasts:
        return jsonify({"message": "Nenhuma previsão pôde ser gerada para os spots e dias especificados."}), 200
    else:
        return jsonify({"pure_forecasts": all_pure_forecasts}), 200