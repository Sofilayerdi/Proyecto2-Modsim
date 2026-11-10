import random

from src.optimization.optimizador import optimizar_politica
from src.optimization.cromosoma import RANGOS
from src.model.tipos import TIPOS_TIENDA


OBJETIVOS = {
    "bodega_s_dias": 10,
    "bodega_S_dias": 30,
    **{f"horizonte_dias_{t}": 4 for t in TIPOS_TIENDA},
    **{f"seguridad_dias_{t}": 2 for t in TIPOS_TIENDA},
    "umbral_valor_q": 50.0,
    "peso_trafico": 0.5,
    "hora_despacho": 10,
}


def simulador_prueba(config, params_politica, semilla):
    costo = 1000.0

    for gen, objetivo in OBJETIVOS.items():
        minimo, maximo = RANGOS[gen]
        diferencia = (
            params_politica[gen] - objetivo
        ) / (maximo - minimo)

        costo += 10000 * diferencia ** 2

    ruido = random.Random(semilla).gauss(0, 10)

    return {
        "costo_total": costo + ruido,
        "nivel_servicio": 0.98,
    }


def test_optimizador_completo():
    random.seed(42)

    resultado = optimizar_politica(
        config={},
        simulador=simulador_prueba,
        tamano_poblacion=30,
        generaciones=50,
    )

    assert len(resultado["mejor_cromosoma"]) == 11
    assert resultado["fitness_final"] > 0
    assert resultado["generaciones_ejecutadas"] >= 1
    assert len(resultado["candidatos_reevaluados"]) >= 1

    mejor = resultado["mejor_cromosoma"]

    for gen, (minimo, maximo) in RANGOS.items():
        assert minimo <= mejor[gen] <= maximo

    assert mejor["bodega_S_dias"] >= mejor["bodega_s_dias"]
    for tipo in TIPOS_TIENDA:
        assert mejor[f"horizonte_dias_{tipo}"] + mejor[f"seguridad_dias_{tipo}"] <= 14
