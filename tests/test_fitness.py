
import pytest

from src.optimization.fitness import evaluar_cromosoma


def simulador_falso(config, params_politica, semilla):
    """Simulador de prueba con resultados controlados."""
    return {
        "costo_total": 10000 + semilla * 100,
        "nivel_servicio": 0.97,
    }


def test_fitness_sin_penalizacion():
    resultado = evaluar_cromosoma(
        cromosoma={"bodega_s_dias": 10},
        config={},
        semillas=[1, 2, 3],
        simulador=simulador_falso,
    )

    assert resultado == pytest.approx(10200)


def test_fitness_con_penalizacion():
    def simulador_bajo_servicio(
        config, params_politica, semilla
    ):
        return {
            "costo_total": 10000,
            "nivel_servicio": 0.90,
        }

    resultado = evaluar_cromosoma(
        cromosoma={},
        config={},
        semillas=[1, 2, 3],
        simulador=simulador_bajo_servicio,
    )

    assert resultado == pytest.approx(15000)


def test_fitness_multiples_replicas():
    semillas_recibidas = []

    def simulador_registro(config, params_politica, semilla):
        semillas_recibidas.append(semilla)
        return {
            "costo_total": 10000,
            "nivel_servicio": 1.0,
        }

    evaluar_cromosoma(
        cromosoma={},
        config={},
        semillas=[1, 2, 3],
        simulador=simulador_registro,
    )

    assert semillas_recibidas == [1, 2, 3]


def test_fitness_sin_semillas():
    with pytest.raises(ValueError):
        evaluar_cromosoma(
            cromosoma={},
            config={},
            semillas=[],
            simulador=simulador_falso,
        )
