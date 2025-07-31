import arrow
import requests
import json
import os
from dotenv import load_dotenv
import sys
import decimal
from exemples.db_utils import get_db_connection, close_db_connection


# Load environment variables from .env file
load_dotenv()

# --- Global Configurations ---
API_KEY = os.getenv('API_KEY_2') 

OUTPUT_DIR = 'data'

# StormGlass.io API endpoint URLs
WEATHER_API_URL = "https://api.stormglass.io/v2/weather/point"
TIDE_SEA_LEVEL_API_URL = "https://api.stormglass.io/v2/tide/sea-level/point" 
TIDE_EXTREMES_API_URL = "https://api.stormglass.io/v2/tide/extremes/point"

HOURS_FILTER = list(range(5, 18))  # 5 AM to 5 PM (local time)
FORECAST_DAYS = 5 

"""
-------------------------------------------------------------------------------
-------------------- SELECT SPOTS TO REQUEST DATA -----------------------------
-------------------------------------------------------------------------------
"""

def get_spots_from_db(cursor):
    """
    Loads registered spots from the database.
    """
    try:
        cursor.execute("SELECT spot_id, spot_name, latitude, longitude FROM spots ORDER BY spot_id;")
        spots_db = cursor.fetchall()
        
        if not spots_db:
            print("No spots found in the database. Please add spots using 'add_spots.py'.")
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

def choose_spot_from_db(available_spots):
    """
    Allows the user to select a spot from the list loaded from the database.
    """
    if not available_spots:
        return None, None

    print("\nChoose one of the available spots in the database:")
    for i, spot in enumerate(available_spots):
        print(f"{i + 1}. {spot['name']}")
    
    while True:
        try:
            choice = int(input("Enter the spot number: ")) - 1
            if 0 <= choice < len(available_spots):
                selected_spot = available_spots[choice]
                return selected_spot['name']
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

"""
-------------------------------------------------------------------------------
-------------------- MAKE REQUEST AND LOCAL SAVE ------------------------------
-------------------------------------------------------------------------------
"""

def fetch_and_save_weather_data(lat, lon, spot_name):
    """
    Fetches hourly weather data from StormGlass and saves it to a JSON file.
    """

    # Parameters for /weather/point endpoint
    PARAMS_WEATHER_API = [
    'waveHeight', 'waveDirection', 'wavePeriod', 'swellHeight', 'swellDirection',
    'swellPeriod', 'secondarySwellHeight', 'secondarySwellDirection',
    'secondarySwellPeriod', 'windSpeed', 'windDirection', 'waterTemperature',
    'airTemperature', 'currentSpeed', 'currentDirection'
    
    ]
    if not API_KEY:
        print("Error: API_KEY not found in environment variables.")
        return

    start_date = arrow.now()
    end_date = start_date.shift(days=FORECAST_DAYS)

    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'params': ','.join(PARAMS_WEATHER_API),
        'start': int(start_date.timestamp()),
        'end': int(end_date.timestamp())
    }
    
    output_filename = os.path.join(OUTPUT_DIR, f'weather_data.json')

    print(f"Fetching weather data for {spot_name} (Lat: {lat}, Lng: {lon})...")
    try:
        response = requests.get(WEATHER_API_URL, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Weather data saved to {output_filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        if response is not None:
            print(f"Status: {response.status_code}, Body: {response.text}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for weather data.")
        if response is not None:
            print(f"Failed response body: {response.text[:500]}...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def fetch_and_save_sea_level_data(lat, lon, spot_name):
    """
    Fetches hourly sea level data from StormGlass and saves it to a JSON file.
    """
    if not API_KEY:
        print("Error: API_KEY not found in environment variables.")
        return

    start_date = arrow.now()
    end_date = start_date.shift(days=FORECAST_DAYS)

    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'params': 'seaLevel', 
        'start': int(start_date.timestamp()),
        'end': int(end_date.timestamp())
    }
    
    output_filename = os.path.join(OUTPUT_DIR, f'sea_level_data.json')

    print(f"Fetching sea level data for {spot_name} (Lat: {lat}, Lng: {lon})...")
    try:
        response = requests.get(TIDE_SEA_LEVEL_API_URL, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Sea level data saved to {output_filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sea level data: {e}")
        if response is not None:
            print(f"Status: {response.status_code}, Body: {response.text}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for sea level data.")
        if response is not None:
            print(f"Failed response body: {response.text[:500]}...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def fetch_and_save_tide_extremes_data(lat, lon, spot_name):
    """
    Fetches tide extremes data from StormGlass and saves it to a JSON file.
    """
    if not API_KEY:
        print("Error: API_KEY not found in environment variables.")
        return

    start_date = arrow.now()
    end_date = start_date.shift(days=FORECAST_DAYS)

    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'start': int(start_date.timestamp()),
        'end': int(end_date.timestamp())
    }
    
    output_filename = os.path.join(OUTPUT_DIR, f'tide_extremes_data.json')

    print(f"Fetching tide extremes data for {spot_name} (Lat: {lat}, Lng: {lon})...")
    try:
        response = requests.get(TIDE_EXTREMES_API_URL, headers=headers, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Tide extremes data saved to {output_filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tide extremes data: {e}")
        if response is not None:
            print(f"Status: {response.status_code}, Body: {response.text}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for tide extremes data.")
        if response is not None:
            print(f"Failed response body: {response.text[:500]}...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
"""
-------------------------------------------------------------------------------
----------------- MERGE WEATHER AND TIDE FORECAST -----------------------------
-------------------------------------------------------------------------------
"""
def load_json_data(filename):
    """Loads JSON data from a specified file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found. Please ensure request scripts were run.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. File might be corrupted.")
        return None

def merge_stormglass_data(weather_filename, sea_level_filename, output_filename):
    """
    Loads weather and sea level data, extracts 'sg' values, and merges them by time.
    """
    print(f"Loading weather data from: {weather_filename}")
    weather_data = load_json_data(weather_filename)
    if not weather_data or 'hours' not in weather_data:
        print("Failed to load valid weather data or 'hours' key is missing.")
        return

    print(f"Loading sea level data from: {sea_level_filename}")
    sea_level_data = load_json_data(sea_level_filename)
    # The crucial change is here: check for 'data' key for sea level
    if not sea_level_data or 'data' not in sea_level_data:
        print("Failed to load valid sea level data or 'data' key is missing.")
        return

    # Convert weather data to a dict indexed by time for easier lookup
    weather_by_time = {
        entry['time']: entry for entry in weather_data.get('hours', [])
    }

    # Corrected: Convert sea level data to a dict indexed by time using 'data'
    sea_level_by_time = {
        entry['time']: entry.get('sg') # Directly get 'sg' from the entry
        for entry in sea_level_data.get('data', [])
    }
    
    merged_results = []
    
    # Iterate through weather data times and merge with corresponding sea level
    # We use weather_by_time as the primary source of timestamps to ensure consistency
    for time_str, weather_entry in weather_by_time.items():
        merged_entry = {
            'time': time_str,
            # Extract 'sg' for each weather parameter
            'waveHeight_sg': weather_entry.get('waveHeight', {}).get('sg'),
            'waveDirection_sg': weather_entry.get('waveDirection', {}).get('sg'),
            'wavePeriod_sg': weather_entry.get('wavePeriod', {}).get('sg'),
            'swellHeight_sg': weather_entry.get('swellHeight', {}).get('sg'),
            'swellDirection_sg': weather_entry.get('swellDirection', {}).get('sg'),
            'swellPeriod_sg': weather_entry.get('swellPeriod', {}).get('sg'),
            'secondarySwellHeight_sg': weather_entry.get('secondarySwellHeight', {}).get('sg'),
            'secondarySwellDirection_sg': weather_entry.get('secondarySwellDirection', {}).get('sg'),
            'secondarySwellPeriod_sg': weather_entry.get('secondarySwellPeriod', {}).get('sg'),
            'windSpeed_sg': weather_entry.get('windSpeed', {}).get('sg'),
            'windDirection_sg': weather_entry.get('windDirection', {}).get('sg'),
            'waterTemperature_sg': weather_entry.get('waterTemperature', {}).get('sg'),
            'airTemperature_sg': weather_entry.get('airTemperature', {}).get('sg'),
            'currentSpeed_sg': weather_entry.get('currentSpeed', {}).get('sg'),
            'currentDirection_sg': weather_entry.get('currentDirection', {}).get('sg'),
            # Add sea level data
            'seaLevel_sg': sea_level_by_time.get(time_str) # Get sea level for this specific time
        }
        merged_results.append(merged_entry)

    # Sort results by time if needed (optional, but good for consistency)
    merged_results.sort(key=lambda x: x['time'])

    # Save the merged data
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(merged_results, f, ensure_ascii=False, indent=4)
        print(f"\nSuccessfully merged data and saved to: {output_filepath}")
        print(f"Total merged entries: {len(merged_results)}")
    except Exception as e:
        print(f"Error saving merged data to file: {e}")

if __name__ == "__main__":    
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    cursor = conn.cursor()

    available_spots = get_spots_from_db(cursor)
    if not available_spots:
        close_db_connection(conn, cursor)
        sys.exit(1)

    spot = choose_spot_from_db(available_spots)
    if not spot:
        close_db_connection(conn, cursor)
        sys.exit(0)

    selected_spot = next(s for s in available_spots if s['name'] == spot)

    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'current_spot.json'), 'w') as f:
        json.dump(selected_spot, f, ensure_ascii=False, indent=4, default=decimal_default)

    
    fetch_and_save_weather_data(selected_spot['latitude'], selected_spot['longitude'], selected_spot['name'])
    fetch_and_save_sea_level_data(selected_spot['latitude'], selected_spot['longitude'], selected_spot['name'])
    fetch_and_save_tide_extremes_data(selected_spot['latitude'], selected_spot['longitude'], selected_spot['name'])


    weather_file = f'weather_data.json'
    sea_level_file = f'sea_level_data.json'
    output_file = f'forecast_data.json'
    
    merge_stormglass_data(weather_file, sea_level_file, output_file)

    close_db_connection(conn, cursor)