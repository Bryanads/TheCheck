-- Extensão para geração de UUIDs (se ainda não estiver habilitada)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Ou gen_random_uuid() para PostgreSQL 13+

CREATE TABLE IF NOT EXISTS spots (
    spot_id SERIAL PRIMARY KEY,
    spot_name VARCHAR(255) UNIQUE NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    timezone VARCHAR(64) NOT NULL -- IANA Time Zone (e.g., 'America/Sao_Paulo')
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
    CONSTRAINT fk_spot FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_forecast_spot_timestamp UNIQUE (spot_id, timestamp_utc)
);

CREATE TABLE IF NOT EXISTS tides_forecast (
    tide_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    tide_type VARCHAR(10) NOT NULL, -- 'high' or 'low'
    height NUMERIC(5, 2) NOT NULL,
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
    last_login_timestamp TIMESTAMP WITH TIME ZONE
);

-- Tabela: user_spot_preferences (Removido: created_at, updated_at, is_deleted)
CREATE TABLE user_spot_preferences (
    user_preference_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    spot_id INTEGER NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    min_wave_period NUMERIC(5, 2),
    max_wave_period NUMERIC(5, 2),
    ideal_wave_period NUMERIC(5, 2),
    min_swell_height NUMERIC(5, 2),
    max_swell_height NUMERIC(5, 2),
    ideal_swell_height NUMERIC(5, 2),
    min_swell_period NUMERIC(5, 2),
    max_swell_period NUMERIC(5, 2),
    ideal_swell_period NUMERIC(5, 2),
    preferred_wave_direction VARCHAR(20),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    ideal_water_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    CONSTRAINT fk_user_pref FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_spot_pref FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_user_spot_pref UNIQUE (user_id, spot_id)
);

-- Tabela: model_spot_preferences (Removido: created_at, updated_at, is_deleted; Adicionado: ideal_current_speed)
CREATE TABLE model_spot_preferences (
    model_preference_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL, -- Adicionado: Referência ao usuário que definiu este modelo
    spot_id INTEGER NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    min_wave_period NUMERIC(5, 2),
    max_wave_period NUMERIC(5, 2),
    ideal_wave_period NUMERIC(5, 2),
    min_swell_height NUMERIC(5, 2),
    max_swell_height NUMERIC(5, 2),
    ideal_swell_height NUMERIC(5, 2),
    min_swell_period NUMERIC(5, 2),
    max_swell_period NUMERIC(5, 2),
    ideal_swell_period NUMERIC(5, 2),
    preferred_wave_direction VARCHAR(20),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    ideal_water_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    ideal_current_speed NUMERIC(5, 2), -- Adicionado para o score de corrente
    CONSTRAINT fk_spot_model_pref_spot FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT fk_spot_model_pref_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT uq_model_spot_pref UNIQUE (user_id, spot_id)
);

-- Tabela: level_spot_preferences (Removido: created_at, updated_at, is_deleted)
CREATE TABLE level_spot_preferences (
    level_preference_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL,
    surf_level VARCHAR(50) NOT NULL,
    min_wave_height NUMERIC(5, 2),
    max_wave_height NUMERIC(5, 2),
    ideal_wave_height NUMERIC(5, 2),
    min_wave_period NUMERIC(5, 2),
    max_wave_period NUMERIC(5, 2),
    ideal_wave_period NUMERIC(5, 2),
    min_swell_height NUMERIC(5, 2),
    max_swell_height NUMERIC(5, 2),
    ideal_swell_height NUMERIC(5, 2),
    min_swell_period NUMERIC(5, 2),
    max_swell_period NUMERIC(5, 2),
    ideal_swell_period NUMERIC(5, 2),
    preferred_wave_direction VARCHAR(20),
    preferred_swell_direction VARCHAR(20),
    ideal_tide_type VARCHAR(10),
    min_sea_level NUMERIC(5, 2),
    max_sea_level NUMERIC(5, 2),
    ideal_sea_level NUMERIC(5, 2),
    min_wind_speed NUMERIC(5, 2),
    max_wind_speed NUMERIC(5, 2),
    ideal_wind_speed NUMERIC(5, 2),
    preferred_wind_direction VARCHAR(20),
    ideal_water_temperature NUMERIC(5, 2),
    ideal_air_temperature NUMERIC(5, 2),
    CONSTRAINT fk_spot_level_pref FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    CONSTRAINT uq_level_spot_pref UNIQUE (spot_id, surf_level)
);

-- Nova Tabela: user_recommendation_presets (Removido: created_at, last_used_at; updated_at é gerenciado na lógica do update)
CREATE TABLE public.user_recommendation_presets (
    preset_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users (user_id) ON DELETE CASCADE,
    preset_name VARCHAR(255) NOT NULL,
    spot_ids INTEGER[] NOT NULL, -- Array de IDs de spots
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    day_offset_default INTEGER[] DEFAULT '{}', -- Alterado para array de inteiros
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT unique_default_preset_per_user UNIQUE (user_id, is_default)
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
    CONSTRAINT fk_rating_snapshot FOREIGN KEY (rating_id) REFERENCES surf_ratings(rating_id)
);