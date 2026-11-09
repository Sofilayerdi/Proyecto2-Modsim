import random

def seleccion_torneo(poblacion, fitness, k=3):
    """
    Selecciona un cromosoma mediante torneo y retorna una copia del ganador.

    Parámetros:
    poblacion: Lista de cromosomas.
    fitness: Lista de costos de cada cromosoma.
    k: Número de participantes del torneo.
    """

    if len(poblacion) != len(fitness):
        raise ValueError(
            "La población y el fitness deben tener el mismo tamaño"
        )

    if not 1 <= k <= len(poblacion):
        raise ValueError(
            "El tamaño del torneo debe estar entre 1 "
            "y el tamaño de la población"
        )

    # Seleccionar k índices aleatorios sin repetición
    participantes = random.sample(
        range(len(poblacion)),
        k
    )

    # Encontrar el índice del individuo con menor costo
    ganador = min(
        participantes,
        key=lambda i: fitness[i]
    )

    # Devolver una copia para proteger el original
    return poblacion[ganador].copy()
