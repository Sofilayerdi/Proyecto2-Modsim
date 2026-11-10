# Optimización ejecutada: semilla 20261109

## Alcance

**Datos sintéticos**, 10 tiendas, 3 productos, 120 días. Población de 30
individuos, máximo 50 generaciones y parada tras 10 sin mejora. La corrida
terminó normalmente en la **generación 18**, después de evaluar **176
candidatos distintos**. El mejor de entrenamiento apareció en la generación 8.

La semilla de operadores es 20261109. Se utilizaron demanda 1–10 para entrenar,
11–40 para reevaluar cinco candidatos y 1001–1030 para la evaluación final.
Hubo 1,950 réplicas: 1,760 de candidatos únicos en entrenamiento, 150 de
reevaluación, 30 finales y 10 para identificar el fitness de entrenamiento
del ganador definitivo. Los genotipos repetidos reutilizaron su evaluación.

## Resultados registrados

| Etapa | Fitness (Q) | Réplicas |
| --- | ---: | ---: |
| Ganador, entrenamiento | 22,378.04 | 10 |
| Ganador, reevaluación | 22,739.86 | 30 |
| Ganador, evaluación final | 23,074.24 | 30 |

En la evaluación final, el costo promedio fue Q23,074.24 y el servicio promedio
98.5556%; no se aplicó penalización. Las 30 réplicas superaron 95% de servicio;
esto describe la muestra y no garantiza el desempeño en otras condiciones.

| Métrica final | Promedio |
| --- | ---: |
| Costo de inventario | Q12,255.13 |
| Costo de traslado | Q209.34 |
| Costo de ventas perdidas | Q10,609.77 |
| Unidades perdidas | 185.77 |
| Viajes consolidados | 2.63 |
| Kilómetros modelados | 12.84 |

Los valores son por período de 120 días, no por día. Los conteos pueden tener
decimales porque se promedian réplicas. El costo es físico; fitness agrega una
penalización si el servicio promedio no alcanza 95%. Aquí ambos coinciden.

Esta carpeta registra solo la optimización. La comparación posterior de
base/regla simple/mejorada/sensibilidad y los controles que separan bodega y
traspasos están en [el estudio experimental](../../experimentos/semillas_1001_1030/README.md).
Los números de esta carpeta por sí solos no demuestran mejora frente a la base.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `ganador.json` | Los 11 parámetros elegidos tras reevaluación |
| `historial.csv` | Mejor fitness histórico, costo, servicio y candidatos únicos por generación |
| `convergencia.png` | Convergencia y servicio en entrenamiento |
| `reevaluacion.csv` | Métricas de 30 semillas por cada uno de cinco candidatos |
| `evaluacion_final.csv` | Todas las métricas y semillas del ganador, 30 filas |
| `resultado.json` | Resultado completo, candidatos, réplicas e hiperparámetros |
| `manifest.json` | Procedencia, configuración, versiones y huellas del código y los CSV |
| `progreso.json` | Última instantánea de entrenamiento; no permite reanudar el RNG |

`historial.csv` representa el mejor candidato de entrenamiento hasta cada
generación, que en general puede diferir del ganador después de reevaluación.
En esta corrida ambos ganadores coinciden. El tiempo de ejecución registrado
fue aproximadamente 56.22 segundos con seis trabajadores; no es una promesa
de tiempo para otros equipos o versiones.

## Repetir

```bash
python -m experiments.optimizar --config config.yaml --salida results/optimizacion/repeticion_20261109 --trabajadores 6
```

Con iguales entradas, versiones y semillas deben coincidir ganador, historial
y métricas. Marcas de tiempo, rutas absolutas y duración del manifiesto cambian.

## Verificación realizada

- Suite completa: **122 pruebas aprobadas** y `git diff --check` sin errores.
- Se verificaron los SHA-256 del código y de ambos CSV contra el manifiesto.
- Se volvieron a ejecutar las 30 semillas finales con el ganador guardado:
  coincidieron exactamente las métricas de todas las réplicas y los agregados.
- Se comprobaron 18 filas de historial, 150 de reevaluación y 30 finales.
- Las pruebas de reproducibilidad verifican que cambiar el RNG global no
  altera el resultado y que ejecución secuencial y paralela coinciden.
