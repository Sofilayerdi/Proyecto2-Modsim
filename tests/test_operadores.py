import pytest
from src.optimization.operadores import (
    seleccion_torneo,
    cruce_uniforme,
    mutacion_gaussiana,
)
from unittest.mock import patch
from src.model.tipos import TIPOS_TIENDA
from src.optimization.cromosoma import (
    crear_cromosoma,
    reparar_cromosoma,
    RANGOS,
)

def test_torneo_selecciona_menor_costo():
    poblacion = [
        {"gen": 1},
        {"gen": 2},
        {"gen": 3},
    ]

    fitness = [500, 200, 800]

    # Con k=3 participan todos
    ganador = seleccion_torneo(poblacion, fitness, k=3)

    assert ganador == {"gen": 2}


def test_torneo_no_modifica_original():
    poblacion = [
        {"gen": 1},
        {"gen": 2},
        {"gen": 3},
    ]

    fitness = [500, 200, 800]

    ganador = seleccion_torneo(poblacion, fitness, k=3)

    ganador["gen"] = 99

    assert poblacion[1]["gen"] == 2


def test_torneo_tamanos_diferentes():
    poblacion = [{"gen": 1}, {"gen": 2}]
    fitness = [100]

    with pytest.raises(ValueError):
        seleccion_torneo(poblacion, fitness)


def test_torneo_k_invalido():
    poblacion = [{"gen": 1}, {"gen": 2}]
    fitness = [100, 200]

    with pytest.raises(ValueError):
        seleccion_torneo(poblacion, fitness, k=3)


def test_torneo_k_cero():
    poblacion = [{"gen": 1}, {"gen": 2}]
    fitness = [100, 200]

    with pytest.raises(ValueError):
        seleccion_torneo(poblacion, fitness, k=0)

from src.optimization.cromosoma import (
    crear_cromosoma,
    RANGOS,
    reparar_cromosoma,
)


def test_mutacion_once_genes():
    cromosoma = crear_cromosoma()

    mutado = mutacion_gaussiana(cromosoma)

    assert set(mutado) == set(RANGOS)

    for gen, (minimo, maximo) in RANGOS.items():
        assert minimo <= mutado[gen] <= maximo

    assert mutado["bodega_S_dias"] >= mutado["bodega_s_dias"]

    for tipo in TIPOS_TIENDA:
        assert mutado[f"horizonte_dias_{tipo}"] + mutado[f"seguridad_dias_{tipo}"] <= 14


def test_mutacion_gen_decimal():
    cromosoma = {
        "bodega_s_dias": 10,
        "bodega_S_dias": 30,
        "horizonte_dias": 4,
        "seguridad_dias": 2,
        "umbral_valor_q": 50.0,
        "peso_trafico": 0.5,
        "hora_despacho": 10,
    }

    with patch(
        "src.optimization.operadores.random.choice",
        return_value="peso_trafico",
    ), patch(
        "src.optimization.operadores.random.gauss",
        return_value=0.15,
    ):
        mutado = mutacion_gaussiana(cromosoma)

    assert mutado["peso_trafico"] == pytest.approx(0.65)
    assert isinstance(mutado["peso_trafico"], float)


def test_mutacion_sigma_invalido():
    cromosoma = crear_cromosoma()

    with pytest.raises(ValueError):
        mutacion_gaussiana(cromosoma, sigma=-0.1)


def test_cruce_once_genes():
    padre1 = crear_cromosoma()
    padre2 = crear_cromosoma()

    hijo1, hijo2 = cruce_uniforme(padre1, padre2)

    for hijo in (hijo1, hijo2):
        assert set(hijo) == set(RANGOS)
        assert hijo["bodega_S_dias"] >= hijo["bodega_s_dias"]
        for tipo in TIPOS_TIENDA:
            assert hijo[f"horizonte_dias_{tipo}"] + hijo[f"seguridad_dias_{tipo}"] <= 14
