from src.simulation.motor import simular
from src.model.traspasos import decidir_traspasos

def simular_politica(config, params_politica, semilla):
    """
    Conecta el algoritmo genético con el motor real
    y la política económica de traspasos.
    """
    return simular(
        config=config,
        params_politica=params_politica,
        semilla=semilla,
        decidir=decidir_traspasos,
    )
