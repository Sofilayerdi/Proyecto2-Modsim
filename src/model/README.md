# Uso del módulo de traspasos

Requiere Python **3.10 o superior** y las dependencias de `requirements.txt`.

## Archivos

| Archivo | Responsabilidad |
| --- | --- |
| `transporte.py` | Matriz de distancias, factor de tráfico, horas y días de tránsito. |
| `costos.py` | Costo fijo y por kilómetro de un viaje. |
| `indicador.py` | Cobertura, exceso, llegadas previstas, ventas proyectadas y valor V. |
| `traspasos.py` | Regla simple y política económica con NetworkX. |

## Conectar con la simulación

```python
from src.simulation.carga import cargar_config
from src.simulation.motor import simular
from src.model.traspasos import decidir_traspasos, decidir_traspasos_simple

config = cargar_config("config.yaml")
base = simular(config, None, semilla=1)
simple = simular(config, {}, semilla=1, decidir=decidir_traspasos_simple)
economica = simular(config, {}, semilla=1, decidir=decidir_traspasos)

# La persona 3 puede pasar los parámetros del candidato por esta misma interfaz.
params = {"horizonte_dias": 4, "seguridad_dias": 2,
          "umbral_valor_q": 5, "peso_trafico": 0.2, "hora_despacho": 10}
candidato = simular(config, params, semilla=1, decidir=decidir_traspasos)
```

La ejecución con archivos requiere `tiendas.csv` y `demanda.csv` en las rutas
indicadas en `config.yaml`. Las pruebas usan estados y datos en memoria.

Para probar la política aisladamente:

```python
traspasos = decidir_traspasos(estado, pronostico, {
    **config,
    "politica": params,
    "ubicaciones_tiendas": ubicaciones,  # matriz (N, 2): latitud, longitud
})
```

También se admite `distancias_km`, una matriz `(N, N)` no negativa que reemplaza
la estimación geográfica. El motor inyecta las ubicaciones automáticamente.

## Contrato y unidades

- `estado` es el `Estado` del motor después de las ventas de hoy.
- El pronóstico `(H, N, K)` empieza **mañana**. Debe cubrir como mínimo
  `ceil(horizonte_dias + seguridad_dias)` días.
- H y SS son escalares comunes a las tiendas en esta versión. El candidato
  reemplaza los valores de `config["traspasos"]` a través de `params_politica`.
- `umbral_valor_q` es el V mínimo **por viaje**, en quetzales. El envío se acepta
  únicamente si V es estrictamente mayor que el umbral.
- Las distancias se estiman con Haversine multiplicada por `factor_ruta`.
  Son kilómetros de ida: esta versión no modela retornos ni rutas multitienda.
- El tráfico depende de la hora de despacho. La llegada se redondea al siguiente
  inicio de día disponible, siempre posterior al día actual.
- Cada vehículo dispone de un viaje diario. Su capacidad se comparte entre
  productos; también se controla el exceso agregado del donante entre viajes.
- Las líneas de productos del mismo viaje tienen un `viaje_id` común.
  **Solo la primera línea lleva el costo y los kilómetros del viaje**: sumar
  esos campos produce los totales correctos sin duplicar cargos.
- `num_traspasos` cuenta viajes consolidados. Para políticas anteriores sin
  `viaje_id`, cada registro sigue contando como un traspaso.

## Comportamiento de las políticas

La política económica proyecta ventas usando la demanda esperada del pronóstico,
las llegadas pendientes y el pedido de bodega previsto para hoy. El reparto de
ese pedido usa la regla `(s, S)`, la media del pronóstico y el stock disponible
en bodega. Es una aproximación: no anticipa todos los pedidos futuros ni integra
la distribución completa de demanda.

Para cada par donante–receptor, un flujo de costo mínimo selecciona cantidades
por beneficio marginal descontado, con capacidad común entre productos y una
salida de costo cero para no enviar unidades innecesarias. Se resta el costo
fijo una vez por viaje. La mejor ruta rentable se reserva, se actualizan stock
y llegadas, y se evalúa el siguiente vehículo. La selección de rutas es voraz;
no garantiza el óptimo global con cargos fijos. Los costos del flujo se
redondean a microquetzales; la aceptación usa V sin redondear.

`peso_trafico` agrega `peso × (factor − 1) × costo_viaje` a la penalización de
decisión. No modifica el costo físico registrado. El retraso por tráfico ya
afecta el momento de las ventas y su descuento.

La regla simple utiliza H y SS como umbrales fijos de cobertura y reserva,
prioriza tiendas y productos por su índice y no busca rentabilidad. Puede
ejecutar viajes con V negativo, para servir como referencia sin optimización.
Ambas políticas respetan exhibición, exceso, tránsito y capacidad, y evitan
contar dos veces los faltantes ya cubiertos por envíos planificados.

## Verificación

Desde la raíz del repositorio:

```bash
python -m pytest -q
```

Las pruebas cubren distancias, tráfico, costo a distancia cero, descuento,
reposición previa al traspaso, riesgo del donante, consolidación, optimalidad
de la carga frente a enumeración exhaustiva, restricciones en estados variados
e integración con conservación de unidades y métricas por viaje.
