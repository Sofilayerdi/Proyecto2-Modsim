"""Genera el contrato sintético de arranque; no representa una cadena real."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def generar_sinteticos(destino, semilla=20261109):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    nombres = ("tiendas.csv", "demanda.csv", "procedencia.json")
    if any((destino / nombre).exists() for nombre in nombres):
        raise FileExistsError("Los datos ya existen; utilice otra carpeta para no sobrescribirlos")
    rng = np.random.default_rng(semilla)
    tipos = ["alta"] * 3 + ["media"] * 4 + ["baja"] * 3
    factores = {"alta": 1.5, "media": 1.0, "baja": 0.6}
    dispersion = {"alta": 2.0, "media": 4.0, "baja": 6.0}
    semanal = np.array([0.90, 0.85, 0.95, 1.0, 1.15, 1.40, 1.10])
    semanal /= semanal.mean()
    tiendas, demanda = [], []
    for i, tipo in enumerate(tipos):
        identificador = f"T{i + 1:02}"
        tiendas.append({"id_tienda": identificador, "tipo_tienda": tipo,
                        "latitud": 14.60 + rng.uniform(-0.07, 0.07),
                        "longitud": -90.52 + rng.uniform(-0.07, 0.07)})
        for producto, base in zip(("P01", "P02", "P03"), (6.0, 3.0, 1.5)):
            media = base * factores[tipo] * rng.lognormal(-0.25**2 / 2, 0.25)
            for dia, factor in enumerate(semanal):
                demanda.append({"id_tienda": identificador, "id_producto": producto,
                                "dia_semana": dia, "media": media * factor,
                                "dispersion": dispersion[tipo]})
    pd.DataFrame(tiendas).to_csv(destino / "tiendas.csv", index=False, float_format="%.6f")
    pd.DataFrame(demanda).to_csv(destino / "demanda.csv", index=False, float_format="%.6f")
    procedencia = {
        "origen": "sintetico", "semilla": semilla, "num_tiendas": 10,
        "productos": ["P01", "P02", "P03"], "tipos": tipos,
        "descripcion": "Coordenadas ficticias alrededor de (14.60, -90.52); no son tiendas reales",
        "medias_base": [6.0, 3.0, 1.5], "factores_tipo": factores,
        "dispersion_varianza_media": dispersion, "factores_semanales": semanal.tolist(),
        "heterogeneidad": "lognormal con sigma=0.25 y media multiplicativa 1",
    }
    (destino / "procedencia.json").write_text(
        json.dumps(procedencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return procedencia


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", default="data/synthetic")
    parser.add_argument("--semilla", type=int, default=20261109)
    args = parser.parse_args()
    generar_sinteticos(args.salida, args.semilla)
    print(f"Datos sintéticos guardados en {args.salida}")
