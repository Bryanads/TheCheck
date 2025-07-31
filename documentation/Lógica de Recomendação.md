## Planejamento da Lógica dos Níveis de Surf para Recomendações

Vamos detalhar como construir essa inteligência, começando com o padrão e evoluindo para a personalização.

### 1. A Base: Preferências por Nível em Cada Spot (`level_spot_preferences`)

Esta tabela é o seu ponto de partida. Ela vai dizer ao "TheCheck" o que é uma **onda boa para cada nível de surfista, em cada spot específico**.

**Como Construir:**

* **Definição dos Parâmetros:** Para cada um dos 8 **Níveis de Surf** (Iniciante Total, Iniciante, Maroleiro, Longboarder, Intermediário, Intermediário-Avançado, Avançado, Big Rider) e para cada **Spot** que você cadastrar, você precisará preencher as seguintes informações (baseado na sua tabela `level_spot_preferences`):
    * `min_wave_height` (altura mínima da onda ideal)
    * `max_wave_height` (altura máxima da onda ideal)
    * `preferred_swell_direction` (direção de swell preferida, ex: "S", "SE", "SW")
    * `min_swell_period` (período mínimo do swell ideal)
    * `max_swell_period` (período máximo do swell ideal)
    * `preferred_wind_direction` (direção do vento preferida, ex: "Offshore", "N", "NE")
    * `max_wind_speed` (velocidade máxima do vento tolerável)
    * `ideal_tide_type` (tipo de maré ideal, ex: "high", "low", "mid", "rising", "falling")
    * `additional_considerations` (qualquer observação extra, tipo "melhor com swell de leste forte").

* **Preenchimento Inicial (Dados Semente):**
    * **Conhecimento Local:** Para os seus spots no Rio (Barra, Prainha, Macumba, etc.), você ou alguém com conhecimento local profundo precisará definir esses parâmetros. Por exemplo:
        * **Prainha / Avançado:** `min_wave_height = 1.5`, `max_wave_height = 3.0`, `preferred_swell_direction = 'SW'`, `min_swell_period = 8`, `max_wind_speed = 10` (nós), `ideal_tide_type = 'rising'`.
        * **Macumba / Longboarder:** `min_wave_height = 0.5`, `max_wave_height = 1.8`, `preferred_swell_direction = 'S, SW'`, `min_swell_period = 6`, `max_wind_speed = 15` (nós), `ideal_tide_type = 'mid'`.
    * Você pode usar um script Python simples ou inserir diretamente via SQL (`INSERT INTO level_spot_preferences ...`) para popular esta tabela inicialmente.

### 2. A Evolução: Preferências Personalizadas do Usuário (`user_spot_preferences`)

Esta tabela permite que o usuário refine (ou sobrescreva) as preferências baseadas no seu nível, tornando a recomendação única para ele.

**Como Construir:**

* **Inicialização Padrão (Cold Start):** Quando um usuário se cadastra e escolhe seu `surf_level` (ex: "Intermediário"), inicialmente sua tabela `user_spot_preferences` estará vazia. Nesses casos, o sistema usará os padrões de `level_spot_preferences`.
* **Interface de Preferências:** Crie uma tela no aplicativo/site onde o usuário possa:
    1.  **Selecionar um Spot:** Ele escolhe um spot que frequenta ou que gostaria de receber recomendações personalizadas.
    2.  **Pré-preencher com o Padrão:** Ao selecionar o spot, você deve **carregar os valores da `level_spot_preferences` correspondentes ao `surf_level` dele e ao `spot_id` selecionado**. Isso dá a ele um ponto de partida.
    3.  **Ajuste Personalizado:** O usuário edita esses valores padrão para refletir suas preferências *pessoais* para aquele spot (ex: "Sou Intermediário, mas na Prainha prefiro ondas um pouco menores, até 2.0m, e não gosto de vento acima de 12 nós").
    4.  **Salvamento:** Quando o usuário salva, um `INSERT ... ON CONFLICT DO UPDATE` é feito na `user_spot_preferences`.

### 3. A Lógica de Recomendação em Ação

Essa é a parte que compara as previsões com as preferências e gera o "score" de recomendação.

**Como Implementar (no Backend):**

1.  **Usuário Logado e seu Nível:** Ao gerar recomendações para um usuário logado, primeiro, pegue o `user_id` e o `surf_level` da tabela `users`.
2.  **Busca de Preferências:**
    * Para cada `spot` que você quer recomendar:
        * **Tente buscar preferências em `user_spot_preferences`** para o `user_id` e `spot_id` atuais.
        * **Se encontrar:** Use **essas preferências personalizadas** para o cálculo da adequação.
        * **Se NÃO encontrar:** Significa que o usuário ainda não personalizou aquele spot. Então, **busque as preferências na `level_spot_preferences`** usando o `surf_level` do usuário e o `spot_id`.
        * *Resultado:* Você terá um conjunto de critérios (`min_wave_height`, `max_wind_speed`, etc.) específicos para *aquele usuário e aquele spot*.
3.  **Comparação com Previsão:**
    * Pegue os dados de **previsão horária** (`forecasts`) e **marés** (`tides_forecast`) para o `spot_id` e a `timestamp_utc` que você está avaliando.
    * Compare cada parâmetro da previsão com os critérios definidos nas preferências (personalizadas ou de nível).
    * **Exemplo:** Se a previsão diz `wave_height_sg = 1.2` e a preferência é `min_wave_height = 1.0` e `max_wave_height = 1.8`, essa condição é "boa". Se o vento for `wind_speed_sg = 20` e a preferência `max_wind_speed = 10`, essa condição é "ruim".
4.  **Cálculo de Score:** Atribua pontos ou um peso para cada parâmetro que se encaixa ou não. Você pode ter:
    * **Score Binário:** Bom/Ruim (se todos os critérios forem atendidos, é bom; senão, é ruim).
    * **Score Graduado:** Uma porcentagem ou nota (ex: 0-10) baseada em quantos critérios foram atendidos e quão próximos eles estão do ideal.
    * **Score Ponderado:** Atribua pesos diferentes para critérios (ex: altura da onda e direção do swell são mais importantes que temperatura da água).
5.  **Exibição:** Ordene os spots (e horários dentro dos spots) pelos scores mais altos e exiba na interface.

### 4. O Aprendizado Contínuo: Feedback e `rating_conditions_snapshot`

Esta é a ponte para o Machine Learning, refinando as recomendações ao longo do tempo.

**Como Utilizar:**

* Quando um usuário registra uma avaliação (`surf_ratings`), você captura as condições exatas (`rating_conditions_snapshot`).
* **Aprendizado (Offline/Batch):** Periodicamentem seu modelo de ML (que roda em um servidor ou serviço de ML, não no banco de dados) irá:
    * Olhar para a `rating_conditions_snapshot` (condições de onda, vento, maré *naquele momento*).
    * Olhar para a `surf_ratings` (a `surf_quality` que o usuário deu para aquelas condições).
    * Olhar para o `surf_level` do `users` (quem fez a avaliação).
    * Com esses dados, o modelo pode aprender padrões mais complexos: "Surfistas 'Intermediário-Avançado' tendem a dar notas altas quando o swell é do S com período de 9s e o vento terral, mesmo que a altura da onda não seja gigantesca."
* **Refinamento Futuro:** Em estágios mais avançados, o modelo de ML pode aprender a:
    * **Ajustar os Padrões de Nível:** Sugerir alterações nos `level_spot_preferences` se houver um grande volume de feedback contraditório.
    * **Criar Preferências Personalizadas do Zero:** Se um usuário nunca preencheu `user_spot_preferences` mas deu muitas avaliações, o ML pode "inferir" suas preferências e preencher a tabela para ele.
