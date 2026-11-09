"""Políticas diarias: regla simple y flujo de costo mínimo por viaje.

Cada vehículo hace como máximo un viaje directo diario y consolida productos.
Para cada ruta, el flujo minimiza -beneficio marginal por unidad, con una salida
de costo cero que permite no enviar. Después se descuenta el costo real del
viaje y se elige la ruta con mayor V. Se repite con el siguiente vehículo.
La selección de rutas es voraz: no es el óptimo global del problema de cargos
fijos. El flujo sí optimiza la carga de cada ruta (costos en microquetzales).
"""

from copy import deepcopy
import math

import networkx as nx
import numpy as np

from src.model.costos import costo_viaje
from src.model.indicador import (
    cobertura, exceso_donante, llegadas_previstas, parametros_politica,
    valor_traspaso, ventas_proyectadas,
)
from src.model.transporte import dias_transito, factor_trafico, matriz_distancias
from src.simulation.estado import Traspaso

ESCALA_COSTO = 1_000_000


def _preparar(estado, pronostico, config):
    params = parametros_politica(config)
    pronostico = np.asarray(pronostico, dtype=float)
    if (pronostico.ndim != 3 or pronostico.shape[1:] != estado.inventario.shape
            or not np.isfinite(pronostico).all() or (pronostico < 0).any()):
        raise ValueError("El pronóstico debe ser finito, no negativo y de forma (H, N, K)")
    horizonte = math.ceil(params["horizonte_dias"])
    if len(pronostico) < math.ceil(params["horizonte_dias"] + params["seguridad_dias"]):
        raise ValueError("El pronóstico no cubre horizonte_dias + seguridad_dias")
    transporte = config["transporte"]
    vehiculos, capacidad = transporte["num_vehiculos"], transporte["capacidad_unidades"]
    for nombre, valor in (("num_vehiculos", vehiculos), ("capacidad_unidades", capacidad)):
        if not math.isfinite(valor) or valor < 0 or int(valor) != valor:
            raise ValueError(f"{nombre} debe ser un entero no negativo")
    hora = params.get("hora_despacho", transporte["hora_despacho"])
    factor = factor_trafico(hora, transporte["trafico"])
    if "distancias_km" in config:
        distancias = np.asarray(config["distancias_km"], dtype=float)
    else:
        distancias = matriz_distancias(config["ubicaciones_tiendas"], transporte.get("factor_ruta", 1.3))
    n = len(estado.inventario)
    if distancias.shape != (n, n) or not np.isfinite(distancias).all() or (distancias < 0).any():
        raise ValueError("distancias_km debe ser una matriz finita no negativa (N, N)")
    margenes = np.array([p["margen_q"] for p in config["productos"]], dtype=float)
    if margenes.shape != (estado.inventario.shape[1],) or not np.isfinite(margenes).all() or (margenes < 0).any():
        raise ValueError("Se requiere un margen finito no negativo por producto")
    return params, pronostico, horizonte, int(vehiculos), int(capacidad), hora, factor, distancias, margenes


def _curva_beneficios(estado, pronostico, llegadas, i, j, k, limite, demora, horizonte, descuento, margen):
    """Beneficio acumulado de enviar q=0..limite, proyectado en paralelo."""
    cantidades = np.arange(limite + 1)
    stock_i = estado.inventario[i, k] - cantidades.astype(float)
    stock_j = np.full(limite + 1, estado.inventario[j, k], dtype=float)
    beneficio = np.zeros(limite + 1)
    for t in range(horizonte):
        stock_i += llegadas[t, i, k]
        stock_j += llegadas[t, j, k]
        if t == demora - 1:
            stock_j += cantidades
        ventas_i = np.minimum(stock_i, pronostico[t, i, k])
        ventas_j = np.minimum(stock_j, pronostico[t, j, k])
        beneficio += margen * ((ventas_j - ventas_j[0]) * descuento ** (t + 1)
                               - (ventas_i[0] - ventas_i))
        stock_i -= ventas_i
        stock_j -= ventas_j
    return beneficio


def _carga_flujo(curvas, capacidad):
    grafo = nx.DiGraph()
    grafo.add_node("fuente", demand=-capacidad)
    grafo.add_node("sumidero", demand=capacidad)
    grafo.add_edge("fuente", "sumidero", capacity=capacidad, weight=0)
    for k, curva in curvas.items():
        for q, marginal in enumerate(np.diff(curva), start=1):
            costo = round(marginal * ESCALA_COSTO)
            if costo <= 0:
                continue
            nodo = (k, q)
            grafo.add_edge("fuente", nodo, capacity=1, weight=-costo)
            grafo.add_edge(nodo, "sumidero", capacity=1, weight=0)
    flujo = nx.min_cost_flow(grafo)
    return {k: sum(flujo["fuente"].get((k, q), 0) for q in range(1, len(curva)))
            for k, curva in curvas.items()}


def _decidir(estado, pronostico, config, simple):
    (params, pronostico, horizonte, vehiculos, capacidad, hora,
     factor, distancias, margenes) = _preparar(estado, pronostico, config)
    if vehiculos == 0 or capacidad == 0:
        return []
    trabajo = deepcopy(estado)
    resultado = []
    media = pronostico[:horizonte].mean(axis=0)
    minimo = config["inventario"]["minimo_exhibicion_unidades"]
    for viaje in range(vehiculos):
        excesos = exceso_donante(trabajo.inventario, media, params["horizonte_dias"],
                                 params["seguridad_dias"], minimo)
        llegadas = llegadas_previstas(trabajo, pronostico, config)
        faltantes = np.zeros_like(trabajo.inventario)
        for j, k in np.ndindex(faltantes.shape):
            ventas = ventas_proyectadas(trabajo.inventario[j, k], pronostico[:horizonte, j, k],
                                       llegadas[:horizonte, j, k])
            faltantes[j, k] = max(0, math.ceil((pronostico[:horizonte, j, k] - ventas).sum() - 1e-9))
        coberturas = cobertura(trabajo.inventario, media)
        mejor = None
        for i in range(len(trabajo.inventario)):
            for j in range(len(trabajo.inventario)):
                if i == j:
                    continue
                demora = dias_transito(distancias[i, j], config["transporte"]["velocidad_kmh"], hora, factor)
                # Sin ventas dentro del horizonte o sin espacio en el calendario del motor.
                if demora > horizonte or demora > len(trabajo.llegadas_tiendas):
                    continue
                curvas = {}
                for k in range(trabajo.inventario.shape[1]):
                    limite = min(int(excesos[i, k]), int(faltantes[j, k]), capacidad)
                    if simple and coberturas[j, k] >= params["horizonte_dias"]:
                        continue
                    if limite:
                        curvas[k] = _curva_beneficios(
                            trabajo, pronostico, llegadas, i, j, k, limite, demora, horizonte,
                            1.0 if simple else params["descuento_diario"], 1.0 if simple else margenes[k],
                        )
                if not curvas:
                    continue
                if simple:
                    carga, restante = {}, capacidad
                    for k, curva in curvas.items():
                        # Regla fija: orden de tiendas/productos, sin comparar valor económico.
                        q = min(restante, int(np.count_nonzero(np.diff(curva) > 1e-9)))
                        carga[k] = q
                        restante -= q
                else:
                    carga = _carga_flujo(curvas, capacidad)
                if not any(carga.values()):
                    continue
                beneficio = sum(curvas[k][q] for k, q in carga.items())
                valor = valor_traspaso(beneficio, distancias[i, j], config, factor)
                if not simple and valor <= params["umbral_valor_q"]:
                    continue
                if mejor is None or valor > mejor[0]:
                    mejor = (valor, i, j, demora, carga)
                if simple:
                    break
            if simple and mejor is not None:
                break
        if mejor is None:
            break
        _, i, j, demora, carga = mejor
        costos = config["costos"]
        costo = costo_viaje(distancias[i, j], costos["viaje_fijo_q"], costos["viaje_por_km_q"])
        km = float(distancias[i, j])
        for k, q in carga.items():
            if not q:
                continue
            resultado.append(Traspaso(i, j, k, q, estado.dia + demora, costo=costo, km=km,
                                     viaje_id=f"{estado.dia}:{viaje}"))
            trabajo.inventario[i, k] -= q
            trabajo.llegadas_tiendas[demora - 1, j, k] += q
            costo, km = 0.0, 0.0  # El viaje consolidado se cobra solo en la primera línea.
    return resultado


def decidir_traspasos(estado, pronostico, config) -> list[Traspaso]:
    """Política económica: flujo por viaje y rutas elegidas por mayor V positivo."""
    return _decidir(estado, pronostico, config, simple=False)


def decidir_traspasos_simple(estado, pronostico, config) -> list[Traspaso]:
    """Referencia sin optimizar: cobertura fija y prioridad por índice, aun si V < 0."""
    return _decidir(estado, pronostico, config, simple=True)
