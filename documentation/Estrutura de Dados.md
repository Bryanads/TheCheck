# Documento de Estrutura de Dados do 'TheCheck'

Este documento detalha o esquema do banco de dados relacional (SQL) para o sistema 'TheCheck', com uma explicação para cada tabela e seu propósito.

## 1\. Tabela `praias`

Armazena informações estáticas e geográficas sobre cada pico de surf.

| Nome da Coluna           | Tipo de Dados                 | Descrição                                                                      |
| :----------------------- | :---------------------------- | :----------------------------------------------------------------------------- |
| `id_praia`               | SERIAL PRIMARY KEY            | Identificador único e auto-incrementável da praia.                             |
| `nome_praia`             | VARCHAR(255) UNIQUE NOT NULL  | Nome comum e único da praia (ex: "Reserva", "Macumba").                        |
| `latitude`               | NUMERIC(10, 7) NOT NULL       | Latitude da localização da praia.                                              |
| `longitude`              | NUMERIC(10, 7) NOT NULL       | Longitude da localização da praia.                                             |
| `tipo_fundo`             | VARCHAR(50)                   | Tipo de fundo do mar na praia (ex: "Areia", "Coral", "Pedra", "Misto").        |
| `orientacao_costa`       | VARCHAR(10)                   | Orientação principal da costa da praia (ex: "SE", "NW", "S").                  |
| `descricao`              | TEXT                          | Uma breve descrição geral da praia.                                            |
| `caracteristicas_gerais` | JSONB                         | Características menos estruturadas ou dinâmicas (ex: "crowd", "onda", "melhor\_maré"). |

## 2\. Tabela `previsoes_horarias`

Armazena os dados brutos de previsão do tempo e ondulação da API StormGlass.io, com granularidade horária.

| Nome da Coluna                | Tipo de Dados                          | Descrição                                                                      |
| :---------------------------- | :------------------------------------- | :----------------------------------------------------------------------------- |
| `id_previsao_horaria`         | BIGSERIAL PRIMARY KEY                  | Identificador único e auto-incrementável para cada registro de previsão horária. |
| `id_praia`                    | INTEGER NOT NULL REFERENCES praias(id\_praia) | Chave estrangeira para a tabela `praias`, associando a previsão à praia.       |
| `timestamp_utc`               | TIMESTAMP WITH TIME ZONE NOT NULL      | O timestamp exato (em UTC) para o qual a previsão é válida. Crucial para séries temporais. |
| `wave_height_sg`              | NUMERIC(5, 2)                          | Altura da onda (fonte StormGlass).                                             |
| `wave_direction_sg`           | NUMERIC(6, 2)                          | Direção da onda (fonte StormGlass).                                            |
| `wave_period_sg`              | NUMERIC(5, 2)                          | Período da onda (fonte StormGlass).                                            |
| `swell_height_sg`             | NUMERIC(5, 2)                          | Altura do swell primário (fonte StormGlass).                                   |
| `swell_direction_sg`          | NUMERIC(6, 2)                          | Direção do swell primário (fonte StormGlass).                                  |
| `swell_period_sg`             | NUMERIC(5, 2)                          | Período do swell primário (fonte StormGlass).                                  |
| `secondary_swell_height_sg`   | NUMERIC(5, 2)                          | Altura do swell secundário (fonte StormGlass).                                 |
| `secondary_swell_direction_sg`| NUMERIC(6, 2)                          | Direção do swell secundário (fonte StormGlass).                                |
| `secondary_swell_period_sg`   | NUMERIC(5, 2)                          | Período do swell secundário (fonte StormGlass).                                |
| `wind_speed_sg`               | NUMERIC(5, 2)                          | Velocidade do vento (fonte StormGlass).                                        |
| `wind_direction_sg`           | NUMERIC(6, 2)                          | Direção do vento (fonte StormGlass).                                           |
| `water_temperature_sg`        | NUMERIC(5, 2)                          | Temperatura da água (fonte StormGlass).                                        |
| `air_temperature_sg`          | NUMERIC(5, 2)                          | Temperatura do ar (fonte StormGlass).                                          |
| `current_speed_sg`            | NUMERIC(5, 2)                          | Velocidade da corrente (fonte StormGlass).                                     |
| `current_direction_sg`        | NUMERIC(6, 2)                          | Direção da corrente (fonte StormGlass).                                        |
| `data_coleta`                 | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | O timestamp de quando esta previsão foi coletada e inserida no BD.             |

## 3\. Tabela `mares`

Armazena os eventos de maré (alta/baixa) para cada praia e data.

| Nome da Coluna    | Tipo de Dados                          | Descrição                                                                      |
| :---------------- | :------------------------------------- | :----------------------------------------------------------------------------- |
| `id_mare`         | BIGSERIAL PRIMARY KEY                  | Identificador único e auto-incrementável para cada evento de maré.             |
| `id_praia`        | INTEGER NOT NULL REFERENCES praias(id\_praia) | Chave estrangeira para a tabela `praias`, associando o evento de maré à praia. |
| `timestamp_utc`   | TIMESTAMP WITH TIME ZONE NOT NULL      | O timestamp exato (em UTC) do evento de maré (ex: pico de maré alta/baixa).    |
| `tipo`            | VARCHAR(10) NOT NULL                   | Tipo de evento de maré (ex: "high", "low").                                    |
| `altura`          | NUMERIC(5, 3) NOT NULL                 | Altura da maré naquele ponto.                                                  |
| `data_coleta`     | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | O timestamp de quando esta informação de maré foi coletada e inserida no BD.   |

## 4\. Tabela `usuarios`

Armazena as informações de perfil dos usuários, incluindo suas preferências globais.

| Nome da Coluna           | Tipo de Dados                        | Descrição                                                                      |
| :----------------------- | :----------------------------------- | :----------------------------------------------------------------------------- |
| `id_usuario`             | SERIAL PRIMARY KEY                   | Identificador único e auto-incrementável do usuário.                           |
| `nome`                   | VARCHAR(255) NOT NULL                | Nome do usuário.                                                               |
| `email`                  | VARCHAR(255) UNIQUE NOT NULL         | Endereço de e-mail único do usuário (usado para login/identificação).          |
| `nivel_surf`             | VARCHAR(50)                          | Nível de habilidade do surfista (ex: "Iniciante", "Intermediário", "Avançado").|
| `regiao_preferida`       | VARCHAR(255)                         | Região geográfica preferida do surfista (para filtrar praias inicialmente).    |
| `goofy_regular`          | VARCHAR(10)                          | Posição preferida do surfista na prancha (ex: 'Goofy', 'Regular', 'Ambidestro'). |
| `direcao_onda_preferida` | VARCHAR(20)                          | Direção de onda que o surfista prefere surfar (ex: 'Direita', 'Esquerda', 'Ambas'). |
| `data_cadastro`          | TIMESTAMP WITH TIME ZONE DEFAULT NOW() | O timestamp de quando o usuário se cadastrou no sistema.                       |

## 5\. Tabela `preferencias_usuario_praia`

Armazena as preferências detalhadas de cada usuário para condições de surf **específicas de cada praia**.

| Nome da Coluna             | Tipo de Dados                                | Descrição                                                                      |
| :------------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `id_preferencia`           | SERIAL PRIMARY KEY                           | Identificador único para cada registro de preferência.                         |
| `id_usuario`               | INTEGER NOT NULL REFERENCES usuarios(id\_usuario) | Chave estrangeira para a tabela `usuarios`.                                    |
| `id_praia`                 | INTEGER NOT NULL REFERENCES praias(id\_praia)       | Chave estrangeira para a tabela `praias`.                                      |
| `altura_onda_min`          | NUMERIC(5, 2)                                | Altura mínima de onda preferida para esta praia.                               |
| `altura_onda_max`          | NUMERIC(5, 2)                                | Altura máxima de onda preferida para esta praia.                               |
| `direcao_swell_preferida`  | VARCHAR(50)                                  | Direção(ões) de swell preferida(s) para esta praia (pode ser uma lista de valores, ou campo flexível). |
| `periodo_swell_min`        | NUMERIC(5, 2)                                | Período mínimo de swell preferido para esta praia.                             |
| `periodo_swell_max`        | NUMERIC(5, 2)                                | Período máximo de swell preferido para esta praia.                             |
| `vento_direcao_preferida`  | VARCHAR(50)                                  | Direção(ões) de vento preferida(s) para esta praia (ex: 'N', 'NE', 'Offshore'). |
| `vento_velocidade_max`     | NUMERIC(5, 2)                                | Velocidade máxima de vento tolerada para esta praia.                           |
| `crowd_tolerancia`         | VARCHAR(20)                                  | Nível de tolerância a multidão para esta praia ('Baixa', 'Média', 'Alta').      |
| `consideracoes_adicionais` | TEXT                                         | Notas ou observações adicionais do usuário sobre as preferências desta praia.  |
| `ultima_atualizacao`       | TIMESTAMP WITH TIME ZONE DEFAULT NOW()       | O timestamp da última atualização desta preferência.                           |

---

## 6\. Tabela `preferencias_nivel_praia`

Esta tabela armazenará os presets de "condições ideais" para cada nível de surf em cada praia, preenchidos manualmente ou através de dados agregados iniciais.

| Nome da Coluna             | Tipo de Dados                                | Descrição                                                                      |
| :------------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `id_preferencia_nivel`     | SERIAL PRIMARY KEY                           | Identificador único para cada registro de preferência por nível.               |
| `nivel_surf`               | VARCHAR(50) NOT NULL                         | O nível de surf para o qual esta preferência é definida (ex: "Iniciante", "Intermediário"). |
| `id_praia`                 | INTEGER NOT NULL REFERENCES praias(id_praia) | Chave estrangeira para a tabela `praias`.                                      |
| `altura_onda_min`          | NUMERIC(5, 2)                                | Altura mínima de onda preferida para este nível nesta praia.                   |
| `altura_onda_max`          | NUMERIC(5, 2)                                | Altura máxima de onda preferida para este nível nesta praia.                   |
| `direcao_swell_preferida`  | VARCHAR(50)                                  | Direção(ões) de swell preferida(s) para este nível nesta praia.                |
| `periodo_swell_min`        | NUMERIC(5, 2)                                | Período mínimo de swell preferido para este nível nesta praia.                 |
| `periodo_swell_max`        | NUMERIC(5, 2)                                | Período máximo de swell preferido para este nível nesta praia.                 |
| `vento_direcao_preferida`  | VARCHAR(50)                                  | Direção(ões) de vento preferida(s) para este nível nesta praia.                |
| `vento_velocidade_max`     | NUMERIC(5, 2)                                | Velocidade máxima de vento tolerada para este nível nesta praia.               |
| `mare_ideal_tipo`          | VARCHAR(20)                                  | Tipo de maré ideal (ex: 'high', 'low', 'mid', 'rising', 'falling').           |
| `consideracoes_adicionais` | TEXT                                         | Notas ou observações adicionais sobre as preferências deste nível nesta praia. |
| `ultima_atualizacao`       | TIMESTAMP WITH TIME ZONE DEFAULT NOW()       | O timestamp da última atualização desta preferência.                           |
| **Índice Único** | `UNIQUE (nivel_surf, id_praia)`              | Garante que só haja um conjunto de preferências por nível por praia.           |

---


## 7\. Tabela `avaliacoes_surf`

Armazena o feedback dos usuários sobre a qualidade do surf em um determinado dia/hora para uma praia específica, crucial para o treinamento do modelo de recomendação.

| Nome da Coluna       | Tipo de Dados                                | Descrição                                                                      |
| :------------------- | :------------------------------------------- | :----------------------------------------------------------------------------- |
| `id_avaliacao`       | SERIAL PRIMARY KEY                           | Identificador único e auto-incrementável da avaliação.                         |
| `id_usuario`         | INTEGER NOT NULL REFERENCES usuarios(id\_usuario) | Chave estrangeira para a tabela `usuarios`.                                    |
| `id_praia`           | INTEGER NOT NULL REFERENCES praias(id\_praia)       | Chave estrangeira para a tabela `praias`.                                      |
| `data_avaliacao`     | DATE NOT NULL                                | A data em que o surf foi avaliado.                                             |
| `hora_avaliacao`     | TIME                                         | A hora aproximada em que o surf ocorreu (se o usuário puder especificar).      |
| `qualidade_surf`     | INTEGER NOT NULL                             | Nota numérica (ex: 1 a 5 ou 1 a 10) para a qualidade do surf na sessão avaliada. |
| `comentarios`        | TEXT                                         | Comentários adicionais do usuário sobre a sessão de surf avaliada.             |
| `timestamp_registro` | TIMESTAMP WITH TIME ZONE DEFAULT NOW()       | O timestamp de quando a avaliação foi registrada no sistema.                   |

## SQL Schema (PostgreSQL)

```
sql
-- Criação da Tabela praias
CREATE TABLE praias (
    id_praia SERIAL PRIMARY KEY,
    nome_praia VARCHAR(255) UNIQUE NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    tipo_fundo VARCHAR(50),
    orientacao_costa VARCHAR(10),
    descricao TEXT,
    caracteristicas_gerais JSONB
);

-- Criação da Tabela previsoes_horarias
CREATE TABLE previsoes_horarias (
    id_previsao_horaria BIGSERIAL PRIMARY KEY,
    id_praia INTEGER NOT NULL REFERENCES praias(id_praia),
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
    data_coleta TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (id_praia, timestamp_utc) -- Garante que não haja previsões duplicadas para a mesma praia no mesmo timestamp
);

-- Índices para previsoes_horarias
CREATE INDEX idx_previsoes_horarias_praia_ts ON previsoes_horarias (id_praia, timestamp_utc DESC);
CREATE INDEX idx_previsoes_horarias_ts ON previsoes_horarias (timestamp_utc DESC);


-- Criação da Tabela mares
CREATE TABLE mares (
    id_mare BIGSERIAL PRIMARY KEY,
    id_praia INTEGER NOT NULL REFERENCES praias(id_praia),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    altura NUMERIC(5, 3) NOT NULL,
    data_coleta TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (id_praia, timestamp_utc) -- Garante que não haja eventos de maré duplicados para a mesma praia no mesmo timestamp
);

-- Índice para mares
CREATE INDEX idx_mares_praia_ts ON mares (id_praia, timestamp_utc);

-- Criação da Tabela usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    nivel_surf VARCHAR(50),
    regiao_preferida VARCHAR(255),
    goofy_regular VARCHAR(10),
    direcao_onda_preferida VARCHAR(20),
    data_cadastro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criação da Tabela preferencias_usuario_praia
CREATE TABLE preferencias_usuario_praia (
    id_preferencia SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_praia INTEGER NOT NULL REFERENCES praias(id_praia),
    altura_onda_min NUMERIC(5, 2),
    altura_onda_max NUMERIC(5, 2),
    direcao_swell_preferida VARCHAR(50), -- Pode ser um campo JSONB ou array de strings se múltiplos valores
    periodo_swell_min NUMERIC(5, 2),
    periodo_swell_max NUMERIC(5, 2),
    vento_direcao_preferida VARCHAR(50), -- Pode ser um campo JSONB ou array de strings
    vento_velocidade_max NUMERIC(5, 2),
    crowd_tolerancia VARCHAR(20),
    consideracoes_adicionais TEXT,
    ultima_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (id_usuario, id_praia) -- Garante que um usuário só tenha uma preferência por praia
);

-- Criação da Tabela preferencias_nivel_praia
CREATE TABLE preferencias_nivel_praia (
    id_preferencia_nivel BIGSERIAL PRIMARY KEY,
    nivel_surf VARCHAR(50) NOT NULL,
    id_praia INTEGER NOT NULL REFERENCES praias(id_praia),
    altura_onda_min NUMERIC(5, 2),
    altura_onda_max NUMERIC(5, 2),
    direcao_swell_preferida VARCHAR(50),
    periodo_swell_min NUMERIC(5, 2),
    periodo_swell_max NUMERIC(5, 2),
    vento_direcao_preferida VARCHAR(50),
    vento_velocidade_max NUMERIC(5, 2),
    mare_ideal_tipo VARCHAR(20),
    consideracoes_adicionais TEXT,
    ultima_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (nivel_surf, id_praia)
);

CREATE INDEX idx_preferencias_nivel_praia_nivel_id_praia ON preferencias_nivel_praia (nivel_surf, id_praia);

-- Criação da Tabela avaliacoes_surf
CREATE TABLE avaliacoes_surf (
    id_avaliacao SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_praia INTEGER NOT NULL REFERENCES praias(id_praia),
    data_avaliacao DATE NOT NULL,
    hora_avaliacao TIME,
    qualidade_surf INTEGER NOT NULL,
    comentarios TEXT,
    timestamp_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para avaliacoes_surf
CREATE INDEX idx_avaliacoes_usuario_praia_data ON avaliacoes_surf (id_usuario, id_praia, data_avaliacao);
```

-----
