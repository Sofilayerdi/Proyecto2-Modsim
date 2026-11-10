# Demostración rápida

Con las dependencias del proyecto instaladas y desde la raíz del repositorio:

```bash
python -m experiments.demo
```

Se puede cambiar el horizonte y la semilla con `--dias 60 --semilla 1002`.
El comando compara base y política ganadora con la misma semilla de demanda,
imprime costos, servicio, pérdidas y viajes, y no escribe resultados. El
ganador se optimizó para 120 días, por lo que la demo de 30 días no reproduce
los resultados principales. Una réplica sintética no demuestra una mejora
real ni sustituye las 30 réplicas y el análisis de `results/experimentos/`.

Prueba: `python -m pytest tests/test_demo_rapida.py -q`.
