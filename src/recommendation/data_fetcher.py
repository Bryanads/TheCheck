# src/recommendation/data_fetcher.py
import datetime
import arrow # Para lidar com timestamps

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
            if current_sea_level is not None and prev_extreme['height'] is not None and abs(float(current_sea_level) - float(prev_extreme['height'])) < 0.1: # Threshold for 'low'
                 return 'low'
            elif current_sea_level is not None and next_extreme['height'] is not None and abs(float(current_sea_level) - float(next_extreme['height'])) < 0.1: # Threshold for 'high'
                 return 'high'
            return 'rising'
        elif prev_extreme['type'] == 'high' and next_extreme['type'] == 'low':
            # High to Low: Tide is falling
            if current_sea_level is not None and prev_extreme['height'] is not None and abs(float(current_sea_level) - float(prev_extreme['height'])) < 0.1: # Threshold for 'high'
                 return 'high'
            elif current_sea_level is not None and next_extreme['height'] is not None and abs(float(current_sea_level) - float(next_extreme['height'])) < 0.1: # Threshold for 'low'
                 return 'low'
            return 'falling'

    return 'mid' # Default if exact phase not determined (e.g., in between, not at extreme)

def get_cardinal_direction(degrees):
    """Converts degrees to cardinal direction (e.g., 180 -> 'S')."""
    if degrees is None: return None
    # Adjusting ranges slightly to ensure no gaps and full coverage
    if (degrees >= 337.5 and degrees <= 360) or (degrees >= 0 and degrees < 22.5): return 'N'
    if 22.5 <= degrees < 67.5: return 'NE'
    if 67.5 <= degrees < 112.5: return 'E'
    if 112.5 <= degrees < 157.5: return 'SE'
    if 157.5 <= degrees < 202.5: return 'S'
    if 202.5 <= degrees < 247.5: return 'SW'
    if 247.5 <= degrees < 292.5: return 'W'
    if 292.5 <= degrees < 337.5: return 'NW'
    return None