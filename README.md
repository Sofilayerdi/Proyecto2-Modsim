# Proyecto 2: traspasos de inventario entre tiendas

Simulación diaria de una cadena con bodega central y optimización de los
parámetros de una política de traspasos mediante un algoritmo genético propio.

## Ejecutar

Requiere **Python 3.10+**. Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m experiments.optimizar --config config.yaml --salida results/optimizacion/nueva_ejecucion --trabajadores 6
python -m experiments.comparar --config config.yaml --diseno experiments/diseno.yaml --salida results/experimentos/nueva_ejecucion --trabajadores 6
```

La carpeta de salida debe estar vacía. Se puede usar `--trabajadores 1` para
ejecución secuencial; el orden de evaluación no modifica el resultado. Cada
trabajador evalúa un candidato con todas sus semillas de entrenamiento.

Los CSV sintéticos ya están incluidos; no hay que generarlos para ejecutar.
Su origen y receta se describen en [data/synthetic/README.md](data/synthetic/README.md).
Las dependencias exactas de la corrida guardada se registran en su manifiesto;
`requirements.txt` mantiene los mínimos del proyecto, no un bloqueo de versiones.

## Reproducibilidad

`config.yaml` fija 120 días, población 30, máximo 50 generaciones, paciencia 10
y semilla del genético **20261109**. Cada ejecución registra:

| Uso | Semillas |
| --- | --- |
| Generación de datos sintéticos | 20261109, generador separado |
| Operadores del genético | 20261109, instancia local `random.Random` |
| Entrenamiento con números aleatorios comunes | 1–10 |
| Reevaluación de cinco candidatos distintos | 11–40 |
| Evaluación final del ganador | 1001–1030 |

Los tres grupos de demanda deben ser disjuntos. El conjunto final no participa
en selección, mutación, parada ni elección del ganador. No se usa el estado
aleatorio global para los operadores propios.

## Estructura

```text
data/synthetic/          CSV y procedencia sintéticos
src/simulation/          carga, demanda, pronóstico y motor
src/model/               transporte, costos e indicador y políticas de traspasos
src/optimization/        genético, restricciones, evaluación y convergencia
src/viz/                 inventario, comparación, desglose y sensibilidad
experiments/optimizar.py ejecución reproducible de la optimización (persona 3)
experiments/comparar.py  comparación pareada y estadística (persona 4)
experiments/diseno.yaml  semillas, sensibilidades y comparaciones predefinidas
results/optimizacion/    ganador, semillas, métricas por réplica e historial
results/experimentos/    CSV comparativos, estadística, auditoría y gráficas
tests/                  pruebas automáticas
docs/informe/           informe técnico integrado del proyecto
```

La comparación sintética, estadística y sensibilidad están ejecutadas. La
validación real de la persona 5 sigue pendiente. Los datos reales están
excluidos de Git mediante `data/reference/`.

## Informe técnico

El documento maestro es [docs/informe/informe.md](docs/informe/informe.md).
Integra problema, investigación, modelo, costos, políticas, genético y resultados
experimentales sintéticos. Identifica la validación real pendiente. Se edita en
Markdown y puede exportarse a PDF al cerrar el informe.

## Evidencia guardada

[Corrida con semilla 20261109](results/optimizacion/semilla_20261109/README.md):
10 tiendas, 3 productos, 120 días, 11 genes y 30 individuos. Terminó en 18
generaciones por estancamiento. La evaluación final tiene 30 réplicas.

[Estudio comparativo](results/experimentos/semillas_1001_1030/README.md):
8 condiciones × 30 semillas = 240 réplicas, con controles para separar bodega
y traspasos. La mejorada reduce costo 25.68% frente a base, pero aumenta
unidades perdidas 6.03%; el ahorro se asocia principalmente a la bodega.
Se incluyen IC del 95%, pruebas pareadas con ajuste de Holm y cuatro gráficas.

El manifiesto incluye configuración, rangos, semillas, versiones y SHA-256
de entradas y código. `git_commit_base` identifica el commit previo a estos
cambios; `git_con_cambios=true` indica que se ejecutaron cambios todavía sin
commit. Las huellas identifican el código efectivamente utilizado.

Para reutilizar el ganador:

```python
import json
from pathlib import Path
from src.simulation.carga import cargar_config
from src.optimization.adaptador import simular_politica

config = cargar_config("config.yaml")
params = json.loads(Path("results/optimizacion/semilla_20261109/ganador.json").read_text())
metricas = simular_politica(config, params, semilla=1001)
```

Para el contrato de traspasos, consultar [src/model/README.md](src/model/README.md).
