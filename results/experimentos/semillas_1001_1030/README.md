# Estudio experimental de la persona 4

**Origen: datos sintéticos.** 10 tiendas, 1 bodega, 3 productos, 120 días,
8 condiciones y 30 réplicas por condición: **240 réplicas**. Semillas 1001–1030,
sin reentrenar al ganador de `results/optimizacion/semilla_20261109/`.

El diseño se declaró en `experiments/diseno.yaml` antes de observar resultados.
Además de base, regla simple y mejorada, incluye dos controles de bodega y
tres sensibilidades. Los resultados se integran en el único informe del proyecto:
[docs/informe/informe.md](../../../docs/informe/informe.md).

## Lectura de los resultados

| Condición | Costo promedio por 120 días | Servicio promedio | Unidades perdidas |
| --- | ---: | ---: | ---: |
| Base | Q31,047.76 | 98.6372% | 175.20 |
| Regla simple | Q32,661.15 | 98.7708% | 158.03 |
| Mejorada | Q23,074.24 | 98.5556% | 185.77 |
| Bodega ajustada, sin traspasos | Q23,224.48 | 98.5085% | 191.73 |
| Traspasos con bodega original | Q31,003.05 | 98.6492% | 173.67 |
| Demanda +20% | Q27,583.78 | 98.0022% | 307.17 |
| Tráfico pesado | Q23,193.31 | 98.5205% | 190.23 |
| Un vehículo | Q23,072.75 | 98.5509% | 186.37 |

La mejorada ahorra 25.68% frente a base, pero las pérdidas aumentan 6.03% y
el servicio disminuye 0.0816 puntos porcentuales. La caída del costo se debe
principalmente a mantener menos inventario por el ajuste de bodega. No hay
evidencia suficiente de ahorro incremental de los traspasos con bodega constante.
No se debe presentar este estudio como reducción simultánea de costo y faltantes.

## Condiciones y controles

- `base`: reposición original 10/30 días, sin traspasos.
- `regla_simple`: umbrales fijos H = 3, SS = 2, bodega original.
- `mejorada`: ganador congelado, incluidos s = 6 y S = 15 de bodega.
- `bodega_ajustada`: s = 6 y S = 15, sin traspasos.
- `traspasos_bodega_base`: genes de traspasos ganadores y bodega 10/30.
- `demanda_mas_20`: demanda y media previa ×1.2; inventario inicial y niveles
  (s, S) en unidades permanecen en su referencia ×1.0.
- `trafico_pesado`: factor 2 en todas las franjas, sin cambiar costos por viaje/km.
- `un_vehiculo`: un vehículo en lugar de dos, sin otros cambios.

Se verificó demanda idéntica por semilla entre las siete condiciones nominales.
La distribución cambia en demanda +20%; misma semilla no significa trayectoria
idéntica ni demanda mayor en cada celda. Los inventarios iniciales se mantienen
iguales en las ocho condiciones. No se reoptimiza para las sensibilidades.

## Estadística

- Medias, desviaciones muestrales e IC individuales del 95% mediante t.
- Diferencia = alternativa − referencia; negativo favorece menor costo,
  positivo favorece mayor servicio.
- t pareada bilateral como prueba primaria, aplicada a diferencias por semilla.
- Nueve comparaciones por dos métricas: 18 pruebas, con ajuste de Holm.
- IC individuales no corregidos por multiplicidad; p-Holm define la decisión.
- Wilcoxon bilateral como comprobación no paramétrica, reportado sin ajuste
  y sin sustituir selectivamente la prueba primaria.
- Los 120 días de una réplica no se tratan como observaciones independientes.

La comparación base–mejorada tiene diferencia de costo −Q7,973.51,
IC [−Q8,295.86; −Q7,651.17], p t = 7.68e−30 y p-Holm = 1.33e−28.
El ahorro incremental de agregar traspasos a la bodega ajustada es Q150.24,
con IC de diferencia [−Q411.96; +Q111.49] y p-Holm = 1: no concluyente.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `resultados.csv` | 240 filas; condición, semilla y ocho métricas del motor |
| `resumen.csv` | 64 filas; media, desviación e IC por condición/métrica |
| `pruebas_pareadas.csv` | 18 filas; diferencias, IC, t, Wilcoxon y ajuste de Holm |
| `diferencias_pareadas.csv` | 540 diferencias individuales por semilla |
| `auditoria.csv` | Demanda SHA-256, balances, mínimos e inventario inicial por réplica |
| `verificaciones.json` | Comprobaciones agregadas del diseño y consistencia |
| `series_inventario.csv` | 7,200 filas: base/mejorada, semilla 1001, todas las tiendas/productos |
| `series_bodega.csv` | 720 filas de inventario de bodega para esa semilla y condiciones |
| `manifest.json` | Diseño, escenarios, ganador, semillas, versiones, huellas y duración |
| `graficas/` | Comparación, sensibilidad, inventario temporal y desglose de costos |

`nivel_servicio` se guarda como fracción 0–1; las figuras e informe muestran
porcentaje. La trayectoria gráfica usa P03 y la primera tienda de cada tipo
(T01, T04, T08), elegidos a priori. La gráfica de convergencia permanece en
la carpeta de la optimización de la persona 3.

## Verificación y repetición

Conservación, inventario no negativo, costos, servicio, demanda nominal común
e inventario inicial constante pasaron en las 240 réplicas. La mejorada nominal
coincide con las 30 réplicas previamente guardadas del ganador. La suite completa
pasó con **131 pruebas**. La corrida tomó aproximadamente 4.44 segundos con
seis trabajadores; tiempos y marcas de fecha no son resultados reproducibles.

Desde la raíz, hacia una carpeta vacía:

```bash
python -m experiments.comparar --config config.yaml --diseno experiments/diseno.yaml --salida results/experimentos/repeticion --trabajadores 6
```

Con iguales datos, código, versiones y semillas deben coincidir métricas,
estadística y series. El manifiesto conserva el commit base y las huellas del
código ejecutado con cambios aún sin commit. Los datos reales y su validación
siguen siendo responsabilidad de la siguiente etapa del proyecto.
