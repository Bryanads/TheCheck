
import arrow
import requests
import json
import os
import sys
import decimal
from src.db.queries import get_all_spots, insert_forecast_data, insert_extreme_tides_data
from src.config import (
    API_KEY_STORMGLASS, REQUEST_DIR, FORECAST_DAYS,
    WEATHER_API_URL, TIDE_SEA_LEVEL_API_URL, TIDE_EXTREMES_API_URL, PARAMS_WEATHER_API,
    TREATED_DIR
)
from src.forecast.data_processing import merge_stormglass_data, filter_forecast_time
from src.utils.utils import convert_to_localtime, load_json_data
from src.db.connection import get_db_connection, close_db_connection
from src.forecast.make_request import fetch_and_save_data, choose_spot_from_db

if __name__ == "__main__":
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)

    cursor = conn.cursor()

    available_spots = get_all_spots()
    if not available_spots:
        close_db_connection(conn, cursor)
        sys.exit(1)

    selected_spot = choose_spot_from_db(available_spots)
    if selected_spot is None:
        close_db_connection(conn, cursor)
        sys.exit(0)

    # Salva o spot selecionado
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError

    os.makedirs(REQUEST_DIR, exist_ok=True)
    with open(os.path.join(REQUEST_DIR, 'current_spot.json'), 'w') as f:
        json.dump(selected_spot, f, ensure_ascii=False, indent=4, default=decimal_default)

    spot_id = selected_spot['spot_id']

    # Configuração do período de previsão
    start = arrow.now()
    end = start.shift(days=FORECAST_DAYS)
    headers = {'Authorization': API_KEY_STORMGLASS}

    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Busca os dados da API
    weather_data = fetch_and_save_data(
        WEATHER_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'params': ','.join(PARAMS_WEATHER_API),
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'weather_data.json',
        "weather"
    )

    sea_level_data = fetch_and_save_data(
        TIDE_SEA_LEVEL_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'params': 'seaLevel',
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'sea_level_data.json',
        "sea level"
    )

    tide_extremes_data = fetch_and_save_data(
        TIDE_EXTREMES_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'tide_extremes_data.json',
        "tide extremes"
    )

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

    conn.commit()
    close_db_connection(conn, cursor)
    print("Dados processados e inseridos com sucesso.")

