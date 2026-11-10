"""Evidencia de convergencia de la persona 3, independiente del dashboard."""


def graficar_convergencia(historial, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ejes = plt.subplots(1, 2, figsize=(11, 4))
    generaciones = [r["generacion"] for r in historial]
    ejes[0].plot(generaciones, [r["mejor_fitness"] for r in historial], label="Mejor fitness")
    ejes[0].plot(generaciones, [r["mejor_costo_promedio"] for r in historial], label="Costo del mejor histórico")
    ejes[0].set(xlabel="Generación", ylabel="Quetzales (Q)", title="Convergencia en entrenamiento")
    ejes[0].legend()
    ejes[1].plot(generaciones, [100 * r["mejor_servicio_promedio"] for r in historial], label="Servicio del mejor histórico")
    ejes[1].axhline(95, linestyle="--", color="red", label="Objetivo: 95%")
    ejes[1].set(xlabel="Generación", ylabel="Nivel de servicio (%)", title="Servicio durante la búsqueda")
    ejes[1].legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
