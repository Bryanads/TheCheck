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

def get_user_surf_level(user_id):
    """
    Fetches the surf level for a given user.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor()
        cur.execute("SELECT surf_level FROM users WHERE user_id = %s;", (user_id,))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            print(f"User with ID {user_id} not found.")
            return None
    except Exception as e:
        print(f"Error fetching surf level for user {user_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_spot_preferences(spot_id, user_id=None, surf_level=None):
    """
    Fetches preferences for a given spot. Prioritizes user-specific preferences,
    falls back to surf_level preferences if user_id is provided and no specific
    user preference is found for the spot.

    Args:
        spot_id (int): The ID of the surf spot.
        user_id (int, optional): The ID of the user. If provided, user_spot_preferences
                                 will be checked first.
        surf_level (str, optional): The surf level (e.g., 'Intermediário', 'Maroleiro').
                                    Used if user_id is None or no user-specific preference exists.

    Returns:
        dict: A dictionary of preferences for the spot.
              Returns None if no preferences are found for the given criteria.
    """
    conn = None
    cur = None
    preferences = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor()

        # 1. Try to get user-specific preferences first
        if user_id:
            cur.execute("""
                SELECT
                    min_wave_height, max_wave_height, ideal_wave_height, preferred_wave_direction,
                    preferred_swell_direction, min_swell_period, max_swell_period, ideal_swell_period,
                    min_swell_height, max_swell_height, ideal_swell_height,
                    min_secondary_swell_height, max_secondary_swell_height, preferred_secondary_swell_direction,
                    min_secondary_swell_period, max_secondary_swell_period,
                    preferred_wind_direction, max_wind_speed, ideal_wind_speed,
                    ideal_tide_type,
                    min_water_temperature, max_water_temperature, ideal_water_temperature,
                    min_air_temperature, max_air_temperature, ideal_air_temperature,
                    max_current_speed, preferred_current_direction,
                    min_sea_level, max_sea_level, ideal_sea_level,
                    additional_considerations
                FROM user_spot_preferences
                WHERE user_id = %s AND spot_id = %s;
            """, (user_id, spot_id))
            user_pref = cur.fetchone()
            if user_pref:
                preferences = {
                    'min_wave_height': user_pref[0],
                    'max_wave_height': user_pref[1],
                    'ideal_wave_height': user_pref[2],
                    'preferred_wave_direction': user_pref[3],
                    'preferred_swell_direction': user_pref[4],
                    'min_swell_period': user_pref[5],
                    'max_swell_period': user_pref[6],
                    'ideal_swell_period': user_pref[7],
                    'min_swell_height': user_pref[8],
                    'max_swell_height': user_pref[9],
                    'ideal_swell_height': user_pref[10],
                    'min_secondary_swell_height': user_pref[11],
                    'max_secondary_swell_height': user_pref[12],
                    'preferred_secondary_swell_direction': user_pref[13],
                    'min_secondary_swell_period': user_pref[14],
                    'max_secondary_swell_period': user_pref[15],
                    'preferred_wind_direction': user_pref[16],
                    'max_wind_speed': user_pref[17],
                    'ideal_wind_speed': user_pref[18],
                    'ideal_tide_type': user_pref[19],
                    'min_water_temperature': user_pref[20],
                    'max_water_temperature': user_pref[21],
                    'ideal_water_temperature': user_pref[22],
                    'min_air_temperature': user_pref[23],
                    'max_air_temperature': user_pref[24],
                    'ideal_air_temperature': user_pref[25],
                    'max_current_speed': user_pref[26],
                    'preferred_current_direction': user_pref[27],
                    'min_sea_level': user_pref[28],
                    'max_sea_level': user_pref[29],
                    'ideal_sea_level': user_pref[30],
                    'additional_considerations': user_pref[31]
                }
                print(f"Found user-specific preferences for spot {spot_id} and user {user_id}.")
                return preferences

        # 2. If no user-specific preferences or no user_id, fall back to surf_level preferences
        if surf_level:
            cur.execute("""
                SELECT
                    min_wave_height, max_wave_height, ideal_wave_height, preferred_wave_direction,
                    preferred_swell_direction, min_swell_period, max_swell_period, ideal_swell_period,
                    min_swell_height, max_swell_height, ideal_swell_height,
                    min_secondary_swell_height, max_secondary_swell_height, preferred_secondary_swell_direction,
                    min_secondary_swell_period, max_secondary_swell_period,
                    preferred_wind_direction, max_wind_speed, ideal_wind_speed,
                    ideal_tide_type,
                    min_water_temperature, max_water_temperature, ideal_water_temperature,
                    min_air_temperature, max_air_temperature, ideal_air_temperature,
                    max_current_speed, preferred_current_direction,
                    min_sea_level, max_sea_level, ideal_sea_level,
                    additional_considerations
                FROM level_spot_preferences
                WHERE surf_level = %s AND spot_id = %s;
            """, (surf_level, spot_id))
            level_pref = cur.fetchone()
            if level_pref:
                preferences = {
                    'min_wave_height': level_pref[0],
                    'max_wave_height': level_pref[1],
                    'ideal_wave_height': level_pref[2],
                    'preferred_wave_direction': level_pref[3],
                    'preferred_swell_direction': level_pref[4],
                    'min_swell_period': level_pref[5],
                    'max_swell_period': level_pref[6],
                    'ideal_swell_period': level_pref[7],
                    'min_swell_height': level_pref[8],
                    'max_swell_height': level_pref[9],
                    'ideal_swell_height': level_pref[10],
                    'min_secondary_swell_height': level_pref[11],
                    'max_secondary_swell_height': level_pref[12],
                    'preferred_secondary_swell_direction': level_pref[13],
                    'min_secondary_swell_period': level_pref[14],
                    'max_secondary_swell_period': level_pref[15],
                    'preferred_wind_direction': level_pref[16],
                    'max_wind_speed': level_pref[17],
                    'ideal_wind_speed': level_pref[18],
                    'ideal_tide_type': level_pref[19],
                    'min_water_temperature': level_pref[20],
                    'max_water_temperature': level_pref[21],
                    'ideal_water_temperature': level_pref[22],
                    'min_air_temperature': level_pref[23],
                    'max_air_temperature': level_pref[24],
                    'ideal_air_temperature': level_pref[25],
                    'max_current_speed': level_pref[26],
                    'preferred_current_direction': level_pref[27],
                    'min_sea_level': level_pref[28],
                    'max_sea_level': level_pref[29],
                    'ideal_sea_level': level_pref[30],
                    'additional_considerations': level_pref[31]
                }
                print(f"Found level-specific preferences for spot {spot_id} and level '{surf_level}'.")
                return preferences
        print(f"No preferences found for spot {spot_id} (user: {user_id}, level: {surf_level}).")
        return None

    except Exception as e:
        print(f"Error fetching preferences for spot {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_forecast_data_for_spot(spot_id, start_time_utc, end_time_utc):
    """
    Fetches hourly forecast data for a specific spot within a time range.
    """
    conn = None
    cur = None
    forecasts = []
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        cur.execute("""
            SELECT
                timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
                swell_height_sg, swell_direction_sg, swell_period_sg, secondary_swell_height_sg,
                secondary_swell_direction_sg, secondary_swell_period_sg, wind_speed_sg,
                wind_direction_sg, water_temperature_sg, air_temperature_sg, current_speed_sg,
                current_direction_sg, sea_level_sg
            FROM forecasts
            WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
            ORDER BY timestamp_utc;
        """, (spot_id, start_time_utc, end_time_utc))

        rows = cur.fetchall()
        for row in rows:
            forecasts.append({
                'timestamp_utc': row[0],
                'waveHeight_sg': row[1],
                'waveDirection_sg': row[2],
                'wavePeriod_sg': row[3],
                'swellHeight_sg': row[4],
                'swellDirection_sg': row[5],
                'swellPeriod_sg': row[6],
                'secondarySwellHeight_sg': row[7],
                'secondarySwellDirection_sg': row[8],
                'secondarySwellPeriod_sg': row[9],
                'windSpeed_sg': row[10],
                'windDirection_sg': row[11],
                'waterTemperature_sg': row[12],
                'airTemperature_sg': row[13],
                'currentSpeed_sg': row[14],
                'currentDirection_sg': row[15],
                'seaLevel_sg': row[16],
            })
        return forecasts
    except Exception as e:
        print(f"Error fetching forecast data for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_tide_extremes_for_spot(spot_id, start_time_utc, end_time_utc):
    """
    Fetches tide extremes data for a specific spot within a time range.
    """
    conn = None
    cur = None
    tide_extremes = []
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        cur.execute("""
            SELECT
                timestamp_utc, tide_type, height
            FROM tides_forecast
            WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
            ORDER BY timestamp_utc;
        """, (spot_id, start_time_utc, end_time_utc))

        rows = cur.fetchall()
        for row in rows:
            tide_extremes.append({
                'timestamp_utc': row[0],
                'type': row[1],
                'height': row[2]
            })
        return tide_extremes
    except Exception as e:
        print(f"Error fetching tide extremes for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)
