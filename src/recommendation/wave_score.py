import numpy as np

def calcular_score_tamanho_onda(previsao_onda, tamanho_minimo, tamanho_ideal, tamanho_maximo):
    """
    Calcula um score para o tamanho de uma onda, penalizando assimetricamente.

    Args:
        previsao_onda (float ou array-like): O tamanho da onda previsto.
        tamanho_minimo (float): O tamanho mínimo aceitável da onda.
        tamanho_ideal (float): O tamanho ideal da onda (score = 1.0).
        tamanho_maximo (float): O tamanho máximo aceitável da onda (score próximo de 0).

    Returns:
        float ou array-like: O score calculado (entre 0 e 1).
    """

    previsao_onda = np.asarray(previsao_onda, dtype=float)
    # Converter explicitamente os parâmetros de entrada para float
    tamanho_minimo = float(tamanho_minimo)
    tamanho_ideal = float(tamanho_ideal)
    tamanho_maximo = float(tamanho_maximo)

    score = np.zeros_like(previsao_onda, dtype=float)

    ##################################################################################################################
    # Calculo do lado esquerdo (Ondas menores ou iguais ao tamanho ideal):
    mask_left = previsao_onda <= tamanho_ideal
    # Garante que k1 não seja negativo ou cause problemas se tamanho_minimo > tamanho_ideal
    k1_denom = (tamanho_ideal - tamanho_minimo)
    if k1_denom <= 0: # Evita divisão por zero ou k1 inválido
        k1 = 1.0 # Valor padrão se não houver faixa válida
    else:
        # Ajuste k1 para controlar a queda do score. Um valor maior significa queda mais rápida.
        # k1 = 1.0 / k1_denom # Uma opção linear simples
        k1 = 2.0 / (k1_denom + 1e-6) # Uma opção com ajuste para evitar divisão por zero e controlar inclinação
    
    score[mask_left] = np.exp(-k1 * (tamanho_ideal - previsao_onda[mask_left])**2)
    """
    Função exponencial quadrática:
    f(x) = exp(-k1 * (tamanho_ideal - x)^2)
    Onde:
    - f(x) é o score calculado.
    - k1 é uma constante de proporcionalidade que determina a suavidade da curva.
    - tamanho_ideal é o tamanho ideal da onda.
    - x é o tamanho da onda previsto.

    Usamos essa função pois é uma curva suave, com o k1 sendo calculado dinamicamente. 
    Isso garante que, para valores de tamanho mínimo próximos ao tamanho ideal, o score ainda será alto.
    Já para valores de tamanho mínimo muito distantes do tamanho ideal, o score será baixo.
    """
    
    ##################################################################################################################
    # Cálculo do lado direito (Ondas maiores que o tamanho ideal): 
    mask_right = previsao_onda > tamanho_ideal
    if (tamanho_maximo - tamanho_ideal) >= 1.0:
        p_direita = 6 
    else:
        p_direita = 3 

    epsilon = 0.1 # Score desejado no tamanho_maximo
    denominador = (tamanho_maximo - tamanho_ideal)**p_direita

    if denominador == 0:
        k2 = 1.0 # Caso de divisão por zero (se tamanho_maximo == tamanho_ideal)
    else:
        k2 = -np.log(epsilon) / denominador
        
    score[mask_right] = np.exp(-k2 * (previsao_onda[mask_right] - tamanho_ideal)**p_direita)

    score = score * 100
    score = np.round(score, 2)

    return score

def calcular_score_direcao_onda(previsao_direcao, direcao_ideal):
    """
    Calcula um score para a direção de uma onda, penalizando assimetricamente.

    Args:
        previsao_direcao (float ou array-like): A direção da onda prevista em graus.
        direcao_ideal (float): A direção ideal da onda (score = 1.0).

    Returns:
        float ou array-like: O score calculado (entre 0 e 1).
    """
    
    previsao_direcao = np.asarray(previsao_direcao, dtype=float)
    direcao_ideal = float(direcao_ideal) # Converter para float
    
    # Calcula a diferença angular
    diferenca = np.abs(previsao_direcao - direcao_ideal) % 360
    diferenca = np.minimum(diferenca, 360 - diferenca)  # Considera o menor ângulo

    # Define o score
    score = np.exp(-diferenca**2 / (45**2))  # Penaliza diferenças maiores que 45 graus

    score = score * 100
    score = np.round(score, 2)

    return score

def calcular_score_periodo_onda(previsao_periodo, periodo_ideal):

    """
    Calcula um score para o período das ondas, penalizando simetricamente.

    Args:
        previsao_periodo (float ou array-like): O período da onda previsto.
        periodo_ideal (float): O período ideal da onda (score = 1.0).

    Returns:
        float ou array-like: O score calculado (entre 0 e 1).
    """
    
    previsao_periodo = np.asarray(previsao_periodo, dtype=float)
    periodo_ideal = float(periodo_ideal) # Converter para float
    score = np.exp(-((previsao_periodo - periodo_ideal) ** 2) / (periodo_ideal + 1e-6)) # Adicionado 1e-6 para evitar divisão por zero

    score = score * 100
    score = np.round(score, 2)

    return score

def calcular_impacto_swell_secundario(
    previsao_swell_secundario_tamanho,
    previsao_swell_secundario_periodo,
    previsao_swell_secundario_direcao,
    previsao_onda_tamanho,        
    previsao_onda_periodo,          
    previsao_onda_direcao           
):
    """
    Calcula o impacto de um swell secundário nas ondas principais,
    retornando um score entre -1 (impacto muito negativo) e 1 (impacto muito positivo).

    Args:
        previsao_swell_secundario_tamanho (float ou array-like): Tamanho do swell secundário (metros).
        previsao_swell_secundario_periodo (float ou array-like): Período do swell secundário (segundos).
        previsao_swell_secundario_direcao (float ou array-like): Direção do swell secundário (graus).
        previsao_onda_tamanho (float ou array-like): Tamanho da onda principal (metros).
        previsao_onda_periodo (float ou array-like): Período da onda principal (segundos).
        previsao_onda_direcao (float ou array-like): Direção da onda principal (graus).

    Returns:
        float ou array-like: O score de impacto (-1 a 1).
    """

    # Garante que todas as entradas são arrays numpy para cálculos vetorizados e convertidas para float
    previsao_swell_secundario_tamanho = np.asarray(previsao_swell_secundario_tamanho, dtype=float)
    previsao_swell_secundario_periodo = np.asarray(previsao_swell_secundario_periodo, dtype=float)
    previsao_swell_secundario_direcao = np.asarray(previsao_swell_secundario_direcao, dtype=float)
    previsao_onda_tamanho = np.asarray(previsao_onda_tamanho, dtype=float)
    previsao_onda_periodo = np.asarray(previsao_onda_periodo, dtype=float)
    previsao_onda_direcao = np.asarray(previsao_onda_direcao, dtype=float)

    # --- 1. Cálculo do Impacto da Direção ---
    # Calcula a menor diferença angular entre as direções (0 a 180 graus)
    delta_direcao = np.abs(previsao_swell_secundario_direcao - previsao_onda_direcao) % 360
    delta_direcao = np.minimum(delta_direcao, 360 - delta_direcao) 
    
    # Fator de alinhamento da direção:
    # cos(0°) = 1 (mesma direção - positivo)
    # cos(90°) = 0 (perpendicular - neutro)
    # cos(180°) = -1 (oposta - negativo)
    fator_alinhamento_direcao = np.cos(np.radians(delta_direcao))

    # --- 2. Cálculo do Impacto do Período (com assimetria) ---
    # Para evitar divisão por zero ou por períodos muito pequenos da onda principal,
    # usamos um valor mínimo de referência.
    periodo_onda_referencia = np.maximum(previsao_onda_periodo, 1.0) # Assume mínimo de 1.0s para referência

    # Calcula a razão da diferença de período (positivo se swell for mais longo, negativo se for mais curto)
    razao_diferenca_periodo = (previsao_swell_secundario_periodo - periodo_onda_referencia) / periodo_onda_referencia

    # Coeficientes para a assimetria do período:
    # Penaliza mais fortemente períodos secundários curtos (mais negativos)
    K_periodo_curto = 2.5 
    # Bonifica/penaliza suavemente períodos secundários longos (mais suaves/positivos)
    K_periodo_longo = 0.8 

    fator_impacto_periodo = np.where(
        razao_diferenca_periodo < 0,
        K_periodo_curto * razao_diferenca_periodo,  # Torna valores negativos mais negativos (forte penalidade)
        K_periodo_longo * razao_diferenca_periodo   # Torna valores positivos menos pronunciados (bônus suave)
    )

    # --- 3. Combinação dos Fatores e Escala pela Magnitude do Swell Secundário ---
    
    # Pesos que determinam a importância relativa de direção e período.
    # Ajuste-os conforme o que você considera mais crítico para o impacto.
    PESO_DIRECAO = 2.0  # Quão importante é o alinhamento da direção
    PESO_PERIODO = 3.0  # Quão importante é a adequação do período

    # Score base antes de considerar o tamanho do swell secundário
    # Um score positivo indica uma tendência de impacto positivo, negativo para impacto negativo.
    score_base_combinado = (PESO_DIRECAO * fator_alinhamento_direcao) + (PESO_PERIODO * fator_impacto_periodo)

    # O tamanho do swell secundário atua como um multiplicador.
    # Se o swell for muito pequeno, o 'X_final' será próximo de zero, resultando em tanh(X) ~ 0 (impacto nulo/irrelevante).
    # Se o swell for grande, ele amplifica o score_base_combinado, empurrando o tanh(X) para -1 ou 1.
    X_final = score_base_combinado * previsao_swell_secundario_tamanho

    # Calcula o score de impacto final usando a função tangente hiperbólica
    # Ela mapeia qualquer valor real de X_final para o intervalo [-1, 1].
    score_impacto = np.tanh(X_final)

    score_impacto = score_impacto * 100
    score_impacto = np.round(score_impacto, 2)

    return score_impacto