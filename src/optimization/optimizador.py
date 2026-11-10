from src.optimization.algoritmo_genetico import algoritmo_genetico
from src.optimization.operadores import (
    cruce_uniforme,
    mutacion_gaussiana,
)
from src.optimization.reevaluacion import reevaluar_candidatos
from src.optimization.fitness import evaluar_cromosoma

def optimizar_politica(
    config,
    simulador,
    tamano_poblacion=30,
    generaciones=50,
):
    """
    Ejecuta entrenamiento, reevaluación y evaluación final
    con semillas independientes.
    """

    # 1. Entrenamiento
    entrenamiento = algoritmo_genetico(
        config=config,
        simulador=simulador,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=tamano_poblacion,
        generaciones=generaciones,
        semillas=range(1, 11),
        cantidad_candidatos=5,
    )

    # 2. Reevaluación de los cinco mejores
    reevaluacion = reevaluar_candidatos(
        candidatos=entrenamiento["candidatos"],
        config=config,
        simulador=simulador,
        semillas=range(11, 41),
    )

    mejor = reevaluacion["mejor_cromosoma"]

    # 3. Evaluación final independiente
    fitness_final = evaluar_cromosoma(
        cromosoma=mejor,
        config=config,
        semillas=range(1001, 1031),
        simulador=simulador,
    )

    return {
        "mejor_cromosoma": mejor,
        "fitness_entrenamiento": entrenamiento["mejor_fitness"],
        "fitness_reevaluacion": reevaluacion["mejor_fitness"],
        "fitness_final": fitness_final,
        "historial": entrenamiento["historial"],
        "generaciones_ejecutadas": entrenamiento[
            "generaciones_ejecutadas"
        ],
        "candidatos_reevaluados": reevaluacion["resultados"],
    }
