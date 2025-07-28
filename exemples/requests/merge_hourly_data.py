import json
import os

OUTPUT_DIR = 'api_responses'

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
    # Define the filenames based on the beach you requested earlier (e.g., 'Barra')
    praia_nome_sanitized = "barra" # Must match the sanitized name in the filename
    
    weather_file = f'weather_data_{praia_nome_sanitized}.json'
    sea_level_file = f'sea_level_data_{praia_nome_sanitized}.json'
    output_file = f'merged_hourly_data_{praia_nome_sanitized}.json'
    
    merge_stormglass_data(weather_file, sea_level_file, output_file)