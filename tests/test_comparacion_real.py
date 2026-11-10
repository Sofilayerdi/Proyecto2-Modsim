from pathlib import Path

import pandas as pd
import pytest

from src.validation.comparacion import cerrar, tabla_comparacion


def modelos():
    a = {"ventas_totales": 80, "mae": 2, "error_relativo_pct": 20,
         "costo_total": 1000, "servicio_pct": 96, "unidades_perdidas": 4, "num_traspasos": 0}
    return {"base": a, "mejorada": {**a, "ventas_totales": 75, "costo_total": 900}}


def test_diferencias_reales_y_costos_no_observados():
    tabla = tabla_comparacion(100, modelos()).set_index("metrica")
    assert tabla.loc["ventas_totales", "base_vs_real_pct"] == -20
    assert tabla.loc["ventas_totales", "mejorada_menos_real"] == -25
    assert tabla.loc["ventas_totales", "mejorada_vs_base_pct"] == -6.25
    assert pd.isna(tabla.loc["costo_total", "real"])
    assert pd.isna(tabla.loc["costo_total", "base_menos_real"])
    assert tabla.loc["costo_total", "mejorada_vs_base_pct"] == -10


def test_referencia_cero_no_produce_porcentajes_infinitos():
    tabla = tabla_comparacion(0, modelos()).set_index("metrica")
    assert pd.isna(tabla.loc["ventas_totales", "base_vs_real_pct"])


def test_cierre_recalcula_evidencia_guardada_sin_validacion_ficticia(tmp_path):
    origen = Path(__file__).resolve().parents[1] / "results/validacion/m5"
    tabla, resumen = cerrar(origen, tmp_path / "cierre")
    assert resumen["ventas_reales_totales"] == 426
    assert resumen["replicas_por_condicion"] == 30
    assert resumen["replicas_servicio_bajo_95"] == {"base": 9, "mejorada": 12}
    assert not resumen["zip_fuente_verificado"]
    assert not resumen["reproduccion_exacta_cuatro_archivos"]
    assert resumen["sin_traspasos_en_m5"]
    assert len(tabla) == 7
    assert len(pd.read_csv(tmp_path / "cierre/estadistica_modelo.csv")) == 8
    with pytest.raises(FileExistsError):
        cerrar(origen, tmp_path / "cierre")


def test_zip_incorrecto_no_se_certifica(tmp_path):
    falso = tmp_path / "m5.zip"
    falso.write_bytes(b"otro archivo")
    with pytest.raises(ValueError, match="ZIP"):
        cerrar(Path(__file__).resolve().parents[1] / "results/validacion/m5", tmp_path / "cierre", falso)
