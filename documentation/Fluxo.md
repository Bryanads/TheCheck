
## Fluxo de Dados no 'TheCheck': Da Previsão à Recomendação e Aprendizado

### 1. **Configuração Inicial: As Praias (`praias`)**
* **Informação que chega:** Dados estáticos e geográficos sobre cada pico de surf.
* **Como chega:** Manualmente inserida por administradores ou importada de uma fonte de dados de referência (ex: um CSV, JSON).
* **Onde é armazenada:** Tabela `praias`.
* **Exemplo:**
    * `id_praia: 1`, `nome_praia: "Reserva"`, `latitude: -23.01`, `longitude: -43.46`, `tipo_fundo: "Areia"`, `orientacao_costa: "SE"`.

### 2. **Coleta de Previsões em Tempo Real (`previsoes_horarias` e `mares`)**
* **Informação que chega:** Dados brutos e horários de previsão do tempo (onda, vento, swell, temperatura) e eventos de maré para as próximas 5-7 dias.
* **Como chega:** Requisições automatizadas (ex: via `make_request.py` rodando periodicamente) à API da StormGlass.io.
* **Onde é armazenada:**
    * `previsoes_horarias`: Guarda todos os parâmetros de onda, vento, etc., por hora.
    * `mares`: Guarda os eventos pontuais de maré (alta/baixa) com sua altura e timestamp.
* **Exemplo:**
    * `previsoes_horarias`: `id_praia: 1`, `timestamp_utc: "2025-07-27 10:00:00Z"`, `wave_height_sg: 1.5`, `wind_direction_sg: 90`, etc.
    * `mares`: `id_praia: 1`, `timestamp_utc: "2025-07-27 14:30:00Z"`, `tipo: "high"`, `altura: 1.2`.

### 3. **Configuração de Preferências do Usuário (`usuarios`, `preferencias_nivel_praia`, `preferencias_usuario_praia`)**
* **Informação que chega:**
    * Dados de perfil do usuário (nome, email, nível de surf, goofy/regular, direção de onda preferida).
    * Presets de condições ideais para cada nível de surf por praia (o "padrão").
    * Preferências personalizadas do usuário para cada praia.
* **Como chega:**
    * `usuarios`: No cadastro do usuário.
    * `preferencias_nivel_praia`: Inserida manualmente por administradores/especialistas no surf do 'TheCheck' para "preencher" o sistema no início.
    * `preferencias_usuario_praia`: Inserida pelo próprio usuário, refinando suas preferências para praias específicas através da interface do aplicativo.
* **Onde é armazenada:** As respectivas tabelas.
* **Exemplo:**
    * `usuarios`: `id_usuario: 101`, `nome: "Carlos"`, `nivel_surf: "Intermediário"`, `goofy_regular: "Regular"`.
    * `preferencias_nivel_praia`: `nivel_surf: "Intermediário"`, `id_praia: 1`, `altura_onda_min: 1.0`, `mare_ideal_tipo: "low"`.
    * `preferencias_usuario_praia`: `id_usuario: 101`, `id_praia: 1`, `altura_onda_min: 1.2`, `crowd_tolerancia: "Baixa"`.

### 4. **Geração de Recomendação em Tempo Real (NO FLUXO, NÃO EM UMA TABELA)**
* **Informação que chega:** O sistema precisa recomendar a melhor praia/horário *agora*.
* **Como é processada:**
    1.  O sistema busca as **previsões mais recentes** para as praias (`previsoes_horarias`).
    2.  Busca as **preferências do usuário** logado (`preferencias_usuario_praia` para ele e `usuarios` para nível/estilo).
    3.  **Se o usuário for novo (cold start) ou não tiver preferências explícitas:** O sistema usa os **presets de nível** (`preferencias_nivel_praia`) como base.
    4.  A **lógica de recomendação** (inicialmente baseada em regras/presets, depois em ML) combina essas informações para determinar o quão "boa" é a previsão atual para *aquele usuário* ou *aquele nível*.
* **Onde é armazenada:** **O resultado da recomendação é gerado "na hora" e exibido na interface do usuário (ex: no aplicativo, site). Ele NÃO é gravado em uma tabela como `historico_momentos_praia`.** O resultado é temporário e específico para a consulta atual.
* **Exemplo de Geração (Interna):**
    * Sistema consulta `previsoes_horarias` para "Reserva" às 10h: onda 1.5m, vento terral NE.
    * Sistema consulta `preferencias_usuario_praia` (se houver) ou `preferencias_nivel_praia` (para "Intermediário") para "Reserva": gosta de ondas 1.0-1.8m, vento terral NE.
    * **RESULTADO (exibido na UI):** "Reserva está ÓTIMA para você agora (condições ideais!)"

### 5. **Feedback do Usuário: A Realidade (`avaliacoes_surf`)**
* **Informação que chega:** O usuário foi surfar e avalia a qualidade da sessão.
* **Como chega:** O usuário interage com a interface do aplicativo para registrar sua experiência.
* **Onde é armazenada:** Tabela `avaliacoes_surf`. Esta é a **verdade fundamental** sobre o que realmente aconteceu do ponto de vista do surfista.
* **Exemplo:**
    * Carlos (`id_usuario: 101`) avalia: `id_praia: 1`, `data_avaliacao: "2025-07-27"`, `hora_avaliacao: "10:30"`, `qualidade_surf: 5` (Perfeito!).

### 6. **Construção do Histórico Detalhado para ML (`historico_momentos_praia`)**
* **Informação que chega:** As `previsoes_horarias` e `mares` mais antigas (após 7-15 dias de retenção completa).
* **Como é processada:** Um job diário ou semanal (processamento em batch) lê os dados de `previsoes_horarias` e `mares` que já não são "recentes". Ele agrega esses dados em resumos por "momentos do dia" (Madrugada, Manhã, Tarde, Noite).
* **Onde é armazenada:** Tabela `historico_momentos_praia`.
* **Exemplo:**
    * O job processa as previsões de "2025-07-20" para a "Reserva".
    * Calcula a média da altura da onda, direção dominante do vento, etc., para o "Momento: Manhã" (06:00-12:00) daquele dia.
    * Insere: `id_praia: 1`, `data_historico: "2025-07-20"`, `momento_do_dia: "Manhã"`, `avg_wave_height: 1.3`, `dom_wind_direction: 95`, etc.

### 7. **Treinamento e Refinamento do Modelo de Machine Learning (CICLO DE APRENDIZADO)**
* **Informação que chega:**
    * O **histórico das condições** (`historico_momentos_praia`).
    * O **feedback dos usuários** sobre essas condições (`avaliacoes_surf`), vinculado ao usuário (`usuarios`) e ao momento.
* **Como é processada:**
    1.  O modelo de ML é treinado periodicamente (ex: semanalmente).
    2.  Ele aprende as correlações: "Quando as condições históricas no `historico_momentos_praia` eram X (onda, vento, maré) e o `nivel_surf` do usuário era Y, a `qualidade_surf` em `avaliacoes_surf` era consistentemente alta."
    3.  Aprende também as **preferências individuais** do usuário quando há dados suficientes: "Quando o Carlos (usuário Z) surfou com condições A na praia B, ele avaliou como ótima."
* **Onde é armazenada:** O modelo de ML treinado é um **arquivo de modelo** (ex: um arquivo `.pkl`, `.h5`), não uma tabela do banco de dados relacional. Ele é carregado pelo sistema para fazer as recomendações em tempo real (Passo 4).
