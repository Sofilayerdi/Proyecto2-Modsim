from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.model.tipos import TIPOS_TIENDA

COLUMNAS_TIENDAS = ("id_tienda", "latitud", "longitud")
COLUMNAS_DEMANDA = ("id_tienda", "id_producto", "dia_semana", "media", "dispersion")

SECCIONES_OBLIGATORIAS = (
    "simulacion",
    "datos",
    "bodega",
    "productos",
    "costos",
    "inventario",
    "reposicion",
    "pronostico",
)


def cargar_config(ruta) -> dict:
    """Lee config.yaml; las rutas de "datos" quedan relativas a la carpeta del config."""
    ruta = Path(ruta)
    with open(ruta, encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)

    if not isinstance(config, dict):
        raise ValueError(f"{ruta} está vacío o no tiene formato de diccionario")

    faltantes = [seccion for seccion in SECCIONES_OBLIGATORIAS if seccion not in config]
    if faltantes:
        raise ValueError(f"{ruta} no tiene las secciones: {faltantes}")

    carpeta = ruta.resolve().parent
    for nombre, ruta_dato in config["datos"].items():
        config["datos"][nombre] = carpeta / ruta_dato

    return config


def cargar_tiendas(ruta) -> tuple[list[str], np.ndarray]:
    """Devuelve ids y ubicaciones (N, 2) = [latitud, longitud]. La tienda i es la fila i."""
    tiendas = pd.read_csv(ruta, dtype={"id_tienda": str})

    faltantes = [col for col in COLUMNAS_TIENDAS if col not in tiendas.columns]
    if faltantes:
        raise ValueError(f"{ruta} no tiene las columnas: {faltantes}")
    if tiendas.empty:
        raise ValueError(f"{ruta} no tiene tiendas")

    repetidos = tiendas.loc[tiendas["id_tienda"].duplicated(), "id_tienda"].tolist()
    if repetidos:
        raise ValueError(f"{ruta} tiene ids de tienda repetidos: {repetidos}")

    ubicaciones = tiendas[["latitud", "longitud"]].to_numpy(dtype=float)
    if np.isnan(ubicaciones).any():
        raise ValueError(f"{ruta} tiene latitudes o longitudes vacías")
    latitud_valida = np.abs(ubicaciones[:, 0]) <= 90
    longitud_valida = np.abs(ubicaciones[:, 1]) <= 180
    if not (latitud_valida.all() and longitud_valida.all()):
        raise ValueError(f"{ruta} tiene coordenadas fuera de rango (¿latitud y longitud invertidas?)")

    return tiendas["id_tienda"].tolist(), ubicaciones


def cargar_demanda(ruta, ids_tiendas, ids_productos) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve media y dispersion (varianza/media), ambas (N, K, 7)."""
    demanda = pd.read_csv(ruta, dtype={"id_tienda": str, "id_producto": str})

    faltantes = [col for col in COLUMNAS_DEMANDA if col not in demanda.columns]
    if faltantes:
        raise ValueError(f"{ruta} no tiene las columnas: {faltantes}")
    if demanda[list(COLUMNAS_DEMANDA)].isna().any().any():
        raise ValueError(f"{ruta} tiene celdas vacías")

    indice_tienda = {id_tienda: i for i, id_tienda in enumerate(ids_tiendas)}
    indice_producto = {id_producto: k for k, id_producto in enumerate(ids_productos)}
    i = demanda["id_tienda"].map(indice_tienda)
    k = demanda["id_producto"].map(indice_producto)

    desconocidas = demanda.loc[i.isna(), "id_tienda"].unique().tolist()
    if desconocidas:
        raise ValueError(f"{ruta} tiene tiendas que no están en tiendas.csv: {desconocidas}")
    desconocidos = demanda.loc[k.isna(), "id_producto"].unique().tolist()
    if desconocidos:
        raise ValueError(f"{ruta} tiene productos que no están en config.yaml: {desconocidos}")

    d = demanda["dia_semana"].to_numpy(dtype=float)
    if not np.all((d >= 0) & (d <= 6) & (d == np.round(d))):
        raise ValueError(f"{ruta}: dia_semana debe ser un entero entre 0 y 6")

    claves = demanda[["id_tienda", "id_producto", "dia_semana"]]
    repetidas = claves[claves.duplicated()].values.tolist()
    if repetidas:
        raise ValueError(f"{ruta} tiene combinaciones repetidas: {repetidas[:5]}")

    num_tiendas, num_productos = len(ids_tiendas), len(ids_productos)
    esperadas = num_tiendas * num_productos * 7
    if len(demanda) != esperadas:
        raise ValueError(
            f"{ruta} tiene {len(demanda)} filas; se esperaban {esperadas} "
            f"({num_tiendas} tiendas × {num_productos} productos × 7 días)"
        )

    if (demanda["media"] < 0).any():
        raise ValueError(f"{ruta} tiene medias negativas")
    if (demanda["dispersion"] < 1).any():
        raise ValueError(f"{ruta} tiene dispersiones menores que 1")

    media = np.zeros((num_tiendas, num_productos, 7))
    dispersion = np.ones((num_tiendas, num_productos, 7))
    indices = (i.to_numpy(dtype=int), k.to_numpy(dtype=int), d.astype(int))
    media[indices] = demanda["media"].to_numpy(dtype=float)
    dispersion[indices] = demanda["dispersion"].to_numpy(dtype=float)
    return media, dispersion


def cargar_datos(config: dict) -> dict:
    ids_productos = [str(producto["id"]) for producto in config["productos"]]
    ids_tiendas, ubicaciones = cargar_tiendas(config["datos"]["tiendas"])
    tabla_tiendas = pd.read_csv(config["datos"]["tiendas"], dtype={"id_tienda": str})
    tipos = tabla_tiendas.get("tipo_tienda", pd.Series(["media"] * len(ids_tiendas))).tolist()
    if any(tipo not in TIPOS_TIENDA for tipo in tipos):
        raise ValueError(f"tipo_tienda debe pertenecer a {TIPOS_TIENDA}")
    media, dispersion = cargar_demanda(config["datos"]["demanda"], ids_tiendas, ids_productos)

    for arreglo in (ubicaciones, media, dispersion):
        arreglo.flags.writeable = False

    return {
        "ids_tiendas": ids_tiendas,
        "ids_productos": ids_productos,
        "ubicaciones": ubicaciones,
        "tipos_tiendas": tipos,
        "media": media,
        "dispersion": dispersion,
    }
