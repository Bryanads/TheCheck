import arrow
import datetime
from psycopg2 import sql
from src.db.connection import get_db_connection, close_db_connection

def add_spot_to_db(name, latitude, longitude):
    """
    Add a new beach (spot) to the database.
    If the beach already exists, it will not be added again.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        # Verifica se a praia já existe
        cur.execute("SELECT spot_id FROM spots WHERE spot_name = %s", (name,))
        if cur.fetchone():
            print(f"Spot '{name}' already exists in the database.")
            return

        cur.execute(
            """
            INSERT INTO spots (spot_name, latitude, longitude)
            VALUES (%s, %s, %s)
            RETURNING spot_id;
            """,
            (name, latitude, longitude)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Spot '{name}' (ID: {new_id}, Lat: {latitude}, Lng: {longitude}) addition completed!")
        return new_id

    except Exception as e:
        print(f"Error while adding '{name}': {e}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error.")
        return None
    finally:
        close_db_connection(conn, cur)


def get_all_spots_from_db():
    """
    Loads all registered spots from the database.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        cur.execute("SELECT spot_id, spot_name, latitude, longitude FROM spots ORDER BY spot_id;")
        spots_db = cur.fetchall()

        if not spots_db:
            print("No spots found in the database. Please add spots.")
            return []

        formatted_spots = []
        for s_id, s_name, s_lat, s_lon in spots_db:
            formatted_spots.append({
                'spot_id': s_id,
                'name': s_name,
                'latitude': s_lat,
                'longitude': s_lon
            })
        return formatted_spots
    except Exception as e:
        print(f"Error loading spots from the database: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def insert_forecast_data(cursor, spot_id, forecast_data):
    """
    Inserts/Updates the forecast data into the forecasts table.
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

def insert_extreme_tides_data(cursor, spot_id, extremes_data):
    """
    Inserts/Updates the tide extremes data into the tides_forecast table.
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

def get_spot_by_id(spot_id):
    """
    Fetches details for a single surf spot by its ID.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor()
        cur.execute("SELECT spot_id, spot_name, latitude, longitude FROM spots WHERE spot_id = %s;", (spot_id,))

        result = cur.fetchone()
        if result:
            return {
                'spot_id': result[0],
                'name': result[1], # Certifique-se de que este 'name' corresponde ao índice da coluna que você selecionou acima
                'latitude': result[2],
                'longitude': result[3]
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching spot details for ID {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)
