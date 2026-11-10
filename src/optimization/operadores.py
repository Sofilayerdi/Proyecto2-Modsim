
import random

from src.optimization.cromosoma import (
    RANGOS,
    reparar_cromosoma,
)


def seleccion_torneo(poblacion, fitness, k=3):
    """
    Selecciona un cromosoma mediante torneo y retorna
    una copia del ganador.

    Gana el individuo con menor fitness (costo).
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

    # Seleccionar k individuos aleatoriamente
    participantes = random.sample(
        range(len(poblacion)),
        k
    )

    # Encontrar el individuo con menor costo
    ganador = min(
        participantes,
        key=lambda i: fitness[i]
    )

    # Devolver una copia para proteger el original
    return poblacion[ganador].copy()

def cruce_uniforme(padre1, padre2):
    """
    Combina los genes de dos padres para generar
    dos hijos mediante cruce uniforme.

    Cada gen tiene probabilidad de 0.5 de
    heredarse de cualquiera de los padres.
    """

    hijo1 = {}
    hijo2 = {}

    for gen in RANGOS:

        if random.random() < 0.5:
            hijo1[gen] = padre1[gen]
            hijo2[gen] = padre2[gen]
        else:
            hijo1[gen] = padre2[gen]
            hijo2[gen] = padre1[gen]

    # Reparar posibles restricciones incumplidas
    hijo1 = reparar_cromosoma(hijo1)
    hijo2 = reparar_cromosoma(hijo2)

    return hijo1, hijo2


def mutacion_gaussiana(cromosoma, sigma=0.10):
    """
    Muta un gen aleatorio mediante una perturbación
    gaussiana proporcional al rango del gen.

    sigma representa una fracción del rango total.
    """

    if not 0 <= sigma:
        raise ValueError("Sigma no puede ser negativo")

    mutado = cromosoma.copy()

    # Seleccionar un gen aleatoriamente
    gen = random.choice(list(RANGOS.keys()))

    minimo, maximo = RANGOS[gen]

    # Calcular desviación según el rango del gen
    amplitud = maximo - minimo
    desviacion = sigma * amplitud

    perturbacion = random.gauss(0, desviacion)

    # Modificar el gen seleccionado
    mutado[gen] += perturbacion

    # Reparar restricciones
    return reparar_cromosoma(mutado)
