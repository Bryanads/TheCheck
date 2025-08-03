import arrow
import requests
import json
import os
import sys
import decimal
from src.db.connection import get_db_connection, close_db_connection
from src.db.queries import get_all_spots_from_db
from src.config import (
    API_KEY_STORMGLASS, REQUEST_DIR, FORECAST_DAYS,
    WEATHER_API_URL, TIDE_SEA_LEVEL_API_URL, TIDE_EXTREMES_API_URL, PARAMS_WEATHER_API
)

def choose_spot_from_db(available_spots):
    if not available_spots:
        return None, None

    print("\nChoose one of the available spots in the database:")
    for i, spot in enumerate(available_spots):
        print(f"{i + 1}. {spot['name']}")

    while True:
        try:
            choice = int(input("Enter the spot number: ")) - 1
            if 0 <= choice < len(available_spots):
                return available_spots[choice]
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def fetch_and_save_data(api_url, params, headers, filename, label):
    print(f"Fetching {label} data...")
    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        os.makedirs(REQUEST_DIR, exist_ok=True)
        with open(os.path.join(REQUEST_DIR, filename), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"{label} data saved to {filename}")
        return data
    except Exception as e:
        print(f"Error fetching {label} data: {e}")
        return None

if __name__ == "__main__":
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)

    available_spots = get_all_spots_from_db()
    if not available_spots:
        close_db_connection(conn, None)
        sys.exit(1)

    selected_spot = choose_spot_from_db(available_spots)
    if selected_spot is None:
        close_db_connection(conn, None)
        sys.exit(0)

    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError

    os.makedirs(REQUEST_DIR, exist_ok=True)
    with open(os.path.join(REQUEST_DIR, 'current_spot.json'), 'w') as f:
        json.dump(selected_spot, f, ensure_ascii=False, indent=4, default=decimal_default)

    start = arrow.now()
    end = start.shift(days=FORECAST_DAYS)
    headers = {'Authorization': API_KEY_STORMGLASS}

    fetch_and_save_data(
        WEATHER_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'params': ','.join(PARAMS_WEATHER_API),
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'weather_data.json',
        "weather"
    )

    fetch_and_save_data(
        TIDE_SEA_LEVEL_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'params': 'seaLevel',
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'sea_level_data.json',
        "sea level"
    )

    fetch_and_save_data(
        TIDE_EXTREMES_API_URL,
        {
            'lat': selected_spot['latitude'],
            'lng': selected_spot['longitude'],
            'start': int(start.timestamp()),
            'end': int(end.timestamp())
        },
        headers,
        'tide_extremes_data.json',
        "tide extremes"
    )

    close_db_connection(conn, None)
