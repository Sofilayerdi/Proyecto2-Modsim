import random

# Valores permitidos para cada gen
RANGOS = {
    "bodega_s_dias": (5, 20),
    "bodega_S_dias": (15, 45),
}


def crear_cromosoma():
    """Genera un cromosoma aleatorio válido."""
    cromosoma = {}

    for gen, (minimo, maximo) in RANGOS.items():
        cromosoma[gen] = random.randint(minimo, maximo)

    return reparar_cromosoma(cromosoma)


def reparar_cromosoma(cromosoma):
    """Corrige los genes que incumplen restricciones."""
    reparado = cromosoma.copy()

    for gen, (minimo, maximo) in RANGOS.items():
        reparado[gen] = max(
            minimo,
            min(maximo, round(reparado[gen]))
        )

    # Restricción: S >= s
    if reparado["bodega_S_dias"] < reparado["bodega_s_dias"]:
        reparado["bodega_S_dias"] = reparado["bodega_s_dias"]

    return reparado


def crear_poblacion(tamano=30):
    """Genera una población inicial de cromosomas."""
    if tamano < 1:
        raise ValueError("El tamaño debe ser positivo")

    return [
        crear_cromosoma()
        for _ in range(tamano)
    ]
