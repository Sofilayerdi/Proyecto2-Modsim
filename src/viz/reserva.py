from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLOR = "#52677f"
TINTA = "#52514e"
REJILLA = "#e1e0d9"
REFERENCIA_LITERATURA = 8.3  # % de productos agotados en anaquel (Gruen et al., 2002)


def graficar_reserva(resumen, ruta, etiqueta="{} días"):
    """Ahorro y ganancia de servicio de los traspasos frente a los faltantes sin traspasos."""
    x = resumen.dias_agotado_sin_pct.to_numpy()
    fig, ejes = plt.subplots(1, 2, figsize=(12, 4.6))
    paneles = (
        (ejes[0], resumen.ahorro_pct.to_numpy(),
         (resumen.ahorro_pct - resumen.ahorro_pct_ic_inf).to_numpy(),
         (resumen.ahorro_pct_ic_sup - resumen.ahorro_pct).to_numpy(),
         "Ahorro de los traspasos: media e IC del 95%", "Ahorro sobre el costo sin traspasos (%)"),
        (ejes[1], resumen.ganancia_servicio_pp.to_numpy(), None, None,
         "Ganancia de servicio de los traspasos", "Puntos porcentuales"),
    )
    for ax, y, abajo, arriba, titulo, unidad in paneles:
        ax.axvspan(REFERENCIA_LITERATURA - .5, REFERENCIA_LITERATURA + .5, color=REJILLA, zorder=0)
        ax.text(REFERENCIA_LITERATURA, .98, "retail ~8 %", transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=8, color=TINTA)
        ax.axhline(0, color="#c3c2b7", linewidth=1)
        yerr = None if abajo is None else np.vstack([abajo, arriba])
        ax.errorbar(x, y, yerr=yerr, color=COLOR, marker="o", markersize=7, linewidth=2, capsize=4)
        for xi, yi, nivel in zip(x, y, resumen.nivel):
            ax.annotate(etiqueta.format(nivel), (xi, yi), textcoords="offset points", xytext=(6, 6),
                        fontsize=8, color=TINTA)
        ax.set(title=titulo, ylabel=unidad,
               xlabel="Días tienda-producto agotados sin traspasos (%)")
        ax.grid(alpha=.3, color=REJILLA)
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
    fig.tight_layout()
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=160)
    plt.close(fig)


SERIES = (
    ("por_entrega", "Entrega bodega → tienda más lenta", "#008a7e", "o", "L = {} d"),
    ("por_reserva", "Menos reserva en las tiendas", "#c47a12", "s", "S = {} d"),
)


def graficar_factores(carpeta_resultados, ruta, figsize=(10, 5.2), formato=None):
    """Ahorro de los traspasos según los faltantes que genera cada factor (una sola escala)."""
    import pandas as pd

    carpeta_resultados = Path(carpeta_resultados)
    fig, ax = plt.subplots(figsize=figsize)
    ax.axhline(0, color="#c3c2b7", linewidth=1.2, zorder=1)
    for carpeta, nombre, color, marcador, etiqueta in SERIES:
        r = pd.read_csv(carpeta_resultados / carpeta / "resumen_niveles.csv").sort_values("dias_agotado_sin_pct")
        x, y = r.dias_agotado_sin_pct.to_numpy(), r.ahorro_pct.to_numpy()
        error = np.vstack([y - r.ahorro_pct_ic_inf.to_numpy(), r.ahorro_pct_ic_sup.to_numpy() - y])
        ax.errorbar(x, y, yerr=error, color=color, marker=marcador, markersize=9, linewidth=2,
                    capsize=4, label=nombre, zorder=3, markeredgecolor="white", markeredgewidth=1.5)
        base = r.nivel.iloc[0]  # el nivel con menos faltantes es el escenario base en ambos factores
        for xi, yi, nivel, p in zip(x, y, r.nivel, r.p_holm_costo):
            if nivel == base:
                if carpeta == "por_reserva":
                    ax.annotate("Base", (xi, yi), textcoords="offset points", xytext=(-14, 0), ha="right", va="center",
                                color=TINTA, fontsize=plt.rcParams["font.size"] * .85, fontweight="bold")
                continue
            texto = etiqueta.format(nivel) + (" *" if p < .05 and yi > 0 else "")
            posicion = dict(xytext=(12, -2), ha="left", va="center") if carpeta == "por_entrega" \
                else dict(xytext=(0, -20), ha="center", va="top")
            ax.annotate(texto, (xi, yi), textcoords="offset points", color=TINTA,
                        fontsize=plt.rcParams["font.size"] * .85,
                        bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.9), **posicion)
    ax.set(xlabel="Días tienda-producto agotados sin traspasos (%)",
           ylabel="Ahorro de los traspasos (% del costo)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0f}%" if v else "0%"))
    ax.grid(alpha=.35, color=REJILLA)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=160, format=formato, bbox_inches="tight", facecolor="white",
                metadata={"Date": None} if str(ruta).endswith(".svg") else None)
    plt.close(fig)


if __name__ == "__main__":
    graficar_factores("results/reserva", "results/reserva/condiciones_traspasos.png")
