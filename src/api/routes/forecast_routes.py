# TheCheck/src/api/routes/forecast_routes.py
from flask import Blueprint, request, jsonify
import arrow
from src.db.queries import get_spot_by_id, get_forecasts_from_db, get_tides_forecast_from_db
from src.recommendation.data_fetcher import determine_tide_phase

"""
Exemplo de requisição para http://127.0.0.1:5000/forecasts

{
    "spotIds": [1],
    "dayOffset": [1]
}

Esta requisição busca previsões para o spot com ID 1, no dia seguinte (dayOffset = 1).

"""

# Cria uma Blueprint específica para as previsões
forecast_bp = Blueprint('forecasts', __name__)

@forecast_bp.route('/forecasts', methods=['POST'])
def get_combined_forecasts_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Requisição inválida: JSON esperado no corpo da requisição."}), 400

    required_fields = ['spotIds', 'dayOffset'] 
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo '{field}' é obrigatório."}), 400

    try:
        spot_ids = [int(s_id) for s_id in data['spotIds']] 
        day_offsets = [int(d_offset) for d_offset in data['dayOffset']] 
    except ValueError as e:
        return jsonify({"error": f"Erro de tipo de dado nos parâmetros: {e}"}), 400
    except TypeError as e:
        return jsonify({"error": f"Erro de tipo de dado ou formato em spotIds/dayOffset: {e}. Certifique-se de que são listas de inteiros."}), 400

    all_combined_forecasts = []
    has_errors = False
    error_messages = []

    # Definir o período do dia inteiro
    # start_time_daily e end_time_daily definem o intervalo para o qual você quer prever.
    # Se você quer dados de um dia inteiro (00:00 a 23:59), é isso que StormGlass (e seu DB) te dá.
    # O determine_tide_phase precisa dos extremos do DIA INTEIRO para calcular a fase corretamente.
    start_time_daily = "00:00"
    end_time_daily = "23:59"

    for day_offset in day_offsets:
        base_date = arrow.utcnow().shift(days=day_offset).floor('day')
        try:
            start_hour, start_minute = map(int, start_time_daily.split(":"))
            end_hour, end_minute = map(int, end_time_daily.split(":"))
        except ValueError:
            error_messages.append(f"Erro interno de formato de hora para dayOffset {day_offset}.")
            has_errors = True
            continue

        # Convertendo para datetime.datetime com timezone UTC para compatibilidade
        start_time_utc = base_date.replace(hour=start_hour, minute=start_minute).datetime
        end_time_utc = base_date.replace(hour=end_hour, minute=end_minute).datetime

        for spot_id in spot_ids:
            spot_details = get_spot_by_id(spot_id)
            if not spot_details:
                error_messages.append(f"Aviso: Spot com ID {spot_id} não encontrado no banco de dados. Ignorando para dayOffset {day_offset}.")
                has_errors = True
                continue

            spot_name = spot_details.get('spotName', f"Spot {spot_id}") 
            spot_timezone = spot_details.get('timezone', 'UTC') # Obter fuso horário do spot

            # 1. Obter dados de previsão (ondas, vento, seaLevel, etc.) - já virão em camelCase
            forecast_data = get_forecasts_from_db(spot_id, start_time_utc, end_time_utc)
            
            # 2. Obter dados de extremos de maré para o DIA INTEIRO 
            start_time_day = start_time_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time_day = end_time_utc.replace(hour=23, minute=59, second=59, microsecond=9)

            tides_extremes_for_day = get_tides_forecast_from_db(spot_id, start_time_day, end_time_day)

            if not forecast_data: # tide_extremes_for_day pode estar vazio, mas se não houver forecast, não há o que combinar
                error_messages.append(f"Nenhum dado de previsão disponível para {spot_name} (ID: {spot_id}) no dia {base_date.format('YYYY-MM-DD')}.")
                has_errors = True
                continue
            
            # 3. Combinar os dados e calcular tideType
            for forecast_entry in forecast_data:
                combined_entry = forecast_entry.copy()
                
                # 'timestampUtc' já é um datetime object em UTC vindo do queries.py
                timestamp_forecast_utc = combined_entry['timestampUtc']
                
                # 'seaLevel' já vem em camelCase do queries.py
                current_sea_level = combined_entry.get('seaLevel') 

                # Determine o tipo de maré (low, high, rising, falling, mid, unknown)
                # determine_tide_phase espera datetime.datetime para current_time_utc
                tide_phase = determine_tide_phase(
                    current_time_utc=timestamp_forecast_utc,
                    current_sea_level=current_sea_level,
                    tide_extremes=tides_extremes_for_day # Passamos os extremos do dia
                )
                combined_entry['tideType'] = tide_phase
                
                # REMOVIDO: combined_entry['tideHeight'] = None (conforme sua solicitação)
                # tideHeight não é enviado como parte da previsão combinada

                # Adicionar detalhes do spot para cada entrada de previsão combinada (já em camelCase)
                combined_entry['spotId'] = spot_id
                combined_entry['spotName'] = spot_name
                combined_entry['spotTimezone'] = spot_timezone # Incluir fuso horário do spot

                all_combined_forecasts.append(combined_entry)

    # Ordenar as previsões combinadas por timestampUtc e depois por spotId para melhor legibilidade
    # As chaves já são camelCase: 'timestampUtc', 'spotId'
    all_combined_forecasts.sort(key=lambda x: (x.get('timestampUtc', ''), x.get('spotId', 0)))

    if has_errors and not all_combined_forecasts:
        return jsonify({"error": "Ocorreram erros ao processar algumas requisições ou nenhum dado encontrado.", "details": error_messages}), 500
    elif has_errors:
        # As chaves de retorno também precisam ser camelCase
        return jsonify({"message": "Algumas previsões foram obtidas, mas ocorreram erros em outras.", "partialForecasts": all_combined_forecasts, "errors": error_messages}), 200
    elif not all_combined_forecasts:
        return jsonify({"message": "Nenhuma previsão pôde ser gerada para os spots e dias especificados."}), 200
    else:
        return jsonify({"combinedForecasts": all_combined_forecasts}), 200