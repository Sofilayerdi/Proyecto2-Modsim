import random

from src.optimization.algoritmo_genetico import algoritmo_genetico
from src.optimization.operadores import (
    cruce_uniforme,
    mutacion_gaussiana,
)

def simulador_controlado(config, params_politica, semilla):
    """
    Simulador artificial con óptimo conocido:
    s = 10, S = 30.
    """
    s = params_politica["bodega_s_dias"]
    S = params_politica["bodega_S_dias"]

    costo = (
        1000
        + 100 * (s - 10) ** 2
        + 100 * (S - 30) ** 2
    )

    # Ruido reproducible que depende de la semilla, pero no del cromosoma.
    ruido = random.Random(semilla).gauss(0, 10)

    return {
        "costo_total": costo + ruido,
        "nivel_servicio": 0.98,
    }


def test_genetico_encuentra_solucion_cercana():
    random.seed(42)

    resultado = algoritmo_genetico(
        config={},
        simulador=simulador_controlado,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=30,
        generaciones=50,
        semillas=range(1, 11),
        paciencia=10,
    )

    mejor = resultado["mejor_cromosoma"]

    assert abs(mejor["bodega_s_dias"] - 10) <= 2
    assert abs(mejor["bodega_S_dias"] - 30) <= 2


def test_genetico_respeta_restricciones():
    random.seed(42)

    resultado = algoritmo_genetico(
        config={},
        simulador=simulador_controlado,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=30,
        generaciones=50,
        semillas=range(1, 11),
    )

    mejor = resultado["mejor_cromosoma"]

    assert 5 <= mejor["bodega_s_dias"] <= 20
    assert 15 <= mejor["bodega_S_dias"] <= 45
    assert mejor["bodega_S_dias"] >= mejor["bodega_s_dias"]


def test_historial_convergencia():
    random.seed(42)

    resultado = algoritmo_genetico(
        config={},
        simulador=simulador_controlado,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=30,
        generaciones=50,
        semillas=range(1, 11),
    )

    historial = resultado["historial"]

    assert len(historial) > 0

    # El mejor fitness histórico nunca debe empeorar.
    assert all(
        historial[i] <= historial[i - 1]
        for i in range(1, len(historial))
    )

    assert resultado["generaciones_ejecutadas"] == len(historial)
