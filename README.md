# Proyecto 2: traspasos de inventario entre tiendas

**Universidad del Valle de Guatemala · Facultad de Ingeniería**

**Modelación y Simulación**

**Guatemala, 10 de noviembre de 2026**

| Integrante | Carné |
| --- | --- |
| Javier Alejandro Chávez León | 23132 |
| Daniel Adolfo Sarmiento Peralta | 231105 |
| Sofía López Ayerdi | 231929 |
| Karen Ximena Toledo Juárez | 23692 |
| Luis Francisco Padilla Juárez | 23663 |

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
src/validation/          calibración M5, contraste de ventas y cierre comparativo
src/viz/                 inventario, comparación, desglose y sensibilidad
experiments/optimizar.py ejecución reproducible de la optimización (persona 3)
experiments/comparar.py  comparación pareada y estadística (persona 4)
experiments/diseno.yaml  semillas, sensibilidades y comparaciones predefinidas
results/optimizacion/    ganador, semillas, métricas por réplica e historial
results/experimentos/    CSV comparativos, estadística, auditoría y gráficas
results/validacion/      contraste M5 y diferencias real/base/mejorada
tests/                  pruebas automáticas
docs/informe/           informe técnico integrado del proyecto
docs/presentacion/      presentación general de 15 minutos, HTML y PDF
```

La comparación sintética, estadística y sensibilidad están ejecutadas. El cierre
usa M5 como referencia pública externa en lugar de datos empresariales no
disponibles: es un contraste parcial de ventas, no validación de inventarios,
costos o de la operación de Walmart. Se verificó el ZIP y se reprodujeron las
60 réplicas y cuatro archivos numéricos originales. La comparación completa
de diferencias está en `results/validacion/cierre_m5/`.
Los datos privados están excluidos de Git mediante `data/reference/`.

## Informe técnico

El documento maestro es [docs/informe/informe.md](docs/informe/informe.md), con
los 14 apartados acordados, comparación externa, conclusiones y contribuciones
del equipo. Los datos institucionales e integrantes están en `docs/proyecto.json`.

- [Informe PDF](docs/informe/informe.pdf).
- [Informe HTML](docs/informe/informe.html), con fórmulas MathML y enlaces locales.
- [Presentación general](docs/presentacion/presentacion.html): 24 diapositivas
  en colores claros, los 14 apartados del informe, siete gráficas, diagrama,
  cinco bloques de tres minutos, notas, índice y temporizador.
- [Presentación PDF](docs/presentacion/presentacion.pdf).

La presentación funciona sin conexión al abrir el HTML junto con el repositorio.
Flechas o espacio avanzan; **N** muestra notas, **F** pantalla completa y **R**
reinicia el reloj. El PDF de diapositivas es autónomo y no incluye las notas.

Para regenerar las exportaciones después de editar el Markdown o las diapositivas:

```bash
python -m pip install -r docs/requirements.txt
python -m playwright install chromium-headless-shell
python docs/generar_entregables.py
```

Estas dependencias son solo documentales y no alteran el entorno científico.
`docs/entregables.json` registra las huellas de fuentes y exportaciones.
Los datos de portada e integrantes ya están incorporados. Las revisiones
y la defensa académica corresponden al equipo.

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
