from dataclasses import dataclass

import numpy as np


@dataclass
class Traspaso:
    origen: int
    destino: int
    producto: int
    cantidad: int
    dia_llegada: int     # debe ser posterior al día actual
    costo: float = 0.0   # Q
    km: float = 0.0
    # Líneas del mismo viaje consolidado comparten id; costo/km se asignan a una sola.
    viaje_id: str | None = None


@dataclass
class Estado:
    """Copia del sistema después de las ventas del día; modificarla no afecta la simulación."""

    dia: int
    dia_semana: int                 # 0 = lunes
    inventario: np.ndarray          # (N, K)
    inventario_bodega: np.ndarray   # (K,)
    llegadas_tiendas: np.ndarray    # (H, N, K): fila h llega el día dia+1+h
    llegadas_bodega: np.ndarray     # (H, K)
    perdidas_acumuladas: np.ndarray # (N, K)
