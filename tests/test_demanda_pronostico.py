import numpy as np

from src.simulation.demanda import generar_demanda
from src.simulation.pronostico import pronosticar


# --- demanda ------------------------------------------------------------------

def test_misma_semilla_misma_demanda():
    media = np.full((3, 2, 7), 4.0)
    dispersion = np.full((3, 2, 7), 2.0)
    a = generar_demanda(media, dispersion, 50, 0, semilla=7)
    b = generar_demanda(media, dispersion, 50, 0, semilla=7)
    c = generar_demanda(media, dispersion, 50, 0, semilla=8)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_media_cero_da_demanda_cero():
    dispersion = np.full((2, 1, 7), 3.0)
    assert generar_demanda(np.zeros((2, 1, 7)), dispersion, 30, 0, semilla=1).sum() == 0


def test_media_y_dispersion_de_la_demanda():
    media = np.full((2, 1, 7), 5.0)
    dispersion = np.ones((2, 1, 7))
    dispersion[1] = 3.0
    demanda = generar_demanda(media, dispersion, 20_000, 0, semilla=1)
    for i, esperada in [(0, 1.0), (1, 3.0)]:
        serie = demanda[:, i, 0]
        assert abs(serie.mean() - 5.0) < 0.1
        assert abs(serie.var() / serie.mean() - esperada) < 0.15


def test_demanda_sigue_el_dia_de_la_semana():
    media = np.zeros((1, 1, 7))
    media[0, 0, 5] = 10.0  # solo se vende el sábado
    demanda = generar_demanda(media, np.ones((1, 1, 7)), 14, dia_semana_inicial=0, semilla=3)
    vende = demanda[:, 0, 0] > 0
    assert set(np.flatnonzero(vende)) <= {5, 12}


# --- pronóstico ---------------------------------------------------------------

def test_sin_historia_usa_la_media_previa():
    media_previa = np.arange(7, dtype=float).reshape(1, 1, 7)
    historial = np.zeros((0, 1, 1))
    pronostico = pronosticar(historial, media_previa, 0, ventana_semanas=4, horizonte=7)
    assert np.allclose(pronostico[:, 0, 0], np.arange(7))


def test_con_historia_completa_promedia_el_mismo_dia_de_la_semana():
    semanas = 4
    historial = np.zeros((7 * semanas, 1, 1))
    historial[::7] = 8.0  # todos los lunes se vendieron 8
    media_previa = np.full((1, 1, 7), 100.0)
    pronostico = pronosticar(historial, media_previa, 0, ventana_semanas=semanas, horizonte=7)
    assert pronostico[0, 0, 0] == 8.0   # el día siguiente es lunes
    assert pronostico[1, 0, 0] == 0.0   # martes


def test_mezcla_historia_y_media_previa_al_inicio():
    historial = np.full((1, 1, 1), 4.0)  # solo se observó el día 0 (lunes)
    media_previa = np.full((1, 1, 7), 8.0)
    pronostico = pronosticar(historial, media_previa, 0, ventana_semanas=4, horizonte=7)
    assert pronostico[6, 0, 0] == (4.0 + 3 * 8.0) / 4  # el próximo lunes
