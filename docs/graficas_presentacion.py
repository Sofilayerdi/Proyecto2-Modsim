"""Gráficas legibles para exposición, derivadas solo de resultados guardados."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

AZUL, VERDE, AMBAR, TINTA = "#7393b3", "#167c80", "#dfa553", "#193442"


def generar_figuras(raiz):
    raiz = Path(raiz)
    destino = raiz / "docs/figuras"
    destino.mkdir(parents=True, exist_ok=True)
    experimento = raiz / "results/experimentos/semillas_1001_1030"
    resumen = pd.read_csv(experimento / "resumen.csv")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13,
                         "axes.titlesize": 16, "axes.labelsize": 13,
                         "xtick.labelsize": 12, "ytick.labelsize": 12,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#b9cbd2", "text.color": TINTA,
                         "axes.labelcolor": TINTA, "xtick.color": TINTA,
                         "ytick.color": TINTA, "svg.hashsalt": "proyecto2-presentacion"})

    def guardar(fig, nombre):
        fig.tight_layout(pad=1.4)
        fig.savefig(destino / f"{nombre}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
        plt.close(fig)

    def barras(ax, condiciones, etiquetas, metrica, titulo, porcentaje=False):
        t = resumen[resumen.metrica == metrica].set_index("condicion").loc[condiciones]
        escala = 100 if porcentaje else 1
        valores = t.media.to_numpy() * escala
        error = np.array([t.media - t.ic95_inferior, t.ic95_superior - t.media]) * escala
        colores = [VERDE if c == "mejorada" else AMBAR if c in ("regla_simple", "demanda_mas_20") else AZUL
                   for c in condiciones]
        barras_ = ax.bar(etiquetas, valores, color=colores, width=.58,
                         yerr=error, capsize=5, error_kw={"elinewidth": 1.6})
        ax.set_title(titulo, pad=25)
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
        ax.bar_label(barras_, labels=[f"{v:.2f}%" if porcentaje else f"{v:,.0f}" for v in valores],
                     padding=15 if porcentaje else 18, fontsize=13, fontweight="bold")
        if porcentaje:
            ax.set_ylim(95, 100)
            ax.axhline(95, linestyle="--", color="#ad7136", linewidth=1)
            ax.set_ylabel("Demanda atendida (%) · eje desde 95%")
        else:
            ax.set_ylim(0, float((t.ic95_superior * escala).max()) * 1.17)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
            ax.set_ylabel("Costo por 120 días (Q)")

    fig, axes = plt.subplots(1, 2, figsize=(13, 3.9))
    condiciones = ["base", "regla_simple", "mejorada"]
    etiquetas = ["Base", "Regla simple", "Mejorada"]
    barras(axes[0], condiciones, etiquetas, "costo_total", "Costo medio e IC del 95%")
    barras(axes[1], condiciones, etiquetas, "nivel_servicio", "Servicio medio e IC del 95%", True)
    guardar(fig, "comparacion_presentacion")

    historia = pd.read_csv(raiz / "results/optimizacion/semilla_20261109/historial.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 3.9))
    axes[0].plot(historia.generacion, historia.mejor_fitness, color=VERDE, linewidth=3)
    axes[0].set(title="Mejor fitness histórico", xlabel="Generación", ylabel="Fitness (Q)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    axes[1].plot(historia.generacion, historia.mejor_servicio_promedio * 100, color=VERDE, linewidth=3)
    axes[1].axhline(95, color=AMBAR, linestyle="--", label="Objetivo 95%")
    axes[1].set(title="Servicio del mejor histórico", xlabel="Generación", ylabel="Demanda atendida (%)", ylim=(94.8, 99))
    axes[1].legend(loc="lower right", frameon=False)
    for ax in axes:
        ax.grid(alpha=.18)
        ax.set_xticks([1, 4, 8, 12, 18])
    guardar(fig, "convergencia_presentacion")

    condiciones = ["base", "bodega_ajustada", "mejorada"]
    fig, ax = plt.subplots(figsize=(12, 4))
    acumulado = np.zeros(3)
    for metrica, etiqueta, color in (("costo_inventario", "Inventario", AZUL),
                                     ("costo_traslado", "Traspasos", AMBAR),
                                     ("costo_ventas_perdidas", "Ventas perdidas", VERDE)):
        valores = resumen[resumen.metrica == metrica].set_index("condicion").loc[condiciones, "media"].to_numpy()
        ax.bar(["Base", "Bodega ajustada\nsin traspasos", "Mejorada"], valores,
               bottom=acumulado, label=etiqueta, color=color, width=.5)
        acumulado += valores
    for x, valor in enumerate(acumulado):
        ax.text(x, valor + 600, f"Q{valor:,.2f}", ha="center", fontweight="bold", fontsize=13)
    ax.set(ylim=(0, 37000), ylabel="Costo medio por 120 días (Q)")
    ax.legend(loc="upper right", frameon=False, ncol=3, bbox_to_anchor=(1, 1.2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)
    guardar(fig, "atribucion_presentacion")

    fig, axes = plt.subplots(1, 2, figsize=(13, 3.9))
    condiciones = ["mejorada", "demanda_mas_20", "trafico_pesado", "un_vehiculo"]
    etiquetas = ["Nominal", "Demanda\n+20%", "Tráfico\npesado", "Un vehículo"]
    barras(axes[0], condiciones, etiquetas, "costo_total", "Costo del ganador congelado")
    barras(axes[1], condiciones, etiquetas, "nivel_servicio", "Servicio del ganador congelado", True)
    guardar(fig, "sensibilidad_presentacion")

    series = pd.read_csv(experimento / "series_inventario.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 3.8), sharex=True)
    for ax, tienda, tipo in zip(axes, ("T01", "T08"), ("alta", "baja")):
        for condicion, etiqueta, color in (("base", "Base", AZUL), ("mejorada", "Mejorada", VERDE)):
            filas = series[(series.condicion == condicion) & (series.id_tienda == tienda) & (series.id_producto == "P03")]
            ax.plot(filas.dia, filas.inventario_cierre, color=color, label=etiqueta, linewidth=2)
        ax.set(title=f"{tienda} · demanda {tipo}", xlabel="Día", ylabel="Inventario al cierre (unidades)")
        ax.set_xticks([0, 30, 60, 90, 120])
        ax.grid(alpha=.18)
        ax.legend(frameon=False)
    guardar(fig, "inventario_presentacion")

    ventas = pd.read_csv(raiz / "results/validacion/m5/ventas_semanales.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9), sharex=True)
    for ax, tienda in zip(axes, ("CA_1", "CA_2", "CA_3")):
        t = ventas[(ventas.tienda == tienda) & (ventas.condicion == "base")].sort_values("semana")
        ax.plot(t.semana, t.ventas_reales, color=TINTA, marker="o", label="Real M5", linewidth=2)
        for condicion, etiqueta, color in (("base", "Base", AZUL), ("mejorada", "Mejorada", VERDE)):
            t = ventas[(ventas.tienda == tienda) & (ventas.condicion == condicion)].sort_values("semana")
            ax.plot(t.semana, t.ventas_simuladas, color=color, marker=".", label=etiqueta, linewidth=2)
        ax.set(title=tienda, xlabel="Semana de contraste", ylabel="Ventas (unidades/semana)")
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8])
        ax.grid(alpha=.18)
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, 1.35), ncol=3, frameon=False)
    guardar(fig, "ventas_m5_presentacion")

    base = ventas[ventas.condicion == "base"].copy()
    base["error"] = (base.ventas_simuladas - base.ventas_reales).abs()
    errores = base.groupby("tienda").error.mean()
    fig, ax = plt.subplots(figsize=(10.5, 3.9))
    bars = ax.bar(errores.index, errores.values, color=VERDE, width=.45)
    ax.bar_label(bars, labels=[f"{e:.2f}" for e in errores], padding=9, fontsize=16, fontweight="bold")
    ax.set(ylabel="MAE (unidades/tienda-semana)", ylim=(0, 7))
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)
    guardar(fig, "mae_m5_presentacion")
    return sorted(destino.glob("*_presentacion.svg"))
