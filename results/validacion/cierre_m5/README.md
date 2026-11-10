# Cierre comparativo de la referencia pública M5

Complementa los resultados originales de `../m5/` sin modificarlos. El alcance
se cierra como **contraste parcial de ventas reales**, no validación de la
operación de Walmart o de inventarios y costos no observados.

## Evidencia

- Se descargó el ZIP público indicado por Nixtla, fuera del repositorio.
- Su SHA-256 coincide con el manifiesto M5 original.
- Se reprodujeron las 60 réplicas desde ese ZIP: cuatro archivos numéricos
  coinciden exactamente, incluso con Python 3.12.16 en lugar del 3.14.7 registrado.
- Se calcularon diferencias real/base/mejorada sin rellenar campos desconocidos.
- Se agregó incertidumbre Monte Carlo y pruebas de las dos magnitudes simuladas.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `comparacion_real.csv` | Diferencias absolutas y porcentuales; lo no observado queda vacío |
| `estadistica_modelo.csv` | Media, desviación e IC del modelo, no del proceso real |
| `pruebas_modelo.csv` | Dos t pareadas con Holm dentro de M5 y Wilcoxon exploratorio |
| `diferencias_modelo.csv` | Diferencias por semilla de costo y servicio |
| `resumen.json` | Alcance, métricas, hashes y comprobación de fuente y reproducción |

La base subestima ventas en 20.74% y la mejorada en 21.44%. La mejorada tiene
servicio simulado 94.51%, con 12/30 réplicas bajo 95%; no realiza traspasos.
Estos resultados limitan la transferencia del ganador sintético. El ahorro
modelado en Q no representa ahorro real observado.

## Repetir

Desde la raíz, conservando el ZIP fuera de Git y usando salidas vacías:

```bash
python -m src.validation.m5 --m5 /ruta/m5.zip --salida /ruta/reproduccion_m5
python -m src.validation.comparacion --origen results/validacion/m5 --salida results/validacion/otro_cierre --zip-fuente /ruta/m5.zip --reproduccion /ruta/reproduccion_m5
```

Si no se pasa `--zip-fuente` o `--reproduccion`, los indicadores correspondientes
quedan falsos; no se certifica una comprobación que no se haya realizado.
El informe único y la presentación general incluyen la interpretación del cierre.
