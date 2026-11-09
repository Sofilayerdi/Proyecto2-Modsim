
from src.optimization.cromosoma import (
    RANGOS,
    crear_cromosoma,
    reparar_cromosoma,
    crear_poblacion,
)


def test_crear_cromosoma():
    cromosoma = crear_cromosoma()

    assert set(cromosoma) == set(RANGOS)

    for gen, (minimo, maximo) in RANGOS.items():
        assert minimo <= cromosoma[gen] <= maximo

    assert cromosoma["bodega_S_dias"] >= cromosoma["bodega_s_dias"]


def test_reparar_fuera_de_rango():
    cromosoma = {
        "bodega_s_dias": -10,
        "bodega_S_dias": 100,
    }

    reparado = reparar_cromosoma(cromosoma)

    assert reparado["bodega_s_dias"] == 5
    assert reparado["bodega_S_dias"] == 45


def test_reparar_restriccion():
    cromosoma = {
        "bodega_s_dias": 18,
        "bodega_S_dias": 12,
    }

    reparado = reparar_cromosoma(cromosoma)

    assert reparado["bodega_S_dias"] >= reparado["bodega_s_dias"]


def test_reparacion_no_modifica_original():
    cromosoma = {
        "bodega_s_dias": 18,
        "bodega_S_dias": 12,
    }

    reparar_cromosoma(cromosoma)

    assert cromosoma["bodega_S_dias"] == 12


def test_crear_poblacion():
    poblacion = crear_poblacion(30)

    assert len(poblacion) == 30

    for cromosoma in poblacion:
        assert cromosoma["bodega_S_dias"] >= cromosoma["bodega_s_dias"]
