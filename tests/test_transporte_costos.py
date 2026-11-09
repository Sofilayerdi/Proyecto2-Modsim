import numpy as np
import pytest

from src.model.costos import costo_viaje
from src.model.transporte import (
    dias_transito, factor_trafico, matriz_distancias, tiempo_viaje_horas,
)


def test_distancias_conocidas_simetricas_y_factor_vial():
    puntos = [[0, 0], [0, 1], [0, 0]]
    distancias = matriz_distancias(puntos, factor_ruta=1)
    assert distancias[0, 1] == pytest.approx(111.195, abs=0.001)
    assert np.array_equal(distancias, distancias.T)
    assert np.all(np.diag(distancias) == 0)
    assert distancias[0, 2] == 0
    assert np.allclose(matriz_distancias(puntos), distancias * 1.3)


@pytest.mark.parametrize("puntos", [[[91, 0]], [[0, 181]], [[float('nan'), 0]], [0, 1]])
def test_coordenadas_invalidas(puntos):
    with pytest.raises(ValueError):
        matriz_distancias(puntos)


def test_franjas_limites_y_tiempo_con_trafico():
    franjas = [{"desde": 0, "hasta": 6, "factor": 1}, {"desde": 6, "hasta": 24, "factor": 2}]
    assert factor_trafico(5.99, franjas) == 1
    assert factor_trafico(6, franjas) == 2
    assert tiempo_viaje_horas(60, 30, factor_trafico(6, franjas)) == 4
    assert dias_transito(60, 30, 23, 2) == 2
    assert dias_transito(0, 30, 10) == 1


@pytest.mark.parametrize("franjas", [[], [{"desde": 1, "hasta": 24, "factor": 1}],
    [{"desde": 0, "hasta": 12, "factor": 1}, {"desde": 11, "hasta": 24, "factor": 2}]])
def test_franjas_incompletas_o_solapadas_fallan(franjas):
    with pytest.raises(ValueError):
        factor_trafico(10, franjas)


def test_costo_distancia_cero_solo_tiene_fijo():
    assert costo_viaje(0, 60, 4) == 60
    assert costo_viaje(10, 60, 4) == 100


@pytest.mark.parametrize("funcion,args", [(costo_viaje, (-1, 60, 4)),
    (tiempo_viaje_horas, (10, 0)), (factor_trafico, (24, [])),
    (matriz_distancias, ([[0, 0]], 0.5))])
def test_parametros_invalidos_fallan(funcion, args):
    with pytest.raises(ValueError):
        funcion(*args)
