import random

from src.optimization.algoritmo_genetico import algoritmo_genetico
from src.optimization.operadores import (
    cruce_uniforme,
    mutacion_gaussiana,
)
from src.optimization.cromosoma import RANGOS

def simulador_controlado(config, params_politica, semilla):
    """
    Simulador artificial con óptimo conocido.
    Evalúa los siete genes del cromosoma.
    """

    objetivos = {
        "bodega_s_dias": 10,
        "bodega_S_dias": 30,
        "horizonte_dias": 4,
        "seguridad_dias": 2,
        "umbral_valor_q": 50.0,
        "peso_trafico": 0.5,
        "hora_despacho": 10,
    }

    costo = 1000.0

    for gen, objetivo in objetivos.items():
        minimo, maximo = RANGOS[gen]

        # Normalizar diferencias para comparar genes
        # con escalas diferentes.
        diferencia = (
            params_politica[gen] - objetivo
        ) / (maximo - minimo)

        costo += 10000 * diferencia ** 2

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
        tamano_poblacion=40,
        generaciones=100,
        semillas=range(1, 11),
        paciencia=20,
    )

    mejor = resultado["mejor_cromosoma"]

    assert abs(mejor["bodega_s_dias"] - 10) <= 3
    assert abs(mejor["bodega_S_dias"] - 30) <= 5
    assert abs(mejor["horizonte_dias"] - 4) <= 2
    assert abs(mejor["seguridad_dias"] - 2) <= 2
    assert abs(mejor["umbral_valor_q"] - 50) <= 30
    assert abs(mejor["peso_trafico"] - 0.5) <= 0.3
    assert abs(mejor["hora_despacho"] - 10) <= 4

def test_genetico_respeta_restricciones():
    random.seed(42)

    resultado = algoritmo_genetico(
        config={},
        simulador=simulador_controlado,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=30,
        generaciones=30,
        semillas=range(1, 11),
    )

    mejor = resultado["mejor_cromosoma"]

    for gen, (minimo, maximo) in RANGOS.items():
        assert minimo <= mejor[gen] <= maximo

    assert mejor["bodega_S_dias"] >= mejor["bodega_s_dias"]

    assert (
        mejor["horizonte_dias"]
        + mejor["seguridad_dias"]
        <= 14
    )

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
