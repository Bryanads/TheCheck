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
    score = np.zeros_like(previsao_onda, dtype=float)
    
    ##################################################################################################################
    # Calculo do lado esquerdo (Ondas menores ou iguais ao tamanho ideal):
    if (previsao_onda <= tamanho_ideal):
        k1 = (tamanho_ideal - tamanho_minimo)
        score = np.exp(-k1 * (tamanho_ideal - previsao_onda)**2)
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
        return score
    
    ##################################################################################################################
    # Calculo do lado direito(Ondas maiores que o tamanho ideal): 
    else:     
        if (tamanho_maximo - tamanho_ideal) >= 1.0:
            # Se a diferença entre tamanho máximo e tamanho ideal for maior ou igual a 1m, a curva será mais suave no início
            p_direita = 6 
        else:
            # Se a diferença entre tamanho máximo e tamanho ideal for menor que 1m, a curva será menos suave no início 
            p_direita = 3 

        # epsilon: Score desejado no tamanho_maximo.
        epsilon = 0.1

        denominador = (tamanho_maximo - tamanho_ideal)**p_direita

        if denominador == 0:
            k2 = 1.0
        else:
            k2 = -np.log(epsilon) / denominador
            """
            k2 = -log(epsilon) / (tamanho_maximo - tamanho_ideal)**p_direita
            """
        
        score = np.exp(-k2 * (previsao_onda - tamanho_ideal)**p_direita)
        """
        Função exponencial polinomial:
        f(x) = exp(-k2 * (x - tamanho_ideal)^p_direita)
        Onde:
        - f(x) é o score calculado.
        - k2 é uma constante de proporcionalidade que determina a suavidade da curva.
        - p_direita é o grau do polinômio que determina a suavidade da curva.
        - tamanho_ideal é o tamanho ideal da onda.
        - x é o tamanho da onda previsto.
        """
        return score
