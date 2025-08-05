import math

def calculate_suitability_score(forecast_entry, spot_preferences, spot, tide_phase, user):
    """
    Calculates a suitability score for a given forecast entry at a specific spot,
    considering user preferences, spot characteristics, and tide conditions.

    Args:
        forecast_entry (dict): Dictionary containing detailed forecast data for a specific hour.
                               (e.g., 'wave_height_sg', 'sea_level_sg').
        spot_preferences (dict): Dictionary of preferences for the specific spot,
                                 either user-defined or model-generated/level-based.
                                 (e.g., 'min_wave_height', 'ideal_tide_type').
        spot (dict): Dictionary containing the spot's characteristics (e.g., bottom_type, coast_orientation).
        tide_phase (str): The calculated tide phase ('low', 'high', 'rising', 'falling').
                          Passado diretamente, não precisa ser extraído de forecast_entry.
        user (dict): Dictionary containing user profile information (e.g., surf_level, goofy_regular_stance).

    Returns:
        float: A suitability score (higher is better).
               Returns 0 if conditions are very unsuitable.
        dict: A dictionary with detailed scores for each category.
    """
    score = 0.0 # Começamos do zero e somamos os bônus/penalidades.
    detailed_scores = {} # Para armazenar os scores de cada categoria

    # --- Funções Auxiliares de Pontuação ---

    def get_pref_float(key):
        """Helper to safely get float preference values from spot_preferences."""
        val = spot_preferences.get(key)
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def get_pref_str(key):
        """Helper to safely get string preference values from spot_preferences."""
        val = spot_preferences.get(key)
        return str(val) if val is not None else None

    def cardinal_to_degrees(cardinal_direction_str):
        """Converts a cardinal direction string to its numerical degree representation (0-360)."""
        if cardinal_direction_str is None:
            return None
        mapping = {
            'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
            'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
            'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
            'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
        }
        return mapping.get(cardinal_direction_str.upper(), None)

    def calculate_angular_difference(angle1, angle2):
        """Calculates the smallest angular difference between two angles (0-360 degrees)."""
        if angle1 is None or angle2 is None:
            return None
        diff = abs(angle1 - angle2)
        return min(diff, 360 - diff)

    def score_proximity_to_range_ideal(current_value, min_val, max_val, ideal_val, param_name=""):
        """
        Pontua um valor atual com base em uma faixa aceitável (min, max) e um ideal.
        Retorna o bônus/penalidade diretamente.
        """
        if current_value is None:
            return 0

        current_value = float(current_value)

        if "height" in param_name.lower():
            ideal_pct_range = 0.1
            good_pct_range = 0.2
            slight_outside_pct = 0.1
            far_outside_pct = 0.2
            max_bonus = 25
            good_bonus = 15
            min_max_bonus = 5
            slight_penalty = 0
            medium_penalty = 0
            severe_penalty = 0 # Changed from -30
        elif "period" in param_name.lower():
            ideal_pct_range = 0.1
            good_pct_range = 0.2
            slight_outside_pct = 0.1
            far_outside_pct = 0.2
            max_bonus = 10
            good_bonus = 5
            min_max_bonus = 0
            slight_penalty = 0
            medium_penalty = 0
            severe_penalty = 0
        elif "sea_level" in param_name.lower():
            ideal_pct_range = 0.05
            good_pct_range = 0.1
            slight_outside_threshold = 0.1
            far_outside_threshold = 0.2
            max_bonus = 10
            good_bonus = 7
            min_max_bonus = 0
            slight_penalty = 0
            medium_penalty = 0
            severe_penalty = 0
        elif "temperature" in param_name.lower():
            ideal_pct_range = 0.05
            max_bonus = 8
            good_bonus = 5
            slight_penalty = 0
            medium_penalty = 0
            severe_penalty = 0
        else:
            ideal_pct_range = 0.1
            good_pct_range = 0.2
            slight_outside_pct = 0.1
            far_outside_pct = 0.2
            max_bonus = 10
            good_bonus = 5
            min_max_bonus = 0
            slight_penalty = 0
            medium_penalty = 0
            severe_penalty = 0

        score_result = 0
        if ideal_val is not None:
            ideal_val = float(ideal_val)
            if abs(current_value - ideal_val) <= ideal_val * ideal_pct_range:
                score_result = max_bonus
            elif abs(current_value - ideal_val) <= ideal_val * good_pct_range:
                score_result = good_bonus

        if min_val is not None and max_val is not None:
            min_val = float(min_val)
            max_val = float(max_val)
            if min_val <= current_value <= max_val:
                if score_result == 0: # Only apply if not already set by ideal proximity
                    score_result = min_max_bonus
            elif current_value < min_val and current_value >= min_val * (1 - slight_outside_pct):
                score_result = slight_penalty
            elif current_value > max_val and current_value <= max_val * (1 + slight_outside_pct):
                score_result = slight_penalty
            elif current_value < min_val * (1 - far_outside_pct) or current_value > max_val * (1 + far_outside_pct):
                score_result = severe_penalty
            elif score_result == 0:
                score_result = medium_penalty

        return score_result

    def score_proximity_to_single_ideal(current_value, ideal_val, param_name=""):
        """
        Pontua um valor atual com base em um único valor ideal.
        Retorna o bônus/penalidade diretamente.
        """
        if current_value is None or ideal_val is None:
            return 0

        current_value = float(current_value)
        ideal_val = float(ideal_val)

        if "secondary_swell" in param_name.lower():
            ideal_pct_range = 0.1
            medium_dev_pct = 0.2
            high_dev_pct = 0.3
            ideal_bonus = 0
            medium_penalty = 0 # Changed from -5
            high_penalty = 0 # Changed from -10
            severe_penalty = 0 # Changed from -20
            if abs(current_value - ideal_val) <= ideal_val * ideal_pct_range:
                return ideal_bonus
            elif abs(current_value - ideal_val) <= ideal_val * medium_dev_pct:
                return -medium_penalty
            elif abs(current_value - ideal_val) <= ideal_val * high_dev_pct:
                return -high_penalty
            else:
                return -severe_penalty
        elif "temperature" in param_name.lower():
            ideal_pct_range_air = 0.05
            ideal_pct_range_water = 0.03
            slight_dev_pct = 0.1
            medium_dev_pct = 0.2
            high_dev_pct = 0.3
            ideal_bonus = 8
            good_bonus = 2
            slight_penalty = 0 # Changed from -3
            medium_penalty = 0
            high_penalty = 0
            severe_penalty = 0

            ideal_pct_range = ideal_pct_range_air if "air" in param_name.lower() else ideal_pct_range_water

            if abs(current_value - ideal_val) <= ideal_val * ideal_pct_range:
                return ideal_bonus
            elif abs(current_value - ideal_val) <= ideal_val * slight_dev_pct:
                return good_bonus
            elif abs(current_value - ideal_val) <= ideal_val * medium_dev_pct:
                return slight_penalty
            elif abs(current_value - ideal_val) <= ideal_val * high_dev_pct:
                return medium_penalty
            else:
                return high_penalty
        elif "current_speed" in param_name.lower():
            ideal_threshold = 0.2
            low_threshold = 0.5
            medium_threshold = 1.0
            high_threshold = 1.5
            ideal_bonus = 3
            low_penalty = 0
            medium_penalty = 0
            high_penalty = 0
            severe_penalty = 0

            if current_value <= ideal_threshold:
                return ideal_bonus
            elif current_value <= low_threshold:
                return low_penalty
            elif current_value <= medium_threshold:
                return medium_penalty
            elif current_value <= high_threshold:
                return high_penalty
            else:
                return severe_penalty
        else:
            ideal_pct_range = 0.1
            medium_dev_pct = 0.2
            high_dev_pct = 0.3
            ideal_bonus = 5
            medium_penalty = 0
            high_penalty = 0

        if abs(current_value - ideal_val) <= ideal_val * ideal_pct_range:
            return ideal_bonus
        elif abs(current_value - ideal_val) <= ideal_val * medium_dev_pct:
            return -medium_penalty
        elif abs(current_value - ideal_val) <= ideal_val * high_dev_pct:
            return -high_penalty
        else:
            return 0 # Changed from -high_penalty * 2

    def calculate_wind_score(wind_speed, wind_direction_degrees, preferred_wind_direction_str, spot_coast_orientation_str):
        """
        Calculates the wind score based on speed and direction,
        considering if it's offshore/onshore for the peak.
        """
        if wind_speed is None or wind_direction_degrees is None or preferred_wind_direction_str is None or spot_coast_orientation_str is None:
            return 0

        wind_speed = float(wind_speed)
        preferred_wind_direction_degrees = cardinal_to_degrees(preferred_wind_direction_str)

        if preferred_wind_direction_degrees is None:
            return 0

        ideal_wind_angle_tolerance = 45

        angular_diff = calculate_angular_difference(wind_direction_degrees, preferred_wind_direction_degrees)
        
        is_ideal_wind_direction = False
        if angular_diff is not None and angular_diff <= ideal_wind_angle_tolerance:
            is_ideal_wind_direction = True

        score_result = 0
        if is_ideal_wind_direction:
            if wind_speed <= 3:
                score_result = 10
            elif 3 < wind_speed <= 10:
                score_result = 25
            elif 10 < wind_speed <= 15:
                score_result = 15
            elif 15 < wind_speed <= 20:
                score_result = 0
            else:
                score_result = 0
        else:
            if wind_speed <= 3:
                score_result = 8
            elif 3 < wind_speed <= 8:
                score_result = 0 # Changed from -10
            elif 8 < wind_speed <= 15:
                score_result = 0
            else:
                score_result = 0
        return score_result

    def calculate_secondary_swell_impact(primary_swell_direction_sg, secondary_swell_height, secondary_swell_direction, secondary_swell_period):
        """
        Evaluates the impact of secondary swell on the primary swell, applying penalties.
        """
        if secondary_swell_height is None or secondary_swell_direction is None or primary_swell_direction_sg is None:
            return 0

        secondary_swell_height = float(secondary_swell_height)
        secondary_swell_direction = float(secondary_swell_direction)
        primary_swell_direction_sg = float(primary_swell_direction_sg)

        HIGH_IMPACT_SECONDARY_SWELL_HEIGHT = 1.5
        if secondary_swell_height < 0.5:
            return 0

        angle_diff = calculate_angular_difference(secondary_swell_direction, primary_swell_direction_sg)
        
        if angle_diff is None:
            return 0

        penalty_base = 0
        if 0 <= angle_diff <= 22.5:
            penalty_base = 0
        elif 22.5 < angle_diff <= 45:
            penalty_base = -5
        elif 45 < angle_diff <= 90:
            penalty_base = 0
        else:
            penalty_base = 0

        height_factor = min(secondary_swell_height / HIGH_IMPACT_SECONDARY_SWELL_HEIGHT, 1.0)
        if secondary_swell_height > HIGH_IMPACT_SECONDARY_SWELL_HEIGHT:
            height_factor = 1.0 + (secondary_swell_height - HIGH_IMPACT_SECONDARY_SWELL_HEIGHT) * 0.5

        impact_score = penalty_base * height_factor

        if secondary_swell_period is not None and forecast_entry.get('swell_period_sg') is not None:
            primary_swell_period_sg = float(forecast_entry['swell_period_sg'])
            if abs(float(secondary_swell_period) - float(primary_swell_period_sg)) < 3 and secondary_swell_height >= 0.8:
                impact_score *= 1.2

        return impact_score

    def calculate_tide_score(tide_phase, sea_level, ideal_tide_type, min_tide_height, max_tide_height, ideal_tide_height):
        """
        Calculates the tide score (phase and level).
        """
        tide_score = 0

        if tide_phase and ideal_tide_type:
            if tide_phase.lower() == ideal_tide_type.lower():
                tide_score += 8
            elif (tide_phase.lower() in ["low", "high"] and ideal_tide_type.lower() in ["rising", "falling"]) or \
                 (tide_phase.lower() in ["rising", "falling"] and ideal_tide_type.lower() in ["low", "high"]):
                tide_score -= 0
            else:
                tide_score -= 0

        if sea_level is not None:
            sea_level = float(sea_level)

            if min_tide_height is not None and sea_level < float(min_tide_height):
                tide_score += 0 # Changed from penalty calculation
            elif max_tide_height is not None and sea_level > float(max_tide_height):
                tide_score += 0 # Changed from penalty calculation
            else:
                if ideal_tide_height is not None:
                    ideal_tide_height = float(ideal_tide_height)
                    if abs(sea_level - ideal_tide_height) <= 0.1:
                        tide_score += 10
                    elif abs(sea_level - ideal_tide_height) <= 0.2:
                        tide_score += 7
                    else:
                        tide_score += 3
                else:
                    tide_score += 5

        return tide_score

    # --- Processing Parameters and Accumulating Score ---
    print(f"\n--- Calculating suitability score for forecast entry at time: {forecast_entry.get('time_sg')} ---")

    # Height
    wave_height_forecast = forecast_entry.get('wave_height_sg')
    min_wave_height = get_pref_float('min_wave_height')
    max_wave_height = get_pref_float('max_wave_height')
    ideal_wave_height = get_pref_float('ideal_wave_height')
    wave_height_score_base = score_proximity_to_range_ideal(
        wave_height_forecast, min_wave_height, max_wave_height, ideal_wave_height, param_name="wave_height"
    )
    print(f"   Wave Height: Forecast={wave_height_forecast}, Prefs=Min:{min_wave_height}/Max:{max_wave_height}/Ideal:{ideal_wave_height}, Base Score={wave_height_score_base}")

    swell_height_forecast = forecast_entry.get('swell_height_sg')
    min_swell_height = get_pref_float('min_swell_height')
    max_swell_height = get_pref_float('max_swell_height')
    ideal_swell_height = get_pref_float('ideal_swell_height')
    swell_height_score_base = score_proximity_to_range_ideal(
        swell_height_forecast, min_swell_height, max_swell_height, ideal_swell_height, param_name="swell_height"
    )
    print(f"   Swell Height: Forecast={swell_height_forecast}, Prefs=Min:{min_swell_height}/Max:{max_swell_height}/Ideal:{ideal_swell_height}, Base Score={swell_height_score_base}")

    height_total_score = (wave_height_score_base * 0.4) + (swell_height_score_base * 0.6)
    score += height_total_score
    detailed_scores['height_total_score'] = height_total_score
    print(f"   Total Height Score (Weighted): {height_total_score}")

    # Period
    wave_period_forecast = forecast_entry.get('wave_period_sg')
    min_wave_period = get_pref_float('min_wave_period')
    max_wave_period = get_pref_float('max_wave_period')
    ideal_wave_period = get_pref_float('ideal_wave_period')
    wave_period_score_base = score_proximity_to_range_ideal(
        wave_period_forecast, min_wave_period, max_wave_period, ideal_wave_period, param_name="wave_period"
    )
    print(f"   Wave Period: Forecast={wave_period_forecast}, Prefs=Min:{min_wave_period}/Max:{max_wave_period}/Ideal:{ideal_wave_period}, Base Score={wave_period_score_base}")

    swell_period_forecast = forecast_entry.get('swell_period_sg')
    min_swell_period = get_pref_float('min_swell_period')
    max_swell_period = get_pref_float('max_swell_period')
    ideal_swell_period = get_pref_float('ideal_swell_period')
    swell_period_score_base = score_proximity_to_range_ideal(
        swell_period_forecast, min_swell_period, max_swell_period, ideal_swell_period, param_name="swell_period"
    )
    print(f"   Swell Period: Forecast={swell_period_forecast}, Prefs=Min:{min_swell_period}/Max:{max_swell_period}/Ideal:{ideal_swell_period}, Base Score={swell_period_score_base}")

    period_total_score = (wave_period_score_base * 0.4) + (swell_period_score_base * 0.6)
    score += period_total_score
    detailed_scores['period_total_score'] = period_total_score
    print(f"   Total Period Score (Weighted): {period_total_score}")

    # Direction (Wave and Primary Swell)
    wave_direction_forecast_degrees = forecast_entry.get('wave_direction_sg')
    pref_wd_str = get_pref_str('preferred_wave_direction')
    pref_wd_degrees = cardinal_to_degrees(pref_wd_str)

    wave_direction_score_base = 0
    if wave_direction_forecast_degrees is not None and pref_wd_degrees is not None:
        angular_diff = calculate_angular_difference(wave_direction_forecast_degrees, pref_wd_degrees)
        if angular_diff is not None:
            if angular_diff <= 0:
                wave_direction_score_base = 3
            elif angular_diff <= 22.5:
                wave_direction_score_base = 1
            elif angular_diff <= 45:
                wave_direction_score_base = -1
            else:
                wave_direction_score_base = -5
    print(f"   Wave Direction: Forecast={wave_direction_forecast_degrees}, Preferred={pref_wd_str} ({pref_wd_degrees} deg), Base Score={wave_direction_score_base}")

    swell_direction_forecast_degrees = forecast_entry.get('swell_direction_sg')
    pref_sd_str = get_pref_str('preferred_swell_direction')
    pref_sd_degrees = cardinal_to_degrees(pref_sd_str)

    swell_direction_score_base = 0
    if swell_direction_forecast_degrees is not None and pref_sd_degrees is not None:
        angular_diff = calculate_angular_difference(swell_direction_forecast_degrees, pref_sd_degrees)
        if angular_diff is not None:
            if angular_diff <= 0:
                swell_direction_score_base = 3
            elif angular_diff <= 22.5:
                swell_direction_score_base = 1
            elif angular_diff <= 45:
                swell_direction_score_base = -1
            else:
                swell_direction_score_base = -5
    print(f"   Swell Direction: Forecast={swell_direction_forecast_degrees}, Preferred={pref_sd_str} ({pref_sd_degrees} deg), Base Score={swell_direction_score_base}")

    direction_total_score = (wave_direction_score_base * 0.4) + (swell_direction_score_base * 0.6)
    score += direction_total_score
    detailed_scores['direction_total_score'] = direction_total_score
    print(f"   Total Direction Score (Weighted): {direction_total_score}")

    # Secondary Swell
    secondary_swell_height_forecast = forecast_entry.get('secondary_swell_height_sg')
    secondary_swell_direction_forecast = forecast_entry.get('secondary_swell_direction_sg')
    secondary_swell_period_forecast = forecast_entry.get('secondary_swell_period_sg')
    primary_swell_direction_for_sec_swell = forecast_entry.get('swell_direction_sg')

    secondary_swell_impact_score = calculate_secondary_swell_impact(
        primary_swell_direction_for_sec_swell,
        secondary_swell_height_forecast,
        secondary_swell_direction_forecast,
        secondary_swell_period_forecast
    )
    score += secondary_swell_impact_score
    detailed_scores['secondary_swell_impact_score'] = secondary_swell_impact_score
    print(f"   Secondary Swell: Height={secondary_swell_height_forecast}, Dir={secondary_swell_direction_forecast}, Period={secondary_swell_period_forecast}, Impact Score={secondary_swell_impact_score}")

    # Wind
    wind_speed_forecast = forecast_entry.get('wind_speed_sg')
    wind_direction_forecast = forecast_entry.get('wind_direction_sg')
    preferred_wind_direction = get_pref_str('preferred_wind_direction')
    coast_orientation = spot.get('coast_orientation')

    wind_score = calculate_wind_score(
        wind_speed_forecast, wind_direction_forecast, preferred_wind_direction, coast_orientation
    )
    score += wind_score
    detailed_scores['wind_score'] = wind_score
    print(f"   Wind: Speed={wind_speed_forecast}, Direction={wind_direction_forecast}, Preferred={preferred_wind_direction}, Score={wind_score}")

    # Tide
    sea_level_forecast = forecast_entry.get('sea_level_sg')
    ideal_tide_type = get_pref_str('ideal_tide_type')
    min_sea_level = get_pref_float('min_sea_level')
    max_sea_level = get_pref_float('max_sea_level')
    ideal_sea_level = get_pref_float('ideal_sea_level')

    tide_score = calculate_tide_score(
        tide_phase, sea_level_forecast, ideal_tide_type, min_sea_level, max_sea_level, ideal_sea_level
    )
    score += tide_score
    detailed_scores['tide_score'] = tide_score
    print(f"   Tide: Phase={tide_phase}, Level={sea_level_forecast}, Prefs=Type:{ideal_tide_type}/Min:{min_sea_level}/Max:{max_sea_level}/Ideal:{ideal_sea_level}, Score={tide_score}")

    # Water Temperature
    water_temperature_forecast = forecast_entry.get('water_temperature_sg')
    ideal_water_temperature = get_pref_float('ideal_water_temperature')
    water_temperature_score = score_proximity_to_single_ideal(
        water_temperature_forecast, ideal_water_temperature, param_name="water_temperature"
    )
    score += water_temperature_score
    detailed_scores['water_temperature_score'] = water_temperature_score
    print(f"   Water Temperature: Forecast={water_temperature_forecast}, Preferred={ideal_water_temperature}, Score={water_temperature_score}")

    # Air Temperature
    air_temperature_forecast = forecast_entry.get('air_temperature_sg')
    ideal_air_temperature = get_pref_float('ideal_air_temperature')
    air_temperature_score = score_proximity_to_single_ideal(
        air_temperature_forecast, ideal_air_temperature, param_name="air_temperature"
    )
    score += air_temperature_score
    detailed_scores['air_temperature_score'] = air_temperature_score
    print(f"   Air Temperature: Forecast={air_temperature_forecast}, Preferred={ideal_air_temperature}, Score={air_temperature_score}")

    # Current
    current_speed_forecast = forecast_entry.get('current_speed_sg')
    ideal_current_speed = 0
    current_speed_score = score_proximity_to_single_ideal(
        current_speed_forecast, ideal_current_speed, param_name="current_speed"
    )
    score += current_speed_score
    detailed_scores['current_speed_score'] = current_speed_score
    print(f"   Current Speed: Forecast={current_speed_forecast}, Preferred={ideal_current_speed}, Score={current_speed_score}")

    # User Level - additional penalties based on surfer level
    user_surf_level = user.get('surf_level')
    wave_height = forecast_entry.get('wave_height_sg')
    user_level_penalty = 0

    if user_surf_level == 'beginner' and wave_height is not None:
        if wave_height > 1.5:
            user_level_penalty -= 0 # Changed from -10
        if wave_height > 2.5:
            user_level_penalty -= 0 # Changed from -20
    elif user_surf_level == 'intermediate' and wave_height is not None:
        if wave_height > 3.0:
            user_level_penalty -= 0 # Changed from -10
    
    score += user_level_penalty
    if user_level_penalty != 0:
        detailed_scores['user_level_penalty'] = user_level_penalty
        print(f"   User Level ({user_surf_level}) Penalty: {user_level_penalty} (for wave height {wave_height})")

    # Ensures the final score is not negative and does not exceed 100.
    final_score = max(0, min(100, score))
    print(f"--- Final Score: {final_score} (Raw Score: {score}) ---")
    print(f"--- Detailed Scores: {detailed_scores} ---")

    return final_score, detailed_scores