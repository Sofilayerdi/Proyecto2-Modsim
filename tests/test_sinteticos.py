from pathlib import Path

import pandas as pd
import pytest

from src.simulation.carga import cargar_config, cargar_datos
from src.simulation.sinteticos import generar_sinteticos


def test_datos_reproducibles_completos_y_tipados(tmp_path):
    generar_sinteticos(tmp_path / "a", 123)
    generar_sinteticos(tmp_path / "b", 123)
    for nombre in ("tiendas.csv", "demanda.csv", "procedencia.json"):
        assert (tmp_path / "a" / nombre).read_bytes() == (tmp_path / "b" / nombre).read_bytes()
    config = cargar_config(Path(__file__).resolve().parents[1] / "config.yaml")
    config["datos"] = {"tiendas": tmp_path / "a/tiendas.csv", "demanda": tmp_path / "a/demanda.csv"}
    datos = cargar_datos(config)
    assert datos["media"].shape == (10, 3, 7)
    assert set(datos["tipos_tiendas"]) == {"alta", "media", "baja"}
    assert len(pd.read_csv(config["datos"]["demanda"])) == 210
    with pytest.raises(FileExistsError):
        generar_sinteticos(tmp_path / "a", 123)


def test_tipo_desconocido_falla_antes_de_simular(tmp_path):
    generar_sinteticos(tmp_path, 123)
    tabla = pd.read_csv(tmp_path / "tiendas.csv")
    tabla.loc[0, "tipo_tienda"] = "invalido"
    tabla.to_csv(tmp_path / "tiendas.csv", index=False)
    config = {"productos": [{"id": p} for p in ("P01", "P02", "P03")],
              "datos": {"tiendas": tmp_path / "tiendas.csv", "demanda": tmp_path / "demanda.csv"}}
    with pytest.raises(ValueError, match="tipo_tienda"):
        cargar_datos(config)
