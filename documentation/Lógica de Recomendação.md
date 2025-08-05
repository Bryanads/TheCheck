
# Lógica de Recomendação - Sistema 'TheCheck'

Este documento detalha as decisões e a lógica para o modelo de recomendação de picos de surf do sistema 'TheCheck', com foco na pontuação das condições do mar para o surf.

---

## Abordagem de Pontuação Refatorada

**Objetivo:** Simplificar e flexibilizar a calibração do modelo, movendo de múltiplos pesos e penalidades globais para uma abordagem paramétrica intrínseca às funções de pontuação.

**Princípios:**
* **Remoção de Pesos Globais (`WEIGHT_MAJOR`, `WEIGHT_MINOR`, `WEIGHT_TERTIARY`):** A importância de um parâmetro será definida pela sua curva de pontuação, ou seja, quão drasticamente a pontuação cai/sobe com o desvio do ideal/aceitável.
* **Consolidação de Bônus/Penalidades:** As funções auxiliares de pontuação (`score_proximity_to_range_ideal`, `score_proximity_to_single_ideal`, e futuras funções específicas) retornarão diretamente o valor de pontuação ponderado (positivo para bônus, negativo para penalidade).

**Funções de Pontuação:**
* **`score_proximity_to_range_ideal(current_value, min_val, max_val, ideal_val, param_type)`:** Utilizada para parâmetros com faixa aceitável (`min`, `max`) e um `ideal`. A pontuação variará de forma mais suave, com penalidades acentuadas fora da faixa. O `param_type` será usado para aplicar curvas de sensibilidade específicas.
* **`score_proximity_to_single_ideal(current_value, ideal_val)`:** Para parâmetros onde apenas um valor ideal é relevante.

---

## 1. Parâmetros de Onda (Wave)

### 1.1. `wave_height` (Altura da Onda)

* **Definição:** Uma das partes principais do surf, com margem de erro relativamente grande dentro dos limites aceitáveis, mas penalidade drástica fora dos mesmos.
* **Impacto no Score:** Pontuação de impacto "muito alta".
* **Curva de Sensibilidade:** "Média".
* **Proposta de Lógica (`score_proximity_to_range_ideal` para `wave_height`):**
    * **Ideal (`ideal_wh`):** Se `current_value` estiver `+/- 5-10%` do `ideal_wh`, bônus máximo (`+20` a `+25`).
    * **Próximo do Ideal / Dentro da Faixa Média:** Se `current_value` estiver entre `ideal_wh +/- 20%` OU na metade da faixa `min_wh` e `max_wh`, bônus bom (`+10` a `+15`).
    * **Dentro da Faixa Aceitável (Extremos Min/Max):** Se `current_value` estiver próximo do `min_wh` ou `max_wh` (mas ainda dentro da faixa), bônus menor ou neutro (`+2` a `0`).
    * **Ligeiramente Fora (até 10%):** Se `current_value` estiver até `10%` abaixo do `min_wh` ou acima do `max_wh`, penalidade média (`-5` a ` -10`).
    * **Muito Fora (mais de 10%):** Se `current_value` estiver mais de `10%` fora (ex: `< min_wh * 0.9` ou `> max_wh * 1.1`), penalidade severa (`-20` a `-30`), podendo levar o score a um valor mínimo ou desqualificar.

### 1.2. `wave_direction` (Direção da Onda)

* **Definição:** Importante, mas variações pequenas não são tão impactantes.
* **Impacto no Score:** Pontuação de impacto "baixa".
* **Curva de Sensibilidade:** "Muito longa" (penalidade só significativa para grandes desvios).
* **Proposta de Lógica (Função Auxiliar de Direção):**
    * **Perfeito:** Se `current_direction` for igual a `preferred_wave_direction`, bônus pequeno (`+3`).
    * **Tolerável:** Diferença angular até `22.5` graus (metade de uma direção cardinal), bônus neutro (`0`) ou pequeno (`+1`).
    * **Aceitável (Cross):** Diferença angular até `45` graus (direção cardinal adjacente), penalidade muito pequena (`-1`).
    * **Ruim (Oposto/Quase Oposto):** Diferença angular maior que `45` graus, penalidade maior (`-3` a `-5`).

### 1.3. `wave_period` (Período da Onda)

* **Definição:** Boa relevância, não pode variar muito.
* **Impacto no Score:** Pontuação de impacto "média".
* **Curva de Sensibilidade:** "Média".
* **Proposta de Lógica (`score_proximity_to_range_ideal` para `wave_period`):**
    * **Ideal (`ideal_wp`):** Se `current_value` estiver `+/- 5-10%` do `ideal_wp`, bônus bom (`+10`).
    * **Próximo do Ideal / Dentro da Faixa Média:** Se `current_value` estiver entre `ideal_wp +/- 20%` OU na metade da faixa `min_wp` e `max_wp`, bônus razoável (`+5`).
    * **Dentro da Faixa Aceitável (Extremos Min/Max):** Se `current_value` estiver próximo do `min_wp` ou `max_wp` (mas ainda dentro da faixa), bônus neutro (`0`).
    * **Ligeiramente Fora (até 10%):** Se `current_value` estiver até `10%` abaixo do `min_wp` ou acima do `max_wp`, penalidade pequena (`-3`).
    * **Muito Fora (mais de 10%):** Se `current_value` estiver mais de `10%` fora (ex: `< min_wp * 0.9` ou `> max_wp * 1.1`), penalidade média a severa (`-7` a `-15`).

---

## 2. Parâmetros de Ondulação (Swell)

### 2.1. `swell_height`, `swell_direction`, `swell_period`

* **Lógica Individual:** Seguirão as mesmas lógicas de pontuação (curvas de sensibilidade) definidas para `wave_height`, `wave_direction` e `wave_period`, respectivamente.

### 2.2. Ponderação `Wave` vs. `Swell` (Definição da "Origem" Principal)

* **Objetivo:** Combinar os scores de `wave` e `swell` de forma a refletir que o swell é frequentemente o *driver* principal da qualidade da onda.
* **Abordagem:** Média ponderada dos scores individuais de cada parâmetro.
    * **Pontuação da Altura Total:** `score_height_total = (score_wave_height * 0.4) + (score_swell_height * 0.6)`
    * **Pontuação do Período Total:** `score_period_total = (score_wave_period * 0.4) + (score_swell_period * 0.6)`
    * **Pontuação da Direção Total:** `score_direction_total = (score_wave_direction * 0.4) + (score_swell_direction * 0.6)`
* **Notas:** Os pesos (0.4 e 0.6) são um ponto de partida e podem ser calibrados. Eles dão maior relevância aos parâmetros de swell.

---

## 3. Swell Secundário (`secondary_swell`)

* **Objetivo:** Avaliar se o swell secundário "atrapalha" o swell primário, aplicando penalidades baseadas na diferença de direção, ponderada pela altura e período do swell secundário.

* **Lógica de Impacto (`calculate_secondary_swell_impact`):**
    1.  **Relevância da Altura:**
        * Se `secondary_swell_height` for muito pequeno (ex: `< 0.5m`), impacto neutro (retorna `0`).
        * Alturas maiores (ex: `> 1.5m`) terão maior potencial de penalidade.
    2.  **Diferença Angular (`secondary_swell_direction` vs. `primary_swell_direction_sg`):**
        * **Pequena Diferença (0-22.5 graus):** Neutro.
        * **Média Diferença (22.5-45 graus):** Pequena penalidade (ex: `-5`).
        * **Grande Diferença (45-90 graus):** Penalidade média (ex: `-15`).
        * **Oposta/Muito Diferente (> 90 graus):** Penalidade severa (ex: `-30`).
    3.  **Ponderação da Penalidade pela Altura do Swell Secundário:**
        A penalidade baseada na diferença angular será multiplicada por um `height_factor`.
        * `height_factor` será calculado de forma que swells secundários menores que um `HIGH_IMPACT_SECONDARY_SWELL_HEIGHT` (ex: 1.5m) tenham sua penalidade reduzida proporcionalmente.
        * O `height_factor` pode ser limitado para não gerar penalidades excessivas (ex: `min(height_factor, 1.5)`).
    4.  **Ponderação Opcional pelo Período (Avançado):**
        Se o período do swell secundário for similar ao primário (ex: diferença `< 3s`) E a altura for relevante, a penalidade pode ser aumentada (ex: `* 1.2`) para refletir maior potencial de "fechadeiras" ou ondas cruzadas mais fortes.

* **Integração no Score Total:** O `impact_score` retornado por `calculate_secondary_swell_impact` (que será negativo ou zero) será somado ao score principal.

---

### 4. Parâmetros de Vento (`wind_speed_sg`, `wind_direction_sg`)

* **Objetivo:** Pontuar o vento considerando sua velocidade e direção, com uma lógica diferenciada para ventos ideais (offshore/cross-offshore) e não ideais (onshore/cross-onshore).
* **Princípios:**
    * Ventos fracos são geralmente bons, independentemente da direção.
    * Ventos fortes são ruins, a menos que sejam na direção ideal.
    * Ventos na direção ideal (offshore/cross-offshore) alisam a onda e permitem maior tolerância à velocidade.
    * Ventos na direção não ideal (onshore/cross-onshore) mexem o mar, com a qualidade da onda decaindo drasticamente com o aumento da velocidade.

* **Pré-requisito:** Definição de `preferred_wind_direction` (direção de vento ideal para o pico) e `spot_coast_orientation` (orientação da costa do pico em graus ou cardinal para determinar offshore/onshore).

* **Abordagem: Duas Curvas de Pontuação:**

    * **Curva A: Vento Ideal (Offshore/Cross-Offshore)**
        * **Velocidade muito baixa (ex: <= 3 nós):** Score bom (`+10`).
        * **Velocidade baixa a média (ex: > 3 e <= 10 nós):** Score máximo (`+25`). Representa o vento ideal que alisa e modela a onda.
        * **Velocidade alta (ex: > 10 e <= 15 nós):** Score ainda positivo, mas decrescente (`+15`). Ainda é offshore, mas pode começar a ser forte demais para alguns surfistas.
        * **Velocidade muito alta (ex: > 15 e <= 20 nós):** Score negativo (`-5`). Mesmo offshore, vento muito forte dificulta.
        * **Velocidade extrema (ex: > 20 nós):** Score severamente negativo e crescente (ex: `-20 - (velocidade - 20) * 2`).

    * **Curva B: Vento Não Ideal (Onshore/Cross-Onshore ou Outras Direções)**
        * **Velocidade muito baixa (ex: <= 3 nós):** Score bom (`+8`). Vento quase nulo não atrapalha muito.
        * **Velocidade baixa (ex: > 3 e <= 8 nós):** Score negativo inicial (`-10`). O mar começa a ficar mexido.
        * **Velocidade média (ex: > 8 e <= 15 nós):** Score fortemente negativo (`-30`). O mar já está bem mexido.
        * **Velocidade alta (ex: > 15 nós):** Score extremamente negativo e crescente (ex: `-50 - (velocidade - 15) * 5`). Vento onshore forte inutiliza a sessão. Pode levar a uma desqualificação do pico para o surf.

* **Função Proposta:** `calculate_wind_score(wind_speed, wind_direction, preferred_wind_direction, spot_coast_orientation)`
    * Esta função determinará se o vento atual é "ideal" com base na `wind_direction` e `spot_coast_orientation`.
    * Aplicará a Curva A ou B conforme a classificação da direção do vento.


### 5. Parâmetros de Temperatura

Ambos `air_temperature` (temperatura do ar) e `water_temperature` (temperatura da água) seguirão uma lógica similar: buscar um valor ideal ou uma faixa confortável, com penalidades crescentes para desvios que tornam a experiência de surf desconfortável. A ideia é que estes fatores contribuem para o "conforto" geral da sessão de surf, mas raramente desqualificam um pico por si só, a menos que sejam extremos (muito frio/quente).

A pontuação para temperatura será "baixa a média", e a curva de sensibilidade será "média".

#### 5.1. `air_temperature` (Temperatura do Ar)

* **Definição:** Contribui para o conforto geral. Extremamente baixas ou altas temperaturas podem ser um problema.
* **Impacto no Score:** Pontuação de impacto "baixa a média".
* **Curva de Sensibilidade:** "Média".
* **Proposta de Lógica (`score_proximity_to_range_ideal` para `air_temperature`):**
    * **Ideal (`ideal_at`):** Se `current_value` estiver `+/- 2-3°C` do `ideal_at`, bônus bom (`+5` a `+8`).
    * **Próximo do Ideal / Faixa Confortável:** Se `current_value` estiver `+/- 5°C` do `ideal_at` (mas fora da zona ideal perfeita), bônus neutro a pequeno (`+2` a `0`).
    * **Ligeiramente Fora da Faixa Confortável (ex: -5°C a -10°C ou +5°C a +10°C do ideal):** Penalidade pequena (`-3` a `-7`). Começa a ficar frio/quente demais.
    * **Muito Fora (Extremos - ex: > 10°C de desvio):** Penalidade maior (`-10` a `-15`), tornando a sessão bem menos agradável. Condições extremas (ex: congelando ou escaldante) podem gerar penalidades mais severas.

#### 5.2. `water_temperature` (Temperatura da Água)

* **Definição:** Crucial para o conforto térmico no mar e a necessidade de roupa de borracha.
* **Impacto no Score:** Pontuação de impacto "baixa a média" (similar ao ar, mas pode ser ligeiramente mais influente para o conforto imediato do surf).
* **Curva de Sensibilidade:** "Média".
* **Proposta de Lógica (`score_proximity_to_range_ideal` para `water_temperature`):**
    * **Ideal (`ideal_wt`):** Se `current_value` estiver `+/- 1-2°C` do `ideal_wt`, bônus bom (`+5` a `+8`). (Margem ligeiramente mais apertada que o ar, pois a sensação térmica na água é mais imediata).
    * **Próximo do Ideal / Faixa Confortável:** Se `current_value` estiver `+/- 3-4°C` do `ideal_wt`, bônus neutro a pequeno (`+2` a `0`).
    * **Ligeiramente Fora da Faixa Confortável (ex: -4°C a -8°C ou +4°C a +8°C do ideal):** Penalidade pequena (`-5` a `-10`). O uso de roupa de borracha (ou sua ausência) pode ser mais crítico aqui.
    * **Muito Fora (Extremos - ex: > 8°C de desvio):** Penalidade maior (`-15` a `-20`), indicando condições de água muito fria (risco de hipotermia) ou muito quente (desconforto).

---

### 6. Parâmetros de Corrente (`current_speed_sg`, `current_direction_sg`)

* **Objetivo:** Avaliar o impacto da correnteza no surf, priorizando correntes fracas e penalizando progressivamente as correntes mais fortes.
* **Princípios:**
    * Correntezas fortes são prejudiciais ao surf, dificultando a remada, a permanência no pico e a segurança.
    * Correntezas muito fracas ou nulas são as ideais.
    * A direção da corrente é menos crítica que sua velocidade e seu impacto geral no score é **secundário** em comparação com ondas e vento.

* **Impacto no Score:** Pontuação "baixa" (contribui para o conforto e a facilidade, mas raramente desqualifica).
* **Curva de Sensibilidade:** "Média" (a penalidade aumenta com a velocidade, mas em uma escala menor).

* **Proposta de Lógica (`score_proximity_to_single_ideal` adaptada para correnteza):**

    * **Velocidade Ideal (Muito Fraca/Nula - ex: <= 0.2 nós):** Bônus pequeno (`+3`). Condições ideais com pouca ou nenhuma corrente.
    * **Velocidade Baixa (ex: > 0.2 e <= 0.5 nós):** Score neutro(`0`). Correnteza perceptível, mas geralmente gerenciável e com impacto mínimo no score.
    * **Velocidade Média (ex: > 0.5 e <= 1.0 nós):** Penalidade pequena (`-2`). A remada fica mais difícil e a posição no pico pode ser levemente comprometida.
    * **Velocidade Alta (ex: > 1.0 e <= 1.5 nós):** Penalidade média (`-5`). O surf se torna mais desgastante.
    * **Velocidade Muito Alta (ex: > 1.5 nós):** Penalidade significativa (`-10`). Surf ainda possível para experientes, mas muito exaustivo.

---

### 7. Parâmetros de Maré (`tide_phase`, `sea_level_sg`)

* **Objetivo:** Avaliar a adequação das condições de maré (fase e altura) para um determinado pico, que é altamente dependente das características específicas do spot.
* **Princípios:**
    * Cada pico de surf tem fases de maré e níveis de água ideais/aceitáveis.
    * Desvios significativos do nível de água aceitável podem tornar o surf impossível (muito raso ou muito fundo).
    * A fase da maré (enchente, vazante, cheia, seca) influencia a formação e quebra da onda.

* **Impacto no Score:** Pontuação "média a alta", pois a maré pode ser um fator desqualificador para um pico específico.
* **Curva de Sensibilidade:** "Média a acentuada" para o `sea_level_sg` (nível da maré), e "discreta" para a `tide_phase`.

* **Pré-requisitos (Preferências do Spot):** Para cada `spot`, serão necessários os seguintes parâmetros de preferência de maré:
    * `ideal_tide_type` (lista de strings): Ex: `['low', 'falling']`, `['high']`.
    * `min_tide_height` (float): Nível mínimo de maré (ex: em metros ou pés).
    * `max_tide_height` (float): Nível máximo de maré.
    * `ideal_tide_height` (float, opcional): Nível ideal de maré (ponto ótimo).

* **Lógica (`calculate_tide_score`):**

    1.  **Pontuação da Fase da Maré (`tide_phase`):**
        * Se `tide_phase` estiver em `ideal_tide_type`: Bônus positivo (`+8`).
        * Se `tide_phase` não for ideal, mas não for a "oposta": Penalidade leve (`-2`).
        * Se `tide_phase` for a "oposta" (ex: preferência 'low', mas é 'high'): Penalidade maior (`-5`).

    2.  **Pontuação do Nível do Mar (`sea_level_sg`):**
        * **Fora dos Limites Críticos (`min_tide_height`, `max_tide_height`):**
            * Se `sea_level < min_tide_height`: Penalidade severa. Quanto mais abaixo, maior a penalidade (ex: `-15` base, mais `-5` por cada `0.1m` abaixo). Se muito abaixo (ex: `> 0.5m` de desvio), penalidade extra (`-20`).
            * Se `sea_level > max_tide_height`: Penalidade severa. Quanto mais acima, maior a penalidade (ex: `-15` base, mais `-5` por cada `0.1m` acima). Se muito acima (ex: `> 0.5m` de desvio), penalidade extra (`-20`).
        * **Dentro da Faixa Aceitável (`min_tide_height` a `max_tide_height`):**
            * **Com `ideal_tide_height` definido:** Pontuar pela proximidade ao `ideal_tide_height`.
                * Muito próximo (ex: `+/- 0.1m`): Bônus máximo (`+10`).
                * Próximo (ex: dentro de `20%` do meio da faixa `min/max`): Bônus bom (`+7`).
                * Dentro de `50%` do meio da faixa: Bônus pequeno (`+3`).
                * Mais distante dentro da faixa: Bônus neutro (`+0`).
            * **Sem `ideal_tide_height` (apenas `min/max`):** Bônus neutro a pequeno (`+5`) por estar em uma altura aceitável.

---