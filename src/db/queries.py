import os
import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from src.db.connection import get_db_connection, close_db_connection
from contextlib import contextmanager

# --- Context Manager para conexão e cursor ---

@contextmanager
def db_cursor(dict_cursor=False):
    conn = get_db_connection()
    cur = None
    try:
        if conn is None:
            raise Exception("Could not establish database connection.")
        if dict_cursor:
            cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cur = conn.cursor()
        yield conn, cur
    finally:
        close_db_connection(conn, cur)

# --- Funções de Escrita de Dados (INSERT/UPDATE) ---

def add_spot_to_db(name, latitude, longitude, timezone):
    """
    Add a new beach (spot) to the database.
    If the beach already exists, it will not be added again.
    """
    with db_cursor() as (conn, cur):
        cur.execute("SELECT spot_id FROM spots WHERE spot_name = %s", (name,))
        if cur.fetchone():
            print(f"Spot '{name}' already exists in the database.")
            return None

        cur.execute(
            """
            INSERT INTO spots (spot_name, latitude, longitude, timezone)
            VALUES (%s, %s, %s, %s)
            RETURNING spot_id;
            """,
            (name, latitude, longitude, timezone)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Spot '{name}' (ID: {new_id}, Lat: {latitude}, Lng: {longitude}, Timezone: {timezone}) addition completed!")
        return new_id

def insert_forecast_data(spot_id, forecast_data):
    """
    Inserts/Updates the forecast data into the forecasts table.
    Usa context manager para conexão e cursor.
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
    with db_cursor() as (conn, cursor):
        for entry in forecast_data:
            timestamp_utc = datetime.datetime.fromisoformat(entry['time'])
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
        conn.commit()
    print("Forecast insertion/update process finished.")

def insert_extreme_tides_data(spot_id, extremes_data):
    """
    Inserts/Updates the tide extremes data into the tides_forecast table.
    Usa context manager para conexão e cursor.
    """
    if not extremes_data:
        print("No tide extremes data to insert.")
        return

    insert_query_tide = sql.SQL("""
        INSERT INTO tides_forecast (spot_id, timestamp_utc, tide_type, height)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (spot_id, timestamp_utc) DO UPDATE SET
            tide_type = EXCLUDED.tide_type,
            height = EXCLUDED.height;
    """)
    print(f"Starting insertion/update of {len(extremes_data)} tide extremes...")
    with db_cursor() as (conn, cursor):
        for extreme in extremes_data:
            timestamp_utc = datetime.datetime.fromisoformat(extreme['time'].replace('Z', '+00:00')).replace(tzinfo=datetime.timezone.utc)
            tide_type = extreme['type']
            tide_height = extreme.get('height')
            try:
                cursor.execute(insert_query_tide, (spot_id, timestamp_utc, tide_type, tide_height))
            except Exception as e:
                print(f"Error inserting/updating tide extreme for {spot_id} at {timestamp_utc}: {e}")
        conn.commit()
    print("Tide extremes insertion/update process finished.")

# --- Funções de Leitura de Dados (GET) ---

def get_all_spots():
    """
    Recupera todos os spots de surf do banco de dados.
    Retorna uma lista de dicionários, cada um representando um spot, com chaves em snake_case.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots ORDER BY spot_id;")
        spots = cur.fetchall()
        if not spots:
            print("No spots found in the database. Please add spots.")
            return []
        return spots

def get_spot_by_id(spot_id):
    """
    Fetches details for a single surf spot by its ID.
    Returns a dictionary with keys in snake_case.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots WHERE spot_id = %s;", (spot_id,))
        spot = cur.fetchone()
        return spot

def get_forecasts_from_db(spot_id, start_utc, end_utc):
    """
    Fetches forecast data for a specific spot within a given UTC time range.
    Returns a list of dictionaries with forecast entries.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = """
        SELECT
            timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
            swell_height_sg, swell_direction_sg, swell_period_sg,
            secondary_swell_height_sg, secondary_swell_direction_sg, secondary_swell_period_sg,
            wind_speed_sg, wind_direction_sg, water_temperature_sg, air_temperature_sg,
            current_speed_sg, current_direction_sg, sea_level_sg
        FROM forecasts
        WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
        ORDER BY timestamp_utc;
        """
        cur.execute(query, (spot_id, start_utc, end_utc))
        forecasts = cur.fetchall()
        return forecasts

def get_tides_forecast_from_db(spot_id, start_utc, end_utc):
    """
    Fetches tide forecast data for a specific spot within a given UTC time range.
    Returns a list of dictionaries with tide entries.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = """
        SELECT
            timestamp_utc, tide_type, height
        FROM tides_forecast
        WHERE spot_id = %s AND timestamp_utc BETWEEN %s AND %s
        ORDER BY timestamp_utc;
        """
        cur.execute(query, (spot_id, start_utc, end_utc))
        tides = cur.fetchall()
        return tides

# --- Funções de Usuário ---

def create_user(name, email, password_hash, surf_level, goofy_regular_stance,
                preferred_wave_direction, bio, profile_picture_url):
    with db_cursor() as (conn, cur):
        query = """
        INSERT INTO users (name, email, password_hash, surf_level, goofy_regular_stance,
                            preferred_wave_direction, bio, profile_picture_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id;
        """
        cur.execute(query, (name, email, password_hash, surf_level, goofy_regular_stance,
                            preferred_wave_direction, bio, profile_picture_url))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id

def get_user_by_email(email):
    with db_cursor(dict_cursor=True) as (_, cur):
        query = "SELECT * FROM users WHERE email = %s;"
        cur.execute(query, (email,))
        user = cur.fetchone()
        return user

def get_user_by_id(user_id):
    """
    Fetches user data by user_id.
    Returns a dictionary with keys in snake_case.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = "SELECT user_id, name, email, password_hash, surf_level, goofy_regular_stance, preferred_wave_direction, bio, profile_picture_url, registration_timestamp, last_login_timestamp FROM users WHERE user_id = %s;"
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        return user

def update_user_last_login(user_id):
    with db_cursor() as (conn, cur):
        query = """
        UPDATE users
        SET last_login_timestamp = NOW()
        WHERE user_id = %s;
        """
        cur.execute(query, (str(user_id),))
        conn.commit()

def update_user_profile(user_id, updates: dict):
    with db_cursor() as (conn, cur):
        query_parts = []
        values_for_query = []
        for key, value in updates.items():
            query_parts.append(f"{key} = %s")
            values_for_query.append(value)

        if not query_parts:
            return

        query_sql = f"UPDATE users SET {', '.join(query_parts)} WHERE user_id = %s;"
        values_for_query.append(str(user_id))
        cur.execute(query_sql, tuple(values_for_query))
        conn.commit()

def get_user_surf_level(user_id):
    """
    Recupera o nível de surf de um usuário pelo seu ID.
    Retorna o nível de surf como string ou None se não encontrado.
    """
    with db_cursor() as (_, cur):
        query = "SELECT surf_level FROM users WHERE user_id = %s;"
        cur.execute(query, (str(user_id),))
        result = cur.fetchone()
        return result[0] if result else None

def get_spot_preferences(user_id, spot_id, preference_type='model'):
    """
    Recupera as preferências de um spot para um usuário,
    podendo ser do modelo ('model') ou manual ('user').
    Retorna um dicionário com as preferências ou None.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        if preference_type == 'model':
            table_name = "model_spot_preferences"
        elif preference_type == 'user':
            table_name = "user_spot_preferences"
        else:
            raise ValueError("preference_type deve ser 'model' ou 'user'.")

        query = sql.SQL("SELECT * FROM {} WHERE user_id = %s AND spot_id = %s;").format(
            sql.Identifier(table_name)
        )
        cur.execute(query, (str(user_id), spot_id))
        preferences = cur.fetchone()
        return preferences

def get_level_spot_preferences(surf_level, spot_id):
    """
    Recupera as preferências de um spot para um nível de surf específico.
    Retorna um dicionário com as preferências ou None.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = """
        SELECT * FROM level_spot_preferences
        WHERE surf_level = %s AND spot_id = %s;
        """
        cur.execute(query, (surf_level, spot_id))
        preferences = cur.fetchone()
        return preferences

# --- Funções para user_recommendation_presets ---

def create_user_recommendation_preset(user_id, preset_name, spot_ids, start_time, end_time, day_offset_default=None, is_default=False):
    """
    Cria um novo preset de recomendação para um usuário.
    day_offset_default agora aceita uma lista de inteiros. Se None, usa o padrão do DB.
    """
    with db_cursor() as (conn, cur):
        if is_default:
            cur.execute("UPDATE user_recommendation_presets SET is_default = FALSE WHERE user_id = %s AND is_default = TRUE;", (str(user_id),))

        if day_offset_default is None:
            day_offset_value = None
        elif not isinstance(day_offset_default, list):
            day_offset_value = [day_offset_default]
        else:
            day_offset_value = day_offset_default

        query = """
        INSERT INTO user_recommendation_presets (user_id, preset_name, spot_ids, start_time, end_time, day_offset_default, is_default)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING preset_id;
        """
        cur.execute(query, (str(user_id), preset_name, spot_ids, start_time, end_time, day_offset_value, is_default))
        preset_id = cur.fetchone()[0]
        conn.commit()
        return preset_id

def get_user_recommendation_presets(user_id):
    """
    Recupera todos os presets de recomendação de um usuário.
    Retorna uma lista de dicionários.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = "SELECT * FROM user_recommendation_presets WHERE user_id = %s AND is_active = TRUE ORDER BY preset_name;"
        cur.execute(query, (str(user_id),))
        presets = cur.fetchall()
        return presets

def get_default_user_recommendation_preset(user_id):
    """
    Recupera o preset de recomendação padrão (is_default = TRUE) de um usuário.
    Retorna um dicionário ou None.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = "SELECT * FROM user_recommendation_presets WHERE user_id = %s AND is_default = TRUE AND is_active = TRUE;"
        cur.execute(query, (str(user_id),))
        preset = cur.fetchone()
        return preset

def get_user_recommendation_preset_by_id(preset_id, user_id):
    """
    Recupera um preset de recomendação específico pelo ID e user_id.
    Retorna um dicionário ou None.
    """
    with db_cursor(dict_cursor=True) as (_, cur):
        query = "SELECT * FROM user_recommendation_presets WHERE preset_id = %s AND user_id = %s AND is_active = TRUE;"
        cur.execute(query, (preset_id, str(user_id)))
        preset = cur.fetchone()
        return preset

def update_user_recommendation_preset(preset_id, user_id, updates: dict):
    """
    Atualiza um preset de recomendação existente.
    Permite atualizar nome, spot_ids, horários, day_offset_default (como lista) e is_default.
    """
    with db_cursor() as (conn, cur):
        query_parts = []
        values_for_query = []

        if 'is_default' in updates and updates['is_default']:
            cur.execute("UPDATE user_recommendation_presets SET is_default = FALSE WHERE user_id = %s AND is_default = TRUE AND preset_id != %s;", (str(user_id), preset_id))

        for key, value in updates.items():
            query_parts.append(f"{key} = %s")
            if key in ['spot_ids', 'day_offset_default']:
                if not isinstance(value, list):
                    raise ValueError(f"Campo '{key}' deve ser uma lista.")
                values_for_query.append(value)
            elif isinstance(value, datetime.time):
                values_for_query.append(value.strftime('%H:%M:%S'))
            else:
                values_for_query.append(value)

        if not query_parts:
            return False

        query_sql = f"UPDATE user_recommendation_presets SET {', '.join(query_parts)}, updated_at = NOW() WHERE preset_id = %s AND user_id = %s;"
        values_for_query.append(preset_id)
        values_for_query.append(str(user_id))

        cur.execute(query_sql, tuple(values_for_query))
        conn.commit()
        return cur.rowcount > 0

def delete_user_recommendation_preset(preset_id, user_id):
    """
    "Soft-deleta" um preset de recomendação, marcando-o como inativo.
    """
    with db_cursor() as (conn, cur):
        query = """
        UPDATE user_recommendation_presets
        SET is_active = FALSE, updated_at = NOW()
        WHERE preset_id = %s AND user_id = %s;
        """
        cur.execute(query, (preset_id, str(user_id)))
        conn.commit()
        return cur.rowcount > 0

# --- Sugestão de índice para performance ---
# Certifique-se de ter índices em:
# - spots(spot_name)
# - forecasts(spot_id, timestamp_utc)
# - tides_forecast(spot_id, timestamp_utc)
# - users(email)
# - user_recommendation_presets(user_id, is_active)