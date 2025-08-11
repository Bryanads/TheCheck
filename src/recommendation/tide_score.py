import numpy as np

def calcular_score_mare(previsao_mare, mare_ideal, mare_tipo_previsao, mare_tipo_ideal):
    previsao_mare = np.asarray(previsao_mare, dtype=float)
    dist_rel = np.abs(previsao_mare - mare_ideal) / mare_ideal
    fator_escala = 3.0  # controla a inclinação da queda

    # Removi o clip em 0.8, para não ter platô no topo
    score_altura = 1 - np.tanh(dist_rel * fator_escala)
    score_altura = np.clip(score_altura, 0, 1)  # Limita só para não passar de 1

    bonus_tipo = np.where(np.array(mare_tipo_previsao) == mare_tipo_ideal, 0.2, 0.0)

    score_total = score_altura + bonus_tipo
    return np.clip(score_total, 0, 1)