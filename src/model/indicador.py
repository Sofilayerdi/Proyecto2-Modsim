"""Valor económico aproximado usando el pronóstico como demanda esperada.

Las ventas extra y el riesgo del donante se estiman proyectando inventarios,
no observando la demanda futura de la simulación. Solo se anticipa el pedido
de bodega de hoy; los pedidos de días futuros todavía no son conocidos.
"""

import math

import numpy as np

from src.model.costos import costo_viaje

PARAMETROS = {
    "horizonte_dias": 3,
    "seguridad_dias": 2,
    "descuento_diario": 0.98,
    "umbral_valor_q": 0.0,
    "peso_trafico": 0.0,
}


def parametros_politica(config) -> dict:
    """Los parámetros del candidato prevalecen sobre los valores fijos."""
    params = {**PARAMETROS, **config.get("traspasos", {}), **(config.get("politica") or {})}
    for nombre in ("horizonte_dias", "seguridad_dias", "umbral_valor_q", "peso_trafico"):
        if not math.isfinite(params[nombre]) or params[nombre] < 0:
            raise ValueError(f"{nombre} debe ser finito y no negativo")
    if params["horizonte_dias"] < 1 or not 0 < params["descuento_diario"] <= 1:
        raise ValueError("Se requiere horizonte >= 1 y descuento_diario en (0, 1]")
    return params


def cobertura(inventario, media) -> np.ndarray:
    """Días de stock; demanda cero implica cobertura infinita."""
    inventario, media = np.broadcast_arrays(inventario, media)
    return np.divide(inventario, media, out=np.full(media.shape, np.inf), where=media > 0)


def exceso_donante(inventario, media, horizonte_dias, seguridad_dias, minimo) -> np.ndarray:
    reserva = np.maximum(minimo, media * (horizonte_dias + seguridad_dias))
    return np.maximum(0, np.floor(inventario - reserva)).astype(np.int64)


def llegadas_previstas(estado, pronostico, config) -> np.ndarray:
    """Llegadas ya comprometidas más una estimación del despacho de bodega de hoy.

    El pedido previsto usa la misma regla (s, S) y reparto proporcional del motor,
    con la media del pronóstico. No supone existencias infinitas en bodega.
    """
    dias = len(pronostico)
    llegadas = np.zeros_like(pronostico, dtype=float)
    n = min(dias, len(estado.llegadas_tiendas))
    llegadas[:n] = estado.llegadas_tiendas[:n]
    reposicion = config["reposicion"]["tiendas"]
    demora = int(reposicion["tiempo_entrega_dias"])
    if demora < 1:
        raise ValueError("El tiempo de reposición debe ser al menos 1 día")
    if demora > dias:
        return llegadas
    media = pronostico.mean(axis=0)
    posicion = estado.inventario + estado.llegadas_tiendas.sum(axis=0)
    s = media * (demora + reposicion["dias_seguridad"])
    objetivo = media * reposicion["dias_objetivo"]
    pedido = np.maximum(0, np.where(posicion <= s, np.ceil(objetivo - posicion), 0))
    total = pedido.sum(axis=0)
    proporcion = np.minimum(1, np.divide(
        estado.inventario_bodega, total, out=np.ones_like(total), where=total > 0,
    ))
    llegadas[demora - 1] += np.floor(pedido * proporcion)
    return llegadas


def ventas_proyectadas(stock, demanda, llegadas, cantidad=0, demora=1) -> np.ndarray:
    """Ventas esperadas por día; la fila cero corresponde a mañana."""
    ventas = np.zeros(len(demanda))
    for t, mu in enumerate(demanda):
        stock += llegadas[t]
        if t == demora - 1:
            stock += cantidad
        ventas[t] = min(stock, mu)
        stock -= ventas[t]
    return ventas


def beneficio_producto(estado, pronostico, llegadas, origen, destino, producto,
                       cantidad, demora, margen_q, horizonte, descuento) -> float:
    """Beneficio antes del viaje: ventas extra descontadas menos riesgo del donante."""
    if cantidad < 0 or cantidad > estado.inventario[origen, producto]:
        raise ValueError("Cantidad fuera del inventario del donante")
    demanda = pronostico[:horizonte, :, producto]
    recibidos = llegadas[:horizonte, :, producto]
    stock_i = estado.inventario[origen, producto]
    stock_j = estado.inventario[destino, producto]
    base_j = ventas_proyectadas(stock_j, demanda[:, destino], recibidos[:, destino])
    extra_j = ventas_proyectadas(stock_j, demanda[:, destino], recibidos[:, destino], cantidad, demora)
    base_i = ventas_proyectadas(stock_i, demanda[:, origen], recibidos[:, origen])
    menos_i = ventas_proyectadas(stock_i - cantidad, demanda[:, origen], recibidos[:, origen])
    descuentos = descuento ** np.arange(1, len(demanda) + 1)
    return float(margen_q * (np.dot(extra_j - base_j, descuentos) - (base_i - menos_i).sum()))


def valor_traspaso(beneficio_q, distancia_km, config, factor=1.0) -> float:
    """V de un viaje completo, con costo fijo una sola vez y umbral en Q/viaje.

    peso_trafico agrega una penalización de decisión en Q; no se factura como
    costo físico. El efecto del tráfico sobre la llegada ya afecta las ventas.
    """
    params = parametros_politica(config)
    costos = config["costos"]
    viaje = costo_viaje(distancia_km, costos["viaje_fijo_q"], costos["viaje_por_km_q"])
    penalizacion = params["peso_trafico"] * max(0, factor - 1) * viaje
    return float(beneficio_q - viaje - penalizacion)
