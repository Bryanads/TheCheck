from flask import Blueprint, request, jsonify
import arrow
from src.db.queries import get_spot_by_id, get_forecasts_from_db, get_tides_forecast_from_db
from src.recommendation.data_fetcher import determine_tide_phase

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
        base_date = arrow.utcnow().shift(days=day_offset).floor('day')
        start_utc = base_date.replace(hour=0, minute=0, second=0, microsecond=0).to('utc').datetime
        end_utc = base_date.replace(hour=23, minute=59, second=59, microsecond=999999).to('utc').datetime

        for s_id in spot_ids:
            spot_details = get_spot_by_id(s_id)
            if not spot_details:
                error_messages.append(f"Spot com ID {s_id} não encontrado.")
                has_errors = True
                continue

            spot_name = spot_details['spot_name']
            spot_timezone = spot_details['timezone']

            forecasts = get_forecasts_from_db(s_id, start_utc, end_utc)
            tides = get_tides_forecast_from_db(s_id, start_utc, end_utc)

            if not forecasts:
                error_messages.append(f"Nenhum dado de previsão para o spot {spot_name} (ID: {s_id}) no dia {base_date.format('YYYY-MM-DD')}.")
                has_errors = True
                continue

            for forecast in forecasts:
                timestamp_utc = forecast['timestamp_utc']
                sea_level_sg = forecast.get('sea_level_sg')
                tide_phase = determine_tide_phase(timestamp_utc, sea_level_sg, tides)

                local_time = arrow.get(timestamp_utc).to(spot_timezone).format('YYYY-MM-DD HH:mm:ss ZZ')

                flat_forecast_entries.append({
                    **forecast,
                    "tide_phase": tide_phase,
                    "local_time": local_time,
                    "spot_id": s_id,
                    "spot_name": spot_name,
                    "timezone": spot_timezone,
                    "date": base_date.format('YYYY-MM-DD')
                })

    if has_errors:
        return jsonify({"errors": error_messages, "forecast_data": flat_forecast_entries}), 404
    else:
        return jsonify(flat_forecast_entries), 200
