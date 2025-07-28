Excellent, those name changes make perfect sense for clarity and consistency\!

Here's the updated schema with `hourly_forecasts` becoming `forecasts` and `tides` becoming `tides_forecast`, including the new `rating_conditions_snapshot` table.

-----

# Data Structure Document for 'TheCheck'

This document details the relational database (SQL) schema for the 'TheCheck' system, with an explanation for each table and its purpose.

## 1\. `spots` Table

Stores static and geographical information about each surf spot.

| Column Name | Data Type | Description |
| :----------------------- | :---------------------------- | :----------------------------------------------------------------------------- |
| `spot_id` | SERIAL PRIMARY KEY | Unique and auto-incrementing identifier for the surf spot. |
| `spot_name` | VARCHAR(255) UNIQUE NOT NULL | Common and unique name of the surf spot (e.g., "Reserva", "Macumba"). |
| `latitude` | NUMERIC(10, 7) NOT NULL | Latitude of the surf spot's location. |
| `longitude` | NUMERIC(10, 7) NOT NULL | Longitude of the surf spot's location. |
| `bottom_type` | VARCHAR(50) | Type of seafloor at the spot (e.g., "Sand", "Coral", "Reef", "Mixed"). |
| `coast_orientation` | VARCHAR(10) | Primary orientation of the spot's coastline (e.g., "SE", "NW", "S"). |
| `description` | TEXT | A brief general description of the surf spot. |
| `general_characteristics` | JSONB | Less structured or dynamic characteristics (ex: "crowd", "wave", "best\_tide"). |

-----

## 2\. `forecasts` Table

Store weather, ondulation, wind and tide forecast data.

| Column Name | Data Type | Description |
| :---------------------------- | :------------------------------------- | :----------------------------------------------------------------------------- |
| `forecast_id` | BIGSERIAL PRIMARY KEY | Unique and auto-incrementing identifier for each hourly forecast record. |
| `spot_id` | INTEGER NOT NULL REFERENCES spots(spot\_id) | Foreign key to the `spots` table, associating the forecast with the surf spot. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The exact timestamp (in UTC) for which the forecast is valid. Crucial for time series. |
| `wave_height_sg` | NUMERIC(5, 2) | Wave height (StormGlass source). |
| `wave_direction_sg` | NUMERIC(6, 2) | Wave direction (StormGlass source). |
| `wave_period_sg` | NUMERIC(5, 2) | Wave period (StormGlass source). |
| `swell_height_sg` | NUMERIC(5, 2) | Primary swell height (StormGlass source). |
| `swell_direction_sg` | NUMERIC(6, 2) | Primary swell direction (StormGlass source). | |
| `swell_period_sg` | NUMERIC(5, 2) | Primary swell period (StormGlass source). |
| `secondary_swell_height_sg` | NUMERIC(5, 2) | Secondary swell height (StormGlass source). |
| `secondary_swell_direction_sg` | NUMERIC(6, 2) | Secondary swell direction (StormGlass source). |
| `secondary_swell_period_sg` | NUMERIC(5, 2) | Secondary swell period (StormGlass source). |
| `wind_speed_sg` | NUMERIC(5, 2) | Wind speed (StormGlass source). |
| `wind_direction_sg` | NUMERIC(6, 2) | Wind direction (StormGlass source). |
| `water_temperature_sg` | NUMERIC(5, 2) | Water temperature (StormGlass source). |
| `air_temperature_sg` | NUMERIC(5, 2) | Air temperature (StormGlass source). |
| `current_speed_sg` | NUMERIC(5, 2) | Current speed (StormGlass source). |
| `current_direction_sg` | NUMERIC(6, 2) | Current direction (StormGlass source). |
| `sea_level_sg` | NUMERIC(5, 2) | Relative sea level (in meters) provided by StormGlass.io. |
| `collection_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of when this forecast was collected and inserted into the DB. |

-----

## 3\. `tides_forecast` Table

Stores tide events (high/low) for each spot and date.

| Column Name | Data Type | Description |
| :---------------- | :------------------------------------- | :----------------------------------------------------------------------------- |
| `tide_forecast_id` | BIGSERIAL PRIMARY KEY | Unique and auto-incrementing identifier for each tide event. |
| `spot_id` | INTEGER NOT NULL REFERENCES spots(spot\_id) | Foreign key to the `spots` table, associating the tide event with the surf spot. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The exact timestamp (in UTC) of the tide event (e.g., peak high/low tide). |
| `tide_type` | VARCHAR(10) NOT NULL | Type of tide event (e.g., "high", "low"). |
| `height` | NUMERIC(5, 3) NOT NULL | Height of the tide at that point. |
| `collection_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of when this tide information was collected and inserted into the DB. |

-----

## 4\. `users` Table

Stores user profile information, including their global preferences.

| Column Name | Data Type | Description |
| :----------------------- | :----------------------------------- | :----------------------------------------------------------------------------- |
| `user_id` | SERIAL PRIMARY KEY | Unique and auto-incrementing identifier for the user. |
| `name` | VARCHAR(255) NOT NULL | User's name. |
| `email` | VARCHAR(255) UNIQUE NOT NULL | User's unique email address (used for login/identification). |
| `surf_level` | VARCHAR(50) | Surfer's skill level (e.g., "Beginner", "Intermediate", "Advanced"). |
| `preferred_region` | VARCHAR(255) | Surfer's preferred geographical region (to filter spots initially). |
| `goofy_regular_stance` | VARCHAR(10) | Surfer's preferred stance on the board (e.g., 'Goofy', 'Regular', 'Ambidextrous'). |
| `preferred_wave_direction` | VARCHAR(20) | Wave direction the surfer prefers to ride (e.g., 'Right', 'Left', 'Both'). |
| `registration_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of when the user registered in the system. |

-----

## 5\. `user_spot_preferences` Table

Stores detailed surf condition preferences for each user **specific to each surf spot**.

| Column Name | Data Type | Description |
| :------------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `preference_id` | SERIAL PRIMARY KEY | Unique identifier for each preference record. |
| `user_id` | INTEGER NOT NULL REFERENCES users(user\_id) | Foreign key to the `users` table. |
| `spot_id` | INTEGER NOT NULL REFERENCES spots(spot\_id) | Foreign key to the `spots` table. |
| `min_wave_height` | NUMERIC(5, 2) | Minimum preferred wave height for this spot. |
| `max_wave_height` | NUMERIC(5, 2) | Maximum preferred wave height for this spot. |
| `preferred_swell_direction` | VARCHAR(50) | Preferred swell direction(s) for this spot (can be a list of values, or flexible field). |
| `min_swell_period` | NUMERIC(5, 2) | Minimum preferred swell period for this spot. |
| `max_swell_period` | NUMERIC(5, 2) | Maximum preferred swell period for this spot. |
| `preferred_wind_direction` | VARCHAR(50) | Preferred wind direction(s) for this spot (e.g., 'N', 'NE', 'Offshore'). |
| `max_wind_speed` | NUMERIC(5, 2) | Maximum tolerated wind speed for this spot. |
| `additional_considerations` | TEXT | Additional notes or observations from the user about preferences for this spot. |
| `last_updated` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of the last update to this preference. |

-----

## 6\. `level_spot_preferences` Table

This table will store "ideal conditions" presets for each surf level at each spot, either manually entered or derived from aggregated initial data.

| Column Name | Data Type | Description |
| :------------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `level_preference_id` | BIGSERIAL PRIMARY KEY | Unique identifier for each level preference record. |
| `surf_level` | VARCHAR(50) NOT NULL | The surf level for which this preference is defined (e.g., "Beginner", "Intermediate"). |
| `spot_id` | INTEGER NOT NULL REFERENCES spots(spot\_id) | Foreign key to the `spots` table. |
| `min_wave_height` | NUMERIC(5, 2) | Minimum preferred wave height for this level at this spot. |
| `max_wave_height` | NUMERIC(5, 2) | Maximum preferred wave height for this level at this spot. |
| `preferred_swell_direction` | VARCHAR(50) | Preferred swell direction(s) for this level at this spot. |
| `min_swell_period` | NUMERIC(5, 2) | Minimum preferred swell period for this level at this spot. |
| `max_swell_period` | NUMERIC(5, 2) | Maximum preferred swell period for this level at this spot. |
| `preferred_wind_direction` | VARCHAR(50) | Preferred wind direction(s) for this level at this spot. |
| `max_wind_speed` | NUMERIC(5, 2) | Maximum tolerated wind speed for this level at this spot. |
| `ideal_tide_type` | VARCHAR(20) | Ideal tide type (ex: 'high', 'low', 'mid', 'rising', 'falling'). |
| `additional_considerations` | TEXT | Additional notes or observations about the preferences for this level at this spot. |
| `last_updated` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of the last update to this preference. |
| **Unique Index** | `UNIQUE (surf_level, spot_id)` | Ensures only one set of preferences per level per spot. |

-----

## 7\. `surf_ratings` Table

Stores user feedback on surf quality for a specific day/time at a particular spot, crucial for training the recommendation model.

| Column Name | Data Type | Description |
| :------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `rating_id` | SERIAL PRIMARY KEY | Unique and auto-incrementing identifier for the rating. |
| `user_id` | INTEGER NOT NULL REFERENCES users(user\_id) | Foreign key to the `users` table. |
| `spot_id` | INTEGER NOT NULL REFERENCES spots(spot\_id) | Foreign key to the `spots` table. |
| `rating_date` | DATE NOT NULL | The date on which the surf was rated. |
| `rating_time` | TIME | The approximate time the surf session occurred (if the user can specify). |
| `surf_quality` | INTEGER NOT NULL | Numeric score (e.g., 1 to 5 or 1 to 10) for the surf quality of the rated session. |
| `comments` | TEXT | Additional comments from the user about the rated surf session. |
| `registration_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp of when the rating was recorded in the system. |

-----

## 8\. `rating_conditions_snapshot` Table

Stores a snapshot of environmental conditions (weather, swell, wind, tide) at the exact time a user surfed and provided a rating. This ensures historical context is preserved even if original forecast data is purged.

| Column Name | Data Type | Description |
| :------------------------------- | :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `snapshot_id` | BIGSERIAL PRIMARY KEY | Unique identifier for each conditions snapshot. |
| `rating_id` | INTEGER NOT NULL UNIQUE REFERENCES surf\_ratings(rating\_id) | Foreign key to the `surf_ratings` table. **Unique** constraint ensures one snapshot per rating. |
| `timestamp_utc` | TIMESTAMP WITH TIME ZONE NOT NULL | The UTC timestamp of the original conditions being snapshotted. Should ideally match the combined `rating_date` and `rating_time` from `surf_ratings`. |
| `wave_height_sg` | NUMERIC(5, 2) | Snapshotted wave height from StormGlass. |
| `wave_direction_sg` | NUMERIC(6, 2) | Snapshotted wave direction from StormGlass. |
| `wave_period_sg` | NUMERIC(5, 2) | Snapshotted wave period from StormGlass. |
| `swell_height_sg` | NUMERIC(5, 2) | Snapshotted primary swell height from StormGlass. |
| `swell_direction_sg` | NUMERIC(6, 2) | Snapshotted primary swell direction from StormGlass. |
| `swell_period_sg` | NUMERIC(5, 2) | Snapshotted primary swell period from StormGlass. |
| `secondary_swell_height_sg` | NUMERIC(5, 2) | Snapshotted secondary swell height from StormGlass. |
| `secondary_swell_direction_sg` | NUMERIC(6, 2) | Snapshotted secondary swell direction from StormGlass. |
| `secondary_swell_period_sg` | NUMERIC(5, 2) | Snapshotted secondary swell period from StormGlass. |
| `wind_speed_sg` | NUMERIC(5, 2) | Snapshotted wind speed from StormGlass. |
| `wind_direction_sg` | NUMERIC(6, 2) | Snapshotted wind direction from StormGlass. |
| `water_temperature_sg` | NUMERIC(5, 2) | Snapshotted water temperature from StormGlass. |
| `air_temperature_sg` | NUMERIC(5, 2) | Snapshotted air temperature from StormGlass. |
| `current_speed_sg` | NUMERIC(5, 2) | Snapshotted current speed from StormGlass. |
| `current_direction_sg` | NUMERIC(6, 2) | Snapshotted current direction from StormGlass. |
| `sea_level_sg` | NUMERIC(5, 2) | Snapshotted relative sea level from StormGlass. |
| `tide_type` | VARCHAR(10) | Snapshotted tide type (high/low/etc.) for the rating time. |
| `tide_height` | NUMERIC(5, 3) | Snapshotted tide height for the rating time. |
| `snapshot_timestamp` | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | The timestamp when this conditions snapshot was created. |

-----

## SQL Schema (PostgreSQL)

```sql
-- Table creation for spots
CREATE TABLE spots (
    spot_id SERIAL PRIMARY KEY,
    spot_name VARCHAR(255) UNIQUE NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    bottom_type VARCHAR(50),
    coast_orientation VARCHAR(10),
    description TEXT,
    general_characteristics JSONB
);

-- Table creation for forecasts
CREATE TABLE forecasts (
    forecast_id BIGSERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL REFERENCES spots(spot_id),
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
    collection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (spot_id, timestamp_utc) -- Ensures no duplicate forecasts for the same spot at the same timestamp
);

-- Indexes for forecasts
CREATE INDEX idx_forecasts_spot_ts ON forecasts (spot_id, timestamp_utc DESC);
CREATE INDEX idx_forecasts_ts ON forecasts (timestamp_utc DESC);


-- Table creation for tides_forecast
CREATE TABLE tides_forecast (
    tide_forecast_id BIGSERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL REFERENCES spots(spot_id),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    tide_type VARCHAR(10) NOT NULL,
    height NUMERIC(5, 3) NOT NULL,
    collection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (spot_id, timestamp_utc) -- Ensures no duplicate tide events for the same spot at the same timestamp
);

-- Index for tides_forecast
CREATE INDEX idx_tides_forecast_spot_ts ON tides_forecast (spot_id, timestamp_utc);

-- Table creation for users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    surf_level VARCHAR(50),
    preferred_region VARCHAR(255),
    goofy_regular_stance VARCHAR(10),
    preferred_wave_direction VARCHAR(20),
    registration_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table creation for user_spot_preferences
CREATE TABLE user_spot_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    spot_id INTEGER NOT NULL REFERENCES spots(spot_id),
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    preferred_swell_direction VARCHAR(50), -- Can be a JSONB field or array of strings for multiple values
    min_swell_period NUMERIC(5, 2),
    max_swell_period NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(50), -- Can be a JSONB field or array of strings
    max_wind_speed NUMERIC(5, 2),
    additional_considerations TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, spot_id) -- Ensures a user only has one preference per spot
);

-- Table creation for level_spot_preferences
CREATE TABLE level_spot_preferences (
    level_preference_id BIGSERIAL PRIMARY KEY,
    surf_level VARCHAR(50) NOT NULL,
    spot_id INTEGER NOT NULL REFERENCES spots(spot_id),
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    preferred_swell_direction VARCHAR(50),
    min_swell_period NUMERIC(5, 2),
    max_swell_period NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(50),
    max_wind_speed NUMERIC(5, 2),
    ideal_tide_type VARCHAR(20),
    additional_considerations TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (surf_level, spot_id)
);

CREATE INDEX idx_level_spot_preferences_level_spot_id ON level_spot_preferences (surf_level, spot_id);

-- Table creation for surf_ratings
CREATE TABLE surf_ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    spot_id INTEGER NOT NULL REFERENCES spots(spot_id),
    rating_date DATE NOT NULL,
    rating_time TIME,
    surf_quality INTEGER NOT NULL,
    comments TEXT,
    registration_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for surf_ratings
CREATE INDEX idx_surf_ratings_user_spot_date ON surf_ratings (user_id, spot_id, rating_date);

-- Table creation for rating_conditions_snapshot
CREATE TABLE rating_conditions_snapshot (
    snapshot_id BIGSERIAL PRIMARY KEY,
    rating_id INTEGER NOT NULL UNIQUE REFERENCES surf_ratings(rating_id),
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
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for rating_conditions_snapshot
CREATE INDEX idx_rating_conditions_snapshot_rating_id ON rating_conditions_snapshot (rating_id);
CREATE INDEX idx_rating_conditions_snapshot_ts ON rating_conditions_snapshot (timestamp_utc);
```

-----

This schema now incorporates all your latest improvements:

  * **`spots`** (instead of `praias`)
  * **`forecasts`** (instead of `previsoes_horarias`)
  * **`tides_forecast`** (instead of `mares`)
  * **`rating_conditions_snapshot`** for preserving historical rating context.
  * All column names are consistently in English.

This is a robust and well-structured database design for 'TheCheck'.

Would you like to move on to updating the Python scripts to reflect these new table and column names for insertion, or perhaps discuss the logic for populating the `rating_conditions_snapshot` table?