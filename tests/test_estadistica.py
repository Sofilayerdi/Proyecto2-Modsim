import numpy as np
import pandas as pd
import pytest

from experiments.estadistica import ajustar_holm, comparar_pareado, intervalo_media


def test_intervalo_t_con_muestra_pequena_y_ddof_uno():
    resumen = intervalo_media([1, 2, 3, 4])
    assert resumen["media"] == 2.5
    assert resumen["desviacion_estandar"] == pytest.approx(np.sqrt(5 / 3))
    margen = 3.182446305284263 * np.sqrt(5 / 3) / 2
    assert resumen["ic95_inferior"] == pytest.approx(2.5 - margen)
    assert resumen["ic95_superior"] == pytest.approx(2.5 + margen)


def test_comparacion_empareja_semilla_no_orden_de_filas():
    a = pd.DataFrame({"condicion": "base", "semilla": [1, 2, 3, 4],
                      "costo_total": [100, 110, 120, 130], "nivel_servicio": [.9, .91, .92, .93]})
    b = pd.DataFrame({"condicion": "mejorada", "semilla": [4, 2, 1, 3],
                      "costo_total": [123, 107, 99, 115], "nivel_servicio": [.94, .92, .91, .93]})
    pruebas, diferencias = comparar_pareado(pd.concat([a, b]), [("base", "mejorada")])
    costo = pruebas[pruebas.metrica == "costo_total"].iloc[0]
    assert costo.diferencia_media == -4
    assert costo.desviacion_diferencias == pytest.approx(np.sqrt(20 / 3))
    assert diferencias[diferencias.metrica == "costo_total"].diferencia.tolist() == [-1, -3, -5, -7]
    assert 0 < costo.p_t <= costo.p_t_holm <= 1


def test_diferencias_nulas_no_generan_nan_ni_significancia():
    tabla = pd.DataFrame({"condicion": ["a"] * 3 + ["b"] * 3, "semilla": [1, 2, 3] * 2,
                          "costo_total": [10, 20, 30] * 2, "nivel_servicio": [.9, .95, 1] * 2})
    pruebas, _ = comparar_pareado(tabla, [("a", "b")])
    assert (pruebas.metodo == "diferencia_nula").all()
    assert (pruebas.p_t == 1).all() and (pruebas.p_wilcoxon == 1).all()
    assert (pruebas.ic95_diferencia_inferior == 0).all()
    assert not pruebas.significativa_holm_005.any()


def test_holm_es_monotono_y_conserva_casos_no_definidos():
    assert ajustar_holm([.01, .04, .03, None]) == [.03, .06, .06, None]


@pytest.mark.parametrize("caso", ["faltante", "duplicado"])
def test_pareamiento_invalido_falla(caso):
    filas = [{"condicion": "a", "semilla": s, "costo_total": 10, "nivel_servicio": .9} for s in [1, 2]]
    filas += [{"condicion": "b", "semilla": s, "costo_total": 12, "nivel_servicio": .91}
              for s in ([1] if caso == "faltante" else [1, 1, 2])]
    with pytest.raises(ValueError):
        comparar_pareado(pd.DataFrame(filas), [("a", "b")])
