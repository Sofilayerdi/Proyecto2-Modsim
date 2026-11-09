from src.optimization.fitness import evaluar_cromosoma

def reevaluar_candidatos(
    candidatos,
    config,
    simulador,
    semillas=range(11, 41),
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

    for cromosoma in candidatos:
        fitness = evaluar_cromosoma(
            cromosoma=cromosoma,
            config=config,
            semillas=semillas,
            simulador=simulador,
        )

        resultados.append({
            "cromosoma": cromosoma.copy(),
            "fitness": fitness,
        })

    resultados.sort(
        key=lambda resultado: resultado["fitness"]
    )

    return {
        "mejor_cromosoma": resultados[0]["cromosoma"],
        "mejor_fitness": resultados[0]["fitness"],
        "resultados": resultados,
    }
