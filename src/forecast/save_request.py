import json
import os
import arrow
import sys
import datetime
from src.db.connection import get_db_connection, close_db_connection
from src.db.queries import insert_forecast_data, insert_extreme_tides_data
from src.config import OUTPUT_DIR # Importa OUTPUT_DIR do config


"""
-------------------------------------------------------------------------------
----------------------- LOAD DATA FROM LOCAL JSON -----------------------------
-------------------------------------------------------------------------------
"""
def load_selected_spot():
    filepath = os.path.join(OUTPUT_DIR, 'current_spot.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar o spot selecionado: {e}")
        return None

def load_merged_data(filename):
    """Loads merged hourly data from a JSON file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Merged data file '{filepath}' not found. Please run make_request.py first.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. File might be corrupted.")
        return None

def load_tide_extremes_data(filename):
    """Loads tide extremes data from a JSON file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Tide extremes API has a 'data' key for the list of extremes
            return data.get('data', [])
    except FileNotFoundError:
        print(f"Error: Tide extremes data file '{filepath}' not found. Please run make_request.py first.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. File might be corrupted.")
        return None

if __name__ == "__main__":
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    cursor = conn.cursor()

    spot = load_selected_spot()
    if spot is None:
        print("Nenhum spot selecionado foi encontrado. Rode make_request.py primeiro.")
        close_db_connection(conn, cursor)
        sys.exit(1)
    spot_id = spot['spot_id']

    forecast_data = load_merged_data('forecast_data.json')
    if forecast_data is None:
        print("No forecast data to process. Exiting.")
        close_db_connection(conn, cursor)
        sys.exit(1)
    else:
        # Chama a função de queries para inserir
        insert_forecast_data(cursor, spot_id, forecast_data)


    tide_extremes_data = load_tide_extremes_data('tide_extremes_data.json')
    if tide_extremes_data is None:
        print("No tide extremes data to process. Exiting.")
        close_db_connection(conn, cursor)
        sys.exit(1)
    else:
        # Chama a função de queries para inserir
        insert_extreme_tides_data(cursor, spot_id, tide_extremes_data)

    conn.commit()
    close_db_connection(conn, cursor)