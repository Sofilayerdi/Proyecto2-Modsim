"""Demostración breve de escenarios sintéticos; no modifica resultados guardados."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from src.optimization.adaptador import simular_politica
from src.simulation.carga import cargar_config
from src.simulation.motor import simular


def comparar(config, ganador, semilla=1001, dias=30):
    if dias < 1:
        raise ValueError("El horizonte debe ser de al menos un día")
    config = deepcopy(config)
    config["simulacion"]["horizonte_dias"] = dias
    base = simular(config, None, semilla)
    mejorada = simular_politica(config, ganador, semilla)
    return {"base": base, "mejorada": mejorada,
            "diferencia_costo": mejorada["costo_total"] - base["costo_total"],
            "diferencia_servicio_pp": 100 * (mejorada["nivel_servicio"] - base["nivel_servicio"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--ganador", default="results/optimizacion/semilla_20261109/ganador.json")
    parser.add_argument("--semilla", type=int, default=1001)
    parser.add_argument("--dias", type=int, default=30)
    args = parser.parse_args()
    resultado = comparar(cargar_config(args.config), json.loads(Path(args.ganador).read_text()), args.semilla, args.dias)
    print(f"Demostración sintética: {args.dias} días, semilla {args.semilla}, una réplica")
    print("Métricas por período:              Base         Mejorada")
    for clave, etiqueta, escala in (("costo_total", "Costo total (Q)", 1),
                                   ("nivel_servicio", "Servicio (%)", 100),
                                   ("unidades_perdidas", "Unidades perdidas", 1),
                                   ("num_traspasos", "Viajes", 1)):
        print(f"{etiqueta:26s} {resultado['base'][clave] * escala:12.2f} {resultado['mejorada'][clave] * escala:16.2f}")
    print(f"Cambio de costo (mejorada - base): Q{resultado['diferencia_costo']:+.2f}")
    print(f"Cambio de servicio: {resultado['diferencia_servicio_pp']:+.2f} puntos porcentuales")
    print("Una sola réplica sintética no demuestra una mejora real ni sustituye el estudio experimental.")


if __name__ == "__main__":
    main()
