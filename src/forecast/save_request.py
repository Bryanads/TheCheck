import json
import os
import sys
from src.db.connection import get_db_connection, close_db_connection
from src.db.queries import insert_forecast_data, insert_extreme_tides_data
from src.config import OUTPUT_DIR, REQUEST_DIR, TREATED_DIR
from src.forecast.data_processing import merge_stormglass_data, filter_forecast_time
from src.utils.utils import convert_to_localtime, load_json_data


def load_selected_spot():
    return load_json_data('current_spot.json', REQUEST_DIR)

if __name__ == "__main__":
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    cursor = conn.cursor()

    spot = load_selected_spot()
    if not spot:
        print("Nenhum spot selecionado. Rode make_request.py primeiro.")
        close_db_connection(conn, cursor)
        sys.exit(1)

    spot_id = spot['spot_id']

    # Etapa 1: merge dos dados
    merged = merge_stormglass_data('weather_data.json', 'sea_level_data.json', 'forecast_data.json')
    if not merged:
        print("Erro ao mesclar dados. Abortando inserção.")
        close_db_connection(conn, cursor)
        sys.exit(1)

    # Etapa 2: converter e filtrar
    localtime_data = convert_to_localtime(merged)
    filtered = filter_forecast_time(localtime_data)

    if not filtered:
        print("Nenhum dado de previsão válido após filtro. Abortando.")
        close_db_connection(conn, cursor)
        sys.exit(1)

    # Salvando no diretório 'treated'
    os.makedirs(TREATED_DIR, exist_ok=True)
    with open(os.path.join(TREATED_DIR, 'forecast_data.json'), 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=4)

    # Inserir no banco
    insert_forecast_data(cursor, spot_id, filtered)

    # Etapa 3: dados de marés extremas
    tide_raw = load_json_data('tide_extremes_data.json', REQUEST_DIR)
    if tide_raw and 'data' in tide_raw:
        tide_data = convert_to_localtime(tide_raw['data'])

        # Salvando no diretório 'treated'
        with open(os.path.join(TREATED_DIR, 'tide_extremes_filtered.json'), 'w', encoding='utf-8') as f:
            json.dump(tide_data, f, ensure_ascii=False, indent=4)

        insert_extreme_tides_data(cursor, spot_id, tide_data)
    else:
        print("Erro ao carregar marés extremas. Abortando.")
        close_db_connection(conn, cursor)
        sys.exit(1)

    conn.commit()
    close_db_connection(conn, cursor)
