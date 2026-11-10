# Contraste parcial con ventas públicas M5

Fuente: competición [M5 Forecasting Accuracy de Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data), ventas diarias de Walmart en EE. UU. El ZIP utilizado es la copia publicada por [Nixtla](https://github.com/Nixtla/m5-forecasts/tree/main/datasets). Consultar las condiciones de la fuente original antes de redistribuir el conjunto. No se incorpora el ZIP al repositorio.

Selección explícita: CA_1, CA_2 y CA_3; FOODS_1_001, FOODS_1_002 y FOODS_1_003. Calibración: 28/10/2015–28/02/2016 (124 días); comparación: 29/02/2016–24/04/2016 (56 días, ocho semanas). Son 24 observaciones tienda-semana, sumando los tres productos; 30 réplicas con semillas 1001–1030 por condición. Las medias y dispersiones por día semanal se estiman exclusivamente con calibración; la varianza/media se limita inferiormente a 1.

Las ventas reales pueden estar censuradas por faltantes y no equivalen a demanda. Las tiendas, su política y sus inventarios reales no se conocen. Las coordenadas, inventarios iniciales, costos, márgenes y reposiciones son **supuestos del modelo**, no datos Walmart; los costos en quetzales no son comparables con costos reales. Se reutiliza el ganador entrenado en datos sintéticos, sin afirmar que sea óptimo para M5. Una comparación de ventas no valida traspasos, inventarios ni costos reales.

| Métrica, período de validación | Referencia real | Simulación base | Simulación mejorada |
| --- | ---: | ---: | ---: |
| Ventas totales, unidades | 426 | 337.67 | 334.67 |
| MAE tienda-semana, unidades | — | 5.56 | 5.61 |
| Error absoluto agregado / ventas reales | — | 31.35 % | 31.63 % |

El MAE compara cada observación real con el promedio de las 30 simulaciones. El error relativo agregado es 100 × suma de diferencias absolutas / suma de ventas reales; incluye semanas con cero ventas, sin división por cero individual. Un denominador total cero se reporta como no disponible. Los resultados muestran correspondencia limitada, no una validación integral.

La diferencia entre el total medio de la base y el real es −88.33 unidades (−20.74 % del total real). El 31.35 % de la tabla es otro indicador: suma errores absolutos por tienda-semana y por ello no permite que desviaciones positivas y negativas se cancelen.

En este caso la mejorada simula tres unidades vendidas menos que la base (−0.89 %), y el costo supuesto baja de Q1,156.34 a Q1,067.47 (−Q88.87, −7.69 %). No se registraron viajes en las réplicas de la mejorada: la diferencia no demuestra ningún efecto de traspasos. No hay costo real comparable ni se ha medido una mejora en Walmart. Ninguno de estos resultados sustituye validar con datos de inventario y operación reales.

El costo supuesto presenta desviación estándar entre réplicas de Q365.57 en la base y Q453.82 en la mejorada; el servicio medio fue 95.32 % y 94.51 %, respectivamente, con desviaciones de 2.98 y 3.22 puntos porcentuales. Esta variabilidad describe el generador de demanda y los supuestos, no un intervalo de confianza sobre el desempeño real. Solo hay tres tiendas y tres artículos seleccionados; no se puede generalizar a Walmart o a Guatemala. La prueba tampoco representa las ubicaciones reales de las tiendas: utiliza coordenadas hipotéticas en Guatemala.

`ventas_semanales.csv` contiene las observaciones y el promedio de réplicas para la futura gráfica; `ventas_semanales_replicas.csv` conserva cada réplica; `metricas_replicas.csv` contiene métricas del motor; `resumen.json` registra períodos, errores y hash del ZIP. `manifest.json` identifica versiones, semillas y SHA-256 de código, configuración, ganador, ZIP y resultados. Los cuatro archivos de resultados se reprodujeron exactamente con las mismas dependencias y entradas. Las versiones futuras pueden generar diferencias.

Para reproducir, obtener `m5.zip` desde la fuente indicada y ejecutar desde la raíz, en una carpeta de salida vacía:

```bash
python -m src.validation.m5 --m5 /ruta/m5.zip --salida results/validacion/nueva
```

Las gráficas `graficas/ventas_reales_simuladas.png` y `graficas/mae_por_tienda.png`
comparan las ventas observadas con el promedio de réplicas y muestran el MAE
de la base por tienda, respectivamente. Se reproducen desde los resultados ya
generados, en una carpeta vacía, con:

```bash
python -m src.viz.validacion --ventas results/validacion/m5/ventas_semanales.csv --salida results/validacion/nuevas_graficas
```

El manifiesto describe la ejecución de la simulación; el código de gráficas se
agregó después y no modifica los resultados numéricos.
