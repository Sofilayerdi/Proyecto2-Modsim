"""Distancias estimadas y transporte de un viaje directo, sin retorno."""

import math

import numpy as np

RADIO_TIERRA_KM = 6371.0088


def matriz_distancias(ubicaciones, factor_ruta=1.3) -> np.ndarray:
    """Haversine × factor vial estimado; entradas [latitud, longitud] en grados."""
    puntos = np.asarray(ubicaciones, dtype=float)
    if puntos.ndim != 2 or puntos.shape[1] != 2 or not np.isfinite(puntos).all():
        raise ValueError("Las ubicaciones deben ser una matriz finita (N, 2)")
    if (np.abs(puntos[:, 0]) > 90).any() or (np.abs(puntos[:, 1]) > 180).any():
        raise ValueError("Coordenadas fuera de rango")
    if not math.isfinite(factor_ruta) or factor_ruta < 1:
        raise ValueError("factor_ruta debe ser finito y al menos 1")
    lat, lon = np.radians(puntos).T
    a = (np.sin((lat[:, None] - lat) / 2) ** 2
         + np.cos(lat[:, None]) * np.cos(lat) * np.sin((lon[:, None] - lon) / 2) ** 2)
    distancias = 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1))) * factor_ruta
    np.fill_diagonal(distancias, 0.0)
    return distancias


def factor_trafico(hora, franjas) -> float:
    """Usa la franja [desde, hasta) de la hora de salida, como en el plan."""
    if not math.isfinite(hora) or not 0 <= hora < 24:
        raise ValueError("La hora debe estar entre 0 y 24 (excluido)")
    ordenadas = sorted(franjas, key=lambda f: f["desde"])
    extremo = 0
    for franja in ordenadas:
        desde, hasta, factor = franja["desde"], franja["hasta"], franja["factor"]
        if desde != extremo or not desde < hasta <= 24:
            raise ValueError("Las franjas de tráfico deben cubrir 0–24 sin huecos ni solapamientos")
        if not math.isfinite(factor) or factor < 1:
            raise ValueError("El factor de tráfico debe ser finito y al menos 1")
        extremo = hasta
    if extremo != 24:
        raise ValueError("Las franjas de tráfico deben cubrir 0–24")
    return float(next(f["factor"] for f in ordenadas if f["desde"] <= hora < f["hasta"]))


def tiempo_viaje_horas(distancia_km, velocidad_kmh, factor=1.0) -> float:
    if not all(math.isfinite(v) for v in (distancia_km, velocidad_kmh, factor)):
        raise ValueError("Los parámetros de transporte deben ser finitos")
    if distancia_km < 0 or velocidad_kmh <= 0 or factor < 1:
        raise ValueError("Distancia no negativa, velocidad positiva y factor >= 1 requeridos")
    return distancia_km / velocidad_kmh * factor


def dias_transito(distancia_km, velocidad_kmh, hora_despacho, factor=1.0) -> int:
    """Redondea al siguiente inicio de día; el motor no admite llegadas hoy."""
    if not math.isfinite(hora_despacho) or not 0 <= hora_despacho < 24:
        raise ValueError("La hora debe estar entre 0 y 24 (excluido)")
    horas = tiempo_viaje_horas(distancia_km, velocidad_kmh, factor)
    return max(1, math.ceil((hora_despacho + horas) / 24))
