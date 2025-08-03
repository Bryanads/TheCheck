# Documentação das Respostas da API

Este documento organiza os dados retornados pela API em seções para facilitar a visualização.

## Dados de Previsão
Nesta seção, encontram-se os dados de previsão coletados em diferentes horários.

```json
[
    {
        "air_temperature_sg": "17.10",
        "current_direction_sg": "92.60",
        "current_speed_sg": "0.01",
        "date": "2025-08-04",
        "local_time": "2025-08-04 08:00:00 +00:00",
        "sea_level_sg": "-0.25",
        "secondary_swell_direction_sg": "155.87",
        "secondary_swell_height_sg": "0.34",
        "secondary_swell_period_sg": "9.45",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "swell_direction_sg": "111.95",
        "swell_height_sg": "0.69",
        "swell_period_sg": "7.13",
        "tide_phase": "falling",
        "timestamp_utc": "Mon, 04 Aug 2025 08:00:00 GMT",
        "timezone": "UTC",
        "water_temperature_sg": "21.17",
        "wave_direction_sg": "116.55",
        "wave_height_sg": "0.60",
        "wave_period_sg": "4.31",
        "wind_direction_sg": "1.43",
        "wind_speed_sg": "2.05"
    },
    {
        "air_temperature_sg": "16.86",
        "current_direction_sg": "94.44",
        "current_speed_sg": "0.01",
        "date": "2025-08-04",
        "local_time": "2025-08-04 09:00:00 +00:00",
        "sea_level_sg": "-0.26",
        "secondary_swell_direction_sg": "156.20",
        "secondary_swell_height_sg": "0.34",
        "secondary_swell_period_sg": "9.50",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "swell_direction_sg": "111.80",
        "swell_height_sg": "0.65",
        "swell_period_sg": "7.08",
        "tide_phase": "rising",
        "timestamp_utc": "Mon, 04 Aug 2025 09:00:00 GMT",
        "timezone": "UTC",
        "water_temperature_sg": "21.16",
        "wave_direction_sg": "116.65",
        "wave_height_sg": "0.58",
        "wave_period_sg": "4.40",
        "wind_direction_sg": "5.62",
        "wind_speed_sg": "2.07"
    }
]
```

## Recomendações
Esta seção apresenta sugestões com base na pontuação de adequação, de forma que se possa identificar os melhores horários e condições.

```json
{
    "recommendations": [
        {
            "air_temperature_sg": "22.99",
            "current_direction_sg": "266.70",
            "current_speed_sg": "0.00",
            "local_time": "2025-08-04 16:00:00 UTC",
            "sea_level_sg": "0.21",
            "secondary_swell_direction_sg": "155.34",
            "secondary_swell_height_sg": "0.25",
            "secondary_swell_period_sg": "9.47",
            "spot_id": 1,
            "spot_name": "Barra Posto 4",
            "suitability_score": 765.0,
            "swell_direction_sg": "113.48",
            "swell_height_sg": "0.56",
            "swell_period_sg": "7.07",
            "tide_phase": "rising",
            "timestamp_utc": "2025-08-04T16:00:00+00:00",
            "water_temperature_sg": "21.77",
            "wave_direction_sg": "116.77",
            "wave_height_sg": "0.50",
            "wave_period_sg": "4.97",
            "wind_direction_sg": "15.10",
            "wind_speed_sg": "2.93"
        },
        {
            "air_temperature_sg": "16.83",
            "current_direction_sg": "99.76",
            "current_speed_sg": "0.01",
            "local_time": "2025-08-04 10:00:00 UTC",
            "sea_level_sg": "-0.22",
            "secondary_swell_direction_sg": "155.78",
            "secondary_swell_height_sg": "0.32",
            "secondary_swell_period_sg": "9.44",
            "spot_id": 1,
            "spot_name": "Barra Posto 4",
            "suitability_score": 715.0,
            "swell_direction_sg": "111.71",
            "swell_height_sg": "0.64",
            "swell_period_sg": "7.07",
            "tide_phase": "rising",
            "timestamp_utc": "2025-08-04T10:00:00+00:00",
            "water_temperature_sg": "21.16",
            "wave_direction_sg": "116.75",
            "wave_height_sg": "0.56",
            "wave_period_sg": "4.48",
            "wind_direction_sg": "1.82",
            "wind_speed_sg": "2.16"
        }
    ]
}
```

## Informações dos Spots
Lista com dados dos spots disponíveis, incluindo localização e fuso horário.

```json
[
    {
        "latitude": "-23.0040000",
        "longitude": "-43.3760000",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "timezone": "UTC"
    },
    {
        "latitude": "-23.0075000",
        "longitude": "-43.3700000",
        "spot_id": 2,
        "spot_name": "Barra Posto 8",
        "timezone": "UTC"
    }
]
```
[
    {
        "air_temperature_sg": "17.10",
        "current_direction_sg": "92.60",
        "current_speed_sg": "0.01",
        "date": "2025-08-04",
        "local_time": "2025-08-04 08:00:00 +00:00",
        "sea_level_sg": "-0.25",
        "secondary_swell_direction_sg": "155.87",
        "secondary_swell_height_sg": "0.34",
        "secondary_swell_period_sg": "9.45",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "swell_direction_sg": "111.95",
        "swell_height_sg": "0.69",
        "swell_period_sg": "7.13",
        "tide_phase": "falling",
        "timestamp_utc": "Mon, 04 Aug 2025 08:00:00 GMT",
        "timezone": "UTC",
        "water_temperature_sg": "21.17",
        "wave_direction_sg": "116.55",
        "wave_height_sg": "0.60",
        "wave_period_sg": "4.31",
        "wind_direction_sg": "1.43",
        "wind_speed_sg": "2.05"
    },
    {
        "air_temperature_sg": "16.86",
        "current_direction_sg": "94.44",
        "current_speed_sg": "0.01",
        "date": "2025-08-04",
        "local_time": "2025-08-04 09:00:00 +00:00",
        "sea_level_sg": "-0.26",
        "secondary_swell_direction_sg": "156.20",
        "secondary_swell_height_sg": "0.34",
        "secondary_swell_period_sg": "9.50",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "swell_direction_sg": "111.80",
        "swell_height_sg": "0.65",
        "swell_period_sg": "7.08",
        "tide_phase": "rising",
        "timestamp_utc": "Mon, 04 Aug 2025 09:00:00 GMT",
        "timezone": "UTC",
        "water_temperature_sg": "21.16",
        "wave_direction_sg": "116.65",
        "wave_height_sg": "0.58",
        "wave_period_sg": "4.40",
        "wind_direction_sg": "5.62",
        "wind_speed_sg": "2.07"
    }
]

{
    "recommendations": [
        {
            "air_temperature_sg": "22.99",
            "current_direction_sg": "266.70",
            "current_speed_sg": "0.00",
            "local_time": "2025-08-04 16:00:00 UTC",
            "sea_level_sg": "0.21",
            "secondary_swell_direction_sg": "155.34",
            "secondary_swell_height_sg": "0.25",
            "secondary_swell_period_sg": "9.47",
            "spot_id": 1,
            "spot_name": "Barra Posto 4",
            "suitability_score": 765.0,
            "swell_direction_sg": "113.48",
            "swell_height_sg": "0.56",
            "swell_period_sg": "7.07",
            "tide_phase": "rising",
            "timestamp_utc": "2025-08-04T16:00:00+00:00",
            "water_temperature_sg": "21.77",
            "wave_direction_sg": "116.77",
            "wave_height_sg": "0.50",
            "wave_period_sg": "4.97",
            "wind_direction_sg": "15.10",
            "wind_speed_sg": "2.93"
        },
        {
            "air_temperature_sg": "16.83",
            "current_direction_sg": "99.76",
            "current_speed_sg": "0.01",
            "local_time": "2025-08-04 10:00:00 UTC",
            "sea_level_sg": "-0.22",
            "secondary_swell_direction_sg": "155.78",
            "secondary_swell_height_sg": "0.32",
            "secondary_swell_period_sg": "9.44",
            "spot_id": 1,
            "spot_name": "Barra Posto 4",
            "suitability_score": 715.0,
            "swell_direction_sg": "111.71",
            "swell_height_sg": "0.64",
            "swell_period_sg": "7.07",
            "tide_phase": "rising",
            "timestamp_utc": "2025-08-04T10:00:00+00:00",
            "water_temperature_sg": "21.16",
            "wave_direction_sg": "116.75",
            "wave_height_sg": "0.56",
            "wave_period_sg": "4.48",
            "wind_direction_sg": "1.82",
            "wind_speed_sg": "2.16"
        }
    ]
} 


[
    {
        "latitude": "-23.0040000",
        "longitude": "-43.3760000",
        "spot_id": 1,
        "spot_name": "Barra Posto 4",
        "timezone": "UTC"
    },
    {
        "latitude": "-23.0075000",
        "longitude": "-43.3700000",
        "spot_id": 2,
        "spot_name": "Barra Posto 8",
        "timezone": "UTC"
    }
]