from src.optimization.algoritmo_genetico import algoritmo_genetico
from src.optimization.operadores import (
    cruce_uniforme,
    mutacion_gaussiana,
)
from src.optimization.reevaluacion import reevaluar_candidatos
from src.optimization.fitness import evaluar_replicas

def optimizar_politica(
    config,
    simulador,
    tamano_poblacion=30,
    generaciones=50,
    semilla_genetico=2026,
    semillas_entrenamiento=range(1, 11),
    semillas_reevaluacion=range(11, 41),
    semillas_finales=range(1001, 1031),
    paciencia=10,
    mapear=map,
    progreso=None,
):
    """
    Ejecuta entrenamiento, reevaluación y evaluación final
    con semillas independientes.
    """

    grupos = [tuple(s) for s in (semillas_entrenamiento, semillas_reevaluacion, semillas_finales)]
    if any(not g or len(set(g)) != len(g) for g in grupos):
        raise ValueError("Cada grupo debe tener semillas no vacías y sin duplicados")
    if any(set(grupos[i]) & set(grupos[j]) for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Las semillas de las tres etapas deben ser independientes")
    # 1. Entrenamiento
    entrenamiento = algoritmo_genetico(
        config=config,
        simulador=simulador,
        cruzar=cruce_uniforme,
        mutar=mutacion_gaussiana,
        tamano_poblacion=tamano_poblacion,
        generaciones=generaciones,
        semillas=grupos[0],
        cantidad_candidatos=5,
        semilla_genetico=semilla_genetico,
        paciencia=paciencia,
        mapear=mapear,
        progreso=progreso,
    )

    # 2. Reevaluación de los cinco mejores
    reevaluacion = reevaluar_candidatos(
        candidatos=entrenamiento["candidatos"],
        config=config,
        simulador=simulador,
        semillas=grupos[1],
        mapear=mapear,
    )

    mejor = reevaluacion["mejor_cromosoma"]

    # 3. Evaluación final independiente
    evaluacion_final = evaluar_replicas(
        cromosoma=mejor,
        config=config,
        semillas=grupos[2],
        simulador=simulador,
    )

    return {
        "mejor_cromosoma": mejor,
        "fitness_entrenamiento": evaluar_replicas(mejor, config, grupos[0], simulador)["fitness"],
        "mejor_fitness_entrenamiento": entrenamiento["mejor_fitness"],
        "ganador_entrenamiento": entrenamiento["mejor_cromosoma"],
        "fitness_reevaluacion": reevaluacion["mejor_fitness"],
        "fitness_final": evaluacion_final["fitness"],
        "evaluacion_final": evaluacion_final,
        "historial": entrenamiento["historial"],
        "generaciones_ejecutadas": entrenamiento[
            "generaciones_ejecutadas"
        ],
        "candidatos_reevaluados": reevaluacion["resultados"],
        "historial_detallado": entrenamiento["historial_detallado"],
        "motivo_paro": entrenamiento["motivo_paro"],
        "candidatos_unicos_evaluados": entrenamiento["candidatos_unicos_evaluados"],
        "semillas": {"genetico": semilla_genetico, "entrenamiento": list(grupos[0]),
                     "reevaluacion": list(grupos[1]), "evaluacion_final": list(grupos[2])},
        "hiperparametros": {"tamano_poblacion": tamano_poblacion, "generaciones_maximas": generaciones,
                            "paciencia": paciencia, "prob_cruce": 0.85, "prob_mutacion": 0.10,
                            "elitismo": 2, "torneo_k": 3, "sigma_mutacion": 0.10},
    }
