import arrow
import datetime
from psycopg2 import sql
from src.db.connection import get_db_connection, close_db_connection


def _fetch_results_as_dict(cursor, fetch_method='all'):
    """
    Busca resultados de um cursor e os formata como uma lista de dicionários (ou um único dicionário),
    com as chaves em snake_case.
    """
    columns = [desc.name for desc in cursor.description]

    if fetch_method == 'one':
        row = cursor.fetchone()
        if not row:
            return None
        return dict(zip(columns, row))
    elif fetch_method == 'all':
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    return []

# --- Funções de Escrita de Dados (INSERT/UPDATE) ---

def add_spot_to_db(name, latitude, longitude, timezone):
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
            return None # Retorna None se já existe

        cur.execute(
            """
            INSERT INTO spots (spot_name, latitude, longitude, timezone)
            VALUES (%s, %s, %s, %s)
            RETURNING spot_id;
            """,
            (name, latitude, longitude, timezone) # Adicionado timezone aqui
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Spot '{name}' (ID: {new_id}, Lat: {latitude}, Lng: {longitude}, Timezone: {timezone}) addition completed!")
        return new_id

    except Exception as e:
        print(f"Error while adding '{name}': {e}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error.")
        return None
    finally:
        close_db_connection(conn, cur)

def insert_forecast_data(cursor, spot_id, forecast_data):
    """
    Inserts/Updates the forecast data into the forecasts table.
    Assumes cursor and connection handling are managed by the calling function.
    """
    if not forecast_data:
        print("No hourly data to insert.")
        return

    columns_names = sql.SQL("""
        spot_id, timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
        swell_height_sg, swell_direction_sg, swell_period_sg, secondary_swell_height_sg,
        secondary_swell_direction_sg, secondary_swell_period_sg, wind_speed_sg,
        wind_direction_sg, water_temperature_sg, air_temperature_sg, current_speed_sg,
        current_direction_sg, sea_level_sg
    """)

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
        # As chaves de entrada do 'entry' permanecem em camelCase (vindo da API externa)
        # mas são mapeadas para as colunas snake_case do banco de dados.
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
            # Note: For bulk inserts, consider adding failed items to a list and handling transaction rollback for all
    print("Forecast insertion/update process finished.")

def insert_extreme_tides_data(cursor, spot_id, extremes_data):
    """
    Inserts/Updates the tide extremes data into the tides_forecast table.
    Assumes cursor and connection handling are managed by the calling function.
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
            # Note: For bulk inserts, consider adding failed items to a list and handling transaction rollback for all
    print("Tide extremes insertion/update process finished.")

# --- Funções de Leitura de Dados (GET) ---

def get_all_spots():
    """
    Recupera todos os spots de surf do banco de dados.
    Retorna uma lista de dicionários, cada um representando um spot, com chaves em snake_case.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots ORDER BY spot_id;")

        spots = _fetch_results_as_dict(cur, fetch_method='all')

        if not spots:
            print("No spots found in the database. Please add spots.")
            return []

        return spots
    except Exception as e:
        print(f"Error loading spots from the database: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_spot_by_id(spot_id):
    """
    Fetches details for a single surf spot by its ID.
    Returns a dictionary with keys in snake_case.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor()
        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots WHERE spot_id = %s;", (spot_id,))

        spot = _fetch_results_as_dict(cur, fetch_method='one')

        if not spot:
            print(f"No spot found with ID {spot_id}.")
        return spot
    except Exception as e:
        print(f"Error fetching spot details for ID {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_user_surf_level(user_id):
    """
    Fetches the surf level for a given user.
    Assumes 'surf_level' column is directly in the 'users' table.
    Returns a string or None.
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
            print(f"User with ID {user_id} not found or no surf level set.")
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

    Returns:
        dict: A dictionary of preferences for the spot, with keys in snake_case.
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

        # 1. Tenta obter as preferências específicas do usuário primeiro
        if user_id:
            query = """
                SELECT
                    min_wave_height, max_wave_height, ideal_wave_height, preferred_wave_direction,
                    min_wave_period, max_wave_period, ideal_wave_period,
                    min_swell_height, max_swell_height, ideal_swell_height, preferred_swell_direction,
                    min_swell_period, max_swell_period, ideal_swell_period,
                    ideal_secondary_swell_height, preferred_secondary_swell_direction, ideal_secondary_swell_period,
                    min_wind_speed, max_wind_speed, ideal_wind_speed, preferred_wind_direction,
                    ideal_tide_type,
                    min_sea_level, max_sea_level, ideal_sea_level,
                    ideal_water_temperature,
                    ideal_air_temperature,
                    ideal_current_speed, preferred_current_direction,
                    additional_considerations
                FROM user_spot_preferences
                WHERE user_id = %s AND spot_id = %s;
            """
            cur.execute(query, (user_id, spot_id))
            preferences = _fetch_results_as_dict(cur, fetch_method='one')

            if preferences:
                print(f"Found user-specific preferences for spot {spot_id} and user {user_id}.")
                return preferences

        # 2. Se não houver preferências específicas do usuário ou user_id, volta para as preferências de nível de surf
        if surf_level:
            query = """
                SELECT
                    min_wave_height, max_wave_height, ideal_wave_height, preferred_wave_direction,
                    min_wave_period, max_wave_period, ideal_wave_period,
                    min_swell_height, max_swell_height, ideal_swell_height, preferred_swell_direction,
                    min_swell_period, max_swell_period, ideal_swell_period,
                    ideal_secondary_swell_height, preferred_secondary_swell_direction, ideal_secondary_swell_period,
                    min_wind_speed, max_wind_speed, ideal_wind_speed, preferred_wind_direction,
                    ideal_tide_type,
                    min_sea_level, max_sea_level, ideal_sea_level,
                    ideal_water_temperature,
                    ideal_air_temperature,
                    ideal_current_speed, preferred_current_direction,
                    additional_considerations
                FROM level_spot_preferences
                WHERE surf_level = %s AND spot_id = %s;
            """
            cur.execute(query, (surf_level, spot_id))
            preferences = _fetch_results_as_dict(cur, fetch_method='one')

            if preferences:
                print(f"Found level-specific preferences for spot {spot_id} and level '{surf_level}'.")
                return preferences

        print(f"No preferences found for spot {spot_id} (user: {user_id}, level: {surf_level}).")
        return None

    except Exception as e:
        print(f"Error fetching preferences for spot {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_forecasts_from_db(spot_id, start_time_utc, end_time_utc):
    """
    Fetches hourly forecast data for a specific spot within a time range.
    Returns a list of dictionaries with keys in snake_case.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        query = """
            SELECT
                spot_id, timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
                swell_height_sg, swell_direction_sg, swell_period_sg, secondary_swell_height_sg,
                secondary_swell_direction_sg, secondary_swell_period_sg, wind_speed_sg,
                wind_direction_sg, water_temperature_sg, air_temperature_sg, current_speed_sg,
                current_direction_sg, sea_level_sg
            FROM forecasts
            WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
            ORDER BY timestamp_utc;
        """
        cur.execute(query, (spot_id, start_time_utc, end_time_utc))

        forecasts = _fetch_results_as_dict(cur, fetch_method='all')
        return forecasts
    except Exception as e:
        print(f"Error fetching forecast data for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_tides_forecast_from_db(spot_id, start_time_utc, end_time_utc):
    """
    Fetches tide extremes data for a specific spot within a time range.
    Returns a list of dictionaries with keys in snake_case.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        query = """
            SELECT
                timestamp_utc, tide_type, height
            FROM tides_forecast
            WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
            ORDER BY timestamp_utc;
        """
        cur.execute(query, (spot_id, start_time_utc, end_time_utc))

        tide_extremes = _fetch_results_as_dict(cur, fetch_method='all')
        return tide_extremes
    except Exception as e:
        print(f"Error fetching tide extremes for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)