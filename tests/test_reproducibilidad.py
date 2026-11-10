from concurrent.futures import ProcessPoolExecutor
import random

import pytest

from src.model.tipos import TIPOS_TIENDA
from src.optimization.cromosoma import RANGOS
from src.optimization.optimizador import optimizar_politica


def simulador_determinista(config, params_politica, semilla):
    return {"costo_total": sum((v - RANGOS[k][0]) ** 2 for k, v in params_politica.items()) + semilla,
            "nivel_servicio": 0.98}


def ejecutar(mapear=map):
    return optimizar_politica(
        {"pronostico": {"horizonte_dias": 4}}, simulador_determinista,
        tamano_poblacion=5, generaciones=4, semilla_genetico=73,
        semillas_entrenamiento=[1, 2], semillas_reevaluacion=[11, 12],
        semillas_finales=[1001, 1002], mapear=mapear,
    )


def test_semilla_local_reproduce_resultado_sin_alterar_rng_global():
    random.seed(1)
    estado = random.getstate()
    primero = ejecutar()
    assert random.getstate() == estado
    random.seed(999)
    segundo = ejecutar()
    assert primero == segundo
    assert primero["semillas"]["genetico"] == 73
    for tipo in TIPOS_TIENDA:
        c = primero["mejor_cromosoma"]
        assert c[f"horizonte_dias_{tipo}"] + c[f"seguridad_dias_{tipo}"] <= 4


def test_paralelismo_no_cambia_resultados():
    secuencial = ejecutar()
    with ProcessPoolExecutor(max_workers=2) as pool:
        paralelo = ejecutar(pool.map)
    assert paralelo == secuencial


def test_etapas_no_comparten_semillas():
    with pytest.raises(ValueError, match="independientes"):
        optimizar_politica({}, simulador_determinista, semillas_entrenamiento=[1, 2],
                          semillas_reevaluacion=[2, 3])


def test_historial_separa_costo_y_penalizacion():
    def servicio_bajo(config, params_politica, semilla):
        return {"costo_total": 1000.0, "nivel_servicio": 0.90}

    resultado = optimizar_politica({}, servicio_bajo, tamano_poblacion=3, generaciones=1)
    fila = resultado["historial_detallado"][0]
    assert fila["mejor_fitness"] == pytest.approx(6000)
    assert fila["mejor_costo_promedio"] == 1000
    assert fila["costo_penalizacion"] == pytest.approx(5000)
    assert [r["semilla"] for r in resultado["evaluacion_final"]["replicas"]] == list(range(1001, 1031))
