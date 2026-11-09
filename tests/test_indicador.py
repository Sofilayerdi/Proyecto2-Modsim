from types import SimpleNamespace

import numpy as np
import pytest

from src.model.indicador import (
    beneficio_producto, cobertura, exceso_donante, llegadas_previstas,
    parametros_politica, valor_traspaso,
)


def ejemplo():
    estado = SimpleNamespace(
        inventario=np.array([[30], [0]]), inventario_bodega=np.array([0]),
        llegadas_tiendas=np.zeros((7, 2, 1)),
    )
    pronostico = np.full((7, 2, 1), 2.0)
    config = {
        "reposicion": {"tiendas": {"tiempo_entrega_dias": 2, "dias_seguridad": 1, "dias_objetivo": 6}},
        "costos": {"viaje_fijo_q": 10, "viaje_por_km_q": 2},
    }
    return estado, pronostico, config


def test_cobertura_y_exceso_respetan_seguridad_y_exhibicion():
    assert np.isinf(cobertura([10], [0])[0])
    assert cobertura([10], [2])[0] == 5
    assert np.array_equal(exceso_donante(np.array([10, 10]), np.array([2, 0]), 3, 1, 3), [2, 7])


def test_valor_descuenta_tiempo_y_resta_riesgo_del_donante():
    e, p, _ = ejemplo()
    llegadas = np.zeros_like(p)
    temprano = beneficio_producto(e, p, llegadas, 0, 1, 0, 4, 1, 10, 3, 0.9)
    tarde = beneficio_producto(e, p, llegadas, 0, 1, 0, 4, 3, 10, 3, 0.9)
    assert temprano == pytest.approx(20 * 0.9 + 20 * 0.9**2)
    assert 0 < tarde < temprano
    e.inventario[0, 0] = 4
    riesgo = beneficio_producto(e, p, llegadas, 0, 1, 0, 4, 1, 10, 3, 0.9)
    assert riesgo == pytest.approx(temprano - 40)


def test_reposicion_antes_del_traspaso_elimina_beneficio():
    e, p, c = ejemplo()
    e.inventario_bodega[:] = 100
    llegadas = llegadas_previstas(e, p, c)
    assert llegadas[1, 1, 0] == 12
    assert beneficio_producto(e, p, llegadas, 0, 1, 0, 4, 3, 10, 5, 0.98) == 0


def test_pedidos_pendientes_y_bodega_limitada():
    e, p, c = ejemplo()
    e.inventario_bodega[:] = 3
    assert llegadas_previstas(e, p, c)[1, 1, 0] == 3
    e.llegadas_tiendas[0, 1, 0] = 20
    llegadas = llegadas_previstas(e, p, c)
    assert llegadas[:, 1, 0].sum() == 20


def test_valor_cobra_viaje_y_penalizacion_una_vez():
    _, _, config = ejemplo()
    assert valor_traspaso(100, 5, config) == 80
    config["politica"] = {"peso_trafico": 0.5}
    assert valor_traspaso(100, 5, config, factor=2) == 70


@pytest.mark.parametrize("params", [{"horizonte_dias": 0}, {"seguridad_dias": -1},
    {"descuento_diario": 1.1}, {"peso_trafico": float('nan')}])
def test_parametros_invalidos(params):
    with pytest.raises(ValueError):
        parametros_politica({"politica": params})
