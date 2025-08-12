# 📄 Documentação do Endpoint de Forecasts

## Endpoint

```
POST http://127.0.0.1:5000/forecasts
```

---

## Request Body

```json
{
	"spot_ids": ["int"],
	"day_offset": ["int"]
}
```

---

## Response Body

```json
[
	{
		"spot_id": "int",
		"spot_name": "string",
		"latitude": "float",
		"longitude": "float",
		"timezone": "string",
		"tide_phase": "string",
		"timestamp_utc": "string (ISO 8601 datetime)",
		"wave_height_sg": "float",
		"wave_direction_sg": "float",
		"wave_period_sg": "float",
		"swell_height_sg": "float",
		"swell_direction_sg": "float",
		"swell_period_sg": "float",
		"secondary_swell_height_sg": "float",
		"secondary_swell_direction_sg": "float",
		"secondary_swell_period_sg": "float",
		"wind_speed_sg": "float",
		"wind_direction_sg": "float",
		"water_temperature_sg": "float",
		"air_temperature_sg": "float",
		"current_speed_sg": "float",
		"current_direction_sg": "float",
		"sea_level_sg": "float"
	}
]
```

---

## Observações

- Os campos marcados como `string (ISO 8601 datetime)` seguem o padrão de data/hora ISO 8601.
- Arrays são indicados por colchetes, por exemplo: `["int"]` significa array de inteiros.
- Campos `null` indicam que o valor pode ser nulo.
# 📄 Documentação do Endpoint de Recomendação

## Endpoint

```
POST http://127.0.0.1:5000/recommendations
```

---

## Request Body

```json
{
	"user_id": "string (UUID)",
	"spot_ids": ["int"],
	"day_offset": ["int"],
	"start_time": "string (HH:MM)",
	"end_time": "string (HH:MM)"
}
```

---

## Response Body

```json
[
	{
		"spot_name": "string",
		"spot_id": "int",
		"preferences_used_for_spot": {
			"level_preference_id": "int",
			"spot_id": "int",
			"surf_level": "string",
			"min_wave_height": "float",
			"max_wave_height": "float",
			"ideal_wave_height": "float",
			"min_wave_period": "float",
			"max_wave_period": "float",
			"ideal_wave_period": "float",
			"min_swell_height": "float",
			"max_swell_height": "float",
			"ideal_swell_height": "float",
			"min_swell_period": "float",
			"max_swell_period": "float",
			"ideal_swell_period": "float",
			"preferred_wave_direction": "string",
			"preferred_swell_direction": "string",
			"ideal_tide_type": "string",
			"min_sea_level": "float",
			"max_sea_level": "float",
			"ideal_sea_level": "float",
			"min_wind_speed": "float",
			"max_wind_speed": "float",
			"ideal_wind_speed": "float",
			"preferred_wind_direction": "string",
			"ideal_water_temperature": "float",
			"ideal_air_temperature": "float",
			"created_at": "string (ISO 8601 datetime)",
			"updated_at": "string (ISO 8601 datetime)",
			"is_deleted": "boolean"
		},
		"day_offsets": [
			{
				"day_offset": "int",
				"recommendations": [
					{
						"timestamp_utc": "string (ISO 8601 datetime)",
						"suitability_score": "float",
						"detailed_scores": {
							"wave_height_score": "float",
							"swell_direction_score": "float",
							"swell_period_score": "float",
							"wind_score": "float",
							"tide_score": "float",
							"water_temperature_score": "float",
							"air_temperature_score": "float",
							"secondary_swell_impact": "float"
						},
						"forecast_conditions": {
							"wave_height_sg": "float",
							"wave_direction_sg": "float",
							"wave_period_sg": "float",
							"swell_height_sg": "float",
							"swell_direction_sg": "float",
							"swell_period_sg": "float",
							"secondary_swell_height_sg": "float",
							"secondary_swell_direction_sg": "float",
							"secondary_swell_period_sg": "float",
							"wind_speed_sg": "float",
							"wind_direction_sg": "float",
							"water_temperature_sg": "float",
							"air_temperature_sg": "float",
							"current_speed_sg": "float",
							"current_direction_sg": "float",
							"sea_level_sg": "float",
							"tide_phase": "string"
						},
						"spot_characteristics": {
							"bottom_type": "string|null",
							"coast_orientation": "string|null",
							"general_characteristics": "string|null"
						}
					}
				]
			}
		]
	}
]
```

---

## Observações

- Os campos marcados como `string (ISO 8601 datetime)` seguem o padrão de data/hora ISO 8601.
- Arrays são indicados por colchetes, por exemplo: `["int"]` significa array de inteiros.
- Campos `null` indicam que o valor pode ser nulo.
