# src/recommendation/data_fetcher.py
import datetime
import decimal # Importar o módulo decimal para verificar o tipo

def determine_tide_phase(current_timestamp, tides_extremes):
    """
    Determines the tide phase (e.g., 'low', 'high', 'rising', 'falling')
    for a given timestamp based on a list of tide extreme events.

    Args:
        current_timestamp (datetime.datetime): The specific timestamp (UTC) for which
                                                to determine the tide phase.
        tides_extremes (list): A list of dictionaries, each representing a tide extreme event,
                                with 'timestamp_utc', 'tide_type' ('low' or 'high'), and 'height'.

    Returns:
        str: The determined tide phase ('low', 'high', 'rising', 'falling'),
             or 'unknown' if not enough data.
    """
    if not tides_extremes:
        return 'unknown'

    # Ensure current_timestamp is timezone-aware UTC
    if current_timestamp.tzinfo is None:
        current_timestamp = current_timestamp.replace(tzinfo=datetime.timezone.utc)
    else:
        current_timestamp = current_timestamp.astimezone(datetime.timezone.utc)

    # Sort tide extremes by timestamp
    sorted_extremes = sorted(tides_extremes, key=lambda x: x['timestamp_utc'])

    previous_extreme = None
    next_extreme = None

    # Find the closest previous and next extreme tide events
    for i, extreme in enumerate(sorted_extremes):
        extreme_time = extreme['timestamp_utc']
        if extreme_time <= current_timestamp:
            previous_extreme = extreme
        elif extreme_time > current_timestamp:
            next_extreme = extreme
            break # Found the first extreme after current_timestamp

    if previous_extreme is None and next_extreme is None:
        return 'unknown' # No extremes found

    if previous_extreme and current_timestamp == previous_extreme['timestamp_utc']:
        return previous_extreme['tide_type'] # Exactly at an extreme

    if next_extreme and current_timestamp == next_extreme['timestamp_utc']:
        return next_extreme['tide_type'] # Exactly at an extreme

    if previous_extreme and not next_extreme:
        # We are past the last known extreme for the day/range provided
        # Could extrapolate, but safer to return a known state or 'unknown'
        return f"after_{previous_extreme['tide_type']}" # Or just 'unknown'

    if not previous_extreme and next_extreme:
        # We are before the first known extreme for the day/range provided
        return f"before_{next_extreme['tide_type']}" # Or just 'unknown'

    # Determine rising or falling
    if previous_extreme and next_extreme:
        if previous_extreme['tide_type'] == 'low' and next_extreme['tide_type'] == 'high':
            return 'rising'
        elif previous_extreme['tide_type'] == 'high' and next_extreme['tide_type'] == 'low':
            return 'falling'
    
    return 'unknown'

def get_cardinal_direction(degrees):
    """
    Converts degrees (0-360) to a cardinal or intercardinal direction.
    Handles decimal.Decimal input by converting to float.
    """
    if degrees is None:
        return "N/A"
    
    # Adicionar esta linha para garantir que 'degrees' seja um float
    if isinstance(degrees, decimal.Decimal):
        degrees = float(degrees)

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    
    # Adiciona 11.25 para ajustar o ponto de partida (N é de 348.75 a 11.25)
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]