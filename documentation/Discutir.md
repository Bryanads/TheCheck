
# Pontos de Discussão Futuros para o 'TheCheck'

Este documento lista os tópicos que ainda precisam ser discutidos e definidos para o desenvolvimento contínuo do sistema 'TheCheck', cobrindo aspectos de coleta de dados, gerenciamento de histórico, e refinamento do modelo de recomendação.

## 1. Coleta e Armazenamento de Dados da Previsão

* **Granularidade da Previsão (1h vs. Maior):**
    * Revisar e confirmar a decisão de manter a granularidade horária (`previsoes_horarias`) para as previsões ativas (próximos X dias) versus um intervalo maior (ex: 3h, 6h).
    * Discutir as implicações de custo (requisições à API) e volume de dados para a decisão final.

* **Estratégia de Histórico e Agregação:**
    * Definir o período exato de retenção da granularidade horária completa (ex: 7 dias, 15 dias).
    * Detalhar o processo de agregação de dados para o histórico de médio e longo prazo (diário, semanal). Quais métricas exatas (média, máxima, mínima, predominante) serão salvas?
    * Discutir a tecnologia/ferramenta para implementar o "job" de agregação (ex: script Python com `cron`, Apache Airflow, etc.).
    * Avaliar a necessidade de uma ferramenta de Data Warehousing ou Data Lake se o volume de dados históricos se tornar massivo.

* **Confiabilidade e Tratamento de Erros da API:**
    * Como lidar com falhas na requisição à StormGlass.io (API down, limites de requisição excedidos)? Implementar retries, logging, alertas.
    * Estratégia para dados ausentes ou inconsistentes vindos da API.

## 2. Refinamento do Modelo de Recomendação

* **Implementação da Abordagem Híbrida e Evolutiva:**
    * Detalhar como o modelo de Machine Learning irá consumir dados das tabelas `usuarios`, `preferencias_usuario_praia`, `previsoes_horarias` e `avaliacoes_surf`.
    * Definir os algoritmos iniciais para o modelo de recomendação (ex: filtragem colaborativa, modelos baseados em conteúdo, ou uma combinação).
    * Estabelecer critérios para quando um usuário "sai" da fase de "cold start" e começa a receber recomendações mais individualizadas.

* **Coleta de Feedback do Usuário (`avaliacoes_surf`):**
    * Discutir a interface de usuário para a coleta de avaliações (como encorajar os usuários a fornecerem feedback regular).
    * Definir a escala de avaliação (`qualidade_surf`: 1-5, 1-10, emojis?).
    * Estratégias para validar a qualidade do feedback (ex: evitar avaliações fraudulentas).

* **Parametrização das Preferências do Usuário:**
    * Como a interface permitirá que o usuário defina suas preferências em `preferencias_usuario_praia` (sliders, checkboxes, campos de texto?).
    * Considerar a granularidade de `direcao_swell_preferida` e `vento_direcao_preferida` (texto livre, lista pré-definida, multiple select?).

## 3. Arquitetura Geral do Sistema 'TheCheck'

* **Tecnologias de Backend:**
    * Definir o framework/linguagem principal para o backend da aplicação (Python/Flask/Django, Node.js/Express, etc.).
    * Como o backend irá interagir com o banco de dados (ORM, SQL puro?).

* **Interface do Usuário (Frontend):**
    * Discutir as tecnologias para o frontend (React, Vue, Angular, mobile-first?).
    * Como os dados de previsão e recomendação serão visualizados para o surfista.

* **Infraestrutura e Deploy:**
    * Plataforma de hospedagem (AWS, Google Cloud, Azure, Heroku, VPS?).
    * Estratégia de deploy (Docker, Kubernetes?).
    * Monitoramento e logging do sistema.

## 4. Próximos Passos Imediatos

* Confirmar a estrutura final das tabelas.
* Iniciar a configuração do ambiente de desenvolvimento e banco de dados (PostgreSQL).
* Começar a adaptar o script `make_request.py` para inserir dados no banco de dados.

