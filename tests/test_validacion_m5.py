import numpy as np
import pandas as pd
import pytest
import zipfile

from src.validation import m5
from src.validation.m5 import CAL_DAYS, ITEMS, STORES, VAL_DAYS, error_metrics, preparar


def test_error_agregado_y_ceros():
    result = error_metrics([0, 10], [2, 8])
    assert result == {"mae": 2.0, "error_relativo_pct": 40.0}
    assert error_metrics([0], [1])["error_relativo_pct"] is None


def test_error_rechaza_formas_y_nan():
    with pytest.raises(ValueError):
        error_metrics([1, 2], [1])
    with pytest.raises(ValueError):
        error_metrics([1], [np.nan])
    with pytest.raises(ValueError):
        error_metrics([-1], [1])


def test_calibracion_no_usa_periodo_de_validacion():
    dates = pd.Series(pd.date_range("2015-10-28", periods=CAL_DAYS + VAL_DAYS))
    values = np.ones((len(STORES), len(ITEMS), CAL_DAYS + VAL_DAYS))
    baseline = preparar(values, dates)
    values[:, :, CAL_DAYS:] = 999
    changed = preparar(values, dates)
    np.testing.assert_equal(baseline["media"], changed["media"])
    np.testing.assert_equal(baseline["dispersion"], changed["dispersion"])
    assert (baseline["dispersion"] >= 1).all()


def test_flujo_integral_y_salida_no_se_sobrescribe(tmp_path, monkeypatch):
    days = [f"d_{i}" for i in range(m5.FIRST_DAY, m5.FIRST_DAY + CAL_DAYS + VAL_DAYS)]
    rows = [{"store_id": store, "item_id": item, **dict.fromkeys(days, 1)}
            for store in STORES for item in ITEMS]
    calendar = pd.DataFrame({"date": pd.date_range("2011-01-29", periods=m5.FIRST_DAY - 1 + len(days))})
    source = tmp_path / "m5.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("sales_train_validation.csv", pd.DataFrame(rows).to_csv(index=False))
        archive.writestr("calendar.csv", calendar.to_csv(index=False))
    monkeypatch.setattr(m5, "SEEDS", range(1001, 1003))
    destination = tmp_path / "salida"
    summary = m5.run(source, "config.yaml", "results/optimizacion/semilla_20261109/ganador.json", destination)
    weekly = pd.read_csv(destination / "ventas_semanales_replicas.csv")
    assert len(weekly) == 2 * 2 * 8 * 3
    assert summary["observaciones"] == 24
    assert summary["total_real"] == 3 * 3 * VAL_DAYS
    assert (destination / "manifest.json").is_file()
    with pytest.raises(ValueError, match="vacía"):
        m5.run(source, "config.yaml", "results/optimizacion/semilla_20261109/ganador.json", destination)
