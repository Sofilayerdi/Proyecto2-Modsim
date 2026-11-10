"""Ejecuta la optimización de la persona 3 y conserva evidencia por etapa."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import pandas as pd

from src.optimization.adaptador import simular_politica
from src.optimization.cromosoma import RANGOS
from src.optimization.optimizador import optimizar_politica
from src.simulation.carga import cargar_config, cargar_datos


def guardar_json(ruta, contenido):
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(json.dumps(contenido, indent=2, ensure_ascii=False, default=str,
                                   allow_nan=False) + "\n", encoding="utf-8")
    temporal.replace(ruta)


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def ejecutar(ruta_config, salida, trabajadores=1):
    if trabajadores < 1:
        raise ValueError("trabajadores debe ser positivo")
    config = cargar_config(ruta_config)
    datos = cargar_datos(config)  # Fallar antes de iniciar procesos si hay entradas inválidas.
    opciones = config["optimizacion"]
    salida = Path(salida)
    if salida.exists() and any(salida.iterdir()):
        raise FileExistsError("La carpeta de salida debe estar vacía; no se sobrescriben ejecuciones")
    salida.mkdir(parents=True, exist_ok=True)
    raiz = Path(__file__).resolve().parents[1]
    fuentes = sorted([*raiz.glob("src/**/*.py"), *raiz.glob("experiments/**/*.py")])
    codigo = {str(p.relative_to(raiz)): huella(p) for p in fuentes}
    entradas = {nombre: {"ruta": str(ruta), "sha256": huella(ruta)}
                for nombre, ruta in config["datos"].items()}
    manifest = {
        "estado": "en_ejecucion", "inicio_utc": datetime.now(timezone.utc).isoformat(),
        "origen_datos": "sintetico" if "synthetic" in str(config["datos"]["tiendas"]) else "no_declarado",
        "num_tiendas": len(datos["ids_tiendas"]), "num_productos": len(datos["ids_productos"]),
        "tipos_tiendas": dict(zip(datos["ids_tiendas"], datos["tipos_tiendas"])),
        "horizonte_dias": config["simulacion"]["horizonte_dias"],
        "configuracion": config, "rangos_genes": RANGOS,
        "entradas": entradas, "codigo_sha256": codigo, "config_sha256": huella(Path(ruta_config)),
        "git_commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
        "git_con_cambios": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=raiz, text=True)),
        "python": platform.python_version(), "plataforma": platform.platform(),
        "dependencias": {n: version(n) for n in ("numpy", "pandas", "networkx", "pyyaml", "matplotlib")},
        "trabajadores": trabajadores,
    }
    guardar_json(salida / "manifest.json", manifest)
    inicio = time.perf_counter()

    def progreso(estado):
        guardar_json(salida / "progreso.json", estado)
        pd.DataFrame(estado["historial"]).to_csv(salida / "historial.csv", index=False)
        fila = estado["historial"][-1]
        print(f"Generación {fila['generacion']}: fitness={fila['mejor_fitness']:.4f}; "
              f"candidatos únicos={fila['candidatos_unicos_evaluados']}", flush=True)

    def semillas(nombre):
        primero, ultimo = opciones[nombre]
        if not isinstance(primero, int) or not isinstance(ultimo, int) or primero > ultimo:
            raise ValueError(f"Rango inválido: {nombre}")
        return range(primero, ultimo + 1)

    kwargs = dict(
        config=config, simulador=simular_politica,
        tamano_poblacion=opciones["tamano_poblacion"], generaciones=opciones["generaciones"],
        semilla_genetico=opciones["semilla_genetico"], paciencia=opciones["paciencia"],
        semillas_entrenamiento=semillas("semillas_entrenamiento"),
        semillas_reevaluacion=semillas("semillas_reevaluacion"),
        semillas_finales=semillas("semillas_evaluacion_final"), progreso=progreso,
    )
    try:
        if trabajadores == 1:
            resultado = optimizar_politica(**kwargs)
        else:
            with ProcessPoolExecutor(max_workers=trabajadores) as pool:
                resultado = optimizar_politica(**kwargs, mapear=pool.map)
        guardar_json(salida / "resultado.json", resultado)
        guardar_json(salida / "ganador.json", resultado["mejor_cromosoma"])
        pd.DataFrame(resultado["evaluacion_final"]["replicas"]).to_csv(
            salida / "evaluacion_final.csv", index=False,
        )
        filas = []
        for i, candidato in enumerate(resultado["candidatos_reevaluados"], start=1):
            filas.extend({"candidato": i, **replica} for replica in candidato["replicas"])
        pd.DataFrame(filas).to_csv(salida / "reevaluacion.csv", index=False)
        from src.optimization.graficas import graficar_convergencia
        graficar_convergencia(resultado["historial_detallado"], salida / "convergencia.png")
        manifest.update(estado="completado", semillas=resultado["semillas"],
                        generaciones_ejecutadas=resultado["generaciones_ejecutadas"],
                        motivo_paro=resultado["motivo_paro"])
        print(f"Optimización completada: {salida}", flush=True)
        return resultado
    except BaseException as exc:
        manifest.update(estado="fallido", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["duracion_segundos"] = time.perf_counter() - inicio
        manifest["fin_utc"] = datetime.now(timezone.utc).isoformat()
        guardar_json(salida / "manifest.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--salida", default="results/optimizacion/semilla_20261109")
    parser.add_argument("--trabajadores", type=int, default=min(6, os.cpu_count() or 1))
    args = parser.parse_args()
    ejecutar(args.config, args.salida, args.trabajadores)


if __name__ == "__main__":
    main()
