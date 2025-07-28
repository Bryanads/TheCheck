import arrow
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('API_KEY_3')
TIDE_SEA_LEVEL_API_URL = "https://api.stormglass.io/v2/tide/sea-level/point"
OUTPUT_DIR = 'api_responses'

DIAS_PREVISAO = 5 # Forecast for 5 days

def fetch_and_save_sea_level_data(lat, lon, nome_praia):
    """
    Fetches hourly sea level data from StormGlass and saves it to a JSON file.
    """
    if not API_KEY:
        print("Error: API_KEY not found in environment variables.")
        return

    start_date = arrow.now()
    end_date = start_date.shift(days=DIAS_PREVISAO)

    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'params': 'seaLevel', # Explicitly requesting 'seaLevel'
        'start': int(start_date.timestamp()),
        'end': int(end_date.timestamp())
    }
    
    output_filename = os.path.join(OUTPUT_DIR, f'sea_level_data_{nome_praia.replace(" ", "_").lower()}.json')

    print(f"Fetching sea level data for {nome_praia} (Lat: {lat}, Lng: {lon})...")
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

if __name__ == "__main__":
    # Example usage for Barra da Tijuca
    praia_nome = "Barra"
    praia_lat = -23.0094000
    praia_lon = -43.3659000
    fetch_and_save_sea_level_data(praia_lat, praia_lon, praia_nome)
    