# Datos sintéticos del contrato de arranque

**No son observaciones de una empresa ni ubicaciones de tiendas reales.**
Permiten ejecutar y verificar la optimización mientras se obtiene la referencia
real de la persona 5.

- 10 tiendas: 3 de demanda alta, 4 media y 3 baja.
- 3 productos: P01, P02 y P03, en el orden de `config.yaml`.
- 210 combinaciones completas: 10 tiendas × 3 productos × 7 días semanales.
- Semilla de generación: **20261109**, independiente de la semilla del genético
  aunque se haya elegido el mismo número para identificarlas.
- Las medias base son 6, 3 y 1.5 unidades/día; se multiplican por el factor
  de tipo, heterogeneidad por tienda/producto y estacionalidad semanal.
- La dispersión es varianza/media, no desviación estándar. Valores 2, 4 y 6
  producen demanda binomial negativa sobredispersa.
- Las coordenadas ficticias se distribuyen alrededor de (14.60, −90.52).

`procedencia.json` conserva todos los parámetros de generación. La clase se
asigna antes de simular, y no se calcula con demanda futura ni semillas finales.

## Archivos

- `tiendas.csv`: `id_tienda,tipo_tienda,latitud,longitud`.
- `demanda.csv`: `id_tienda,id_producto,dia_semana,media,dispersion`.

Para regenerar **en una carpeta nueva**, desde la raíz:

```bash
python -m src.simulation.sinteticos --salida /tmp/proyecto2-sinteticos --semilla 20261109
```

El generador rechaza sobrescribir archivos. Una misma semilla y las mismas
versiones de dependencias reproducen sus contenidos. Los SHA-256 de los CSV
utilizados se registran en el manifiesto de cada optimización.
