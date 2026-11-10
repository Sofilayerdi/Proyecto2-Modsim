# Proyecto 2: traspasos de inventario entre tiendas

**Universidad del Valle de Guatemala · CC3074 Modelización y Simulación · Ciclo 2, 2026**

| Integrante | Carné |
| --- | --- |
| Javier Alejandro Chávez León | 23132 |
| Daniel Adolfo Sarmiento Peralta | 231105 |
| Sofía López Ayerdi | 231929 |
| Karen Ximena Toledo Juárez | 23692 |
| Luis Francisco Padilla Juárez | 23663 |

## Descripción

Simulación diaria del inventario de una cadena de 10 tiendas abastecida desde una
bodega central, con 3 productos y un horizonte de 120 días. La demanda es aleatoria
(binomial negativa) y la reposición sigue una regla (s, S). Sobre ese modelo se
evalúa una política de **traspasos entre tiendas**:

- **Técnica vista en clase:** flujo de costo mínimo (NetworkX) para decidir la carga de cada viaje.
- **Técnica adicional:** algoritmo genético con restricciones que ajusta los 11 parámetros de la
  política, usando la simulación como función de evaluación.

**Pregunta de investigación:** ¿cuánto se reducen el costo total y las ventas perdidas
si los traspasos se deciden con una política optimizada, en lugar de depender solo de
la reposición desde bodega?

## Requisitos

- Python 3.10 o superior.
- Las dependencias de [requirements.txt](requirements.txt): numpy, pandas, scipy,
  statsmodels, networkx, matplotlib, pyyaml y pytest.
- Para la demo visual se necesita Tkinter, que viene incluido con Python en Windows y macOS.

## Instalación

Desde la raíz del repositorio:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Todos los comandos siguientes se ejecutan desde la raíz del repositorio con el
entorno activado.

## 1. Verificar la instalación

```bash
python -m pytest -q
```

Ejecuta las 155 pruebas automáticas: conservación de unidades, inventario no
negativo, demanda cero, inventario muy grande, reproducibilidad con la misma
semilla, restricciones de los traspasos, operadores del genético y estadística.

## 2. Demostración

Comparación rápida en consola entre el escenario base y la política optimizada,
con la misma semilla de demanda. No escribe archivos.

```bash
python -m experiments.demo
python -m experiments.demo --dias 60 --semilla 1002
```

Demostración visual (ventana con gráficas de inventario, costo y servicio, y
selector de escenarios):

```bash
python -m experiments.demo_ui
```

Una sola réplica sirve para ilustrar el funcionamiento; los resultados del
proyecto provienen de las 30 réplicas por condición descritas abajo.

## 3. Reproducir los experimentos

Los resultados del informe ya están guardados en `results/`. Para volver a
generarlos, ejecutar los comandos en este orden. **Cada carpeta de salida debe
ser nueva o estar vacía**, para no sobrescribir la evidencia guardada.
`--trabajadores` indica cuántos procesos usar; con `--trabajadores 1` se ejecuta
de forma secuencial y el resultado es el mismo.

| Paso | Comando | Qué hace | Tiempo aprox. (6 procesos) |
| --- | --- | --- | --- |
| a | `python -m experiments.optimizar --salida results/nueva/optimizacion --trabajadores 6` | Ejecuta el algoritmo genético y guarda el ganador | 1 min |
| b | `python -m experiments.comparar --salida results/nueva/experimentos --trabajadores 6` | Compara 8 condiciones × 30 réplicas con pruebas pareadas y genera las gráficas | 30 s |
| c | `python -m experiments.reserva --factor reserva --salida results/nueva/por_reserva --trabajadores 6` | Análisis de condiciones: variar la reserva de las tiendas | 2 min |
| d | `python -m experiments.reserva --factor entrega --salida results/nueva/por_entrega --trabajadores 6` | Análisis de condiciones: variar el tiempo de entrega de bodega | 2 min |

Por defecto, `comparar` usa el ganador guardado
(`results/optimizacion/semilla_20261109/ganador.json`). Para usar el ganador de
una nueva corrida, agregar `--ganador results/nueva/optimizacion/ganador.json`.

Las semillas están fijas y separadas por etapa:

| Etapa | Semillas |
| --- | --- |
| Datos sintéticos y operadores del genético | 20261109 |
| Entrenamiento del genético | 1–10 |
| Reevaluación de los 5 finalistas | 11–40 |
| Evaluación final y comparación de condiciones | 1001–1030 |

Cada corrida guarda un `manifest.json` con la configuración, las semillas, las
versiones de las bibliotecas y la huella SHA-256 de las entradas y del código.

## 4. Comparación con datos reales (M5)

Los datos reales son ventas públicas de Walmart de la competencia
[M5 Forecasting Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data).
El ZIP **no se incluye** en el repositorio; se descarga de la copia pública de Nixtla:

1. Descargar `m5.zip` desde <https://github.com/Nixtla/m5-forecasts/blob/main/datasets/m5.zip>
   y guardarlo fuera del repositorio. Su SHA-256 debe ser
   `cc704ba15d6802f8262e6ec7d4c6041e4ad6366a94365e8c84f721e450eed774`.
2. Ejecutar la calibración y el contraste (30 réplicas base y 30 mejoradas):

   ```bash
   python -m src.validation.m5 --m5 /ruta/a/m5.zip --salida results/nueva/m5
   ```

3. Generar la tabla real / base / mejorada y verificar la fuente:

   ```bash
   python -m src.validation.comparacion --origen results/nueva/m5 --salida results/nueva/cierre_m5 --zip-fuente /ruta/a/m5.zip
   ```

Para regenerar solo las gráficas de validación a partir de los resultados guardados:

```bash
python -m src.viz.validacion --ventas results/validacion/m5/ventas_semanales.csv --salida results/nueva/graficas_m5
```

## Datos

| Datos | Ubicación | Tipo |
| --- | --- | --- |
| Tiendas, coordenadas y demanda media por día de la semana | `data/synthetic/` | Sintéticos (semilla 20261109) |
| Costos, márgenes, capacidad, velocidad, tráfico y reposición | `config.yaml` | Estimaciones y supuestos del equipo |
| Ventas diarias de Walmart (3 tiendas, 3 productos) | Se descarga (sección 4) | Reales, públicos |
| Métricas, semillas y manifiestos | `results/` | Generados por el modelo |

Los datos sintéticos ya están incluidos. Para regenerarlos en otra carpeta:

```bash
python -m src.simulation.sinteticos --salida results/nueva/sinteticos --semilla 20261109
```

Los datos privados de referencia, si se usan, van en `data/reference/`, que está
excluida de Git.

## Estructura del repositorio

```text
config.yaml              parámetros del modelo (horizonte, costos, vehículos, reposición, genes)
data/synthetic/          tiendas.csv, demanda.csv y procedencia de los datos sintéticos
src/simulation/          carga de datos, demanda, pronóstico y motor diario con reposición (s, S)
src/model/               distancias, tráfico, costos, indicador V y políticas de traspasos
src/optimization/        algoritmo genético: cromosoma, operadores, fitness y reevaluación
src/validation/          calibración y contraste con ventas reales M5
src/viz/                 gráficas de escenarios, sensibilidad, condiciones y validación
experiments/             puntos de entrada: optimizar, comparar, reserva, demo y demo_ui
experiments/diseno.yaml  condiciones experimentales, semillas y comparaciones
tests/                   pruebas automáticas (pytest)
results/                 resultados guardados de cada experimento
docs/                    informe y presentación
```

## Resultados principales

Resultados guardados con 30 réplicas por condición (semillas 1001–1030):

| Condición | Costo medio (Q) | Servicio (%) | Unidades perdidas |
| --- | ---: | ---: | ---: |
| Base (sin traspasos) | 31,047.76 | 98.64 | 175.20 |
| Mejorada (política optimizada) | 23,074.24 | 98.56 | 185.77 |

- La política optimizada reduce el costo total en **25.68 %**, pero casi todo el
  ahorro (98 %) proviene de ajustar la bodega; los traspasos solos no dan un ahorro
  significativo con entrega de bodega en 2 días.
- Cuando la entrega de bodega tarda 5 o 7 días, los traspasos sí ahorran 1.88 % y
  3.12 % del costo y mejoran el servicio.
- Contra ventas reales M5, el modelo base tiene MAE de 5.56 unidades por
  tienda-semana y error relativo de 31.35 % (correspondencia limitada).

El detalle está en `results/optimizacion/`, `results/experimentos/`,
`results/reserva/` y `results/validacion/`, y en el informe dentro de `docs/informe/`.


