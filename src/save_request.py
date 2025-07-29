import json
import os
import arrow
import sys
import datetime
from psycopg2 import sql
from dotenv import load_dotenv
from db_utils import get_db_connection, close_db_connection

load_dotenv()

OUTPUT_DIR = 'data' # Directory where merged JSON is located

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
        print(f"Error: Merged data file '{filepath}' not found. Please run merge_data.py first.")
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
        print(f"Error: Tide extremes data file '{filepath}' not found. Please run request_tide_extremes.py first.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. File might be corrupted.")
        return None
    
"""
-------------------------------------------------------------------------------
----------------------- INSERT DATA INTO DATABASE -----------------------------
-------------------------------------------------------------------------------
"""

def insert_forecast(cursor, spot_id, forecast_data):
    """
    Inserts/Updates the forecast data into the previsoes_horarias table.
    """
    if not forecast_data:
        print("No hourly data to insert.")
        return

    # Define columns for INSERT
    columns_names = sql.SQL("""
        spot_id, timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
        swell_height_sg, swell_direction_sg, swell_period_sg, secondary_swell_height_sg,
        secondary_swell_direction_sg, secondary_swell_period_sg, wind_speed_sg,
        wind_direction_sg, water_temperature_sg, air_temperature_sg, current_speed_sg,
        current_direction_sg, sea_level_sg
    """)
    
    # Define columns for ON CONFLICT DO UPDATE SET
    # These match the order of values provided in the execute call
    cols_to_update = [
        "wave_height_sg", "wave_direction_sg", "wave_period_sg",
        "swell_height_sg", "swell_direction_sg", "swell_period_sg",
        "secondary_swell_height_sg", "secondary_swell_direction_sg",
        "secondary_swell_period_sg", "wind_speed_sg", "wind_direction_sg",
        "water_temperature_sg", "air_temperature_sg", "current_speed_sg",
        "current_direction_sg", "sea_level_sg"
    ]
    
    update_set_parts = [
        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
        for col in cols_to_update
    ]
    update_set_parts.append(sql.SQL("collection_timestamp = NOW()"))

    update_set = sql.SQL(", ").join(update_set_parts)

    insert_query = sql.SQL("""
        INSERT INTO forecasts ({columns})
        VALUES ({values})
        ON CONFLICT (spot_id, timestamp_utc) DO UPDATE SET
            {update_set};
    """).format(
        columns=columns_names,
        values=sql.SQL(', ').join(sql.Placeholder() * (len(cols_to_update) + 2)), # +2 for spot_id, timestamp_utc
        update_set=update_set
    )

    print(f"Starting insertion/update of {len(forecast_data)} hourly forecasts...")
    for entry in forecast_data:
        # Convert timestamp string to datetime object (UTC timezone from StormGlass)
        timestamp_utc = arrow.get(entry['time']).to('utc').datetime.replace(tzinfo=datetime.timezone.utc)
        values_to_insert = (
            spot_id,
            timestamp_utc,
            entry.get('waveHeight_sg'),
            entry.get('waveDirection_sg'),
            entry.get('wavePeriod_sg'),
            entry.get('swellHeight_sg'),
            entry.get('swellDirection_sg'),
            entry.get('swellPeriod_sg'),
            entry.get('secondarySwellHeight_sg'),
            entry.get('secondarySwellDirection_sg'),
            entry.get('secondarySwellPeriod_sg'),
            entry.get('windSpeed_sg'),
            entry.get('windDirection_sg'),
            entry.get('waterTemperature_sg'),
            entry.get('airTemperature_sg'),
            entry.get('currentSpeed_sg'),
            entry.get('currentDirection_sg'),
            entry.get('seaLevel_sg') 
        )
        try:
            cursor.execute(insert_query, values_to_insert)
        except Exception as e:
            print(f"Error inserting/updating forecast for {spot_id} at {timestamp_utc}: {e}")
            # If an error occurs, the current transaction is aborted. 
            # We continue processing, but you might want to log/handle this differently.
            # A rollback is typically done at the end of the main transaction if ANY errors occur.
    print("Forecast insertion/update process finished.")

def insert_extreme_tides(cursor, spot_id, extremes_data):
    """
    Inserts/Updates the tide extremes data into the mares table.
    """
    if not extremes_data:
        print("No tide extremes data to insert.")
        return

    insert_query_tide = sql.SQL("""
        INSERT INTO tides_forecast (spot_id, timestamp_utc, tide_type, height)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (spot_id, timestamp_utc) DO UPDATE SET
            tide_type = EXCLUDED.tide_type,
            height = EXCLUDED.height,
            collection_timestamp = NOW();
    """)
    print(f"Starting insertion/update of {len(extremes_data)} tide extremes...")
    for extreme in extremes_data:
        timestamp_utc = arrow.get(extreme['time']).to('utc').datetime
        tide_type = extreme['type']
        tide_height = extreme.get('height') 

        try:
            cursor.execute(insert_query_tide, (spot_id, timestamp_utc, tide_type, tide_height))
        except Exception as e:
            print(f"Error inserting/updating tide extreme for {spot_id} at {timestamp_utc}: {e}")
            # Similar to hourly forecast, errors abort the transaction.
    print("Tide extremes insertion/update process finished.")

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
        insert_forecast(cursor, spot_id, forecast_data)


    tide_extremes_data = load_tide_extremes_data('tide_extremes_data.json')
    if tide_extremes_data is None:
        print("No tide extremes data to process. Exiting.")
        close_db_connection(conn, cursor)
        sys.exit(1)
    else:
        insert_extreme_tides(cursor, spot_id, tide_extremes_data)

    conn.commit()
    close_db_connection(conn, cursor)