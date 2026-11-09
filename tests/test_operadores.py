import pytest
from src.optimization.operadores import seleccion_torneo

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
