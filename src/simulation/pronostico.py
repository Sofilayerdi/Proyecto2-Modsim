import numpy as np


def pronosticar(
    historial: np.ndarray,
    media_previa: np.ndarray,
    dia_semana_inicial: int,
    ventana_semanas: int,
    horizonte: int,
) -> np.ndarray:
    """Promedio móvil por día de la semana para los días t+1 ... t+horizonte → (horizonte, N, K).

    historial son las ventas de los días 0..t; las semanas sin dato se rellenan con media_previa.
    """
    hoy = historial.shape[0] - 1
    por_dia_semana = np.empty((7,) + media_previa.shape[:2])

    for w in range(7):
        ultimo = hoy - (dia_semana_inicial + hoy - w) % 7
        dias = np.arange(ultimo, ultimo - 7 * ventana_semanas, -7)
        dias = dias[dias >= 0]
        semanas_sin_dato = ventana_semanas - len(dias)
        suma = historial[dias].sum(axis=0) + semanas_sin_dato * media_previa[:, :, w]
        por_dia_semana[w] = suma / ventana_semanas

    dias_futuros = (dia_semana_inicial + hoy + 1 + np.arange(horizonte)) % 7
    return por_dia_semana[dias_futuros]
