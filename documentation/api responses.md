# Documentação das Respostas da API TheCheck

Este documento detalha os formatos de requisição e resposta para os endpoints da API TheCheck.

---

## 1. Autenticação e Usuários

### 1.1. `POST /register` (Registro de Usuário)

**Propósito:** Permite que um novo usuário crie uma conta no sistema.

**Requisição:**
`POST http://127.0.0.1:5000/register`
`Content-Type: application/json`

```json
{
    "name": "Maria Onda",
    "email": "maria.onda@example.com",
    "password": "umaSenhaSegura!",
    "surf_level": "beginner",
    "goofy_regular_stance": "goofy",
    "preferred_wave_direction": "south",
    "bio": "Adoro surfar ondas pequenas e aprender sempre mais.",
    "profile_picture_url": "[https://example.com/maria_onda.jpg](https://example.com/maria_onda.jpg)"
}
````

**Respostas de Sucesso:**

  * **`201 Created`**: Usuário registrado com sucesso.
    ```json
    {
        "message": "User registered successfully",
        "user_id": "301c40ed-d8ca-4e51-b1ad-0df5eb28b230"
    }
    ```

-----

### 1.2. `POST /login` (Login de Usuário)

**Propósito:** Autentica um usuário existente e retorna um token JWT.

**Requisição:**
`POST http://127.0.0.1:5000/login`
`Content-Type: application/json`

```json
{
    "email": "joao.surfista@example.com",
    "password": "umaSenhaSegura123!"
}
```

**Respostas de Sucesso:**

  * **`200 OK`**: Login bem-sucedido.
    ```json
    {
        "message": "Login successful",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMzAxYzQwZWQtZDhjYS00ZTUxLWIxYWQtMGRmNWViMjhiMjMwIiwiZW1haWwiOiJqb2FvLnN1cmZpc3RhQGV4YW1wbGUuY29tIiwiZXhwIjoxNjczMDc1NDY0fQ.some_jwt_signature_here",
        "user_id": "301c40ed-d8ca-4e51-b1ad-0df5eb28b230"
    }
    ```

-----

### 1.3. `/profile/<user_id>` (Gerenciamento de Perfil de Usuário)

**Propósito:** Permite obter ou atualizar os dados de perfil de um usuário específico.
*Nota: Em um ambiente de produção, esta rota deve ser protegida com autenticação JWT para garantir que apenas o usuário autenticado possa acessar/modificar seu próprio perfil.*

**Requisição GET:**
`GET http://127.0.0.1:5000/profile/<user_id>`

**Respostas de Sucesso (GET):**

  * **`200 OK`**: Dados do perfil retornados.
    ```json
    {
        "user_id": "301c40ed-d8ca-4e51-b1ad-0df5eb28b230",
        "name": "João Surfista",
        "email": "joao.surfista@example.com",
        "surf_level": "advanced",
        "goofy_regular_stance": "regular",
        "preferred_wave_direction": "northwest",
        "bio": "Experiente em ondas grandes e tubos.",
        "profile_picture_url": "[https://example.com/joao.jpg](https://example.com/joao.jpg)",
        "registration_timestamp": "2024-01-15T10:30:00.000000Z",
        "last_login_timestamp": "2025-08-04T14:00:00.000000Z"
    }
    ```

**Requisição PUT:**
`PUT http://127.0.0.1:5000/profile/<user_id>`
`Content-Type: application/json`

```json
{
    "surf_level": "expert",
    "bio": "Agora sou um surfista expert, focado em ondas perfeitas!"
    // Você pode enviar apenas os campos que deseja atualizar.
}
```

**Respostas de Sucesso (PUT):**

  * **`200 OK`**: Perfil atualizado com sucesso. Retorna os dados atualizados do usuário.
    ```json
    {
        "message": "Profile updated successfully",
        "user": {
            "user_id": "301c40ed-d8ca-4e51-b1ad-0df5eb28b230",
            "name": "João Surfista",
            "email": "joao.surfista@example.com",
            "surf_level": "expert",
            "goofy_regular_stance": "regular",
            "preferred_wave_direction": "northwest",
            "bio": "Agora sou um surfista expert, focado em ondas perfeitas!",
            "profile_picture_url": "[https://example.com/joao.jpg](https://example.com/joao.jpg)",
            "registration_timestamp": "2024-01-15T10:30:00.000000Z",
            "last_login_timestamp": "2025-08-04T14:05:00.000000Z"
        }
    }
    ```
-----

## 2\. Dados de Previsão

### 2.1. `POST /forecasts` (Previsão Combinada)

**Propósito:** Retorna dados de previsão de tempo, ondulação e maré combinados para os spots e dias especificados.

**Requisição:**
`POST http://127.0.0.1:5000/forecasts`
`Content-Type: application/json`

```json
{
    "spot_ids": [1, 2],
    "day_offset": [0, 1]
}
```

* **Resposta (Exemplo de Estrutura):**
    ```json
    [
        {
            "air_temperature_sg": "string",
            "current_direction_sg": "string",
            "current_speed_sg": "string",
            "latitude": "string",
            "longitude": "string",
            "sea_level_sg": "string",
            "secondary_swell_direction_sg": "string",
            "secondary_swell_height_sg": "string",
            "secondary_swell_period_sg": "string",
            "spot_id": "integer",
            "spot_name": "string",
            "swell_direction_sg": "string",
            "swell_height_sg": "string",
            "swell_period_sg": "string",
            "tide_phase": "string",
            "timestamp_utc": "string (GMT date format, e.g., 'Tue, 05 Aug 2025 08:00:00 GMT')",
            "timezone": "string (e.g., 'America/Sao_Paulo')",
            "water_temperature_sg": "string",
            "wave_direction_sg": "string",
            "wave_height_sg": "string",
            "wave_period_sg": "string",
            "wind_direction_sg": "string",
            "wind_speed_sg": "string",
            "local_time": "string (YYYY-MM-DD HH:mm:ss ZZ)",
            "date": "string (YYYY-MM-DD)"
        }
        // ... pode conter múltiplos objetos
    ]
    ```
-----

## 3\. Recomendações

### 3.1. `POST /recommendations` (Geração de Recomendações de Spots)

**Propósito:** Gera uma lista de recomendações de picos de surf com base nas preferências do usuário e nas condições de previsão para um determinado período.

**Requisição de Exemplo:**
`POST http://127.0.0.1:5000/recommendations`
`Content-Type: application/json`

```json
{
    "user_id": "301c40ed-d8ca-4e51-b1ad-0df5eb28b230",
    "spot_ids": [1, 2],
    "day_offset": 1,
    "start_time": "08:00",
    "end_time": "12:00"
}
```


* **Resposta (Exemplo de Estrutura):**
    ```json
    {
        "recommendations": [
            {
                "detailed_scores": {
                    "swell_direction_score": "integer",
                    "tide_score": "integer",
                    "wave_height_score": "integer",
                    "wind_score": "integer"
                },
                "forecast_conditions": {
                    "air_temperature_sg": "string",
                    "current_direction_sg": "string",
                    "current_speed_sg": "string",
                    "sea_level_sg": "string",
                    "secondary_swell_direction_sg": "string",
                    "secondary_swell_height_sg": "string",
                    "secondary_swell_period_sg": "string",
                    "swell_direction_sg": "string",
                    "swell_height_sg": "string",
                    "swell_period_sg": "string",
                    "water_temperature_sg": "string",
                    "wave_direction_sg": "string",
                    "wave_height_sg": "string",
                    "wave_period_sg": "string",
                    "wind_direction_sg": "string",
                    "wind_speed_sg": "string"
                },
                "local_time": "string (YYYY-MM-DD HH:mm:ss -ZZ)",
                "preferences_used": {
                    "additional_considerations": "string",
                    "created_at": "string (GMT date format)",
                    "ideal_air_temperature": "string",
                    "ideal_current_speed": "string",
                    "ideal_sea_level": "string",
                    "ideal_secondary_swell_height": "string | null",
                    "ideal_secondary_swell_period": "string | null",
                    "ideal_swell_height": "string",
                    "ideal_swell_period": "string",
                    "ideal_tide_type": "string",
                    "ideal_water_temperature": "string",
                    "ideal_wave_height": "string",
                    "ideal_wave_period": "string",
                    "ideal_wind_speed": "string",
                    "max_sea_level": "string",
                    "max_swell_height": "string",
                    "max_swell_period": "string",
                    "max_wave_height": "string",
                    "max_wave_period": "string",
                    "max_wind_speed": "string",
                    "min_sea_level": "string",
                    "min_swell_height": "string",
                    "min_swell_period": "string",
                    "min_wave_height": "string",
                    "min_wave_period": "string",
                    "min_wind_speed": "string",
                    "preference_id": "string (UUID)",
                    "preferred_current_direction": "string",
                    "preferred_secondary_swell_direction": "string | null",
                    "preferred_swell_direction": "string",
                    "preferred_wave_direction": "string | null",
                    "preferred_wind_direction": "string",
                    "spot_id": "integer",
                    "surf_level": "string",
                    "updated_at": "string (GMT date format)"
                },
                "spot_characteristics": {
                    "bottom_type": "string | null",
                    "coast_orientation": "string | null",
                    "general_characteristics": "object (JSONB) | null"
                },
                "spot_id": "integer",
                "spot_name": "string",
                "suitability_score": "float",
                "tide_info": {
                    "sea_level_sg": "string",
                    "tide_phase": "string"
                },
                "timestamp_utc": "string (ISO 8601 UTC timestamp)"
            }

            // ... pode conter múltiplos objetos
        ]
    }
    ```

-----

## 4\. Spots

### 4.1. `GET /spots` (Listagem de Spots)

**Propósito:** Retorna uma lista de todos os spots de surf disponíveis cadastrados no sistema.

**Requisição:**
`GET http://127.0.0.1:5000/spots`

**Respostas de Sucesso:**

  * **`200 OK`**: Lista de objetos de spots.
    ```json
    [
        {
            "latitude": "string",
            "longitude": "string",
            "spot_id": "integer",
            "spot_name": "string",
            "timezone": "string"
        }
    ]
    ```

<!-- end list -->

