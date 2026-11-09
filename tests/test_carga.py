from pathlib import Path

import numpy as np
import pytest

from src.simulation.carga import cargar_config, cargar_datos, cargar_demanda, cargar_tiendas

RAIZ = Path(__file__).resolve().parents[1]


def escribir(ruta: Path, texto: str) -> Path:
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def csv_demanda(tiendas, productos, media=2.0, dispersion=1.0, omitir=None) -> str:
    filas = ["id_tienda,id_producto,dia_semana,media,dispersion"]
    for t in tiendas:
        for p in productos:
            for d in range(7):
                if (t, p, d) != omitir:
                    filas.append(f"{t},{p},{d},{media},{dispersion}")
    return "\n".join(filas) + "\n"


# --- cargar_config ---------------------------------------------------------

def test_config_del_repo_carga():
    config = cargar_config(RAIZ / "config.yaml")
    assert config["simulacion"]["horizonte_dias"] > 0
    assert config["datos"]["tiendas"].is_absolute()


def test_config_sin_seccion_falla(tmp_path):
    ruta = escribir(tmp_path / "c.yaml", "simulacion: {}\ndatos: {}\nbodega: {}\nproductos: []\n")
    with pytest.raises(ValueError, match="costos"):
        cargar_config(ruta)


def test_config_vacio_falla(tmp_path):
    with pytest.raises(ValueError, match="vacío"):
        cargar_config(escribir(tmp_path / "c.yaml", ""))


def test_rutas_relativas_a_la_carpeta_del_config(tmp_path):
    texto = (RAIZ / "config.yaml").read_text(encoding="utf-8")
    config = cargar_config(escribir(tmp_path / "c.yaml", texto))
    assert config["datos"]["tiendas"] == tmp_path.resolve() / "data/synthetic/tiendas.csv"


# --- cargar_tiendas ---------------------------------------------------------

def test_tiendas_validas(tmp_path):
    ruta = escribir(tmp_path / "t.csv", "id_tienda,latitud,longitud\n001,14.6,-90.5\n002,14.7,-90.6\n")
    ids, ubicaciones = cargar_tiendas(ruta)
    assert ids == ["001", "002"]  # el id se conserva como texto
    assert ubicaciones.shape == (2, 2)


def test_tiendas_repetidas_fallan(tmp_path):
    ruta = escribir(tmp_path / "t.csv", "id_tienda,latitud,longitud\nA,14.6,-90.5\nA,14.7,-90.6\n")
    with pytest.raises(ValueError, match="repetidos"):
        cargar_tiendas(ruta)


def test_latitud_longitud_invertidas_fallan(tmp_path):
    ruta = escribir(tmp_path / "t.csv", "id_tienda,latitud,longitud\nA,-90.5,14.6\n")
    with pytest.raises(ValueError, match="fuera de rango"):
        cargar_tiendas(ruta)


def test_tiendas_sin_columna_fallan(tmp_path):
    ruta = escribir(tmp_path / "t.csv", "id_tienda,x_km,y_km\nA,1,2\n")
    with pytest.raises(ValueError, match="latitud"):
        cargar_tiendas(ruta)


# --- cargar_demanda ---------------------------------------------------------

def test_demanda_forma_y_valores(tmp_path):
    ruta = escribir(tmp_path / "d.csv", csv_demanda(["A", "B"], ["P1"], media=3.5, dispersion=2.0))
    media, dispersion = cargar_demanda(ruta, ["A", "B"], ["P1"])
    assert media.shape == (2, 1, 7)
    assert np.all(media == 3.5)
    assert np.all(dispersion == 2.0)


def test_demanda_con_fila_faltante_falla(tmp_path):
    ruta = escribir(tmp_path / "d.csv", csv_demanda(["A"], ["P1"], omitir=("A", "P1", 3)))
    with pytest.raises(ValueError, match="se esperaban 7"):
        cargar_demanda(ruta, ["A"], ["P1"])


def test_demanda_con_producto_desconocido_falla(tmp_path):
    ruta = escribir(tmp_path / "d.csv", csv_demanda(["A"], ["P1", "P9"]))
    with pytest.raises(ValueError, match="P9"):
        cargar_demanda(ruta, ["A"], ["P1"])


def test_demanda_con_dispersion_menor_que_uno_falla(tmp_path):
    ruta = escribir(tmp_path / "d.csv", csv_demanda(["A"], ["P1"], dispersion=0.5))
    with pytest.raises(ValueError, match="dispersiones"):
        cargar_demanda(ruta, ["A"], ["P1"])


def test_cargar_datos_devuelve_arreglos_de_solo_lectura(tmp_path):
    escribir(tmp_path / "t.csv", "id_tienda,latitud,longitud\nA,14.6,-90.5\n")
    escribir(tmp_path / "d.csv", csv_demanda(["A"], ["P1"]))
    config = {"productos": [{"id": "P1"}], "datos": {"tiendas": tmp_path / "t.csv", "demanda": tmp_path / "d.csv"}}
    datos = cargar_datos(config)
    with pytest.raises(ValueError):
        datos["media"][0, 0, 0] = 99
