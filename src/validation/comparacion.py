"""Cierra la comparación M5 con diferencias, incertidumbre y trazabilidad.

Las observaciones reales son ventas; costos, demanda y servicio siguen siendo
magnitudes del modelo. No se rellenan valores reales desconocidos con ceros.
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from experiments.estadistica import comparar_pareado, intervalo_media
from experiments.optimizar import guardar_json, huella
from src.validation.m5 import error_metrics


def tabla_comparacion(real_total, modelos):
    filas = []
    unidades = {"ventas_totales": "unidades", "mae": "unidades/tienda-semana",
                "error_relativo_pct": "%", "costo_total": "Q hipotéticos",
                "servicio_pct": "% de demanda simulada", "unidades_perdidas": "unidades simuladas",
                "num_traspasos": "viajes simulados"}
    for metrica, unidad in unidades.items():
        real = real_total if metrica == "ventas_totales" else None
        base, mejorada = modelos["base"][metrica], modelos["mejorada"][metrica]
        cambio = mejorada - base if base is not None and mejorada is not None else None
        filas.append({
            "metrica": metrica, "unidad": unidad, "real": real, "base": base, "mejorada": mejorada,
            "base_menos_real": base - real if real is not None else None,
            "base_vs_real_pct": 100 * (base - real) / real if real else None,
            "mejorada_menos_real": mejorada - real if real is not None else None,
            "mejorada_vs_real_pct": 100 * (mejorada - real) / real if real else None,
            "mejorada_menos_base": cambio,
            "mejorada_vs_base_pct": 100 * cambio / base if base and cambio is not None else None,
        })
    return pd.DataFrame(filas)


def cerrar(origen, salida, zip_fuente=None, reproduccion=None):
    origen, salida = Path(origen), Path(salida)
    manifest = json.loads((origen / "manifest.json").read_text())
    for nombre, esperado in manifest["resultados_sha256"].items():
        if huella(origen / nombre) != esperado:
            raise ValueError(f"El resultado no coincide con el manifiesto: {nombre}")
    if zip_fuente is not None and huella(Path(zip_fuente)) != manifest["sha256_zip"]:
        raise ValueError("El ZIP no coincide con la fuente M5 registrada")
    if reproduccion is not None:
        for nombre, esperado in manifest["resultados_sha256"].items():
            if huella(Path(reproduccion) / nombre) != esperado:
                raise ValueError(f"La reproducción no coincide: {nombre}")
    ventas = pd.read_csv(origen / "ventas_semanales_replicas.csv")
    medias = pd.read_csv(origen / "ventas_semanales.csv")
    metricas = pd.read_csv(origen / "metricas_replicas.csv")
    semillas = set(manifest["semillas"])
    if metricas.duplicated(["condicion", "semilla"]).any():
        raise ValueError("Réplicas duplicadas")
    for condicion in ("base", "mejorada"):
        if set(metricas.loc[metricas.condicion == condicion, "semilla"]) != semillas:
            raise ValueError("Las semillas deben estar completas y emparejadas")
    observadas = medias[medias.condicion == "base"].ventas_reales
    if len(observadas) != 24:
        raise ValueError("Se requieren 24 observaciones tienda-semana")
    totales = ventas.groupby(["condicion", "semilla"], as_index=False).ventas_simuladas.sum()
    totales = totales.rename(columns={"ventas_simuladas": "ventas_totales"})
    replicas = metricas.merge(totales, on=["condicion", "semilla"], validate="one_to_one")
    modelos, estadistica = {}, []
    for condicion, grupo in replicas.groupby("condicion"):
        semanal = medias[medias.condicion == condicion]
        errores = error_metrics(semanal.ventas_reales, semanal.ventas_simuladas)
        modelos[condicion] = {**errores, "ventas_totales": float(grupo.ventas_totales.mean()),
                             "costo_total": float(grupo.costo_total.mean()),
                             "servicio_pct": float(100 * grupo.nivel_servicio.mean()),
                             "unidades_perdidas": float(grupo.unidades_perdidas.mean()),
                             "num_traspasos": float(grupo.num_traspasos.mean())}
        for metrica in ("ventas_totales", "costo_total", "nivel_servicio", "unidades_perdidas"):
            estadistica.append({"condicion": condicion, "metrica": metrica,
                               **intervalo_media(grupo[metrica])})
    pruebas, diferencias = comparar_pareado(replicas, [("base", "mejorada")])
    if salida.exists() and any(salida.iterdir()):
        raise FileExistsError("La carpeta de cierre debe estar vacía")
    salida.mkdir(parents=True, exist_ok=True)
    tabla = tabla_comparacion(float(observadas.sum()), modelos)
    for nombre, datos in (("comparacion_real", tabla), ("estadistica_modelo", pd.DataFrame(estadistica)),
                          ("pruebas_modelo", pruebas), ("diferencias_modelo", diferencias)):
        datos.to_csv(salida / f"{nombre}.csv", index=False)
    resumen = {
        "alcance": "Contraste externo parcial de ventas M5; no validación operativa de Walmart",
        "observaciones_reales": 24, "replicas_por_condicion": len(semillas),
        "ventas_reales_totales": int(observadas.sum()), "modelos": modelos,
        "replicas_servicio_bajo_95": {c: int((g.nivel_servicio < .95).sum())
                                      for c, g in replicas.groupby("condicion")},
        "sin_traspasos_en_m5": bool(replicas.num_traspasos.eq(0).all()),
        "zip_fuente_verificado": zip_fuente is not None,
        "reproduccion_exacta_cuatro_archivos": reproduccion is not None,
        "sha256_zip": manifest["sha256_zip"],
        "resultado_fuente_sha256": manifest["resultados_sha256"],
        "codigo_comparacion_sha256": huella(Path(__file__)),
        "estadistica_sha256": huella(Path(__file__).resolve().parents[2] / "experiments/estadistica.py"),
        "interpretacion_ic": "Incertidumbre Monte Carlo del modelo; no IC del desempeño real",
        "interpretacion_pruebas": "Dos pruebas t del modelo, ajuste Holm dentro de M5; no mejora real",
    }
    guardar_json(salida / "resumen.json", resumen)
    return tabla, resumen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", default="results/validacion/m5")
    parser.add_argument("--salida", default="results/validacion/cierre_m5")
    parser.add_argument("--zip-fuente")
    parser.add_argument("--reproduccion")
    args = parser.parse_args()
    cerrar(args.origen, args.salida, args.zip_fuente, args.reproduccion)
