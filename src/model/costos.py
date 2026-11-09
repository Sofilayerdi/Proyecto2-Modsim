import math


def costo_viaje(distancia_km, fijo_q, por_km_q) -> float:
    """Q por viaje directo consolidado: fijo + variable, nunca por producto."""
    if not all(math.isfinite(v) and v >= 0 for v in (distancia_km, fijo_q, por_km_q)):
        raise ValueError("Distancia y costos deben ser finitos y no negativos")
    return float(fijo_q + por_km_q * distancia_km)
