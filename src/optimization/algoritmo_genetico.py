import random

from src.optimization.cromosoma import (
    crear_poblacion,
    reparar_cromosoma,
)
from src.optimization.operadores import seleccion_torneo
from src.optimization.fitness import evaluar_cromosoma

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

    if paciencia < 1:
        raise ValueError("La paciencia debe ser positiva")

    semillas = tuple(semillas)

    if not semillas:
        raise ValueError("Debe existir al menos una semilla")

    poblacion = crear_poblacion(tamano_poblacion)

    mejor_cromosoma = None
    mejor_fitness = float("inf")
    sin_mejora = 0
    historial = []

    for generacion in range(generaciones):

        fitness = [
            evaluar_cromosoma(
                cromosoma,
                config,
                semillas,
                simulador,
            )
            for cromosoma in poblacion
        ]

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

        if sin_mejora >= paciencia:
            break

        # Conservar los mejores individuos
        nueva_poblacion = [
            poblacion[i].copy()
            for i in indices_ordenados[:elitismo]
        ]

        while len(nueva_poblacion) < tamano_poblacion:

            padre1 = seleccion_torneo(poblacion, fitness)
            padre2 = seleccion_torneo(poblacion, fitness)

            if random.random() < prob_cruce:
                hijo1, hijo2 = cruzar(padre1, padre2)
            else:
                hijo1 = padre1.copy()
                hijo2 = padre2.copy()

            hijos = [hijo1, hijo2]

            for hijo in hijos:
                if random.random() < prob_mutacion:
                    hijo = mutar(hijo)

                hijo = reparar_cromosoma(hijo)

                if len(nueva_poblacion) < tamano_poblacion:
                    nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    return {
        "mejor_cromosoma": mejor_cromosoma,
        "mejor_fitness": mejor_fitness,
        "historial": historial,
        "generaciones_ejecutadas": len(historial),
    }
