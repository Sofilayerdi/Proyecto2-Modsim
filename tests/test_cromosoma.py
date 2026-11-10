
from src.optimization.cromosoma import (
    RANGOS,
    crear_cromosoma,
    reparar_cromosoma,
    crear_poblacion,
)


def test_cromosoma_siete_genes():
    cromosoma = crear_cromosoma()

    assert len(cromosoma) == 7
    assert set(cromosoma) == set(RANGOS)


def test_genes_enteros_y_decimales():
    cromosoma = crear_cromosoma()

    enteros = [
        "bodega_s_dias",
        "bodega_S_dias",
        "horizonte_dias",
        "seguridad_dias",
        "hora_despacho",
    ]

    decimales = [
        "umbral_valor_q",
        "peso_trafico",
    ]

    for gen in enteros:
        assert isinstance(cromosoma[gen], int)

    for gen in decimales:
        assert isinstance(cromosoma[gen], float)


def test_reparar_nuevos_genes():
    cromosoma = {
        "bodega_s_dias": 18,
        "bodega_S_dias": 12,
        "horizonte_dias": 100,
        "seguridad_dias": -5,
        "umbral_valor_q": -10.0,
        "peso_trafico": 5.0,
        "hora_despacho": 30,
    }

    reparado = reparar_cromosoma(cromosoma)

    assert reparado["bodega_S_dias"] >= reparado["bodega_s_dias"]
    assert reparado["horizonte_dias"] == 7
    assert reparado["seguridad_dias"] == 0
    assert reparado["umbral_valor_q"] == 0.0
    assert reparado["peso_trafico"] == 2.0
    assert reparado["hora_despacho"] == 23


def test_restriccion_pronostico():
    for _ in range(100):
        cromosoma = crear_cromosoma()

        assert (
            cromosoma["horizonte_dias"]
            + cromosoma["seguridad_dias"]
            <= 14
        )
