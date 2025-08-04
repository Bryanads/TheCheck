from flask import Blueprint, request, jsonify
import datetime
from src.db.queries import get_spot_by_id, get_forecasts_from_db, get_tides_forecast_from_db
from src.recommendation.data_fetcher import determine_tide_phase

"""
Exemplo de requisição para http://127.0.0.1/5000/forecasts
{
    "spot_ids": [1],
    "day_offset": [0]
}
"""

forecast_bp = Blueprint('forecasts', __name__)

@forecast_bp.route('/forecasts', methods=['POST'])
def get_combined_forecasts_endpoint():
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
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Erro de tipo de dado: {e}"}), 400

    flat_forecast_entries = []
    has_errors = False
    error_messages = []

    for day_offset in day_offsets:
        base_date = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=day_offset)

        # Definir o início e fim do dia em UTC
        start_utc = datetime.datetime.combine(base_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        end_utc = datetime.datetime.combine(base_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)

        for spot_id in spot_ids:
            spot = get_spot_by_id(spot_id)
            if not spot:
                error_messages.append(f"Spot com ID {spot_id} não encontrado.")
                has_errors = True
                continue
            
            # Ajustar timezone se necessário para cálculos locais (aqui estamos usando UTC para DB queries)
            # spot_timezone = spot.get('timezone', 'UTC') # Se você tiver timezone na tabela spots

            forecasts = get_forecasts_from_db(spot_id, start_utc, end_utc)
            tides_extremes = get_tides_forecast_from_db(spot_id, start_utc, end_utc)

            if not forecasts:
                error_messages.append(f"Previsões não encontradas para o spot {spot_id} na data {base_date.isoformat()}.")
                has_errors = True
                continue

            for forecast_entry in forecasts:
                # Determinar a fase da maré para cada entrada de previsão
                tide_phase = determine_tide_phase(forecast_entry['timestamp_utc'], tides_extremes)
                
                # Adicionar os dados do spot e da maré à entrada da previsão
                entry_with_spot_and_tide = {
                    "spot_id": spot_id,
                    "spot_name": spot['spot_name'],
                    "latitude": spot['latitude'],
                    "longitude": spot['longitude'],
                    "timezone": spot['timezone'], # Assumindo que timezone está na tabela spots
                    "tide_phase": tide_phase,
                    **forecast_entry # Adiciona todas as chaves/valores da previsão
                }
                flat_forecast_entries.append(entry_with_spot_and_tide)

    if has_errors:
        return jsonify({"message": "Alguns dados não puderam ser recuperados.", "errors": error_messages, "data": flat_forecast_entries}), 207 # Partial Content
    
    return jsonify(flat_forecast_entries), 200