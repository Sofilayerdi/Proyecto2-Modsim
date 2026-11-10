"""Ejecuta condiciones pareadas, controles y sensibilidad sin volver a entrenar."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import pandas as pd
import yaml

from experiments.escenarios import construir_escenarios
from experiments.estadistica import comparar_pareado, resumir
from experiments.optimizar import guardar_json, huella
from src.model.traspasos import decidir_traspasos, decidir_traspasos_simple
from src.simulation.carga import cargar_config, cargar_datos
from src.simulation.motor import METRICAS, simular


def _replica(tarea):
    escenario, semilla, semilla_series = tarea
    funciones = {"ninguna": None, "simple": decidir_traspasos_simple, "economica": decidir_traspasos}
    resultado = simular(escenario["config"], escenario["parametros"], semilla,
                        detalle=True, decidir=funciones[escenario["politica"]])
    detalle = resultado.pop("detalle")
    identificacion = {"condicion": escenario["condicion"], "semilla": semilla}
    balance = detalle["balance"]
    auditoria = {**identificacion,
                 "demanda_sha256": hashlib.sha256(detalle["demanda"].tobytes()).hexdigest(),
                 "demanda_total": int(detalle["demanda"].sum()),
                 "ventas_totales": int(detalle["ventas"].sum()),
                 "inventario_inicial_tiendas": int(detalle["inventario_inicial_tiendas"].sum()),
                 "inventario_inicial_bodega": int(detalle["inventario_inicial_bodega"].sum()),
                 "min_inventario_tiendas": int(detalle["inventario_tiendas"].min()),
                 "min_inventario_bodega": int(detalle["inventario_bodega"].min()),
                 "max_error_balance": int(max(np.abs(v).max() for v in balance.values()))}
    series, bodega = [], []
    if semilla == semilla_series and escenario["condicion"] in ("base", "mejorada"):
        tipos = cargar_datos(escenario["config"])["tipos_tiendas"]
        for t, i, k in np.ndindex(detalle["inventario_tiendas"].shape):
            series.append({**identificacion, "dia": t, "id_tienda": detalle["ids_tiendas"][i],
                           "tipo_tienda": tipos[i], "id_producto": detalle["ids_productos"][k],
                           "inventario_cierre": int(detalle["inventario_tiendas"][t, i, k]),
                           "demanda": int(detalle["demanda"][t, i, k]),
                           "ventas": int(detalle["ventas"][t, i, k]),
                           "perdidas": int(detalle["perdidas"][t, i, k])})
        for t, k in np.ndindex(detalle["inventario_bodega"].shape):
            bodega.append({**identificacion, "dia": t, "id_producto": detalle["ids_productos"][k],
                           "inventario_cierre": int(detalle["inventario_bodega"][t, k])})
    return {"metricas": {**identificacion, **resultado}, "auditoria": auditoria,
            "series": series, "bodega": bodega}


def validar_resultados(resultados, auditoria, condiciones, semillas):
    esperados = {(c, s) for c in condiciones for s in semillas}
    obtenidos = set(zip(resultados.condicion, resultados.semilla))
    if obtenidos != esperados or len(resultados) != len(esperados):
        raise ValueError("Faltan réplicas o hay duplicados en el diseño")
    if not np.isfinite(resultados[list(METRICAS)].to_numpy()).all():
        raise ValueError("Hay métricas no finitas")
    if (auditoria.max_error_balance != 0).any() or (auditoria[["min_inventario_tiendas", "min_inventario_bodega"]] < 0).any().any():
        raise ValueError("Falló conservación o inventario no negativo")
    costo = resultados[["costo_inventario", "costo_traslado", "costo_ventas_perdidas"]].sum(axis=1)
    if not np.allclose(costo, resultados.costo_total, rtol=0, atol=1e-8):
        raise ValueError("Costo total inconsistente")
    nominales = auditoria[auditoria.condicion != "demanda_mas_20"]
    if (nominales.groupby("semilla").demanda_sha256.nunique() != 1).any():
        raise ValueError("La demanda nominal no es común entre políticas")
    iniciales = auditoria.groupby("semilla")[["inventario_inicial_tiendas", "inventario_inicial_bodega"]].nunique()
    if (iniciales != 1).any().any():
        raise ValueError("La sensibilidad cambió el inventario inicial")
    combinado = resultados.merge(auditoria, on=["condicion", "semilla"], validate="one_to_one")
    if not np.allclose(combinado.ventas_totales + combinado.unidades_perdidas, combinado.demanda_total):
        raise ValueError("Ventas y pérdidas no suman demanda")
    demanda_total = combinado.demanda_total.to_numpy(dtype=float)
    servicio = np.divide(combinado.ventas_totales.to_numpy(dtype=float), demanda_total,
                         out=np.ones_like(demanda_total), where=demanda_total > 0)
    if not np.allclose(combinado.nivel_servicio, servicio):
        raise ValueError("Nivel de servicio inconsistente")
    return {"replicas_por_condicion": len(semillas), "condiciones": len(condiciones),
            "replicas_totales": len(resultados), "conservacion": True,
            "inventarios_no_negativos": True, "demanda_nominal_comun": True,
            "inventario_inicial_constante": True, "costos_y_servicio_consistentes": True}


def ejecutar(ruta_config, ruta_diseno, ruta_ganador, salida, trabajadores=1):
    if trabajadores < 1:
        raise ValueError("trabajadores debe ser positivo")
    config = cargar_config(ruta_config)
    datos = cargar_datos(config)
    diseno = yaml.safe_load(Path(ruta_diseno).read_text(encoding="utf-8"))
    ganador = json.loads(Path(ruta_ganador).read_text(encoding="utf-8"))
    primero, ultimo = diseno["semillas"]
    semillas = list(range(primero, ultimo + 1))
    if len(semillas) < 2 or diseno["semilla_series"] not in semillas:
        raise ValueError("Se requieren al menos dos semillas y una semilla de series incluida")
    reservadas = set()
    for nombre in ("semillas_entrenamiento", "semillas_reevaluacion"):
        a, b = config["optimizacion"][nombre]
        reservadas.update(range(a, b + 1))
    if set(semillas) & reservadas:
        raise ValueError("Los experimentos no pueden usar semillas de entrenamiento o selección")
    escenarios = construir_escenarios(config, ganador, diseno)
    salida = Path(salida)
    if salida.exists() and any(salida.iterdir()):
        raise FileExistsError("La carpeta de salida debe estar vacía")
    salida.mkdir(parents=True, exist_ok=True)
    raiz = Path(__file__).resolve().parents[1]
    fuentes = sorted([*raiz.glob("src/**/*.py"), *raiz.glob("experiments/**/*.py")])
    manifest = {
        "estado": "en_ejecucion", "inicio_utc": datetime.now(timezone.utc).isoformat(),
        "origen_datos": "sintetico" if "synthetic" in str(config["datos"]["tiendas"]) else "no_declarado",
        "diseno": diseno, "semillas": semillas,
        "escenarios": escenarios, "configuracion_referencia": config,
        "ganador_sha256": huella(Path(ruta_ganador)), "ganador": ganador,
        "diseno_sha256": huella(Path(ruta_diseno)), "config_sha256": huella(Path(ruta_config)),
        "entradas": {n: {"ruta": str(p), "sha256": huella(p)} for n, p in config["datos"].items()},
        "codigo_sha256": {str(p.relative_to(raiz)): huella(p) for p in fuentes},
        "num_tiendas": len(datos["ids_tiendas"]), "num_productos": len(datos["ids_productos"]),
        "horizonte_dias": config["simulacion"]["horizonte_dias"],
        "git_commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
        "git_con_cambios": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=raiz, text=True)),
        "python": platform.python_version(), "plataforma": platform.platform(),
        "dependencias": {n: version(n) for n in ("numpy", "pandas", "networkx", "scipy", "matplotlib", "pyyaml")},
        "trabajadores": trabajadores,
    }
    guardar_json(salida / "manifest.json", manifest)
    inicio = time.perf_counter()
    try:
        tareas = [(e, s, diseno["semilla_series"]) for e in escenarios for s in semillas]
        if trabajadores == 1:
            respuestas = list(map(_replica, tareas))
        else:
            with ProcessPoolExecutor(max_workers=trabajadores) as pool:
                respuestas = list(pool.map(_replica, tareas))
        resultados = pd.DataFrame([r["metricas"] for r in respuestas])
        auditoria = pd.DataFrame([r["auditoria"] for r in respuestas])
        verificacion = validar_resultados(resultados, auditoria, [e["condicion"] for e in escenarios], semillas)
        referencia = Path(ruta_ganador).parent / "evaluacion_final.csv"
        if referencia.exists():
            anterior = pd.read_csv(referencia).set_index("semilla").sort_index()
            actual = resultados[resultados.condicion == "mejorada"].set_index("semilla").sort_index()
            comparables = actual.index.intersection(anterior.index)
            coincide = len(comparables) == len(actual) and np.allclose(
                actual.loc[comparables, list(METRICAS)], anterior.loc[comparables, list(METRICAS)],
                rtol=0, atol=1e-8,
            )
            if not coincide:
                raise ValueError("La evaluación nominal del ganador difiere de la guardada")
            verificacion["ganador_coincide_con_evaluacion_previa"] = True
        resumen = resumir(resultados, diseno["alpha"])
        pruebas, diferencias = comparar_pareado(resultados, diseno["comparaciones"], diseno["alpha"])
        series = pd.DataFrame([fila for r in respuestas for fila in r["series"]])
        bodega = pd.DataFrame([fila for r in respuestas for fila in r["bodega"]])
        for nombre, tabla in (("resultados", resultados), ("auditoria", auditoria), ("resumen", resumen),
                              ("pruebas_pareadas", pruebas), ("diferencias_pareadas", diferencias),
                              ("series_inventario", series), ("series_bodega", bodega)):
            tabla.to_csv(salida / f"{nombre}.csv", index=False)
        guardar_json(salida / "verificaciones.json", verificacion)
        from src.viz.escenarios import graficar_experimentos
        graficar_experimentos(resumen, series, salida / "graficas", config["simulacion"]["horizonte_dias"])
        manifest.update(estado="completado", verificaciones=verificacion)
        print(f"Experimento completado: {len(resultados)} réplicas en {len(escenarios)} condiciones", flush=True)
        return resultados, resumen, pruebas
    except BaseException as exc:
        manifest.update(estado="fallido", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest.update(duracion_segundos=time.perf_counter() - inicio,
                        fin_utc=datetime.now(timezone.utc).isoformat())
        guardar_json(salida / "manifest.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--diseno", default="experiments/diseno.yaml")
    parser.add_argument("--ganador", default="results/optimizacion/semilla_20261109/ganador.json")
    parser.add_argument("--salida", default="results/experimentos/semillas_1001_1030")
    parser.add_argument("--trabajadores", type=int, default=min(6, os.cpu_count() or 1))
    args = parser.parse_args()
    ejecutar(args.config, args.diseno, args.ganador, args.salida, args.trabajadores)


if __name__ == "__main__":
    main()
