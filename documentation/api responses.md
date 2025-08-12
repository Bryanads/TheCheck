# 📄 Documentação do Endpoint de Spots

## Endpoint Base

```
/spots
```

---

## Listar Todos os Spots

**GET** `/spots`

### Response

```json
[
	{
		"spot_id": "int",
		"spot_name": "string",
		"latitude": "float",
		"longitude": "float",
		"city": "string",
		"state": "string",
		"country": "string"
		// ... outros campos que possam existir no retorno do banco
	}
]
```

- Caso não haja spots cadastrados, retorna:
```json
{
	"message": "Nenhum spot encontrado."
}
```

- Em caso de erro interno:
```json
{
	"error": "Erro ao buscar spots: <mensagem de erro>"
}
```

---

### Observações

- O endpoint retorna uma lista de todos os spots disponíveis no sistema.
- Os campos retornados podem variar conforme o banco de dados, mas normalmente incluem informações como nome, localização e identificador do spot.
# 📄 Documentação do Endpoint de Usuários

## Endpoint Base

```
/users
```

---

## Registrar Usuário

**POST** `/users/register`

### Request Body

```json
{
	"name": "string",
	"email": "string",
	"password": "string",
	"surf_level": "string", // opcional
	"goofy_regular_stance": "string", // opcional
	"preferred_wave_direction": "string", // opcional
	"bio": "string", // opcional
	"profile_picture_url": "string" // opcional
}
```

### Response

```json
{
	"message": "User registered successfully",
	"user_id": "string (UUID)"
}
```

---

## Login

**POST** `/users/login`

### Request Body

```json
{
	"email": "string",
	"password": "string"
}
```

### Response

```json
{
	"message": "Login successful",
	"token": "string (JWT)",
	"user_id": "string (UUID)"
}
```

---

## Buscar Perfil do Usuário

**GET** `/users/profile/{user_id}`

### Response

```json
{
	"user_id": "string (UUID)",
	"name": "string",
	"email": "string",
	"surf_level": "string",
	"goofy_regular_stance": "string",
	"preferred_wave_direction": "string",
	"bio": "string",
	"profile_picture_url": "string",
	"created_at": "string (ISO 8601 datetime)",
	"updated_at": "string (ISO 8601 datetime)"
}
```

---

## Atualizar Perfil do Usuário

**PUT** `/users/profile/{user_id}`

### Request Body

```json
{
	"name": "string", // opcional
	"surf_level": "string", // opcional
	"goofy_regular_stance": "string", // opcional
	"preferred_wave_direction": "string", // opcional
	"bio": "string", // opcional
	"profile_picture_url": "string" // opcional
}
```

### Response

```json
{
	"message": "Profile updated successfully",
	"user": {
		"user_id": "string (UUID)",
		"name": "string",
		"email": "string",
		"surf_level": "string",
		"goofy_regular_stance": "string",
		"preferred_wave_direction": "string",
		"bio": "string",
		"profile_picture_url": "string",
		"created_at": "string (ISO 8601 datetime)",
		"updated_at": "string (ISO 8601 datetime)"
	}
}
```

---

### Observações

- Todos os endpoints retornam erro 400 ou 404 em caso de dados inválidos ou usuário não encontrado.
- O campo `token` retornado no login é um JWT válido por 24 horas.
- O campo `password_hash` nunca é retornado nas respostas.
# 📄 Documentação do Endpoint de Presets

## Endpoint Base

```
/presets
```

---

## Criar Preset

**POST** `/presets`

### Request Body

```json
{
	"user_id": "string (UUID)",
	"preset_name": "string",
	"spot_ids": ["int"],
	"start_time": "string (HH:MM)",
	"end_time": "string (HH:MM)",
	"day_offset_default": ["int"], // opcional
	"is_default": "boolean" // opcional
}
```

### Response

```json
{
	"message": "Preset criado com sucesso!",
	"preset_id": "int"
}
```

---

## Listar Presets do Usuário

**GET** `/presets?user_id=string`

### Response

```json
[
	{
		"preset_id": "int",
		"user_id": "string",
		"preset_name": "string",
		"spot_ids": ["int"],
		"start_time": "string (HH:MM:SS)",
		"end_time": "string (HH:MM:SS)",
		"day_offset_default": ["int"],
		"is_default": "boolean",
		"is_active": "boolean"
	}
]
```

---

## Buscar Preset por ID

**GET** `/presets/{preset_id}?user_id=string`

### Response

```json
{
	"preset_id": "int",
	"user_id": "string",
	"preset_name": "string",
	"spot_ids": ["int"],
	"start_time": "string (HH:MM:SS)",
	"end_time": "string (HH:MM:SS)",
	"day_offset_default": ["int"],
	"is_default": "boolean",
	"is_active": "boolean"
}
```

---

## Atualizar Preset

**PUT** `/presets/{preset_id}`

### Request Body

```json
{
	"user_id": "string (UUID)",
	"preset_name": "string", // opcional
	"spot_ids": ["int"], // opcional
	"start_time": "string (HH:MM)", // opcional
	"end_time": "string (HH:MM)", // opcional
	"day_offset_default": ["int"], // opcional
	"is_default": "boolean", // opcional
	"is_active": "boolean" // opcional
}
```

### Response

```json
{
	"message": "Preset atualizado com sucesso!"
}
```

---

## Deletar (Desativar) Preset

**DELETE** `/presets/{preset_id}?user_id=string`

### Response

```json
{
	"message": "Preset desativado (excluído logicamente) com sucesso!"
}
```

---

## Buscar Preset Padrão

**GET** `/presets/default?user_id=string`

### Response

```json
{
	"preset_id": "int",
	"user_id": "string",
	"preset_name": "string",
	"spot_ids": ["int"],
	"start_time": "string (HH:MM:SS)",
	"end_time": "string (HH:MM:SS)",
	"day_offset_default": ["int"],
	"is_default": "boolean",
	"is_active": "boolean"
}
```

---

### Observações

- Todos os endpoints retornam erro 404 caso o usuário não seja encontrado.
- Os campos de horário seguem o padrão `HH:MM:SS`.
- O campo `day_offset_default` é opcional e pode ser omitido.
- O campo `is_active` indica se o preset está ativo ou foi desativado logicamente.
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
