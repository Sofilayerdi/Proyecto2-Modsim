import numpy as np


def dias_de_la_semana(horizonte: int, dia_semana_inicial: int) -> np.ndarray:
    return (dia_semana_inicial + np.arange(horizonte)) % 7


def generar_demanda(
    media: np.ndarray,
    dispersion: np.ndarray,
    horizonte: int,
    dia_semana_inicial: int,
    semilla: int,
    factor_demanda: float = 1.0,
) -> np.ndarray:
    """Demanda real (T, N, K). Depende solo de la semilla, nunca de la política."""
    rng = np.random.default_rng(semilla)

    dias = dias_de_la_semana(horizonte, dia_semana_inicial)
    mu = factor_demanda * np.moveaxis(media[:, :, dias], 2, 0)
    disp = np.moveaxis(dispersion[:, :, dias], 2, 0)

    demanda = np.zeros(mu.shape, dtype=np.int64)

    es_poisson = disp <= 1.0 + 1e-9
    demanda[es_poisson] = rng.poisson(mu[es_poisson])

    es_binomial_negativa = ~es_poisson & (mu > 0)
    p = 1.0 / disp[es_binomial_negativa]
    n = mu[es_binomial_negativa] / (disp[es_binomial_negativa] - 1.0)
    demanda[es_binomial_negativa] = rng.negative_binomial(n, p)

    return demanda
