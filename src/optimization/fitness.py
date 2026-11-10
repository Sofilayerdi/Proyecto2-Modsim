from statistics import mean

def evaluar_cromosoma(
    cromosoma,
    config,
    semillas,
    simulador,
    penalizacion=100000,
    servicio_minimo=0.95,
):
    return evaluar_replicas(cromosoma, config, semillas, simulador,
                            penalizacion, servicio_minimo)["fitness"]


def evaluar_replicas(cromosoma, config, semillas, simulador,
                     penalizacion=100000, servicio_minimo=0.95):
    """
    Evalúa un cromosoma mediante varias réplicas.

    El objetivo es minimizar el costo total y penalizar
    niveles de servicio inferiores al mínimo permitido.
    """

    semillas = tuple(semillas)
    if not semillas:
        raise ValueError("Debe proporcionarse al menos una semilla")

    if penalizacion < 0:
        raise ValueError("La penalización no puede ser negativa")

    if not 0 <= servicio_minimo <= 1:
        raise ValueError("El servicio mínimo debe estar entre 0 y 1")

    costos = []
    servicios = []
    replicas = []

    for semilla in semillas:
        metricas = simulador(
            config=config,
            params_politica=cromosoma,
            semilla=semilla,
        )

        costos.append(metricas["costo_total"])
        servicios.append(metricas["nivel_servicio"])
        replicas.append({"semilla": semilla, **metricas})

    costo_promedio = mean(costos)
    servicio_promedio = mean(servicios)

    incumplimiento = max(
        0.0,
        servicio_minimo - servicio_promedio
    )

    costo_penalizacion = penalizacion * incumplimiento

    fitness = costo_promedio + costo_penalizacion

    return {
        "fitness": fitness,
        "costo_promedio": costo_promedio,
        "servicio_promedio": servicio_promedio,
        "costo_penalizacion": costo_penalizacion,
        "replicas": replicas,
    }
