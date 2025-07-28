import json
import os
import arrow
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

# Database Connection Details
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

OUTPUT_DIR = 'api_responses' # Directory where merged JSON is located

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def get_praia_id(cursor, nome_praia, latitude, longitude):
    """
    Checks if the beach already exists in the database.
    If it exists, returns its ID. If not, inserts and returns the new ID.
    """
    cursor.execute(
        "SELECT id_praia FROM praias WHERE nome_praia = %s",
        (nome_praia,)
    )
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        # If beach doesn't exist, insert it. Note: 'tipo_fundo', 'orientacao_costa', etc.
        # are optional here. You might want to add them via a separate script or default.
        cursor.execute(
            """
            INSERT INTO praias (nome_praia, latitude, longitude)
            VALUES (%s, %s, %s)
            RETURNING id_praia;
            """,
            (nome_praia, latitude, longitude)
        )
        new_id = cursor.fetchone()[0]
        print(f"Praia '{nome_praia}' inserted with ID: {new_id}")
        return new_id

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

def insert_previsao_horaria(cursor, id_praia, merged_hourly_data):
    """
    Inserts/Updates the hourly forecast data into the previsoes_horarias table.
    """
    if not merged_hourly_data:
        print("No hourly data to insert.")
        return

    # Define columns for INSERT
    columns_names = sql.SQL("""
        id_praia, timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
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
    update_set = sql.SQL(", ").join(update_set_parts)

    insert_query = sql.SQL("""
        INSERT INTO previsoes_horarias ({columns})
        VALUES ({values})
        ON CONFLICT (id_praia, timestamp_utc) DO UPDATE SET
            {update_set};
    """).format(
        columns=columns_names,
        values=sql.SQL(', ').join(sql.Placeholder() * (len(cols_to_update) + 2)), # +2 for id_praia, timestamp_utc
        update_set=update_set
    )

    print(f"Starting insertion/update of {len(merged_hourly_data)} hourly forecasts...")
    for entry in merged_hourly_data:
        # Convert timestamp string to datetime object (UTC timezone from StormGlass)
        timestamp_utc = arrow.get(entry['time']).to('utc').datetime

        values_to_insert = (
            id_praia,
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
            entry.get('seaLevel_sg') # This should now be correct from merged data
        )
        try:
            cursor.execute(insert_query, values_to_insert)
        except Exception as e:
            print(f"Error inserting/updating hourly forecast for {id_praia} at {timestamp_utc}: {e}")
            # If an error occurs, the current transaction is aborted. 
            # We continue processing, but you might want to log/handle this differently.
            # A rollback is typically done at the end of the main transaction if ANY errors occur.
    print("Hourly forecast insertion/update process finished.")

if __name__ == "__main__":
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            exit(1)
        cur = conn.cursor()

        # Define the beach for which we are inserting data
        praia_nome = "Barra"
        # Use the actual coordinates of Barra (or fetch from DB if available)
        praia_lat = -23.0094000
        praia_lon = -43.3659000

        # Get or insert the beach ID
        praia_id = get_praia_id(cur, praia_nome, praia_lat, praia_lon)
        if praia_id is None:
            print(f"Could not get or create ID for beach '{praia_nome}'. Aborting.")
            conn.rollback()
            exit(1)
        
        # Load the merged JSON data
        merged_filename = f'merged_hourly_data_{praia_nome.replace(" ", "_").lower()}.json'
        merged_data = load_merged_data(merged_filename)

        if merged_data:
            insert_previsao_horaria(cur, praia_id, merged_data)
            conn.commit()
            print(f"Hourly forecast data for '{praia_nome}' successfully committed to database.")
        else:
            print("No merged data found to insert.")

    except Exception as e:
        print(f"An unexpected error occurred during hourly forecast insertion: {e}")
        if conn:
            conn.rollback()
            print("Transaction rolled back.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Database connection closed.")