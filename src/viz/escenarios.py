from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments.escenarios import ETIQUETAS

COLORES = ["#52677f", "#db9b35", "#167c80", "#b56576", "#7465a8"]


def _barras(ax, resumen, condiciones, metrica, titulo, unidad, porcentaje=False):
    tabla = resumen[resumen.metrica == metrica].set_index("condicion").loc[condiciones]
    escala = 100 if porcentaje else 1
    medias = tabla.media.to_numpy() * escala
    inferior = tabla.ic95_inferior.to_numpy() * escala
    superior = tabla.ic95_superior.to_numpy() * escala
    x = np.arange(len(condiciones))
    ax.bar(x, medias, yerr=np.array([medias - inferior, superior - medias]),
           color=COLORES[:len(condiciones)], capsize=4)
    ax.set_xticks(x, [ETIQUETAS[c] for c in condiciones], rotation=15, ha="right")
    ax.set(title=titulo, ylabel=unidad)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    if porcentaje:
        ax.axhline(95, linestyle="--", color="#a33d3d", label="Objetivo 95%")
        ax.set_ylim(min(95, float(inferior.min()) - .5), 100)
        ax.legend(fontsize=9)
    else:
        ax.set_ylim(bottom=0)


def graficar_experimentos(resumen, series, carpeta, horizonte_dias):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    principales = ["base", "regla_simple", "mejorada"]
    fig, ejes = plt.subplots(1, 2, figsize=(12, 4.8))
    _barras(ejes[0], resumen, principales, "costo_total", "Costo total: media e IC del 95%",
            f"Costo por {horizonte_dias} días (Q)")
    _barras(ejes[1], resumen, principales, "nivel_servicio", "Servicio: media e IC del 95%",
            "Demanda atendida (%)", porcentaje=True)
    n = int(resumen.n.iloc[0])
    fig.suptitle(f"Comparación de políticas · {n} réplicas pareadas · datos de configuración")
    fig.tight_layout()
    fig.savefig(carpeta / "comparacion_escenarios.png", dpi=160)
    plt.close(fig)

    sensibilidad = ["mejorada", "demanda_mas_20", "trafico_pesado", "un_vehiculo"]
    fig, ejes = plt.subplots(1, 2, figsize=(13, 4.8))
    _barras(ejes[0], resumen, sensibilidad, "costo_total", "Costo ante cambios de condiciones",
            f"Costo por {horizonte_dias} días (Q)")
    _barras(ejes[1], resumen, sensibilidad, "nivel_servicio", "Servicio ante cambios de condiciones",
            "Demanda atendida (%)", porcentaje=True)
    fig.suptitle("Sensibilidad del ganador congelado · medias e IC del 95%")
    fig.tight_layout()
    fig.savefig(carpeta / "sensibilidad.png", dpi=160)
    plt.close(fig)

    # Selección a priori: primera tienda de cada tipo, último producto (P03).
    producto = sorted(series.id_producto.unique())[-1]
    tiendas = []
    for tipo in ("alta", "media", "baja"):
        candidatas = sorted(series.loc[series.tipo_tienda == tipo, "id_tienda"].unique())
        if candidatas:
            tiendas.append((tipo, candidatas[0]))
    fig, ejes = plt.subplots(len(tiendas), 1, figsize=(12, 3 * len(tiendas)), sharex=True, squeeze=False)
    for ax, (tipo, tienda) in zip(ejes[:, 0], tiendas):
        seleccion = series[(series.id_tienda == tienda) & (series.id_producto == producto)]
        for condicion, color in (("base", COLORES[0]), ("mejorada", COLORES[2])):
            datos = seleccion[seleccion.condicion == condicion].sort_values("dia")
            ax.plot(datos.dia, datos.inventario_cierre, label=ETIQUETAS[condicion], color=color, alpha=.85)
        ax.set(title=f"{tienda}: demanda {tipo} · producto {producto}", ylabel="Inventario (unidades)")
        ax.grid(alpha=.2)
        ax.legend(loc="upper right")
    ejes[-1, 0].set_xlabel("Día simulado (0 = lunes inicial)")
    fig.suptitle(f"Inventario al cierre · semilla {int(series.semilla.iloc[0])} · ejemplo, no promedio")
    fig.tight_layout()
    fig.savefig(carpeta / "inventario_temporal.png", dpi=160)
    plt.close(fig)

    condiciones = ["base", "regla_simple", "mejorada", "bodega_ajustada", "traspasos_bodega_base"]
    fig, ax = plt.subplots(figsize=(12, 5))
    acumulado = np.zeros(len(condiciones))
    for metrica, etiqueta, color in zip(
        ("costo_inventario", "costo_traslado", "costo_ventas_perdidas"),
        ("Mantener inventario", "Traspasos", "Ventas perdidas"), COLORES,
    ):
        valores = resumen[resumen.metrica == metrica].set_index("condicion").loc[condiciones, "media"].to_numpy()
        ax.bar(np.arange(len(condiciones)), valores, bottom=acumulado, label=etiqueta, color=color)
        acumulado += valores
    ax.set_xticks(np.arange(len(condiciones)), [ETIQUETAS[c] for c in condiciones], rotation=15, ha="right")
    ax.set(title=f"Desglose de costos y controles de atribución · medias de {n} réplicas",
           ylabel=f"Costo por {horizonte_dias} días (Q)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(carpeta / "desglose_costos.png", dpi=160)
    plt.close(fig)
