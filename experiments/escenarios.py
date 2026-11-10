"""Condiciones y controles de atribución para el diseño de la persona 4."""

from copy import deepcopy

from src.optimization.cromosoma import reparar_cromosoma

ETIQUETAS = {
    "base": "Base",
    "regla_simple": "Regla simple",
    "mejorada": "Mejorada",
    "bodega_ajustada": "Bodega ajustada, sin traspasos",
    "traspasos_bodega_base": "Traspasos, bodega original",
    "demanda_mas_20": "Demanda +20%",
    "trafico_pesado": "Tráfico pesado",
    "un_vehiculo": "Un vehículo",
}


def construir_escenarios(config, ganador, diseno):
    horizonte = int(config["pronostico"]["horizonte_dias"])
    if reparar_cromosoma(ganador, horizonte) != ganador:
        raise ValueError("El ganador debe ser válido y no requerir reparación")
    condiciones = []

    def agregar(nombre, politica, parametros, descripcion, configuracion=None):
        condiciones.append({"condicion": nombre, "etiqueta": ETIQUETAS[nombre],
                            "politica": politica, "parametros": deepcopy(parametros),
                            "descripcion": descripcion,
                            "config": deepcopy(config if configuracion is None else configuracion)})

    agregar("base", "ninguna", None, "Reposición original (10, 30 días), sin traspasos")
    agregar("regla_simple", "simple", {}, "H y SS globales fijos (3, 2), bodega original")
    agregar("mejorada", "economica", ganador, "Ganador congelado, bodega ajustada y traspasos")
    ajustada = deepcopy(config)
    ajustada["reposicion"]["bodega"].update(s_dias=ganador["bodega_s_dias"], S_dias=ganador["bodega_S_dias"])
    agregar("bodega_ajustada", "ninguna", None,
            "Control: solo cambia s y S de bodega, sin traspasos", ajustada)
    bodega_base = {**ganador,
                   "bodega_s_dias": config["reposicion"]["bodega"]["s_dias"],
                   "bodega_S_dias": config["reposicion"]["bodega"]["S_dias"]}
    agregar("traspasos_bodega_base", "economica", bodega_base,
            "Control: parámetros de traspasos ganadores, s y S originales")

    sensibilidad = diseno["sensibilidad"]
    demanda = deepcopy(config)
    demanda["simulacion"].update(factor_demanda=sensibilidad["factor_demanda"],
                                 factor_referencia_inventario=sensibilidad["factor_referencia_inventario"])
    agregar("demanda_mas_20", "economica", ganador,
            "Demanda y media previa +20%, inventario inicial y niveles de reposición constantes", demanda)
    trafico = deepcopy(config)
    for franja in trafico["transporte"]["trafico"]:
        franja["factor"] = sensibilidad["factor_trafico"]
    agregar("trafico_pesado", "economica", ganador,
            "Factor 2 en todas las franjas; mismo costo fijo y por km", trafico)
    vehiculos = deepcopy(config)
    vehiculos["transporte"]["num_vehiculos"] = sensibilidad["num_vehiculos"]
    agregar("un_vehiculo", "economica", ganador, "Un viaje disponible al día en lugar de dos", vehiculos)
    return condiciones
