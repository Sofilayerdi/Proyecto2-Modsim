from src.optimization.algoritmo_genetico import _evaluar_tarea

def reevaluar_candidatos(
    candidatos,
    config,
    simulador,
    semillas=range(11, 41),
    mapear=map,
):
    """
    Reevalúa candidatos con semillas adicionales.

    Selecciona el candidato con menor fitness
    calculado sobre las nuevas réplicas.
    """

    if not candidatos:
        raise ValueError("Debe existir al menos un candidato")

    semillas = tuple(semillas)

    if not semillas:
        raise ValueError("Debe existir al menos una semilla")

    resultados = []

    tareas = [(c, config, semillas, simulador) for c in candidatos]
    for cromosoma, evaluacion in zip(candidatos, mapear(_evaluar_tarea, tareas)):

        resultados.append({
            "cromosoma": cromosoma.copy(),
            **evaluacion,
        })

    resultados.sort(
        key=lambda resultado: resultado["fitness"]
    )

    return {
        "mejor_cromosoma": resultados[0]["cromosoma"],
        "mejor_fitness": resultados[0]["fitness"],
        "resultados": resultados,
    }
