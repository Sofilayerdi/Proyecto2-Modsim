import numpy as np

from src.simulation.carga import cargar_datos
from src.simulation.demanda import generar_demanda
from src.simulation.estado import Estado, Traspaso
from src.simulation.pronostico import pronosticar
from src.model.transporte import matriz_distancias

METRICAS = (
    "costo_total",
    "costo_inventario",
    "costo_traslado",
    "costo_ventas_perdidas",
    "nivel_servicio",
    "unidades_perdidas",
    "num_traspasos",
    "km_recorridos",
)

DIAS_EXTRA_TRANSITO = 60

_datos_cargados: dict = {}


def simular(
    config: dict,
    params_politica: dict | None,
    semilla: int,
    detalle: bool = False,
    decidir=None,
) -> dict:
    """Corre una réplica. params_politica=None es el escenario base; detalle=True agrega las series diarias."""
    clave = (
        str(config["datos"]["tiendas"]),
        str(config["datos"]["demanda"]),
        tuple(str(producto["id"]) for producto in config["productos"]),
    )
    if clave not in _datos_cargados:
        _datos_cargados[clave] = cargar_datos(config)
    return simular_con_datos(config, _datos_cargados[clave], params_politica, semilla, detalle, decidir)


def simular_con_datos(
    config: dict,
    datos: dict,
    params_politica: dict | None,
    semilla: int,
    detalle: bool = False,
    decidir=None,
) -> dict:
    if params_politica is not None and decidir is None:
        raise ValueError("Hay params_politica pero no hay función decidir_traspasos conectada")

    sim = config["simulacion"]
    horizonte = int(sim["horizonte_dias"])
    dia_semana_inicial = int(sim.get("dia_semana_inicial", 0))
    factor_demanda = float(sim.get("factor_demanda", 1.0))
    # Permite estresar demanda sin aumentar existencias ni niveles (s, S).
    # Por defecto conserva exactamente el comportamiento de la optimización.
    factor_referencia = float(sim.get("factor_referencia_inventario", factor_demanda))
    if not np.isfinite(factor_referencia) or factor_referencia < 0:
        raise ValueError("factor_referencia_inventario debe ser finito y no negativo")

    media = datos["media"]
    num_tiendas, num_productos, _ = media.shape
    mu_tienda = factor_referencia * media.mean(axis=2)
    mu_cadena = mu_tienda.sum(axis=0)

    margen = np.array([producto["margen_q"] for producto in config["productos"]], dtype=float)
    costo_mantener = float(config["costos"]["mantener_q_unidad_dia"])
    minimo_exhibicion = int(config["inventario"]["minimo_exhibicion_unidades"])
    transporte = config.get("transporte", {})
    capacidad_dia = transporte.get("num_vehiculos", np.inf) * transporte.get("capacidad_unidades", np.inf)

    reposicion = _parametros_reposicion(config, params_politica, mu_tienda, mu_cadena)
    entrega_tienda = reposicion["tiempo_entrega_tienda"]
    entrega_bodega = reposicion["tiempo_entrega_bodega"]

    pron = config["pronostico"]
    ventana_semanas = int(pron["ventana_semanas"])
    horizonte_pronostico = int(pron.get("horizonte_dias", 14))
    config_politica = {**config, "politica": params_politica,
                       "ubicaciones_tiendas": datos["ubicaciones"],
                       "tipos_tiendas": datos.get("tipos_tiendas", ["media"] * num_tiendas)}
    if decidir is not None and "distancias_km" not in config_politica:
        config_politica["distancias_km"] = matriz_distancias(
            datos["ubicaciones"], transporte.get("factor_ruta", 1.3),
        )

    demanda = generar_demanda(
        media, datos["dispersion"], horizonte, dia_semana_inicial, semilla, factor_demanda
    )

    inicial = config["inventario"]["inicial"]
    inventario = np.round(inicial["dias_cobertura_tienda"] * mu_tienda).astype(np.int64)
    bodega = np.round(inicial["dias_cobertura_bodega"] * mu_cadena).astype(np.int64)
    inventario_inicial, bodega_inicial = inventario.copy(), bodega.copy()

    largo = horizonte + max(entrega_tienda, entrega_bodega) + DIAS_EXTRA_TRANSITO
    llegadas_tiendas = np.zeros((largo, num_tiendas, num_productos), dtype=np.int64)
    llegadas_bodega = np.zeros((largo, num_productos), dtype=np.int64)

    ventas = np.zeros((horizonte, num_tiendas, num_productos), dtype=np.int64)
    perdidas = np.zeros_like(ventas)
    inventario_cierre = np.zeros_like(ventas)
    bodega_cierre = np.zeros((horizonte, num_productos), dtype=np.int64)
    recibido_tiendas = np.zeros_like(inventario)
    enviado_traspasos = np.zeros_like(inventario)
    recibido_bodega = np.zeros_like(bodega)
    despachado_bodega = np.zeros_like(bodega)
    comprado = np.zeros_like(bodega)
    traspasos_hechos: list[Traspaso] = []

    for t in range(horizonte):
        # 1. Llegadas
        inventario += llegadas_tiendas[t]
        recibido_tiendas += llegadas_tiendas[t]
        bodega += llegadas_bodega[t]
        recibido_bodega += llegadas_bodega[t]

        # 2–3. Ventas
        ventas[t] = np.minimum(inventario, demanda[t])
        perdidas[t] = demanda[t] - ventas[t]
        inventario -= ventas[t]

        # 4. Traspasos
        if decidir is not None:
            pronostico = pronosticar(
                ventas[: t + 1], media * factor_demanda, dia_semana_inicial,
                ventana_semanas, horizonte_pronostico,
            )
            estado = Estado(
                dia=t,
                dia_semana=(dia_semana_inicial + t) % 7,
                inventario=inventario.copy(),
                inventario_bodega=bodega.copy(),
                llegadas_tiendas=llegadas_tiendas[t + 1:].copy(),
                llegadas_bodega=llegadas_bodega[t + 1:].copy(),
                perdidas_acumuladas=perdidas[: t + 1].sum(axis=0),
            )
            traspasos = decidir(estado, pronostico, config_politica)
            validar_traspasos(traspasos, inventario, t, minimo_exhibicion, capacidad_dia, largo)
            for tr in traspasos:
                inventario[tr.origen, tr.producto] -= tr.cantidad
                enviado_traspasos[tr.origen, tr.producto] += tr.cantidad
                llegadas_tiendas[tr.dia_llegada, tr.destino, tr.producto] += tr.cantidad
            traspasos_hechos.extend(traspasos)

        # 5. Reposición (s, S)
        en_camino_tiendas = llegadas_tiendas[t + 1:].sum(axis=0)
        pedido = pedido_s_S(inventario + en_camino_tiendas, reposicion["s_tienda"], reposicion["S_tienda"])
        pedido = repartir_disponible(pedido, bodega)
        bodega -= pedido.sum(axis=0)
        despachado_bodega += pedido.sum(axis=0)
        llegadas_tiendas[t + entrega_tienda] += pedido

        en_camino_bodega = llegadas_bodega[t + 1:].sum(axis=0)
        compra = pedido_s_S(bodega + en_camino_bodega, reposicion["s_bodega"], reposicion["S_bodega"])
        comprado += compra
        llegadas_bodega[t + entrega_bodega] += compra

        # 6. Registro
        inventario_cierre[t] = inventario
        bodega_cierre[t] = bodega
        if (inventario < 0).any() or (bodega < 0).any():
            raise RuntimeError(f"Inventario negativo el día {t}")

    balance = {
        "tiendas": inventario_inicial + recibido_tiendas - ventas.sum(axis=0) - enviado_traspasos - inventario,
        "bodega": bodega_inicial + recibido_bodega - despachado_bodega - bodega,
        "sistema": (
            inventario_inicial.sum() + bodega_inicial.sum() + comprado.sum() - ventas.sum()
            - inventario.sum() - bodega.sum() - llegadas_tiendas[horizonte:].sum()
            - llegadas_bodega[horizonte:].sum()
        ),
    }
    if any(np.any(diferencia != 0) for diferencia in balance.values()):
        raise RuntimeError(f"No se conservan las unidades: {balance}")

    unidades_demandadas = int(demanda.sum())
    unidades_vendidas = int(ventas.sum())
    costo_inventario = costo_mantener * float(inventario_cierre.sum() + bodega_cierre.sum())
    costo_traslado = float(sum(tr.costo for tr in traspasos_hechos))
    costo_ventas_perdidas = float((perdidas.sum(axis=(0, 1)) * margen).sum())

    resultado = {
        "costo_total": costo_inventario + costo_traslado + costo_ventas_perdidas,
        "costo_inventario": costo_inventario,
        "costo_traslado": costo_traslado,
        "costo_ventas_perdidas": costo_ventas_perdidas,
        "nivel_servicio": unidades_vendidas / unidades_demandadas if unidades_demandadas else 1.0,
        "unidades_perdidas": int(perdidas.sum()),
        "num_traspasos": (
            len({tr.viaje_id for tr in traspasos_hechos if tr.viaje_id is not None})
            + sum(tr.viaje_id is None for tr in traspasos_hechos)
        ),
        "km_recorridos": float(sum(tr.km for tr in traspasos_hechos)),
    }
    if detalle:
        resultado["detalle"] = {
            "ids_tiendas": datos["ids_tiendas"],
            "ids_productos": datos["ids_productos"],
            "demanda": demanda,
            "ventas": ventas,
            "perdidas": perdidas,
            "inventario_tiendas": inventario_cierre,
            "inventario_bodega": bodega_cierre,
            "inventario_inicial_tiendas": inventario_inicial,
            "inventario_inicial_bodega": bodega_inicial,
            "traspasos": traspasos_hechos,
            "balance": balance,
        }
    return resultado


def _parametros_reposicion(config, params_politica, mu_tienda, mu_cadena) -> dict:
    tiendas = config["reposicion"]["tiendas"]
    bodega = config["reposicion"]["bodega"]
    genes = params_politica or {}

    entrega_tienda = int(tiendas["tiempo_entrega_dias"])
    entrega_bodega = int(bodega["tiempo_entrega_dias"])
    if entrega_tienda < 1 or entrega_bodega < 1:
        raise ValueError("Los tiempos de entrega deben ser de al menos 1 día")

    s_bodega_dias = float(genes.get("bodega_s_dias", bodega["s_dias"]))
    S_bodega_dias = float(genes.get("bodega_S_dias", bodega["S_dias"]))
    if S_bodega_dias < s_bodega_dias:
        raise ValueError("S de bodega debe ser mayor o igual que s")
    if tiendas["dias_objetivo"] < entrega_tienda + tiendas["dias_seguridad"]:
        raise ValueError("S de tiendas debe ser mayor o igual que s")

    return {
        "tiempo_entrega_tienda": entrega_tienda,
        "tiempo_entrega_bodega": entrega_bodega,
        "s_tienda": mu_tienda * (entrega_tienda + tiendas["dias_seguridad"]),
        "S_tienda": mu_tienda * tiendas["dias_objetivo"],
        "s_bodega": mu_cadena * s_bodega_dias,
        "S_bodega": mu_cadena * S_bodega_dias,
    }


def pedido_s_S(posicion: np.ndarray, s: np.ndarray, S: np.ndarray) -> np.ndarray:
    pedido = np.where(posicion <= s, np.ceil(S - posicion), 0)
    return np.maximum(pedido, 0).astype(np.int64)


def repartir_disponible(pedido: np.ndarray, disponible: np.ndarray) -> np.ndarray:
    """Si la bodega no alcanza, reparte en proporción a lo pedido."""
    total = pedido.sum(axis=0)
    no_alcanza = total > disponible
    if no_alcanza.any():
        proporcion = disponible[no_alcanza] / total[no_alcanza]
        pedido = pedido.copy()
        pedido[:, no_alcanza] = np.floor(pedido[:, no_alcanza] * proporcion).astype(np.int64)
    return pedido


def validar_traspasos(traspasos, inventario, dia, minimo_exhibicion, capacidad_dia, largo) -> None:
    num_tiendas, num_productos = inventario.shape
    enviado = np.zeros_like(inventario)
    total = 0
    for tr in traspasos:
        if not (0 <= tr.origen < num_tiendas and 0 <= tr.destino < num_tiendas):
            raise ValueError(f"Tienda fuera de rango: {tr}")
        if tr.origen == tr.destino:
            raise ValueError(f"Origen y destino iguales: {tr}")
        if not 0 <= tr.producto < num_productos:
            raise ValueError(f"Producto fuera de rango: {tr}")
        if tr.cantidad <= 0 or int(tr.cantidad) != tr.cantidad:
            raise ValueError(f"La cantidad debe ser un entero positivo: {tr}")
        if not dia < tr.dia_llegada < largo:
            raise ValueError(f"dia_llegada debe ser posterior al día {dia}: {tr}")
        if tr.costo < 0 or tr.km < 0:
            raise ValueError(f"Costo y km no pueden ser negativos: {tr}")
        enviado[tr.origen, tr.producto] += tr.cantidad
        total += tr.cantidad

    if total > capacidad_dia:
        raise ValueError(f"El día {dia} se envían {total} unidades; la capacidad es {capacidad_dia}")
    donantes = enviado > 0
    if np.any((inventario - enviado)[donantes] < minimo_exhibicion):
        raise ValueError(f"Un traspaso del día {dia} deja a una tienda bajo el mínimo de exhibición")
