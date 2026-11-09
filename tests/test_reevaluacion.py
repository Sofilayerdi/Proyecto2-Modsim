
import pytest
from src.optimization.reevaluacion import reevaluar_candidatos

def simulador_controlado(config, params_politica, semilla):
    s = params_politica["bodega_s_dias"]
    S = params_politica["bodega_S_dias"]

    costo = (
        1000
        + 100 * (s - 10) ** 2
        + 100 * (S - 30) ** 2
    )

    return {
        "costo_total": costo,
        "nivel_servicio": 0.98,
    }


def test_reevaluacion_elige_mejor():
    candidatos = [
        {"bodega_s_dias": 15, "bodega_S_dias": 40},
        {"bodega_s_dias": 10, "bodega_S_dias": 30},
        {"bodega_s_dias": 12, "bodega_S_dias": 35},
    ]

    resultado = reevaluar_candidatos(
        candidatos=candidatos,
        config={},
        simulador=simulador_controlado,
        semillas=[11, 12, 13],
    )

    assert resultado["mejor_cromosoma"] == {
        "bodega_s_dias": 10,
        "bodega_S_dias": 30,
    }

    assert resultado["mejor_fitness"] == pytest.approx(1000)


def test_reevaluacion_ordenada():
    candidatos = [
        {"bodega_s_dias": 15, "bodega_S_dias": 40},
        {"bodega_s_dias": 10, "bodega_S_dias": 30},
    ]

    resultado = reevaluar_candidatos(
        candidatos,
        {},
        simulador_controlado,
        semillas=[11, 12],
    )

    fitness = [
        item["fitness"]
        for item in resultado["resultados"]
    ]

    assert fitness == sorted(fitness)


def test_reevaluacion_sin_candidatos():
    with pytest.raises(ValueError):
        reevaluar_candidatos(
            candidatos=[],
            config={},
            simulador=simulador_controlado,
        )


def test_reevaluacion_sin_semillas():
    with pytest.raises(ValueError):
        reevaluar_candidatos(
            candidatos=[
                {"bodega_s_dias": 10, "bodega_S_dias": 30}
            ],
            config={},
            simulador=simulador_controlado,
            semillas=[],
        )
