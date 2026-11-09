import numpy as np
import pytest

from src.simulation.estado import Traspaso
from src.simulation.motor import METRICAS, simular_con_datos


def config_prueba(**cambios) -> dict:
    config = {
        "simulacion": {"horizonte_dias": 60, "dia_semana_inicial": 0},
        "productos": [{"id": "P1", "margen_q": 10.0}, {"id": "P2", "margen_q": 50.0}],
        "costos": {"mantener_q_unidad_dia": 0.1, "viaje_fijo_q": 50.0, "viaje_por_km_q": 3.0},
        "transporte": {"num_vehiculos": 1, "capacidad_unidades": 100},
        "inventario": {
            "minimo_exhibicion_unidades": 2,
            "inicial": {"dias_cobertura_tienda": 5, "dias_cobertura_bodega": 15},
        },
        "reposicion": {
            "tiendas": {"tiempo_entrega_dias": 2, "dias_seguridad": 2, "dias_objetivo": 8},
            "bodega": {"tiempo_entrega_dias": 5, "s_dias": 8, "S_dias": 20},
        },
        "pronostico": {"ventana_semanas": 4, "horizonte_dias": 7},
    }
    for seccion, valores in cambios.items():
        config[seccion] = {**config[seccion], **valores}
    return config


def datos_prueba(media=4.0, dispersion=2.0, num_tiendas=3) -> dict:
    forma = (num_tiendas, 2, 7)
    return {
        "ids_tiendas": [f"T{i}" for i in range(num_tiendas)],
        "ids_productos": ["P1", "P2"],
        "ubicaciones": np.zeros((num_tiendas, 2)),
        "media": np.full(forma, media),
        "dispersion": np.full(forma, dispersion),
    }


def politica_de_prueba(estado, pronostico, config):
    """Cada día manda 1 unidad del producto 0 de la tienda 0 a la tienda 1 si le sobra."""
    if estado.inventario[0, 0] > 10:
        return [Traspaso(0, 1, 0, 1, estado.dia + 1, costo=20.0, km=4.0)]
    return []


def test_devuelve_todas_las_metricas():
    resultado = simular_con_datos(config_prueba(), datos_prueba(), None, semilla=1)
    assert set(METRICAS) <= set(resultado)
    assert resultado["costo_total"] == pytest.approx(
        resultado["costo_inventario"] + resultado["costo_traslado"] + resultado["costo_ventas_perdidas"]
    )


@pytest.mark.parametrize("decidir", [None, politica_de_prueba])
def test_conservacion_de_unidades(decidir):
    params = None if decidir is None else {}
    resultado = simular_con_datos(config_prueba(), datos_prueba(), params, 1, detalle=True, decidir=decidir)
    balance = resultado["detalle"]["balance"]
    assert np.all(balance["tiendas"] == 0)
    assert np.all(balance["bodega"] == 0)
    assert balance["sistema"] == 0


def test_inventario_nunca_negativo():
    resultado = simular_con_datos(config_prueba(), datos_prueba(media=9.0, dispersion=4.0), None, 2, detalle=True)
    assert resultado["detalle"]["inventario_tiendas"].min() >= 0
    assert resultado["detalle"]["inventario_bodega"].min() >= 0


def test_demanda_cero_da_ventas_cero():
    resultado = simular_con_datos(config_prueba(), datos_prueba(media=0.0), None, 3, detalle=True)
    assert resultado["detalle"]["ventas"].sum() == 0
    assert resultado["unidades_perdidas"] == 0
    assert resultado["nivel_servicio"] == 1.0


def test_inventario_muy_grande_no_pierde_ventas():
    config = config_prueba(simulacion={"horizonte_dias": 30})
    config["inventario"]["inicial"] = {"dias_cobertura_tienda": 1000, "dias_cobertura_bodega": 1000}
    resultado = simular_con_datos(config, datos_prueba(), None, 4)
    assert resultado["unidades_perdidas"] == 0
    assert resultado["nivel_servicio"] == 1.0


def test_misma_semilla_mismos_resultados():
    a = simular_con_datos(config_prueba(), datos_prueba(), None, 5)
    b = simular_con_datos(config_prueba(), datos_prueba(), None, 5)
    assert a == b


def test_misma_semilla_con_distinta_politica_misma_demanda():
    base = simular_con_datos(config_prueba(), datos_prueba(), None, 6, detalle=True)
    con_traspasos = simular_con_datos(config_prueba(), datos_prueba(), {}, 6, detalle=True, decidir=politica_de_prueba)
    assert con_traspasos["num_traspasos"] > 0
    assert np.array_equal(base["detalle"]["demanda"], con_traspasos["detalle"]["demanda"])


def test_traspasos_suman_costo_y_km():
    resultado = simular_con_datos(config_prueba(), datos_prueba(), {}, 7, decidir=politica_de_prueba)
    assert resultado["costo_traslado"] == pytest.approx(20.0 * resultado["num_traspasos"])
    assert resultado["km_recorridos"] == pytest.approx(4.0 * resultado["num_traspasos"])


def test_params_sin_politica_conectada_falla():
    with pytest.raises(ValueError, match="decidir_traspasos"):
        simular_con_datos(config_prueba(), datos_prueba(), {}, 1)


def test_traspaso_bajo_minimo_de_exhibicion_falla():
    def vaciar_tienda(estado, pronostico, config):
        cantidad = int(estado.inventario[0, 0])
        return [Traspaso(0, 1, 0, cantidad, estado.dia + 1)] if cantidad > 0 else []

    with pytest.raises(ValueError, match="mínimo de exhibición"):
        simular_con_datos(config_prueba(), datos_prueba(), {}, 1, decidir=vaciar_tienda)


def test_traspaso_sobre_capacidad_falla():
    def demasiado(estado, pronostico, config):
        return [Traspaso(0, 1, 0, 101, estado.dia + 1)]

    config = config_prueba()
    config["inventario"]["inicial"]["dias_cobertura_tienda"] = 100
    with pytest.raises(ValueError, match="capacidad"):
        simular_con_datos(config, datos_prueba(), {}, 1, decidir=demasiado)


def test_traspaso_que_llega_hoy_falla():
    def mismo_dia(estado, pronostico, config):
        return [Traspaso(0, 1, 0, 1, estado.dia)]

    with pytest.raises(ValueError, match="posterior"):
        simular_con_datos(config_prueba(), datos_prueba(), {}, 1, decidir=mismo_dia)


def test_genes_de_bodega_reemplazan_al_config():
    """Con s y S de bodega en cero, la bodega nunca compra y se acaba: hay más ventas perdidas."""
    def sin_traspasos(estado, pronostico, config):
        return []

    base = simular_con_datos(config_prueba(), datos_prueba(), None, 8)
    sin_compras = simular_con_datos(
        config_prueba(), datos_prueba(), {"bodega_s_dias": 0, "bodega_S_dias": 0}, 8, decidir=sin_traspasos
    )
    assert sin_compras["unidades_perdidas"] > base["unidades_perdidas"]
