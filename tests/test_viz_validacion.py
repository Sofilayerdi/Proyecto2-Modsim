import pandas as pd
import pytest

from src.viz.validacion import graficar_validacion, mae_por_tienda


def ejemplo():
    return pd.DataFrame([
        {"condicion": condicion, "tienda": "CA_1", "semana": semana,
         "ventas_reales": real, "ventas_simuladas": sim}
        for condicion, semana, real, sim in
        [("base", 1, 10, 8), ("base", 2, 0, 4), ("mejorada", 1, 10, 100)]] )


def test_mae_usa_solo_base():
    assert mae_por_tienda(ejemplo())["CA_1"] == 3


def test_graficas_no_sobrescriben(tmp_path):
    rutas = graficar_validacion(ejemplo(), tmp_path)
    assert all(ruta.exists() and ruta.stat().st_size > 0 for ruta in rutas)
    with pytest.raises(FileExistsError):
        graficar_validacion(ejemplo(), tmp_path)
