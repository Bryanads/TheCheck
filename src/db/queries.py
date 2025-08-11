import os
import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from src.db.connection import get_db_connection, close_db_connection


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
    # 'collection_timestamp' is not in the provided schema for forecasts table,
    # so I'm removing it from the update_set_parts. Assuming `updated_at` should be used.
    # REMOVED: update_set_parts.append(sql.SQL("updated_at = NOW()"))

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
        timestamp_utc = datetime.datetime.fromisoformat(entry['time'])

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
            height = EXCLUDED.height;
            -- Removed updated_at as it's not in the provided schema
    """)
    print(f"Starting insertion/update of {len(extremes_data)} tide extremes...")
    for extreme in extremes_data:
        timestamp_utc = datetime.datetime.fromisoformat(extreme['time'].replace('Z', '+00:00')).replace(tzinfo=datetime.timezone.utc)
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
        cur = conn.cursor(cursor_factory=RealDictCursor) # Usando RealDictCursor
        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots ORDER BY spot_id;")
        spots = cur.fetchall()
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
        cur = conn.cursor(cursor_factory=RealDictCursor) # Usando RealDictCursor
        cur.execute("SELECT spot_id, spot_name, latitude, longitude, timezone FROM spots WHERE spot_id = %s;", (spot_id,))
        spot = cur.fetchone()
        return spot
    except Exception as e:
        print(f"Error fetching spot by ID {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_forecasts_from_db(spot_id, start_utc, end_utc):
    """
    Fetches forecast data for a specific spot within a given UTC time range.
    Returns a list of dictionaries with forecast entries.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
    except Exception as e:
        print(f"Error fetching forecasts for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_tides_forecast_from_db(spot_id, start_utc, end_utc):
    """
    Fetches tide forecast data for a specific spot within a given UTC time range.
    Returns a list of dictionaries with tide entries.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor(cursor_factory=RealDictCursor) # Usando RealDictCursor
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
    except Exception as e:
        print(f"Error fetching tides for spot {spot_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# --- Funções de Usuário ---

def create_user(name, email, password_hash, surf_level, goofy_regular_stance,
                preferred_wave_direction, bio, profile_picture_url):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()
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
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        close_db_connection(conn, cur)

def get_user_by_email(email):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM users WHERE email = %s;"
        cur.execute(query, (email,))
        user = cur.fetchone()
        return user
    except Exception as e:
        raise e
    finally:
        close_db_connection(conn, cur)

def get_user_by_id(user_id):
    """
    Fetches user data by user_id.
    Returns a dictionary with keys in snake_case.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT user_id, name, email, password_hash, surf_level, goofy_regular_stance, preferred_wave_direction, bio, profile_picture_url, registration_timestamp, last_login_timestamp FROM users WHERE user_id = %s;"
        cur.execute(query, (user_id,))
        user = cur.fetchone()

        return user
    except Exception as e:
        print(f"Error fetching user by ID {user_id}: {e}") # Adicionar log para depuração
        return None
    finally:
        close_db_connection(conn, cur)

def update_user_last_login(user_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()
        query = """
        UPDATE users
        SET last_login_timestamp = NOW()
        WHERE user_id = %s;
        """
        cur.execute(query, (str(user_id),))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        close_db_connection(conn, cur)

def update_user_profile(user_id, updates: dict):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        query_parts = []
        values_for_query = []
        for key, value in updates.items():
            query_parts.append(f"{key} = %s")
            values_for_query.append(value)

        if not query_parts:
            return # Nada para atualizar

        query_sql = f"UPDATE users SET {', '.join(query_parts)} WHERE user_id = %s;"
        values_for_query.append(str(user_id)) # Adiciona o user_id no final dos valores

        cur.execute(query_sql, tuple(values_for_query))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        close_db_connection(conn, cur)

def get_user_surf_level(user_id):
    """
    Recupera o nível de surf de um usuário pelo seu ID.
    Retorna o nível de surf como string ou None se não encontrado.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor() # Não precisa de RealDictCursor para uma única coluna
        query = "SELECT surf_level FROM users WHERE user_id = %s;"
        cur.execute(query, (str(user_id),))
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching surf level for user {user_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_spot_preferences(user_id, spot_id, preference_type='model'):
    """
    Recupera as preferências de um spot para um usuário,
    podendo ser do modelo ('model') ou manual ('user').
    Retorna um dicionário com as preferências ou None.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor) # Usando RealDictCursor

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
    except Exception as e:
        print(f"Error fetching {preference_type} preferences for user {user_id} and spot {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_level_spot_preferences(surf_level, spot_id):
    """
    Recupera as preferências de um spot para um nível de surf específico.
    Retorna um dicionário com as preferências ou None.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor) # Usando RealDictCursor

        query = """
        SELECT * FROM level_spot_preferences
        WHERE surf_level = %s AND spot_id = %s;
        """
        cur.execute(query, (surf_level, spot_id))
        preferences = cur.fetchone()
        return preferences
    except Exception as e:
        print(f"Error fetching level spot preferences for level {surf_level} and spot {spot_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)


# --- Funções para user_recommendation_presets ---

def create_user_recommendation_preset(user_id, preset_name, spot_ids, start_time, end_time, day_offset_default=None, is_default=False):
    """
    Cria um novo preset de recomendação para um usuário.
    day_offset_default agora aceita uma lista de inteiros. Se None, usa o padrão do DB.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        # Se este preset deve ser o padrão, desativa qualquer outro padrão existente para este usuário
        if is_default:
            cur.execute("UPDATE user_recommendation_presets SET is_default = FALSE WHERE user_id = %s AND is_default = TRUE;", (str(user_id),))

        # Ajusta day_offset_default para o default do DB se não for fornecido explicitamente
        # Ou garante que é uma lista para o psycopg2
        if day_offset_default is None:
            day_offset_value = None # psycopg2 usará o DEFAULT da coluna
        elif not isinstance(day_offset_default, list):
            # Se for um único inteiro (para compatibilidade ou caso de uso), converte para lista
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
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating user recommendation preset: {e}")
        raise e
    finally:
        close_db_connection(conn, cur)

def get_user_recommendation_presets(user_id):
    """
    Recupera todos os presets de recomendação de um usuário.
    Retorna uma lista de dicionários.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM user_recommendation_presets WHERE user_id = %s AND is_active = TRUE ORDER BY preset_name;"
        cur.execute(query, (str(user_id),))
        presets = cur.fetchall()
        return presets
    except Exception as e:
        print(f"Error fetching user recommendation presets for user {user_id}: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_default_user_recommendation_preset(user_id):
    """
    Recupera o preset de recomendação padrão (is_default = TRUE) de um usuário.
    Retorna um dicionário ou None.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM user_recommendation_presets WHERE user_id = %s AND is_default = TRUE AND is_active = TRUE;"
        cur.execute(query, (str(user_id),))
        preset = cur.fetchone()
        return preset
    except Exception as e:
        print(f"Error fetching default user recommendation preset for user {user_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def get_user_recommendation_preset_by_id(preset_id, user_id):
    """
    Recupera um preset de recomendação específico pelo ID e user_id.
    Retorna um dicionário ou None.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM user_recommendation_presets WHERE preset_id = %s AND user_id = %s AND is_active = TRUE;"
        cur.execute(query, (preset_id, str(user_id)))
        preset = cur.fetchone()
        return preset
    except Exception as e:
        print(f"Error fetching user recommendation preset by ID {preset_id}: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def update_user_recommendation_preset(preset_id, user_id, updates: dict):
    """
    Atualiza um preset de recomendação existente.
    Permite atualizar nome, spot_ids, horários, day_offset_default (como lista) e is_default.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()

        query_parts = []
        values_for_query = []

        if 'is_default' in updates and updates['is_default']:
            # Se o preset está sendo definido como padrão, desativa outros padrões
            cur.execute("UPDATE user_recommendation_presets SET is_default = FALSE WHERE user_id = %s AND is_default = TRUE AND preset_id != %s;", (str(user_id), preset_id))

        for key, value in updates.items():
            query_parts.append(f"{key} = %s")
            if key in ['spot_ids', 'day_offset_default']: # Ambos são arrays agora
                if not isinstance(value, list):
                    raise ValueError(f"Campo '{key}' deve ser uma lista.")
                values_for_query.append(value)
            elif isinstance(value, datetime.time): # Para start_time/end_time
                values_for_query.append(value.strftime('%H:%M:%S')) # Formata para string de tempo
            else:
                values_for_query.append(value)

        if not query_parts:
            return False # Nada para atualizar

        query_sql = f"UPDATE user_recommendation_presets SET {', '.join(query_parts)}, updated_at = NOW() WHERE preset_id = %s AND user_id = %s;"
        values_for_query.append(preset_id)
        values_for_query.append(str(user_id))

        cur.execute(query_sql, tuple(values_for_query))
        conn.commit()
        return cur.rowcount > 0 # Retorna True se alguma linha foi afetada
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating user recommendation preset {preset_id}: {e}")
        raise e
    finally:
        close_db_connection(conn, cur)

def delete_user_recommendation_preset(preset_id, user_id):
    """
    "Soft-deleta" um preset de recomendação, marcando-o como inativo.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Could not establish database connection.")
        cur = conn.cursor()
        query = """
        UPDATE user_recommendation_presets
        SET is_active = FALSE, updated_at = NOW()
        WHERE preset_id = %s AND user_id = %s;
        """
        cur.execute(query, (preset_id, str(user_id)))
        conn.commit()
        return cur.rowcount > 0 # Retorna True se alguma linha foi afetada
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting user recommendation preset {preset_id}: {e}")
        raise e
    finally:
        close_db_connection(conn, cur)