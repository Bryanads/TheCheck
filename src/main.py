import sys
import arrow
from src.utils.utils import convert_to_localtime_string
from src.db.queries import (
    get_spot_by_id,
    get_user_surf_level,
    get_spot_preferences,
    get_forecast_data_for_spot,
    get_tide_extremes_for_spot
)
from src.recommendation.data_fetcher import determine_tide_phase, get_cardinal_direction
from src.recommendation.recommendation_logic import calculate_suitability_score


def run_recommendation_for_user_and_spots(user_id, spot_ids_list, start_time_utc, end_time_utc):
    print(f"\n--- Gerando recomendações para o ID de Usuário: {user_id} e Spots: {spot_ids_list} ---")

    surf_level = get_user_surf_level(user_id)
    if not surf_level:
        print(f"Não foi possível determinar o nível de surf para o usuário {user_id}. Saindo.")
        return

    print(f"Usuário {user_id} é um surfista '{surf_level}'.")

    spots_to_process = []
    for s_id in spot_ids_list:
        spot_details = get_spot_by_id(s_id)
        if spot_details:
            spots_to_process.append(spot_details)
        else:
            print(f"Aviso: Spot com ID {s_id} não encontrado no banco de dados. Ignorando.")

    if not spots_to_process:
        print(f"Nenhum spot válido encontrado nos IDs fornecidos: {spot_ids_list}. Nenhuma recomendação pode ser feita.")
        return

    recommendations = []

    for spot in spots_to_process:
        spot_id = spot['spot_id']
        spot_name = spot['name']
        print(f"\n--- Processando spot: {spot_name} (ID: {spot_id}) ---")

        raw_preferences = get_spot_preferences(spot_id, user_id, surf_level)
        preferences = raw_preferences if raw_preferences is not None else {}

        if not preferences:
            print(f"Usando preferências padrão (não específicas) para o spot {spot_name}, pois nenhuma foi encontrada.")

        forecast_data = get_forecast_data_for_spot(spot_id, start_time_utc, end_time_utc)

        day_start = start_time_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = start_time_utc.replace(hour=23, minute=59, second=59, microsecond=0)
        tide_extremes = get_tide_extremes_for_spot(spot_id, day_start, day_end)

        if not forecast_data:
            print(f"Nenhum dado de previsão disponível para {spot_name} no período especificado.")
            continue

        for entry in forecast_data:
            timestamp = entry['timestamp_utc']

            tide_phase = determine_tide_phase(
                timestamp,
                entry.get('seaLevel_sg'),
                tide_extremes
            )
            entry['current_tide_phase'] = tide_phase

            score = calculate_suitability_score(entry, preferences)

            recommendations.append({
                'spot_id': spot_id,
                'spot_name': spot_name,
                'timestamp': timestamp,
                'wave_height': entry.get('waveHeight_sg'),
                'swell_direction': entry.get('swellDirection_sg'),
                'wind_speed': entry.get('windSpeed_sg'),
                'wind_direction': entry.get('windDirection_sg'),
                'tide_phase': tide_phase,
                'sea_level': entry.get('seaLevel_sg'),
                'water_temperature': entry.get('waterTemperature_sg'),
                'air_temperature': entry.get('airTemperature_sg'),
                'current_speed': entry.get('currentSpeed_sg'),
                'current_direction': entry.get('currentDirection_sg'),
                'suitability_score': score
            })


    if recommendations:
        recommendations.sort(key=lambda x: (-x['suitability_score'], x['timestamp']))
        print("\n--- TOP RECOMENDAÇÕES (incluindo scores baixos) ---")
        for rec in recommendations[:20]:
            wave_height_str = f"{rec['wave_height']:.1f}m" if rec['wave_height'] is not None else "N/A"

            swell_dir_val = rec['swell_direction']
            swell_dir_cardinal = get_cardinal_direction(swell_dir_val) if swell_dir_val is not None else "N/A"
            swell_dir_str = f"{swell_dir_val:.2f}° {swell_dir_cardinal}" if swell_dir_val is not None else "N/A"

            wind_speed_str = f"{rec['wind_speed']:.1f}" if rec['wind_speed'] is not None else "N/A"
            wind_dir_val = rec['wind_direction']
            wind_dir_cardinal = get_cardinal_direction(wind_dir_val) if wind_dir_val is not None else "N/A"
            wind_dir_str = f"({wind_dir_val:.2f}° {wind_dir_cardinal})" if wind_dir_val is not None else "(N/A)"

            sea_level_str = f"{rec['sea_level']:.2f}m" if rec['sea_level'] is not None else "N/A"
            water_temp_str = f"{rec['water_temperature']:.1f}°C" if rec['water_temperature'] is not None else "N/A"
            air_temp_str = f"{rec['air_temperature']:.1f}°C" if rec['air_temperature'] is not None else "N/A"

            current_speed_str = f"{rec['current_speed']:.1f}" if rec['current_speed'] is not None else "N/A"
            current_dir_val = rec['current_direction']
            current_dir_cardinal = get_cardinal_direction(current_dir_val) if current_dir_val is not None else "N/A"
            current_dir_str = f"({current_dir_val:.2f}° {current_dir_cardinal})" if current_dir_val is not None else "(N/A)"

            print(f"Spot: {rec['spot_name']} ({convert_to_localtime_string(rec['timestamp'])}) - Onda: {wave_height_str}, Swell Dir: {swell_dir_str}, Vento: {wind_speed_str} m/s {wind_dir_str}, Maré Tipo: {rec['tide_phase']}, Maré Nível: {sea_level_str}, Temp Água: {water_temp_str}, Temp Ar: {air_temp_str}, Corrente: {current_speed_str} {current_dir_str} - Score: {rec['suitability_score']:.2f}")
    else:
        print("Nenhuma recomendação pôde ser gerada (por exemplo, nenhum spot ou nenhum dado de previsão após a filtragem).")


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Uso correto: python -m src.main <user_id> <spot_id_1> <spot_id_2> ... <day> <start_time> <end_time>")
        print("Exemplo: python -m src.main 1 101 102 0 06:00 14:00")
    else:
        try:
            user_id_to_recommend = int(sys.argv[1])
            day_offset = int(sys.argv[-3])
            start_time_str = sys.argv[-2]
            end_time_str = sys.argv[-1]
            spot_ids_to_recommend = [int(arg) for arg in sys.argv[2:-3]]

            # Calcular início e fim com base em day_offset + horários
            base_date = arrow.utcnow().shift(days=day_offset).floor('day')
            start_hour, start_minute = map(int, start_time_str.split(":"))
            end_hour, end_minute = map(int, end_time_str.split(":"))

            start_time_utc = base_date.replace(hour=start_hour, minute=start_minute)
            end_time_utc = base_date.replace(hour=end_hour, minute=end_minute)

            run_recommendation_for_user_and_spots(user_id_to_recommend, spot_ids_to_recommend, start_time_utc.datetime, end_time_utc.datetime)

        except ValueError:
            print("Erro: certifique-se de que os IDs e horários estão no formato correto.")

