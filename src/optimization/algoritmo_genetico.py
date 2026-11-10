import random

from src.optimization.cromosoma import (
    crear_poblacion,
    reparar_cromosoma,
)
from src.optimization.operadores import seleccion_torneo, cruce_uniforme, mutacion_gaussiana
from src.optimization.fitness import evaluar_replicas


def _evaluar_tarea(tarea):
    """Función importable para map secuencial o ProcessPoolExecutor.map."""
    cromosoma, config, semillas, simulador = tarea
    return evaluar_replicas(cromosoma, config, semillas, simulador)

def algoritmo_genetico(
    config,
    simulador,
    cruzar,
    mutar,
    tamano_poblacion=30,
    generaciones=50,
    semillas=range(1, 11),
    prob_cruce=0.85,
    prob_mutacion=0.10,
    elitismo=2,
    paciencia=10,
    cantidad_candidatos=5,
    semilla_genetico=2026,
    mapear=map,
    progreso=None,
):
    """
    Optimiza los parámetros de la política mediante
    un algoritmo genético con restricciones.

    cruzar(padre1, padre2) -> (hijo1, hijo2)
    mutar(cromosoma) -> cromosoma_mutado
    """

    if tamano_poblacion < 3:
        raise ValueError("La población debe tener al menos 3 individuos")

    if generaciones < 1:
        raise ValueError("Debe existir al menos una generación")

    if not 0 <= prob_cruce <= 1:
        raise ValueError("Probabilidad de cruce inválida")

    if not 0 <= prob_mutacion <= 1:
        raise ValueError("Probabilidad de mutación inválida")

    if not 0 <= elitismo < tamano_poblacion:
        raise ValueError("El elitismo debe ser menor que la población")

    if not isinstance(cantidad_candidatos, int) or cantidad_candidatos < 1:
        raise ValueError(
            "La cantidad de candidatos debe ser un entero positivo"
        )

    if paciencia < 1:
        raise ValueError("La paciencia debe ser positiva")

    semillas = tuple(semillas)

    if not semillas:
        raise ValueError("Debe existir al menos una semilla")

    rng = random.Random(semilla_genetico)
    horizonte_pronostico = int(config.get("pronostico", {}).get("horizonte_dias", 14))
    poblacion = crear_poblacion(tamano_poblacion, rng, horizonte_pronostico)

    mejor_cromosoma = None
    mejor_fitness = float("inf")
    sin_mejora = 0
    historial = []
    candidatos = {}
    cache = {}
    historial_detallado = []

    for generacion in range(generaciones):

        claves = [tuple(sorted(c.items())) for c in poblacion]
        nuevos = {clave: c for clave, c in zip(claves, poblacion) if clave not in cache}
        tareas = [(c, config, semillas, simulador) for c in nuevos.values()]
        for clave, evaluacion in zip(nuevos, mapear(_evaluar_tarea, tareas)):
            cache[clave] = evaluacion
        fitness = [cache[clave]["fitness"] for clave in claves]

        for cromosoma, costo in zip(poblacion, fitness):
            clave = tuple(sorted(cromosoma.items()))

            if (
                clave not in candidatos
                or costo < candidatos[clave]["fitness_entrenamiento"]
            ):
                candidatos[clave] = {
                    "cromosoma": cromosoma.copy(),
                    "fitness_entrenamiento": costo,
                }

        # Mantener los mejores candidatos distintos
        mejores = sorted(
            candidatos.items(),
            key=lambda item: item[1]["fitness_entrenamiento"]
        )[:cantidad_candidatos]

        candidatos = dict(mejores)

        indices_ordenados = sorted(
            range(len(poblacion)),
            key=lambda i: fitness[i]
        )

        indice_mejor = indices_ordenados[0]
        costo_generacion = fitness[indice_mejor]

        if costo_generacion < mejor_fitness:
            mejor_fitness = costo_generacion
            mejor_cromosoma = poblacion[indice_mejor].copy()
            sin_mejora = 0
        else:
            sin_mejora += 1

        historial.append(mejor_fitness)
        evaluacion_mejor = cache[tuple(sorted(mejor_cromosoma.items()))]
        historial_detallado.append({
            "generacion": generacion + 1,
            "mejor_fitness": mejor_fitness,
            "mejor_costo_promedio": evaluacion_mejor["costo_promedio"],
            "mejor_servicio_promedio": evaluacion_mejor["servicio_promedio"],
            "costo_penalizacion": evaluacion_mejor["costo_penalizacion"],
            "fitness_promedio_poblacion": sum(fitness) / len(fitness),
            "candidatos_unicos_evaluados": len(cache),
        })
        if progreso is not None:
            progreso({"historial": historial_detallado.copy(),
                      "mejor_cromosoma": mejor_cromosoma.copy(),
                      "semilla_genetico": semilla_genetico,
                      "semillas_demanda": semillas})

        if sin_mejora >= paciencia:
            break

        # Conservar los mejores individuos
        nueva_poblacion = [
            poblacion[i].copy()
            for i in indices_ordenados[:elitismo]
        ]

        while len(nueva_poblacion) < tamano_poblacion:

            padre1 = seleccion_torneo(poblacion, fitness, rng=rng)
            padre2 = seleccion_torneo(poblacion, fitness, rng=rng)

            if rng.random() < prob_cruce:
                if cruzar is cruce_uniforme:
                    hijo1, hijo2 = cruzar(padre1, padre2, rng=rng, horizonte_pronostico=horizonte_pronostico)
                else:
                    hijo1, hijo2 = cruzar(padre1, padre2)
            else:
                hijo1 = padre1.copy()
                hijo2 = padre2.copy()

            hijos = [hijo1, hijo2]

            for hijo in hijos:
                if rng.random() < prob_mutacion:
                    if mutar is mutacion_gaussiana:
                        hijo = mutar(hijo, rng=rng, horizonte_pronostico=horizonte_pronostico)
                    else:
                        hijo = mutar(hijo)

                hijo = reparar_cromosoma(hijo, horizonte_pronostico)

                if len(nueva_poblacion) < tamano_poblacion:
                    nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    return {
        "mejor_cromosoma": mejor_cromosoma,
        "mejor_fitness": mejor_fitness,
        "historial": historial,
        "generaciones_ejecutadas": len(historial),
        "historial_detallado": historial_detallado,
        "semilla_genetico": semilla_genetico,
        "semillas_demanda": list(semillas),
        "candidatos_unicos_evaluados": len(cache),
        "motivo_paro": "sin_mejora" if sin_mejora >= paciencia else "max_generaciones",
        "candidatos": [
            item["cromosoma"].copy()
            for item in candidatos.values()
        ],
    }
