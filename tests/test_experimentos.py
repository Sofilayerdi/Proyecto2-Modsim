from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from experiments.comparar import ejecutar
from experiments.escenarios import construir_escenarios
from src.simulation.carga import cargar_config
from src.simulation.motor import simular_con_datos

RAIZ = Path(__file__).resolve().parents[1]


def entradas():
    config = cargar_config(RAIZ / "config.yaml")
    ganador = json.loads((RAIZ / "results/optimizacion/semilla_20261109/ganador.json").read_text())
    diseno = yaml.safe_load((RAIZ / "experiments/diseno.yaml").read_text())
    return config, ganador, diseno


def test_escenarios_aislan_factores_y_no_modifican_entradas():
    config, ganador, diseno = entradas()
    original, genes = deepcopy(config), ganador.copy()
    escenarios = {e["condicion"]: e for e in construir_escenarios(config, ganador, diseno)}
    assert len(escenarios) == 8
    assert config == original and ganador == genes
    assert escenarios["bodega_ajustada"]["politica"] == "ninguna"
    assert escenarios["bodega_ajustada"]["config"]["reposicion"]["bodega"]["s_dias"] == 6
    assert escenarios["traspasos_bodega_base"]["parametros"]["bodega_s_dias"] == 10
    assert escenarios["demanda_mas_20"]["config"]["simulacion"]["factor_referencia_inventario"] == 1
    assert escenarios["un_vehiculo"]["config"]["transporte"]["num_vehiculos"] == 1
    assert escenarios["mejorada"]["config"]["transporte"]["num_vehiculos"] == 2
    assert all(f["factor"] == 2 for f in escenarios["trafico_pesado"]["config"]["transporte"]["trafico"])


def test_aumento_demanda_puede_mantener_existencias_y_reglas_originales():
    config, _, _ = entradas()
    config["simulacion"]["horizonte_dias"] = 15
    datos = {"ids_tiendas": ["a", "b", "c"], "ids_productos": ["P01", "P02", "P03"],
             "ubicaciones": np.zeros((3, 2)), "media": np.full((3, 3, 7), 4.0),
             "dispersion": np.ones((3, 3, 7))}
    base = simular_con_datos(config, datos, None, 1, detalle=True)
    config["simulacion"].update(factor_demanda=1.2, factor_referencia_inventario=1)
    estres = simular_con_datos(config, datos, None, 1, detalle=True)
    for nombre in ("inventario_inicial_tiendas", "inventario_inicial_bodega"):
        assert np.array_equal(base["detalle"][nombre], estres["detalle"][nombre])
    assert not np.array_equal(base["detalle"]["demanda"], estres["detalle"]["demanda"])
    assert estres["detalle"]["balance"]["sistema"] == 0
    del config["simulacion"]["factor_referencia_inventario"]
    escalado = simular_con_datos(config, datos, None, 1, detalle=True)
    assert (escalado["detalle"]["inventario_inicial_tiendas"] > base["detalle"]["inventario_inicial_tiendas"]).all()


def test_ejecutor_guarda_diseno_completo_estadistica_y_graficas(tmp_path):
    config, ganador, diseno = entradas()
    config["simulacion"]["horizonte_dias"] = 8
    diseno["semillas"] = [1001, 1002]
    config_json = json.loads(json.dumps(config, default=str))
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(config_json))
    (tmp_path / "diseno.yaml").write_text(yaml.safe_dump(diseno))
    (tmp_path / "ganador.json").write_text(json.dumps(ganador))
    salida = tmp_path / "salida"
    resultados, resumen, pruebas = ejecutar(tmp_path / "config.yaml", tmp_path / "diseno.yaml",
                                           tmp_path / "ganador.json", salida)
    assert len(resultados) == 16 and len(resumen) == 64 and len(pruebas) == 18
    assert resultados.groupby("condicion").size().eq(2).all()
    assert len(pd.read_csv(salida / "series_inventario.csv")) == 8 * 10 * 3 * 2
    assert len(list((salida / "graficas").glob("*.png"))) == 4
    assert json.loads((salida / "manifest.json").read_text())["estado"] == "completado"
    assert json.loads((salida / "verificaciones.json").read_text())["demanda_nominal_comun"]
    with pytest.raises(FileExistsError):
        ejecutar(tmp_path / "config.yaml", tmp_path / "diseno.yaml", tmp_path / "ganador.json", salida)
