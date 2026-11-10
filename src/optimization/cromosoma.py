import random
import math

from src.model.tipos import TIPOS_TIENDA

# Valores permitidos para cada gen
RANGOS = {
    "bodega_s_dias": (5, 20),
    "bodega_S_dias": (15, 45),
    **{f"{parametro}_{tipo}": rango for tipo in TIPOS_TIENDA
       for parametro, rango in (("horizonte_dias", (1, 7)), ("seguridad_dias", (0, 7)))},
    "umbral_valor_q": (0.0, 200.0),
    "peso_trafico": (0.0, 2.0),
    "hora_despacho": (0, 23),
}


def crear_cromosoma(rng=None, horizonte_pronostico=14):
    """Genera un cromosoma aleatorio válido."""
    rng = rng if rng is not None else random
    cromosoma = {}

    for gen, (minimo, maximo) in RANGOS.items():
        if isinstance(minimo, int):
            cromosoma[gen] = rng.randint(minimo, maximo)
        else:
            cromosoma[gen] = rng.uniform(minimo, maximo)

    return reparar_cromosoma(cromosoma, horizonte_pronostico)


def reparar_cromosoma(cromosoma, horizonte_pronostico=14):
    """Corrige los genes que incumplen restricciones."""
    reparado = cromosoma.copy()
    if not isinstance(horizonte_pronostico, int) or horizonte_pronostico < 1:
        raise ValueError("El horizonte del pronóstico debe ser un entero positivo")
    # Migración explícita de candidatos antiguos con H y SS globales.
    for parametro in ("horizonte_dias", "seguridad_dias"):
        if parametro in reparado:
            valor_global = reparado.pop(parametro)
            for tipo in TIPOS_TIENDA:
                reparado.setdefault(f"{parametro}_{tipo}", valor_global)
    if set(reparado) != set(RANGOS):
        raise ValueError("El cromosoma debe contener los 11 genes definidos en RANGOS")

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

    for tipo in TIPOS_TIENDA:
        h, ss = f"horizonte_dias_{tipo}", f"seguridad_dias_{tipo}"
        reparado[h] = min(reparado[h], horizonte_pronostico)
        reparado[ss] = min(reparado[ss], horizonte_pronostico - reparado[h])

    return reparado


def crear_poblacion(tamano=30, rng=None, horizonte_pronostico=14):
    """Genera una población inicial de cromosomas."""
    if tamano < 1:
        raise ValueError("El tamaño debe ser positivo")

    return [
        crear_cromosoma(rng, horizonte_pronostico)
        for _ in range(tamano)
    ]
