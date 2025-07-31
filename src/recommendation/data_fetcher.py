import datetime
from src.db.connection import get_db_connection, close_db_connection
from src.db.queries import get_all_spots_from_db
import arrow # Para lidar com timestamps


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
                    min_wave_height, max_wave_height, preferred_swell_direction,
                    min_swell_period, max_swell_period, preferred_wind_direction,
                    max_wind_speed, additional_considerations
                    -- REMOVIDO: ideal_tide_type (não existe na tabela user_spot_preferences conforme seu DDL)
                FROM user_spot_preferences
                WHERE user_id = %s AND spot_id = %s;
            """, (user_id, spot_id))
            user_pref = cur.fetchone()
            if user_pref:
                preferences = {
                    'min_wave_height': user_pref[0],
                    'max_wave_height': user_pref[1],
                    'preferred_swell_direction': user_pref[2],
                    'min_swell_period': user_pref[3],
                    'max_swell_period': user_pref[4],
                    'preferred_wind_direction': user_pref[5],
                    'max_wind_speed': user_pref[6],
                    'ideal_tide_type': None, # Adicionar explicitamente como None, pois não vem da tabela de usuário
                    'additional_considerations': user_pref[7]
                }
                print(f"Found user-specific preferences for spot {spot_id} and user {user_id}.")
                return preferences

        # 2. If no user-specific preferences or no user_id, fall back to surf_level preferences
        if surf_level:
            cur.execute("""
                SELECT
                    min_wave_height, max_wave_height, preferred_swell_direction,
                    min_swell_period, max_swell_period, preferred_wind_direction,
                    max_wind_speed, ideal_tide_type, additional_considerations
                FROM level_spot_preferences
                WHERE surf_level = %s AND spot_id = %s;
            """, (surf_level, spot_id))
            level_pref = cur.fetchone()
            if level_pref:
                preferences = {
                    'min_wave_height': level_pref[0],
                    'max_wave_height': level_pref[1],
                    'preferred_swell_direction': level_pref[2],
                    'min_swell_period': level_pref[3],
                    'max_swell_period': level_pref[4],
                    'preferred_wind_direction': level_pref[5],
                    'max_wind_speed': level_pref[6],
                    'ideal_tide_type': level_pref[7], # Este existe na tabela de nível
                    'additional_considerations': level_pref[8]
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


def determine_tide_phase(current_time_utc, current_sea_level, tide_extremes):
    """
    Determines the tide phase (low, high, rising, falling, mid) at a given time
    based on tide extremes and current sea level.

    Args:
        current_time_utc (datetime): The UTC datetime for which to determine the tide.
        current_sea_level (float): The sea level at current_time_utc.
        tide_extremes (list): A list of dictionaries, each containing 'timestamp_utc',
                              'type' ('low'/'high'), and 'height' for tide extremes.

    Returns:
        str: 'low', 'high', 'rising', 'falling', 'mid', or 'unknown'.
    """
    if not tide_extremes:
        return 'unknown'

    # Ensure tide_extremes are sorted by timestamp
    tide_extremes.sort(key=lambda x: x['timestamp_utc'])

    prev_extreme = None
    next_extreme = None

    for i, extreme in enumerate(tide_extremes):
        if extreme['timestamp_utc'] > current_time_utc:
            next_extreme = extreme
            if i > 0:
                prev_extreme = tide_extremes[i-1]
            break
    if next_extreme is None and tide_extremes: # If current_time_utc is after all extremes
        prev_extreme = tide_extremes[-1]
        # We don't have a 'next' extreme, so it's hard to determine phase
        return 'unknown' # Or assume it's still rising/falling based on last trend


    # If current_time_utc is exactly at an extreme
    if next_extreme and next_extreme['timestamp_utc'] == current_time_utc:
        return next_extreme['type']

    # If current_time_utc is before the first extreme
    if prev_extreme is None:
        # We only have future extremes, hard to know past phase without more data
        return 'unknown'

    # Determine phase between two extremes
    if prev_extreme and next_extreme:
        if prev_extreme['type'] == 'low' and next_extreme['type'] == 'high':
            # Low to High: Tide is rising
            # If current_sea_level is close to prev_extreme['height'], it's low
            # If current_sea_level is close to next_extreme['height'], it's high
            # Otherwise, it's rising
            if abs(current_sea_level - prev_extreme['height']) < 0.1: # Threshold for 'low'
                 return 'low'
            elif abs(current_sea_level - next_extreme['height']) < 0.1: # Threshold for 'high'
                 return 'high'
            return 'rising'
        elif prev_extreme['type'] == 'high' and next_extreme['type'] == 'low':
            # High to Low: Tide is falling
            if abs(current_sea_level - prev_extreme['height']) < 0.1: # Threshold for 'high'
                 return 'high'
            elif abs(current_sea_level - next_extreme['height']) < 0.1: # Threshold for 'low'
                 return 'low'
            return 'falling'

    return 'mid' # Default if exact phase not determined (e.g., in between, not at extreme)