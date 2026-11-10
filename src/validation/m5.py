"""Contraste exploratorio con ventas públicas M5; no valida inventarios reales."""
import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import zipfile

import numpy as np
import pandas as pd

from src.model.traspasos import decidir_traspasos
from src.simulation.carga import cargar_config
from src.simulation.motor import simular_con_datos

STORES = ("CA_1", "CA_2", "CA_3")
ITEMS = ("FOODS_1_001", "FOODS_1_002", "FOODS_1_003")
FIRST_DAY, CAL_DAYS, VAL_DAYS = 1734, 124, 56
SEEDS = range(1001, 1031)


def error_metrics(real, simulated):
    real, simulated = np.asarray(real, float), np.asarray(simulated, float)
    if real.shape != simulated.shape or real.size == 0 or not np.isfinite(real).all() or not np.isfinite(simulated).all():
        raise ValueError("Las series deben ser finitas, no vacías y de igual forma")
    if (real < 0).any() or (simulated < 0).any():
        raise ValueError("Las ventas no pueden ser negativas")
    absolute = np.abs(simulated - real)
    total = real.sum()
    return {"mae": float(absolute.mean()), "error_relativo_pct": float(100 * absolute.sum() / total) if total > 0 else None}


def load_m5(path):
    days = [f"d_{n}" for n in range(FIRST_DAY, FIRST_DAY + CAL_DAYS + VAL_DAYS)]
    with zipfile.ZipFile(path) as archive:
        with archive.open("sales_train_validation.csv") as f:
            df = pd.read_csv(f, usecols=["store_id", "item_id", *days])
        with archive.open("calendar.csv") as f:
            calendar = pd.read_csv(f, usecols=["date"])
    df = df[df.store_id.isin(STORES) & df.item_id.isin(ITEMS)].set_index(["store_id", "item_id"])
    expected = pd.MultiIndex.from_product([STORES, ITEMS], names=["store_id", "item_id"])
    if not df.index.is_unique or not expected.isin(df.index).all():
        raise ValueError("Faltan combinaciones tienda/producto o hay duplicados")
    values = df.loc[expected, days].to_numpy(dtype=float).reshape(len(STORES), len(ITEMS), -1)
    dates = pd.to_datetime(calendar.iloc[FIRST_DAY - 1:FIRST_DAY - 1 + len(days)]["date"]).reset_index(drop=True)
    if len(dates) != len(days) or dates.isna().any() or not np.isfinite(values).all() or (values < 0).any() or not (np.diff(dates.to_numpy()).astype('timedelta64[D]').astype(int) == 1).all():
        raise ValueError("Ventas o fechas inválidas")
    return values, dates


def preparar(values, dates):
    calibration = values[:, :, :CAL_DAYS]
    weekdays = dates[:CAL_DAYS].dt.day_of_week.to_numpy()
    mean = np.zeros((len(STORES), len(ITEMS), 7))
    dispersion = np.ones_like(mean)
    for day in range(7):
        subset = calibration[:, :, weekdays == day]
        mean[:, :, day] = subset.mean(axis=2)
        variance = subset.var(axis=2, ddof=1)
        dispersion[:, :, day] = np.maximum(1, np.divide(variance, mean[:, :, day], out=np.ones_like(variance), where=mean[:, :, day] > 0))
    # Geografía desconocida: ubicaciones hipotéticas, nunca datos de Walmart.
    return {"ids_tiendas": list(STORES), "ids_productos": list(ITEMS),
            "ubicaciones": np.array([[14.60, -90.50], [14.62, -90.52], [14.58, -90.54]]),
            "tipos_tiendas": ["media"] * len(STORES), "media": mean, "dispersion": dispersion}


def run(path, config_path, winner_path, output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("La carpeta de salida debe estar vacía")
    values, dates = load_m5(path)
    data = preparar(values, dates)
    config = cargar_config(config_path)
    config["productos"] = [{"id": item, "margen_q": margin} for item, margin in zip(ITEMS, (12, 35, 90))]
    config["simulacion"].update(horizonte_dias=VAL_DAYS, dia_semana_inicial=int(dates.iloc[CAL_DAYS].day_of_week))
    winner = json.loads(Path(winner_path).read_text())
    weekly = []
    replica_metrics = []
    actual = values[:, :, CAL_DAYS:]
    for condition, params, decide in (("base", None, None), ("mejorada", winner, decidir_traspasos)):
        for seed in SEEDS:
            result = simular_con_datos(deepcopy(config), data, params, seed, detalle=True, decidir=decide)
            sales = result.pop("detalle")["ventas"]
            replica_metrics.append({"condicion": condition, "semilla": seed, **result})
            for week in range(VAL_DAYS // 7):
                for store_idx, store in enumerate(STORES):
                    weekly.append({"condicion": condition, "semilla": seed, "semana": week + 1,
                                   "fecha_inicio": dates.iloc[CAL_DAYS + week * 7].strftime("%Y-%m-%d"),
                                   "tienda": store, "ventas_reales": int(actual[store_idx, :, week*7:(week+1)*7].sum()),
                                   "ventas_simuladas": int(sales[week*7:(week+1)*7, store_idx, :].sum())})
    weekly = pd.DataFrame(weekly)
    means = weekly.groupby(["condicion", "semana", "fecha_inicio", "tienda", "ventas_reales"], as_index=False)["ventas_simuladas"].mean()
    summary = {condition: error_metrics(group.ventas_reales, group.ventas_simuladas)
               for condition, group in means.groupby("condicion")}
    summary["observaciones"] = len(means[means.condicion == "base"])
    summary["total_real"] = int(means[means.condicion == "base"].ventas_reales.sum())
    summary["advertencia"] = "Ventas observadas; inventarios, rutas, costos y operación de Walmart no disponibles. No es validación integral."
    summary["sha256_zip"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    summary["calibracion"] = [str(dates.iloc[0].date()), str(dates.iloc[CAL_DAYS - 1].date())]
    summary["validacion"] = [str(dates.iloc[CAL_DAYS].date()), str(dates.iloc[-1].date())]
    output.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(output / "ventas_semanales_replicas.csv", index=False)
    means.to_csv(output / "ventas_semanales.csv", index=False)
    pd.DataFrame(replica_metrics).to_csv(output / "metricas_replicas.csv", index=False)
    (output / "resumen.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    root = Path(__file__).resolve().parents[2]
    code = sorted((root / "src").rglob("*.py"))
    digest = lambda file: hashlib.sha256(Path(file).read_bytes()).hexdigest()
    manifest = {
        "fuente": "https://github.com/Nixtla/m5-forecasts/blob/main/datasets/m5.zip",
        "sha256_zip": summary["sha256_zip"],
        "config_sha256": digest(config_path), "ganador_sha256": digest(winner_path),
        "codigo_sha256": {str(p.relative_to(root)): digest(p) for p in code},
        "resultados_sha256": {name: digest(output / name) for name in
                              ("ventas_semanales.csv", "ventas_semanales_replicas.csv", "metricas_replicas.csv", "resumen.json")},
        "python": platform.python_version(),
        "dependencias": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "networkx", "pyyaml")},
        "semillas": list(SEEDS), "tiendas": list(STORES), "productos": list(ITEMS),
        "calibracion": summary["calibracion"], "validacion": summary["validacion"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m5", required=True, help="ZIP público M5, conservado fuera del repositorio")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--ganador", default="results/optimizacion/semilla_20261109/ganador.json")
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.m5, args.config, args.ganador, args.salida), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
