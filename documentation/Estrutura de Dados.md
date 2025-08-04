# Data Structure Document for 'TheCheck'

This document details the relational database (SQL) schema for the 'TheCheck' system, with an explanation for each table and its purpose.

## Table of Contents
1.  [`spots` Table](#1-spots-table)
2.  [`forecasts` Table](#2-forecasts-table)
3.  [`tides_forecast` Table](#3-tides_forecast-table)
4.  [`users` Table](#4-users-table)
5.  [`user_spot_preferences` Table](#5-user_spot_preferences-table)
6.  [`model_spot_preferences` Table](#6-model_spot_preferences-table)
7.  [`level_spot_preferences` Table](#7-level_spot_preferences-table)
8.  [`surf_ratings` Table](#8-surf_ratings-table)
9.  [`rating_conditions_snapshot` Table](#9-rating_conditions_snapshot-table)
10. [SQL Schema (PostgreSQL)](#sql-schema-postgresql)

## 1. `spots` Table

Stores static and geographical information about each surf spot.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :----------------------------------------------------------------------------- |
| `spot_id` | SERIAL PRIMARY KEY | Unique and auto-incrementing identifier for the surf spot. |
| `spot_name` | VARCHAR(255) UNIQUE NOT NULL | Common and unique name of the surf spot (e.g., "Reserva", "Macumba"). |
| `latitude` | NUMERIC(10, 7) NOT NULL | Latitude of the surf spot's location. |
| `longitude` | NUMERIC(10, 7) NOT NULL | Longitude of the surf spot's location. |
| `timezone` | VARCHAR(64) NOT NULL | IANA Time Zone string (e.g., 'America/Sao_Paulo') for the spot's local time. |

---

## 2. `forecasts` Table

Stores hourly forecast data for surf conditions at various spots.

| Column Name | Data Type | Description |
| :------------------------------ | :---------------------------- | :----------------------------------------------------------------------------------- |
| `forecast_id` | SERIAL PRIMARY KEY | Unique identifier for each forecast entry. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The UTC timestamp for which the forecast data is valid (usually hourly). |
| `wave_height_sg` | NUMERIC(5, 2) | Significant wave height (m). |
| `wave_direction_sg` | NUMERIC(6, 2) | Wave direction (degrees true). |
| `wave_period_sg` | NUMERIC(5, 2) | Wave period (s). |
| `swell_height_sg` | NUMERIC(5, 2) | Primary swell height (m). |
| `swell_direction_sg` | NUMERIC(6, 2) | Primary swell direction (degrees true). |
| `swell_period_sg` | NUMERIC(5, 2) | Primary swell period (s). |
| `secondary_swell_height_sg` | NUMERIC(5, 2) | Secondary swell height (m). |
| `secondary_swell_direction_sg` | NUMERIC(6, 2) | Secondary swell direction (degrees true). |
| `secondary_swell_period_sg` | NUMERIC(5, 2) | Secondary swell period (s). |
| `wind_speed_sg` | NUMERIC(5, 2) | Wind speed (m/s). |
| `wind_direction_sg` | NUMERIC(6, 2) | Wind direction (degrees true). |
| `water_temperature_sg` | NUMERIC(5, 2) | Water temperature (°C). |
| `air_temperature_sg` | NUMERIC(5, 2) | Air temperature (°C). |
| `current_speed_sg` | NUMERIC(5, 2) | Ocean current speed (m/s). |
| `current_direction_sg` | NUMERIC(6, 2) | Ocean current direction (degrees true). |
| `sea_level_sg` | NUMERIC(5, 2) | Sea level anomaly (m) relative to mean sea level (used for tide calculation). |
| `snapshot_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this forecast entry was retrieved from the external API. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_spot`: Foreign key constraint linking `spot_id` to `spots.spot_id`.
* `uq_forecast_spot_timestamp`: Unique constraint to prevent duplicate forecast entries for the same spot and timestamp.

---

## 3. `tides_forecast` Table

Stores predicted tidal extreme (high/low) times and heights for various spots.

| Column Name | Data Type | Description |
| :---------------- | :---------------------------- | :---------------------------------------------------------------------------------- |
| `tide_id` | SERIAL PRIMARY KEY | Unique identifier for each tide forecast entry. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The UTC timestamp for the predicted high or low tide. |
| `tide_type` | VARCHAR(10) NOT NULL | Type of tide ('high' or 'low'). |
| `height` | NUMERIC(5, 2) NOT NULL | Predicted tide height (m) relative to a local datum. |
| `snapshot_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this tide forecast entry was retrieved from the external API. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_spot_tide`: Foreign key constraint linking `spot_id` to `spots.spot_id`.
* `uq_tide_spot_timestamp_type`: Unique constraint to prevent duplicate tide entries for the same spot, timestamp, and type.

---

## 4. `users` Table

Stores user authentication and profile information.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :------------------------------------------------------------------------------------------------- |
| `user_id` | UUID PRIMARY KEY DEFAULT gen_random_uuid() | Unique identifier for the user (UUID v4). |
| `name` | VARCHAR(255) NOT NULL | User's full name or display name. |
| `email` | VARCHAR(255) UNIQUE NOT NULL | User's email address, used for login and unique identification. |
| `password_hash` | VARCHAR(255) NOT NULL | Hashed password of the user for secure storage. |
| `surf_level` | VARCHAR(50) | User's surf level (e.g., 'beginner', 'intermediate', 'advanced', 'expert'). |
| `goofy_regular_stance` | VARCHAR(10) | User's surfing stance ('goofy' or 'regular'). |
| `preferred_wave_direction` | VARCHAR(20) | User's preferred wave direction (e.g., 'north', 'south', 'east', 'west', 'northeast', etc.). |
| `bio` | TEXT | A short biography or description provided by the user. |
| `profile_picture_url` | VARCHAR(255) | URL to the user's profile picture. |
| `registration_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when the user registered. |
| `last_login_timestamp` | TIMESTAMP WITH TIME ZONE | Timestamp of the user's last successful login. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

---

## 5. `user_spot_preferences` Table

Stores specific preferences for a user for a particular surf spot, overriding general preferences.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :--------------------------------------------------------------------------------------- |
| `user_preference_id` | SERIAL PRIMARY KEY | Unique identifier for each user preference entry. |
| `user_id` | UUID NOT NULL | Foreign key referencing `users.user_id`. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `min_wave_height` | NUMERIC(5, 2) | Minimum preferred wave height (m). |
| `max_wave_height` | NUMERIC(5, 2) | Maximum preferred wave height (m). |
| `ideal_wave_height` | NUMERIC(5, 2) | Ideal wave height (m). |
| `preferred_swell_direction` | VARCHAR(20) | User's preferred swell direction for this spot. |
| `ideal_tide_type` | VARCHAR(10) | User's ideal tide type ('high', 'low', 'mid', 'any'). |
| `min_wind_speed` | NUMERIC(5, 2) | Minimum preferred wind speed (m/s). |
| `max_wind_speed` | NUMERIC(5, 2) | Maximum preferred wind speed (m/s). |
| `ideal_wind_speed` | NUMERIC(5, 2) | Ideal wind speed (m/s). |
| `preferred_wind_direction` | VARCHAR(20) | User's preferred wind direction for this spot. |
| `min_water_temperature` | NUMERIC(5, 2) | Minimum preferred water temperature (°C). |
| `max_water_temperature` | NUMERIC(5, 2) | Maximum preferred water temperature (°C). |
| `ideal_water_temperature` | NUMERIC(5, 2) | Ideal water temperature (°C). |
| `min_air_temperature` | NUMERIC(5, 2) | Minimum preferred air temperature (°C). |
| `max_air_temperature` | NUMERIC(5, 2) | Maximum preferred air temperature (°C). |
| `ideal_air_temperature` | NUMERIC(5, 2) | Ideal air temperature (°C). |
| `min_sea_level` | NUMERIC(5, 2) | Minimum preferred sea level (m). |
| `max_sea_level` | NUMERIC(5, 2) | Maximum preferred sea level (m). |
| `ideal_sea_level` | NUMERIC(5, 2) | Ideal sea level (m). |
| `preferred_current_direction` | VARCHAR(20) | User's preferred current direction for this spot. |
| `max_crowd_tolerance` | VARCHAR(20) | User's tolerance for crowd ('low', 'medium', 'high'). |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_user_pref`: Foreign key constraint linking `user_id` to `users.user_id`.
* `fk_spot_pref`: Foreign key constraint linking `spot_id` to `spots.spot_id`.
* `uq_user_spot_pref`: Unique constraint to ensure only one preference entry per user per spot.

---

## 6. `model_spot_preferences` Table

Stores default preferences for a given surf spot, to be used by the recommendation model if no user or level-specific preference is found. These are generally optimal conditions for the spot itself.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :------------------------------------------------------------------------------------------------- |
| `model_preference_id` | SERIAL PRIMARY KEY | Unique identifier for each model preference entry. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `min_wave_height` | NUMERIC(5, 2) | Minimum preferred wave height (m). |
| `max_wave_height` | NUMERIC(5, 2) | Maximum preferred wave height (m). |
| `ideal_wave_height` | NUMERIC(5, 2) | Ideal wave height (m). |
| `preferred_swell_direction` | VARCHAR(20) | Preferred swell direction for this spot (e.g., 'southwest', 'east'). |
| `ideal_tide_type` | VARCHAR(10) | Ideal tide type ('high', 'low', 'mid', 'any'). |
| `min_wind_speed` | NUMERIC(5, 2) | Minimum preferred wind speed (m/s). |
| `max_wind_speed` | NUMERIC(5, 2) | Maximum preferred wind speed (m/s). |
| `ideal_wind_speed` | NUMERIC(5, 2) | Ideal wind speed (m/s). |
| `preferred_wind_direction` | VARCHAR(20) | Preferred wind direction for this spot (e.g., 'northeast', 'south'). |
| `min_water_temperature` | NUMERIC(5, 2) | Minimum preferred water temperature (°C). |
| `max_water_temperature` | NUMERIC(5, 2) | Maximum preferred water temperature (°C). |
| `ideal_water_temperature` | NUMERIC(5, 2) | Ideal water temperature (°C). |
| `min_air_temperature` | NUMERIC(5, 2) | Minimum preferred air temperature (°C). |
| `max_air_temperature` | NUMERIC(5, 2) | Maximum preferred air temperature (°C). |
| `ideal_air_temperature` | NUMERIC(5, 2) | Ideal air temperature (°C). |
| `min_sea_level` | NUMERIC(5, 2) | Minimum preferred sea level (m). |
| `max_sea_level` | NUMERIC(5, 2) | Maximum preferred sea level (m). |
| `ideal_sea_level` | NUMERIC(5, 2) | Ideal sea level (m). |
| `preferred_current_direction` | VARCHAR(20) | Preferred current direction for this spot. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_spot_model_pref`: Foreign key constraint linking `spot_id` to `spots.spot_id`.
* `uq_model_spot_pref`: Unique constraint to ensure only one model preference entry per spot.

---

## 7. `level_spot_preferences` Table

Stores preferences for a given surf level at a particular surf spot. These preferences are applied if no user-specific preference is defined.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :------------------------------------------------------------------------------------------------- |
| `level_preference_id` | SERIAL PRIMARY KEY | Unique identifier for each level preference entry. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `surf_level` | VARCHAR(50) NOT NULL | Surf level (e.g., 'beginner', 'intermediate', 'advanced', 'expert'). |
| `min_wave_height` | NUMERIC(5, 2) | Minimum preferred wave height (m). |
| `max_wave_height` | NUMERIC(5, 2) | Maximum preferred wave height (m). |
| `ideal_wave_height` | NUMERIC(5, 2) | Ideal wave height (m). |
| `preferred_swell_direction` | VARCHAR(20) | Preferred swell direction for this spot for this level. |
| `ideal_tide_type` | VARCHAR(10) | Ideal tide type ('high', 'low', 'mid', 'any'). |
| `min_wind_speed` | NUMERIC(5, 2) | Minimum preferred wind speed (m/s). |
| `max_wind_speed` | NUMERIC(5, 2) | Maximum preferred wind speed (m/s). |
| `ideal_wind_speed` | NUMERIC(5, 2) | Ideal wind speed (m/s). |
| `preferred_wind_direction` | VARCHAR(20) | Preferred wind direction for this spot for this level. |
| `min_water_temperature` | NUMERIC(5, 2) | Minimum preferred water temperature (°C). |
| `max_water_temperature` | NUMERIC(5, 2) | Maximum preferred water temperature (°C). |
| `ideal_water_temperature` | NUMERIC(5, 2) | Ideal water temperature (°C). |
| `min_air_temperature` | NUMERIC(5, 2) | Minimum preferred air temperature (°C). |
| `max_air_temperature` | NUMERIC(5, 2) | Maximum preferred air temperature (°C). |
| `ideal_air_temperature` | NUMERIC(5, 2) | Ideal air temperature (°C). |
| `min_sea_level` | NUMERIC(5, 2) | Minimum preferred sea level (m). |
| `max_sea_level` | NUMERIC(5, 2) | Maximum preferred sea level (m). |
| `ideal_sea_level` | NUMERIC(5, 2) | Ideal sea level (m). |
| `preferred_current_direction` | VARCHAR(20) | Preferred current direction for this spot for this level. |
| `max_crowd_tolerance` | VARCHAR(20) | Tolerance for crowd ('low', 'medium', 'high') for this level. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_spot_level_pref`: Foreign key constraint linking `spot_id` to `spots.spot_id`.
* `uq_level_spot_pref`: Unique constraint to ensure only one preference entry per spot per surf level.

---

## 8. `surf_ratings` Table

Stores user-submitted ratings for past surf sessions, linking them to a specific spot and providing an overall assessment.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :----------------------------------------------------------------------------- |
| `rating_id` | SERIAL PRIMARY KEY | Unique identifier for each surf rating. |
| `user_id` | UUID NOT NULL | Foreign key referencing `users.user_id`. |
| `spot_id` | INTEGER NOT NULL | Foreign key referencing `spots.spot_id`. |
| `rating_value` | INTEGER NOT NULL | User's rating for the surf session (e.g., 1-5, or a custom scale). |
| `comments` | TEXT | Optional comments from the user about the session. |
| `session_date` | DATE NOT NULL | The date of the surf session. |
| `session_start_time` | TIME WITH TIME ZONE | Optional start time of the session (UTC). |
| `session_end_time` | TIME WITH TIME ZONE | Optional end time of the session (UTC). |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_user_rating`: Foreign key constraint linking `user_id` to `users.user_id`.
* `fk_spot_rating`: Foreign key constraint linking `spot_id` to `spots.spot_id`.

---

## 9. `rating_conditions_snapshot` Table

Stores a snapshot of environmental conditions at the time a `surf_rating` was given. This allows for historical analysis of what conditions led to a good or bad rating.

| Column Name | Data Type | Description |
| :----------------------------- | :---------------------------- | :------------------------------------------------------------------------------------- |
| `snapshot_id` | SERIAL PRIMARY KEY | Unique identifier for each conditions snapshot. |
| `rating_id` | INTEGER UNIQUE NOT NULL | Foreign key referencing `surf_ratings.rating_id`. Each rating can have only one snapshot. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The exact UTC timestamp of the conditions snapshot. |
| `wave_height_sg` | NUMERIC(5, 2) | Significant wave height (m). |
| `wave_direction_sg` | NUMERIC(6, 2) | Wave direction (degrees true). |
| `wave_period_sg` | NUMERIC(5, 2) | Wave period (s). |
| `swell_height_sg` | NUMERIC(5, 2) | Primary swell height (m). |
| `swell_direction_sg` | NUMERIC(6, 2) | Primary swell direction (degrees true). |
| `swell_period_sg` | NUMERIC(5, 2) | Primary swell period (s). |
| `secondary_swell_height_sg` | NUMERIC(5, 2) | Secondary swell height (m). |
| `secondary_swell_direction_sg` | NUMERIC(6, 2) | Secondary swell direction (degrees true). |
| `secondary_swell_period_sg` | NUMERIC(5, 2) | Secondary swell period (s). |
| `wind_speed_sg` | NUMERIC(5, 2) | Wind speed (m/s). |
| `wind_direction_sg` | NUMERIC(6, 2) | Wind direction (degrees true). |
| `water_temperature_sg` | NUMERIC(5, 2) | Water temperature (°C). |
| `air_temperature_sg` | NUMERIC(5, 2) | Air temperature (°C). |
| `current_speed_sg` | NUMERIC(5, 2) | Ocean current speed (m/s). |
| `current_direction_sg` | NUMERIC(6, 2) | Ocean current direction (degrees true). |
| `sea_level_sg` | NUMERIC(5, 2) | Sea level anomaly (m) relative to mean sea level. |
| `tide_type` | VARCHAR(10) | Type of tide at the moment of the snapshot ('high', 'low', 'mid'). |
| `tide_height` | NUMERIC(5, 3) | Actual tide height (m) at the moment of the snapshot. |
| `snapshot_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this snapshot record was created. |
| `created_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp when this record was created in the database. |
| `updated_at` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | Timestamp of the last update to this record. |
| `is_deleted` | BOOLEAN DEFAULT FALSE | Flag to soft delete records. |

**Constraints:**
* `fk_rating_snapshot`: Foreign key constraint linking `rating_id` to `surf_ratings.rating_id`.
* `uq_rating_id`: Unique constraint on `rating_id` to ensure one snapshot per rating.

---

## SQL Schema (PostgreSQL)

```sql
-- Extensão para geração de UUIDs (se ainda não estiver habilitada)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Ou gen_random_uuid() para PostgreSQL 13+

CREATE TABLE IF NOT EXISTS spots (
    spot_id SERIAL PRIMARY KEY,
    spot_name VARCHAR(255) UNIQUE NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    timezone VARCHAR(64) NOT NULL, -- IANA Time Zone (e.g., 'America/Sao_Paulo')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    wave_height_sg NUMERIC(5, 2),
    wave_direction_sg NUMERIC(6, 2),
    wave_period_sg NUMERIC(5, 2),
    swell_height_sg NUMERIC(5, 2),
    swell_direction_sg NUMERIC(6, 2),
    swell_period_sg NUMERIC(5, 2),
    secondary_swell_height_sg NUMERIC(5, 2),
    secondary_swell_direction_sg NUMERIC(6, 2),
    secondary_swell_period_sg NUMERIC(5, 2),
    wind_speed_sg NUMERIC(5, 2),
    wind_direction_sg NUMERIC(6, 2),
    water_temperature_sg NUMERIC(5, 2),
    air_temperature_sg NUMERIC(5, 2),
    current_speed_sg NUMERIC(5, 2),
    current_direction_sg NUMERIC(6, 2),
    sea_level_sg NUMERIC(5, 2),
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_spot FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_forecast_spot_timestamp UNIQUE (spot_id, timestamp_utc)
);

CREATE TABLE IF NOT EXISTS tides_forecast (
    tide_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    tide_type VARCHAR(10) NOT NULL, -- 'high' or 'low'
    height NUMERIC(5, 2) NOT NULL,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_spot_tide FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_tide_spot_timestamp_type UNIQUE (spot_id, timestamp_utc, tide_type)
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- PostgreSQL 13+
    -- user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), -- Para versões anteriores com uuid-ossp
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    surf_level VARCHAR(50), -- e.g., 'beginner', 'intermediate', 'advanced', 'expert'
    goofy_regular_stance VARCHAR(10), -- 'goofy' or 'regular'
    preferred_wave_direction VARCHAR(20), -- 'north', 'south', 'east', 'west', 'northeast', etc.
    bio TEXT,
    profile_picture_url VARCHAR(255),
    registration_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS user_spot_preferences (
    user_preference_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    spot_id INTEGER NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    min_water_temperature NUMERIC(5, 2),
    max_water_temperature NUMERIC(5, 2),
    ideal_water_temperature NUMERIC(5, 2),
    min_air_temperature NUMERIC(5, 2),
    max_air_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    preferred_current_direction VARCHAR(20),
    max_crowd_tolerance VARCHAR(20), -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_user_pref FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_spot_pref FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_user_spot_pref UNIQUE (user_id, spot_id)
);

CREATE TABLE IF NOT EXISTS model_spot_preferences (
    model_preference_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    min_water_temperature NUMERIC(5, 2),
    max_water_temperature NUMERIC(5, 2),
    ideal_water_temperature NUMERIC(5, 2),
    min_air_temperature NUMERIC(5, 2),
    max_air_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    preferred_current_direction VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_spot_model_pref FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_model_spot_pref UNIQUE (spot_id)
);

CREATE TABLE IF NOT EXISTS level_spot_preferences (
    level_preference_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    surf_level VARCHAR(50) NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    min_water_temperature NUMERIC(5, 2),
    max_water_temperature NUMERIC(5, 2),
    ideal_water_temperature NUMERIC(5, 2),
    min_air_temperature NUMERIC(5, 2),
    max_air_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    preferred_current_direction VARCHAR(20),
    max_crowd_tolerance VARCHAR(20), -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_spot_level_pref FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_level_spot_pref UNIQUE (spot_id, surf_level)
);

CREATE TABLE IF NOT EXISTS surf_ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    spot_id INTEGER NOT NULL,
    rating_value INTEGER NOT NULL,
    comments TEXT,
    session_date DATE NOT NULL,
    session_start_time TIME WITH TIME ZONE,
    session_end_time TIME WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_user_rating FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_spot_rating FOREIGN KEY (spot_id) REFERENCES spots(spot_id)
);

CREATE TABLE IF NOT EXISTS rating_conditions_snapshot (
    snapshot_id SERIAL PRIMARY KEY,
    rating_id INTEGER UNIQUE NOT NULL, -- UNIQUE para garantir 1 snapshot por rating
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    wave_height_sg NUMERIC(5, 2),
    wave_direction_sg NUMERIC(6, 2),
    wave_period_sg NUMERIC(5, 2),
    swell_height_sg NUMERIC(5, 2),
    swell_direction_sg NUMERIC(6, 2),
    swell_period_sg NUMERIC(5, 2),
    secondary_swell_height_sg NUMERIC(5, 2),
    secondary_swell_direction_sg NUMERIC(6, 2),
    secondary_swell_period_sg NUMERIC(5, 2),
    wind_speed_sg NUMERIC(5, 2),
    wind_direction_sg NUMERIC(6, 2),
    water_temperature_sg NUMERIC(5, 2),
    air_temperature_sg NUMERIC(5, 2),
    current_speed_sg NUMERIC(5, 2),
    current_direction_sg NUMERIC(6, 2),
    sea_level_sg NUMERIC(5, 2),
    tide_type VARCHAR(10),
    tide_height NUMERIC(5, 3),
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_rating_snapshot FOREIGN KEY (rating_id) REFERENCES surf_ratings(rating_id)
);
````
