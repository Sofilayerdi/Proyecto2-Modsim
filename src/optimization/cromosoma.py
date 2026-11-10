import random
import math

# Valores permitidos para cada gen
RANGOS = {
    "bodega_s_dias": (5, 20),
    "bodega_S_dias": (15, 45),
    "horizonte_dias": (1, 7),
    "seguridad_dias": (0, 7),
    "umbral_valor_q": (0.0, 200.0),
    "peso_trafico": (0.0, 2.0),
    "hora_despacho": (0, 23),
}


def crear_cromosoma():
    """Genera un cromosoma aleatorio válido."""
    cromosoma = {}

    for gen, (minimo, maximo) in RANGOS.items():
        if isinstance(minimo, int):
            cromosoma[gen] = random.randint(minimo, maximo)
        else:
            cromosoma[gen] = random.uniform(minimo, maximo)

    return reparar_cromosoma(cromosoma)


def reparar_cromosoma(cromosoma):
    """Corrige los genes que incumplen restricciones."""
    reparado = cromosoma.copy()

    for gen, (minimo, maximo) in RANGOS.items():
        valor = reparado[gen]

        if not math.isfinite(valor):
            raise ValueError(
                f"El gen {gen} debe ser finito"
            )

        if isinstance(minimo, int):
            valor = round(valor)

        reparado[gen] = max(
            minimo,
            min(maximo, valor)
        )

    # Restricción: S >= s
    if reparado["bodega_S_dias"] < reparado["bodega_s_dias"]:
        reparado["bodega_S_dias"] = reparado["bodega_s_dias"]

    # El pronóstico disponible es de 14 días.
    if (
        reparado["horizonte_dias"]
        + reparado["seguridad_dias"] > 14
    ):
        reparado["seguridad_dias"] = (
            14 - reparado["horizonte_dias"]
        )

    return reparado


def crear_poblacion(tamano=30):
    """Genera una población inicial de cromosomas."""
    if tamano < 1:
        raise ValueError("El tamaño debe ser positivo")

    return [
        crear_cromosoma()
        for _ in range(tamano)
    ]
