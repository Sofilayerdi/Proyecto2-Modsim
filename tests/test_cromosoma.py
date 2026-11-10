
from src.optimization.cromosoma import (
    RANGOS,
    crear_cromosoma,
    reparar_cromosoma,
    crear_poblacion,
)
from src.model.tipos import TIPOS_TIENDA
import random
import pytest


def test_cromosoma_once_genes():
    cromosoma = crear_cromosoma()

    assert len(cromosoma) == 11
    assert set(cromosoma) == set(RANGOS)


def test_genes_enteros_y_decimales():
    cromosoma = crear_cromosoma()

    enteros = [
        "bodega_s_dias",
        "bodega_S_dias",
        *[f"{p}_{t}" for t in TIPOS_TIENDA for p in ("horizonte_dias", "seguridad_dias")],
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
    for tipo in TIPOS_TIENDA:
        assert reparado[f"horizonte_dias_{tipo}"] == 7
        assert reparado[f"seguridad_dias_{tipo}"] == 0
    assert reparado["umbral_valor_q"] == 0.0
    assert reparado["peso_trafico"] == 2.0
    assert reparado["hora_despacho"] == 23


def test_restriccion_pronostico():
    for _ in range(100):
        cromosoma = crear_cromosoma()

        for tipo in TIPOS_TIENDA:
            assert cromosoma[f"horizonte_dias_{tipo}"] + cromosoma[f"seguridad_dias_{tipo}"] <= 14


def test_reparacion_usa_horizonte_configurable_y_no_modifica_original():
    cromosoma = crear_cromosoma(random.Random(3))
    original = cromosoma.copy()
    reparado = reparar_cromosoma(cromosoma, horizonte_pronostico=3)
    assert cromosoma == original
    for tipo in TIPOS_TIENDA:
        assert reparado[f"horizonte_dias_{tipo}"] + reparado[f"seguridad_dias_{tipo}"] <= 3


def test_cromosoma_incompleto_no_se_rellena_silenciosamente():
    with pytest.raises(ValueError, match="11 genes"):
        reparar_cromosoma({"bodega_s_dias": 10})
