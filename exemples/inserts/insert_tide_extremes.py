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

OUTPUT_DIR = 'api_responses' # Directory where JSON is located

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
    (This function is duplicated for self-contained scripts, but in a full app,
    it would be a shared utility).
    """
    cursor.execute(
        "SELECT id_praia FROM praias WHERE nome_praia = %s",
        (nome_praia,)
    )
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
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

def insert_mares_extremas(cursor, id_praia, extremes_data):
    """
    Inserts/Updates the tide extremes data into the mares table.
    """
    if not extremes_data:
        print("No tide extremes data to insert.")
        return

    insert_query_tide = sql.SQL("""
        INSERT INTO mares (id_praia, timestamp_utc, tipo, altura)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id_praia, timestamp_utc) DO UPDATE SET
            tipo = EXCLUDED.tipo,
            altura = EXCLUDED.altura;
    """)
    print(f"Starting insertion/update of {len(extremes_data)} tide extremes...")
    for extreme in extremes_data:
        timestamp_utc = arrow.get(extreme['time']).to('utc').datetime
        tide_type = extreme['type']
        tide_height = extreme.get('height') 

        # IMPORTANT: Based on your schema, 'altura' is NOT NULL.
        # If tide_height can be None from StormGlass, you *must* handle it here
        # by providing a default (e.g., 0.0 or a sentinel value like -999.0)
        # OR by changing your database schema to allow NULL for 'altura'.
        # Since you said the previous script fetched it without nulls, we assume it's always there.
        # If it happens again, consider:
        # if tide_height is None:
        #    tide_height = 0.0 # Or skip the record if invalid without height

        try:
            cursor.execute(insert_query_tide, (id_praia, timestamp_utc, tide_type, tide_height))
        except Exception as e:
            print(f"Error inserting/updating tide extreme for {id_praia} at {timestamp_utc}: {e}")
            # Similar to hourly forecast, errors abort the transaction.
    print("Tide extremes insertion/update process finished.")

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
        
        # Load the tide extremes JSON data
        extremes_filename = f'tide_extremes_data_{praia_nome.replace(" ", "_").lower()}.json'
        extremes_data = load_tide_extremes_data(extremes_filename)

        if extremes_data:
            insert_mares_extremas(cur, praia_id, extremes_data)
            conn.commit()
            print(f"Tide extremes data for '{praia_nome}' successfully committed to database.")
        else:
            print("No tide extremes data found to insert.")

    except Exception as e:
        print(f"An unexpected error occurred during tide extremes insertion: {e}")
        if conn:
            conn.rollback()
            print("Transaction rolled back.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Database connection closed.")