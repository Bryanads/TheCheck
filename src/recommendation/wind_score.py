import numpy as np

def calcular_score_vento(
    wind_speed,
    wind_dir,
    preferred_wind_dir,
    ideal_wind_speed,
    max_wind_speed
):
    """
    Calcula um score para as condições de vento, baseando-se na velocidade e direção.

    Args:
        wind_speed (float or np.ndarray): Velocidade atual do vento.
        wind_dir (float or np.ndarray): Direção atual do vento em graus.
        preferred_wind_dir (float): Direção de vento ideal em graus.
        ideal_wind_speed (float): Velocidade de vento considerada ideal para o score máximo.
        max_wind_speed (float): Velocidade máxima do vento para considerar na escala.

    Returns:
        float or np.ndarray: Score do vento, entre 0 e 1.
    """

    # Converter para arrays numpy para operações vetorizadas, se ainda não forem, e garantir float
    wind_speed = np.asarray(wind_speed, dtype=float)
    wind_dir = np.asarray(wind_dir, dtype=float)
    preferred_wind_dir = float(preferred_wind_dir) # Converter para float
    ideal_wind_speed = float(ideal_wind_speed)     # Converter para float
    max_wind_speed = float(max_wind_speed)         # Converter para float


    # Normalizar ângulos para estarem entre 0 e 360
    wind_dir = np.mod(wind_dir, 360)
    preferred_wind_dir = np.mod(preferred_wind_dir, 360)

    # Calcular a diferença angular mínima entre as direções
    # Isso lida com a transição de 360 para 0 graus
    angle_diff = np.abs(wind_dir - preferred_wind_dir)
    angle_diff = np.minimum(angle_diff, 360 - angle_diff)

    # Definir um limiar para considerar o vento "ideal" em termos de direção
    # Por exemplo, 45 graus de diferença (22.5 para cada lado)
    # Você pode ajustar este valor conforme a necessidade.
    threshold_ideal_dir = 45  # Graus

    # Criar uma máscara booleana para quando a direção é considerada ideal
    is_ideal_direction = angle_diff <= threshold_ideal_dir

    # Inicializar o array de scores com zeros
    scores = np.zeros_like(wind_speed, dtype=float)

    ### Cálculo para Vento com Direção Ideal (Curva Verde) ###
    # Para velocidades menores ou iguais à ideal_wind_speed
    mask_ideal_dir_and_low_speed = is_ideal_direction & (wind_speed <= ideal_wind_speed)
    # Aumenta linearmente de 0.9 para 1.0
    # Adicionado pequena constante para evitar divisão por zero se ideal_wind_speed for 0
    scores[mask_ideal_dir_and_low_speed] = 0.9 + 0.1 * (wind_speed[mask_ideal_dir_and_low_speed] / (ideal_wind_speed + 1e-6))

    # Para velocidades maiores que ideal_wind_speed (decaindo)
    mask_ideal_dir_and_high_speed = is_ideal_direction & (wind_speed > ideal_wind_speed)
    if np.any(mask_ideal_dir_and_high_speed):
        # A curva decai de 1.0. Podemos usar uma função sigmoide ou exponencial decrescente.
        # Vamos tentar uma função exponencial decrescente para simular o decaimento após o pico.
        # Ajuste a taxa de decaimento (o coeficiente de 0.5 abaixo) para moldar a curva.
        decay_factor_ideal = 0.5 # Ajuste este valor para controlar a queda
        # Garante que o score caia gradualmente em direção a 0.5 (ou outro valor mínimo) para ventos muito fortes.
        # Adicionado pequena constante para evitar divisão por zero se (max_wind_speed - ideal_wind_speed) for 0
        denominator = (max_wind_speed - ideal_wind_speed)
        if denominator == 0: # Caso max_wind_speed == ideal_wind_speed
            scores[mask_ideal_dir_and_high_speed] = 0.2 # Definir um valor mínimo razoável
        else:
            scores[mask_ideal_dir_and_high_speed] = 1.0 * np.exp(-decay_factor_ideal * (wind_speed[mask_ideal_dir_and_high_speed] - ideal_wind_speed) / denominator)
            # Para garantir que o score não vá abaixo de um mínimo razoável (ex: 0.2 para ventos muito fortes mas ainda na direção)
            scores[mask_ideal_dir_and_high_speed] = np.maximum(scores[mask_ideal_dir_and_high_speed], 0.2)


    ### Cálculo para Vento com Direção Não Ideal (Curva Vermelha) ###
    mask_non_ideal_dir = ~is_ideal_direction # Onde a direção NÃO é ideal
    if np.any(mask_non_ideal_dir):
        # A curva começa em 0.8 para velocidade 0 e decai.
        # Usaremos uma função exponencial decrescente para simular essa queda.
        decay_factor_non_ideal = 1.5 # Ajuste este valor para controlar a queda, geralmente mais acentuada
        # Adicionado pequena constante para evitar divisão por zero se max_wind_speed for 0
        denominator_non_ideal = max_wind_speed
        if denominator_non_ideal == 0:
            scores[mask_non_ideal_dir] = 0.1 # Definir um valor mínimo
        else:
            scores[mask_non_ideal_dir] = 0.8 * np.exp(-decay_factor_non_ideal * (wind_speed[mask_non_ideal_dir] / denominator_non_ideal))
            # Garantir que o score não caia abaixo de 0.1 para ventos muito fortes e ruins
            scores[mask_non_ideal_dir] = np.maximum(scores[mask_non_ideal_dir], 0.1)

    # Garantir que o score esteja sempre entre 0 e 1
    scores = np.clip(scores, 0.0, 1.0)

    scores = scores * 100
    scores = np.round(scores, 2)

    return scores