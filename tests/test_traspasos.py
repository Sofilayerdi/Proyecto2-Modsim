from copy import deepcopy
from itertools import product
from pathlib import Path

import numpy as np
import pytest

from src.model.indicador import exceso_donante
from src.model.traspasos import _carga_flujo, decidir_traspasos, decidir_traspasos_simple
from src.simulation.carga import cargar_config
from src.simulation.estado import Estado
from src.simulation.motor import simular_con_datos, validar_traspasos


@pytest.fixture
def escenario():
    config = cargar_config(Path(__file__).resolve().parents[1] / "config.yaml")
    config["productos"] = [{"id": "P1", "margen_q": 100}, {"id": "P2", "margen_q": 10}]
    config["costos"].update(viaje_fijo_q=10, viaje_por_km_q=2)
    config["transporte"].update(num_vehiculos=2, capacidad_unidades=8)
    config["distancias_km"] = np.ones((3, 3)) - np.eye(3)
    estado = Estado(
        dia=0, dia_semana=0, inventario=np.array([[50, 50], [0, 0], [0, 0]]),
        inventario_bodega=np.zeros(2, dtype=int),
        llegadas_tiendas=np.zeros((80, 3, 2), dtype=int),
        llegadas_bodega=np.zeros((80, 2), dtype=int),
        perdidas_acumuladas=np.zeros((3, 2), dtype=int),
    )
    return estado, np.full((14, 3, 2), 2.0), config


@pytest.mark.parametrize("politica", [decidir_traspasos, decidir_traspasos_simple])
def test_restricciones_consolidacion_y_no_mutacion(escenario, politica):
    estado, pronostico, config = escenario
    original = deepcopy(estado)
    pron_original = pronostico.copy()
    traspasos = politica(estado, pronostico, config)
    assert traspasos
    validar_traspasos(traspasos, estado.inventario, estado.dia, 2, 16, 81)
    viajes = {tr.viaje_id for tr in traspasos}
    assert len(viajes) <= 2
    enviados = np.zeros_like(estado.inventario)
    for viaje in viajes:
        lineas = [tr for tr in traspasos if tr.viaje_id == viaje]
        assert sum(tr.cantidad for tr in lineas) <= 8
        assert len({(tr.origen, tr.destino, tr.dia_llegada) for tr in lineas}) == 1
        assert sum(tr.costo for tr in lineas) == 12
        assert sum(tr.km for tr in lineas) == 1
    for tr in traspasos:
        enviados[tr.origen, tr.producto] += tr.cantidad
    assert np.all(enviados <= exceso_donante(original.inventario, pronostico[:3].mean(axis=0), 3, 2, 2))
    for campo in vars(estado):
        assert np.array_equal(getattr(estado, campo), getattr(original, campo))
    assert np.array_equal(pronostico, pron_original)
    assert "politica" not in config


def test_flujo_prioriza_margen_alto_con_capacidad_escasa(escenario):
    estado, pronostico, config = escenario
    config["transporte"].update(num_vehiculos=1, capacidad_unidades=4)
    traspasos = decidir_traspasos(estado, pronostico, config)
    assert len(traspasos) == 1
    assert traspasos[0].producto == 0
    assert traspasos[0].cantidad == 4


@pytest.mark.parametrize("capacidad", [1, 3, 4, 8])
def test_flujo_coincide_con_optimo_exhaustivo_de_una_carga(capacidad):
    curvas = {0: np.array([0, 9, 17, 18]), 1: np.array([0, 7, 13, 13])}
    carga = _carga_flujo(curvas, capacidad)
    optimo = max(curvas[0][a] + curvas[1][b]
                 for a, b in product(range(4), repeat=2) if a + b <= capacidad)
    assert sum(carga.values()) <= capacidad
    assert sum(curvas[k][q] for k, q in carga.items()) == optimo


def test_costo_fijo_compartido_hace_viable_consolidar(escenario):
    estado, pronostico, config = escenario
    pronostico[:] = 1 / 3
    config["productos"] = [{"id": "P1", "margen_q": 6}, {"id": "P2", "margen_q": 6}]
    config["costos"]["viaje_por_km_q"] = 0
    config["politica"] = {"descuento_diario": 1}
    config["transporte"]["num_vehiculos"] = 1
    traspasos = decidir_traspasos(estado, pronostico, config)
    assert len(traspasos) == 2  # Cada producto solo no paga el fijo de Q10; juntos sí.
    assert sum(tr.cantidad for tr in traspasos) == 2
    assert sum(tr.costo for tr in traspasos) == 10


def test_regla_simple_no_optimiza_valor_economico(escenario):
    estado, pronostico, config = escenario
    config["costos"]["viaje_fijo_q"] = 1_000_000
    assert decidir_traspasos(estado, pronostico, config) == []
    assert decidir_traspasos_simple(estado, pronostico, config)


@pytest.mark.parametrize("politica", [decidir_traspasos, decidir_traspasos_simple])
@pytest.mark.parametrize("caso", ["sin_demanda", "sin_exceso", "sin_vehiculos", "sin_capacidad", "llegada_tardia", "ya_en_camino"])
def test_no_envia_si_no_hay_oportunidad(escenario, politica, caso):
    estado, pronostico, config = escenario
    if caso == "sin_demanda":
        pronostico[:] = 0
    elif caso == "sin_exceso":
        estado.inventario[:] = 2
    elif caso == "sin_vehiculos":
        config["transporte"]["num_vehiculos"] = 0
    elif caso == "sin_capacidad":
        config["transporte"]["capacidad_unidades"] = 0
    elif caso == "llegada_tardia":
        config["distancias_km"][:] = 10_000
    else:
        estado.llegadas_tiendas[0, 1:] = 20
    assert politica(estado, pronostico, config) == []


def test_evitar_doble_envio_para_la_misma_demanda(escenario):
    estado, pronostico, config = escenario
    estado.inventario[2] = 50
    config["transporte"].update(num_vehiculos=8, capacidad_unidades=50)
    traspasos = decidir_traspasos(estado, pronostico, config)
    assert sum(tr.cantidad for tr in traspasos) == 12
    assert len({tr.viaje_id for tr in traspasos}) == 1


def test_umbral_y_genes_prevalecen_sobre_config(escenario):
    estado, pronostico, config = escenario
    assert decidir_traspasos(estado, pronostico, config)
    config["politica"] = {"umbral_valor_q": 10_000}
    assert decidir_traspasos(estado, pronostico, config) == []


def test_pronostico_corto_falla_explicando_contrato(escenario):
    estado, pronostico, config = escenario
    with pytest.raises(ValueError, match="no cubre"):
        decidir_traspasos(estado, pronostico[:2], config)


def test_trafico_retrasa_llegada_y_puede_hacer_inviable_el_viaje(escenario):
    estado, pronostico, config = escenario
    config["transporte"].update(num_vehiculos=1, velocidad_kmh=10)
    config["distancias_km"][:] = 200
    config["costos"].update(viaje_fijo_q=0, viaje_por_km_q=0)
    config["politica"] = {"hora_despacho": 0}
    normal = decidir_traspasos(estado, pronostico, config)
    assert normal and normal[0].dia_llegada == 1
    config["politica"]["hora_despacho"] = 17
    pesado = decidir_traspasos(estado, pronostico, config)
    assert pesado and pesado[0].dia_llegada == 3
    assert sum(tr.cantidad for tr in pesado) < sum(tr.cantidad for tr in normal)


@pytest.mark.parametrize("politica", [decidir_traspasos, decidir_traspasos_simple])
def test_restricciones_en_estados_heterogeneos(escenario, politica):
    estado, pronostico, config = escenario
    rng = np.random.default_rng(2026)
    config["transporte"].update(num_vehiculos=3, capacidad_unidades=9)
    for _ in range(20):
        estado.inventario[:] = rng.integers(0, 60, size=(3, 2))
        pronostico[:] = rng.uniform(0.1, 5, size=pronostico.shape)
        estado.llegadas_tiendas[:3] = rng.integers(0, 4, size=(3, 3, 2))
        traspasos = politica(estado, pronostico, config)
        validar_traspasos(traspasos, estado.inventario, 0, 2, 27, 81)
        enviados = np.zeros_like(estado.inventario)
        for tr in traspasos:
            enviados[tr.origen, tr.producto] += tr.cantidad
        exceso = exceso_donante(estado.inventario, pronostico[:3].mean(axis=0), 3, 2, 2)
        assert np.all(enviados <= exceso)
        for viaje in {tr.viaje_id for tr in traspasos}:
            assert sum(tr.cantidad for tr in traspasos if tr.viaje_id == viaje) <= 9


@pytest.mark.parametrize("politica", [decidir_traspasos, decidir_traspasos_simple])
def test_integracion_motor_conservacion_y_metricas_por_viaje(escenario, politica, monkeypatch):
    _, _, config = escenario
    config["simulacion"]["horizonte_dias"] = 30
    config["transporte"].update(num_vehiculos=2, capacidad_unidades=40)
    # Un pico conocido agota receptores hoy; el donante conserva stock.
    demanda = np.full((30, 3, 2), 4, dtype=int)
    demanda[0, 0] = 0
    demanda[0, 1:] = 40
    monkeypatch.setattr("src.simulation.motor.generar_demanda", lambda *args: demanda.copy())
    datos = {"ids_tiendas": ["T1", "T2", "T3"], "ids_productos": ["P1", "P2"],
             "ubicaciones": np.zeros((3, 2)), "media": np.full((3, 2, 7), 4.0),
             "dispersion": np.ones((3, 2, 7))}
    base = simular_con_datos(config, datos, None, 3, detalle=True)
    resultado = simular_con_datos(config, datos, {}, 3, detalle=True, decidir=politica)
    traspasos = resultado["detalle"]["traspasos"]
    assert traspasos  # La integración debe ejercitar transferencias reales.
    assert resultado["detalle"]["balance"]["sistema"] == 0
    assert np.array_equal(base["detalle"]["demanda"], resultado["detalle"]["demanda"])
    assert resultado["num_traspasos"] == len({tr.viaje_id for tr in traspasos})
    assert resultado["costo_traslado"] == pytest.approx(sum(tr.costo for tr in traspasos))
    assert resultado["km_recorridos"] == resultado["num_traspasos"]
    assert resultado["costo_traslado"] == 12 * resultado["num_traspasos"]
