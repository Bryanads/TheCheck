## ⚠️ Atenção

> **Sem o arquivo `.env`, nada irá funcionar!**  
> Este arquivo **não foi commitado propositalmente**, pois contém as chaves de API do [Stormglass.io](https://stormglass.io) e as credenciais de acesso ao banco de dados do [SupaBase](https://supabase.com).

---

### 📁 Diretórios

- **`exemples/`**:  
    _Pode ser ignorado._  
    Contém apenas códigos antigos que já foram refatorados.

---

### 📋 Tarefas

- [ ] Revisar o `calculate_suitability_score` de ponta a ponta.
- [ ] Discutir lógica do `main.py`, ou seja, como inputador dados para o `calculate_suitability_score`.
    - Receber hora como parâmetro?
    - Passar uma previsão e ele só devolver o score?
    - Passar todo o banco de dados e ele devolver uma lista dos melhores?
        - A lista pode ser composta com horas sequências de um mesmo dia?
    - Criar uma avaliação do score?
        - Necessitaria criar uma nova tabela?
