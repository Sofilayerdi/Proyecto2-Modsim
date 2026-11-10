"""Análisis adicional: aporte de los traspasos según la reserva o la entrega de las tiendas.

Para cada nivel de reserva (días de demanda hasta los que piden las tiendas) se
fija la bodega en sus valores originales, se entrena el genético solo sobre los
genes de traspasos y se compara, con las mismas semillas finales, la cadena sin
traspasos contra la cadena con la política ganadora. Fue diseñado después de ver
los resultados principales; es exploratorio y no reemplaza el escenario base.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import pandas as pd

from experiments.estadistica import comparar_pareado
from experiments.optimizar import guardar_json, huella
from src.model.indicador import exceso_donante, parametros_politica, parametros_por_tienda
from src.model.traspasos import decidir_traspasos
from src.optimization.adaptador import simular_politica
from src.optimization.optimizador import optimizar_politica
from src.simulation.carga import cargar_config, cargar_datos
from src.simulation.motor import simular

NIVELES = (12, 9, 6, 5, 4)
NIVELES_ENTREGA = (2, 3, 5, 7)
GENES_BODEGA = ("bodega_s_dias", "bodega_S_dias")


def config_nivel(config, dias_objetivo):
    """Escala la reserva de las tiendas manteniendo la proporción seguridad/objetivo.

    La seguridad se reduce en la misma proporción que el objetivo (3/12 en el
    escenario base) para que s <= S en todos los niveles; el inventario inicial
    de las tiendas no supera el nuevo objetivo. Bodega y demanda no cambian.
    """
    if dias_objetivo <= 0:
        raise ValueError("dias_objetivo debe ser positivo")
    nuevo = deepcopy(config)
    tiendas = nuevo["reposicion"]["tiendas"]
    base = config["reposicion"]["tiendas"]
    tiendas["dias_seguridad"] = base["dias_seguridad"] * dias_objetivo / base["dias_objetivo"]
    tiendas["dias_objetivo"] = dias_objetivo
    if dias_objetivo < tiendas["tiempo_entrega_dias"] + tiendas["dias_seguridad"]:
        raise ValueError(f"Con {dias_objetivo} días el punto de reorden supera al objetivo")
    inicial = nuevo["inventario"]["inicial"]
    inicial["dias_cobertura_tienda"] = min(inicial["dias_cobertura_tienda"], dias_objetivo)
    return nuevo


def config_entrega(config, dias_entrega):
    """Alarga la entrega bodega-tienda conservando seguridad y tamaño de pedido.

    s = L + seguridad y S = s + (S - s) del escenario base, de modo que solo
    cambia cuánto tarda en llegar la reposición. Bodega y demanda no cambian.
    """
    if dias_entrega < 1:
        raise ValueError("La entrega debe ser de al menos un día")
    nuevo = deepcopy(config)
    tiendas = nuevo["reposicion"]["tiendas"]
    base = config["reposicion"]["tiendas"]
    holgura = base["dias_objetivo"] - base["tiempo_entrega_dias"] - base["dias_seguridad"]
    tiendas["tiempo_entrega_dias"] = dias_entrega
    tiendas["dias_objetivo"] = dias_entrega + base["dias_seguridad"] + holgura
    return nuevo


FACTORES = {
    "reserva": (config_nivel, NIVELES, "S", "{} días de reserva"),
    "entrega": (config_entrega, NIVELES_ENTREGA, "L", "entrega {} d"),
}


def simular_traspasos_bodega_fija(config, params_politica, semilla):
    """Ignora los genes de bodega: el motor usa la s y S de bodega del config."""
    params = {k: v for k, v in params_politica.items() if k not in GENES_BODEGA}
    return simular_politica(config, params, semilla)


def _indicadores(config, detalle, ganador):
    """Faltantes comparables con la literatura y oportunidades de traspaso."""
    inventario, perdidas = detalle["inventario_tiendas"], detalle["perdidas"]
    datos = cargar_datos(config)
    media = datos["media"].mean(axis=2)
    params = parametros_politica({**config, "politica": ganador})
    horizontes, seguridades = parametros_por_tienda(params, datos["tipos_tiendas"])
    minimo = int(config["inventario"]["minimo_exhibicion_unidades"])
    eventos, con_donante = 0, 0
    for t in range(len(inventario)):
        exceso = exceso_donante(inventario[t], media, horizontes[:, None], seguridades[:, None], minimo)
        hay = exceso > 0
        donantes = hay.sum(axis=0)
        faltan = perdidas[t] > 0
        eventos += int(faltan.sum())
        # Un faltante tiene donante si otra tienda tenía exceso del mismo producto.
        con_donante += int((faltan & ((donantes - hay) > 0)).sum())
    return {"fraccion_dias_agotado": float((inventario == 0).mean()),
            "eventos_faltante": eventos, "eventos_con_donante": con_donante}


def _replica(tarea):
    prefijo, dias, variante, config, ganador, semilla = tarea
    params = ganador if variante == "con" else None
    decidir = decidir_traspasos if variante == "con" else None
    resultado = simular(config, params, semilla, detalle=True, decidir=decidir)
    detalle = resultado.pop("detalle")
    return {"condicion": f"{prefijo}{dias}_{variante}", "nivel": dias, "variante": variante,
            "semilla": semilla, **resultado, **_indicadores(config, detalle, ganador)}


def _semillas(opciones, nombre):
    primero, ultimo = opciones[nombre]
    return range(primero, ultimo + 1)


def ejecutar(ruta_config, salida, factor="reserva", niveles=None, trabajadores=1):
    construir, por_defecto, prefijo, etiqueta = FACTORES[factor]
    niveles = tuple(niveles or por_defecto)
    config = cargar_config(ruta_config)
    opciones = config["optimizacion"]
    salida = Path(salida)
    if salida.exists() and any(salida.iterdir()):
        raise FileExistsError("La carpeta de salida debe estar vacía")
    salida.mkdir(parents=True, exist_ok=True)
    raiz = Path(__file__).resolve().parents[1]
    manifest = {
        "estado": "en_ejecucion", "inicio_utc": datetime.now(timezone.utc).isoformat(),
        "tipo": "analisis_exploratorio_posterior", "factor": factor, "niveles": list(niveles),
        "bodega_fija": {k: config["reposicion"]["bodega"][k] for k in ("s_dias", "S_dias")},
        "config_sha256": huella(Path(ruta_config)),
        "git_commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
        "git_con_cambios": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=raiz, text=True)),
        "python": platform.python_version(), "trabajadores": trabajadores,
    }
    guardar_json(salida / "manifest.json", manifest)
    inicio = time.perf_counter()
    configs = {d: construir(config, d) for d in niveles}
    finales = list(_semillas(opciones, "semillas_evaluacion_final"))
    ganadores, historiales = {}, []
    try:
        with ProcessPoolExecutor(max_workers=trabajadores) as pool:
            for dias in niveles:
                print(f"{etiqueta.format(dias)}: entrenando genético", flush=True)
                resultado = optimizar_politica(
                    config=configs[dias], simulador=simular_traspasos_bodega_fija,
                    tamano_poblacion=opciones["tamano_poblacion"], generaciones=opciones["generaciones"],
                    semilla_genetico=opciones["semilla_genetico"], paciencia=opciones["paciencia"],
                    semillas_entrenamiento=_semillas(opciones, "semillas_entrenamiento"),
                    semillas_reevaluacion=_semillas(opciones, "semillas_reevaluacion"),
                    semillas_finales=finales, mapear=pool.map,
                )
                bodega = configs[dias]["reposicion"]["bodega"]
                ganadores[dias] = {**resultado["mejor_cromosoma"],
                                   "bodega_s_dias": bodega["s_dias"], "bodega_S_dias": bodega["S_dias"]}
                historiales.extend({"nivel": dias, **fila} for fila in resultado["historial_detallado"])
                guardar_json(salida / "ganadores.json", {str(d): g for d, g in ganadores.items()})
            tareas = [(prefijo, d, v, configs[d], ganadores[d], s)
                      for d in niveles for v in ("sin", "con") for s in finales]
            resultados = pd.DataFrame(pool.map(_replica, tareas))
        comparaciones = [[f"{prefijo}{d}_sin", f"{prefijo}{d}_con"] for d in niveles]
        pruebas, diferencias = comparar_pareado(resultados, comparaciones, alpha=0.05)
        resumen = resumir_niveles(resultados, pruebas, niveles, prefijo)
        for nombre, tabla in (("resultados", resultados), ("pruebas_pareadas", pruebas),
                              ("diferencias_pareadas", diferencias), ("resumen_niveles", resumen),
                              ("historial", pd.DataFrame(historiales))):
            tabla.to_csv(salida / f"{nombre}.csv", index=False)
        from src.viz.reserva import graficar_reserva
        graficar_reserva(resumen, salida / f"ahorro_traspasos_por_{factor}.png", etiqueta)
        manifest.update(estado="completado")
        print(resumen.to_string(index=False), flush=True)
        return resumen
    except BaseException as exc:
        manifest.update(estado="fallido", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest.update(duracion_segundos=time.perf_counter() - inicio,
                        fin_utc=datetime.now(timezone.utc).isoformat())
        guardar_json(salida / "manifest.json", manifest)


def resumir_niveles(resultados, pruebas, niveles, prefijo="S"):
    filas = []
    for dias in niveles:
        sin = resultados[resultados.condicion == f"{prefijo}{dias}_sin"]
        con = resultados[resultados.condicion == f"{prefijo}{dias}_con"]
        pares = pruebas[pruebas.referencia == f"{prefijo}{dias}_sin"].set_index("metrica")
        costo, servicio = pares.loc["costo_total"], pares.loc["nivel_servicio"]
        ref = costo.media_referencia
        filas.append({
            "nivel": dias,
            "servicio_sin_pct": 100 * sin.nivel_servicio.mean(),
            "servicio_con_pct": 100 * con.nivel_servicio.mean(),
            "dias_agotado_sin_pct": 100 * sin.fraccion_dias_agotado.mean(),
            "faltantes_con_donante_pct": 100 * sin.eventos_con_donante.sum() / max(1, sin.eventos_faltante.sum()),
            "costo_sin_q": ref, "costo_con_q": costo.media_alternativa,
            "ahorro_q": -costo.diferencia_media,
            "ahorro_pct": -100 * costo.diferencia_media / ref,
            "ahorro_pct_ic_inf": -100 * costo.ic95_diferencia_superior / ref,
            "ahorro_pct_ic_sup": -100 * costo.ic95_diferencia_inferior / ref,
            "p_holm_costo": costo.p_t_holm,
            "ganancia_servicio_pp": 100 * servicio.diferencia_media,
            "p_holm_servicio": servicio.p_t_holm,
            "viajes_con": con.num_traspasos.mean(),
        })
    return pd.DataFrame(filas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--salida", default="results/reserva/nueva_ejecucion")
    parser.add_argument("--factor", choices=sorted(FACTORES), default="reserva")
    parser.add_argument("--niveles", type=int, nargs="+")
    parser.add_argument("--trabajadores", type=int, default=min(6, os.cpu_count() or 1))
    args = parser.parse_args()
    ejecutar(args.config, args.salida, args.factor, args.niveles, args.trabajadores)


if __name__ == "__main__":
    main()
