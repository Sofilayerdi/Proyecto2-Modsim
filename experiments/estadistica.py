"""Resúmenes e inferencia sobre réplicas, nunca sobre observaciones diarias."""

import numpy as np
import pandas as pd
from scipy import stats

from src.simulation.motor import METRICAS


def intervalo_media(valores, alpha=0.05):
    x = np.asarray(valores, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Se requieren al menos dos observaciones finitas")
    if not 0 < alpha < 1:
        raise ValueError("alpha debe estar entre cero y uno")
    media, desviacion = float(x.mean()), float(x.std(ddof=1))
    margen = float(stats.t.ppf(1 - alpha / 2, len(x) - 1) * desviacion / np.sqrt(len(x)))
    return {"n": len(x), "media": media, "desviacion_estandar": desviacion,
            "ic95_inferior": media - margen, "ic95_superior": media + margen}


def resumir(resultados, alpha=0.05):
    if resultados.duplicated(["condicion", "semilla"]).any():
        raise ValueError("Hay condición/semilla duplicadas")
    filas = []
    for condicion, grupo in resultados.groupby("condicion", sort=False):
        for metrica in METRICAS:
            filas.append({"condicion": condicion, "metrica": metrica,
                          **intervalo_media(grupo[metrica], alpha)})
    return pd.DataFrame(filas)


def ajustar_holm(pvalores):
    """Holm para toda la familia de pruebas t; preserva valores no definidos."""
    salida = [None] * len(pvalores)
    indices = sorted((i for i, p in enumerate(pvalores) if p is not None), key=lambda i: pvalores[i])
    anterior = 0.0
    for posicion, i in enumerate(indices):
        anterior = max(anterior, min(1.0, (len(indices) - posicion) * pvalores[i]))
        salida[i] = anterior
    return salida


def comparar_pareado(resultados, comparaciones, alpha=0.05):
    if resultados.duplicated(["condicion", "semilla"]).any():
        raise ValueError("Hay condición/semilla duplicadas")
    pruebas, diferencias = [], []
    for referencia, alternativa in comparaciones:
        a = resultados[resultados.condicion == referencia].set_index("semilla").sort_index()
        b = resultados[resultados.condicion == alternativa].set_index("semilla").sort_index()
        if a.empty or not a.index.equals(b.index):
            raise ValueError(f"Semillas no emparejadas: {referencia}, {alternativa}")
        for metrica in ("costo_total", "nivel_servicio"):
            delta = (b[metrica] - a[metrica]).to_numpy(dtype=float)
            resumen = intervalo_media(delta, alpha)
            constante = bool(np.allclose(delta, delta[0], rtol=0, atol=1e-12))
            nula = bool(np.all(np.abs(delta) <= 1e-12))
            if constante:
                estadistico, pvalor = None, (1.0 if nula else None)
                metodo = "diferencia_nula" if nula else "diferencia_constante"
            else:
                prueba = stats.ttest_1samp(delta, 0, alternative="two-sided")
                estadistico, pvalor = float(prueba.statistic), float(prueba.pvalue)
                metodo = "t_pareada_bilateral"
            # Comprobación no paramétrica predefinida; no sustituye la prueba primaria.
            if nula:
                w, pw = 0.0, 1.0
            else:
                robusta = stats.wilcoxon(np.round(delta, 12), zero_method="wilcox",
                                        alternative="two-sided", method="auto")
                w, pw = float(robusta.statistic), float(robusta.pvalue)
            media_referencia = float(a[metrica].mean())
            pruebas.append({
                "referencia": referencia, "alternativa": alternativa, "metrica": metrica,
                "metodo": metodo, "n": resumen["n"], "diferencia_media": resumen["media"],
                "desviacion_diferencias": resumen["desviacion_estandar"],
                "ic95_diferencia_inferior": resumen["ic95_inferior"],
                "ic95_diferencia_superior": resumen["ic95_superior"],
                "media_referencia": media_referencia, "media_alternativa": float(b[metrica].mean()),
                "cambio_porcentual_medias": 100 * resumen["media"] / media_referencia if media_referencia else None,
                "estadistico_t": estadistico, "p_t": pvalor,
                "estadistico_wilcoxon": w, "p_wilcoxon": pw,
            })
            diferencias.extend({"referencia": referencia, "alternativa": alternativa,
                                "metrica": metrica, "semilla": int(semilla),
                                "valor_referencia": float(a.loc[semilla, metrica]),
                                "valor_alternativa": float(b.loc[semilla, metrica]),
                                "diferencia": float(d)} for semilla, d in zip(a.index, delta))
    ajustados = ajustar_holm([p["p_t"] for p in pruebas])
    for prueba, ajustado in zip(pruebas, ajustados):
        prueba["p_t_holm"] = ajustado
        prueba["significativa_holm_005"] = ajustado < alpha if ajustado is not None else False
    return pd.DataFrame(pruebas), pd.DataFrame(diferencias)
