import datetime
import sys
import arrow
# from src.db.connection import get_db_connection, close_db_connection
from src.db.queries import get_spot_by_id # Importa esta função para buscar detalhes do spot
from src.recommendation.data_fetcher import (
    get_user_surf_level,
    get_spot_preferences,
    get_forecast_data_for_spot,
    get_tide_extremes_for_spot,
    determine_tide_phase
)
from src.recommendation.recommendation_logic import calculate_suitability_score
from src.config import HOURS_FILTER

def run_recommendation_for_user_and_spots(user_id, spot_ids_list):
    """
    Generates surf spot recommendations for a given user for a specific list of spots.
    Ensures all spots with forecast data receive a score.
    """
    print(f"\n--- Generating recommendations for User ID: {user_id} and Spots: {spot_ids_list} ---")

    # 1. Obter o nível de surf do usuário
    surf_level = get_user_surf_level(user_id)
    if not surf_level:
        print(f"Could not determine surf level for user {user_id}. Exiting.")
        return

    print(f"User {user_id} is a '{surf_level}' surfer.")

    # 2. Obter detalhes dos spots fornecidos
    spots_to_process = []
    for s_id in spot_ids_list:
        spot_details = get_spot_by_id(s_id) # Usamos a função get_spot_by_id do queries
        if spot_details:
            spots_to_process.append(spot_details)
        else:
            print(f"Warning: Spot with ID {s_id} not found in database. Skipping.")

    if not spots_to_process:
        print(f"No valid spots found from the provided IDs: {spot_ids_list}. No recommendations can be made.")
        return

    # Definir o período de previsão (próximos 3 dias como exemplo)
    start_time_utc = datetime.datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    end_time_utc = start_time_utc + datetime.timedelta(days=3)

    recommendations = []

    for spot in spots_to_process:
        spot_id = spot['spot_id']
        spot_name = spot['name']
        print(f"\n--- Processing spot: {spot_name} (ID: {spot_id}) ---")

        preferences = get_spot_preferences(spot_id, user_id, surf_level)
        if not preferences:
            print(f"Using default (no specific) preferences for spot {spot_name} as none found.")
            pass

        forecast_data = get_forecast_data_for_spot(spot_id, start_time_utc, end_time_utc)
        tide_extremes = get_tide_extremes_for_spot(spot_id, start_time_utc, end_time_utc)

        if not forecast_data:
            print(f"No forecast data available for {spot_name} in the specified period.")
            continue

        for entry in forecast_data:
            local_time = arrow.get(entry['timestamp_utc']).to('America/Sao_Paulo')
            if local_time.hour not in HOURS_FILTER:
                continue

            tide_phase = determine_tide_phase(
                entry['timestamp_utc'],
                entry.get('seaLevel_sg'),
                tide_extremes
            )
            entry['current_tide_phase'] = tide_phase

            score = calculate_suitability_score(entry, preferences)

            recommendations.append({
                'spot_id': spot_id,
                'spot_name': spot_name,
                'timestamp': entry['timestamp_utc'],
                'local_time': local_time.format('DD/MM HH:mm'),
                'wave_height': entry.get('waveHeight_sg'),
                'swell_direction': entry.get('swellDirection_sg'),
                'wind_speed': entry.get('windSpeed_sg'),
                'wind_direction': entry.get('windDirection_sg'),
                'tide_phase': tide_phase,
                'suitability_score': score
            })

    if recommendations:
        recommendations.sort(key=lambda x: (x['suitability_score'], x['timestamp']), reverse=True)
        print("\n--- TOP RECOMMENDATIONS (including low scores) ---")
        for rec in recommendations[:20]:
            print(f"Spot: {rec['spot_name']} ({rec['local_time']}) - Onda: {rec['wave_height']:.1f}m, Vento: {rec['wind_speed']:.1f} ({rec['wind_direction']}°), Maré: {rec['tide_phase']} - Score: {rec['suitability_score']:.2f}")
    else:
        print("No recommendations could be generated (e.g., no forecast data for the selected spots after filtering).")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Please provide a user ID followed by one or more spot IDs.")
        print("Example: python -m src.main <user_id> <spot_id_1> <spot_id_2> ...")
    else:
        try:
            user_id_to_recommend = int(sys.argv[1])
            spot_ids_to_recommend = [int(arg) for arg in sys.argv[2:]]
            run_recommendation_for_user_and_spots(user_id_to_recommend, spot_ids_to_recommend)
        except ValueError:
            print("Invalid arguments. Please ensure user ID and spot IDs are numeric.")