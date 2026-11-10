"""Visualizaciones del contraste de ventas reales y simuladas por tienda."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def mae_por_tienda(ventas):
    """MAE de la venta real contra el promedio de réplicas, en unidades/semana."""
    base = ventas.loc[ventas["condicion"] == "base"].copy()
    if base.empty or base.duplicated(["tienda", "semana"]).any():
        raise ValueError("Se requiere una observación base única por tienda y semana")
    if base[["ventas_reales", "ventas_simuladas"]].isna().any().any():
        raise ValueError("No se permiten ventas vacías")
    base["error_absoluto"] = (base["ventas_reales"] - base["ventas_simuladas"]).abs()
    return base.groupby("tienda")["error_absoluto"].mean().sort_index()


def graficar_validacion(ventas, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos = [carpeta / "ventas_reales_simuladas.png", carpeta / "mae_por_tienda.png"]
    if any(ruta.exists() for ruta in archivos):
        raise FileExistsError("Las gráficas ya existen; use otra carpeta de salida")
    errores = mae_por_tienda(ventas)
    tiendas = errores.index.tolist()
    fig, ejes = plt.subplots(len(tiendas), 1, figsize=(10, 3 * len(tiendas)), sharex=True, squeeze=False)
    for ax, tienda in zip(ejes[:, 0], tiendas):
        subset = ventas[ventas["tienda"] == tienda]
        base = subset[subset["condicion"] == "base"].sort_values("semana")
        ax.plot(base.semana, base.ventas_reales, marker="o", label="Ventas reales", color="#202020")
        for condition, label, color in (("base", "Base simulada", "#52677f"),
                                        ("mejorada", "Mejorada simulada", "#167c80")):
            serie = subset[subset["condicion"] == condition].sort_values("semana")
            if not serie.empty:
                ax.plot(serie.semana, serie.ventas_simuladas, marker=".", label=label, color=color)
        ax.set(title=tienda, ylabel="Ventas (unidades/semana)")
        ax.grid(alpha=.2)
        ax.legend()
    ejes[-1, 0].set_xlabel("Semana de validación (29/02–24/04/2016)")
    fig.suptitle("Ventas M5 observadas y media de 30 réplicas · 3 productos")
    fig.tight_layout()
    fig.savefig(archivos[0], dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(errores.index, errores.values, color="#52677f")
    ax.set(title="Error de la base frente a ventas M5 por tienda",
           xlabel="Tienda", ylabel="MAE (unidades/semana)")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(archivos[1], dpi=160)
    plt.close(fig)
    return archivos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ventas", default="results/validacion/m5/ventas_semanales.csv")
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()
    graficar_validacion(pd.read_csv(args.ventas), args.salida)


if __name__ == "__main__":
    main()
