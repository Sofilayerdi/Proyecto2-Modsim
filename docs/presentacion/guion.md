# Guion de presentación — Traspasos de inventario entre tiendas

**Universidad del Valle de Guatemala · Facultad de Ingeniería**\
**Modelación y Simulación**\
**Guatemala, 10 de noviembre de 2026**

Duración objetivo: 15 minutos, 29 diapositivas, cinco bloques de tres minutos. Los
tiempos son una guía de ensayo; incluyen pausas y señalamiento de gráficas. Las
indicaciones entre corchetes no se leen en voz alta. Cada integrante puede asumir
uno de los bloques según el reparto acordado por el equipo.

| Bloque | Diapositivas | Tiempo | Tema |
| --- | --- | --- | --- |
| Expositor 1 | 1–6 | 0:00–3:00 | Presentación, problema, objetivos, fuentes y entradas |
| Expositor 2 | 7–11 | 3:00–6:00 | Modelo, pasos de un día, costos, implementación e inventario |
| Expositor 3 | 12–15 | 6:00–9:00 | Genético, evaluación, convergencia y salidas |
| Expositor 4 | 16–22 | 9:00–12:00 | Diseño, resultados, atribución, sensibilidad y condiciones |
| Expositor 5 | 23–29 | 12:00–15:00 | Validación, comparación real y cierre |

Respecto de la versión anterior se agregaron cinco diapositivas: entradas (6),
pasos de un día (8), salidas (15) y el análisis de condiciones (21 y 22). Los
demás textos se acortaron para conservar los 15 minutos.

## Bloque 1 — Presentación, problema, objetivos, fuentes y entradas

### Diapositiva 1. Portada — 0:00–0:20

“Buenos días. Somos Javier Chávez, Daniel Sarmiento, Sofía López, Karen Toledo
y Luis Padilla. Presentamos nuestro proyecto de traspasos de inventario entre
tiendas. Estudiamos cuándo conviene mover productos entre establecimientos y
cómo ajustar esa decisión con un algoritmo genético.”

### Diapositiva 2. Recorrido del informe — 0:20–0:35

“Primero veremos el problema, los objetivos y los datos. Después el modelo y la
optimización. Al final, los experimentos, la comparación real y las conclusiones.”

### Diapositiva 3. El desbalance entre tiendas — 0:35–1:15

[Señalar donante, decisión y receptora, de izquierda a derecha.]

“Una cadena puede tener un producto acumulado en una tienda y agotado en otra.
Esperar la reposición desde bodega puede costar ventas, aunque existan unidades
en otro establecimiento.

Un traspaso podría resolverlo, pero puede ser caro, llegar tarde o dejar corta a
la tienda donante. Por eso preguntamos cuánto cambian el costo y las ventas
perdidas cuando los traspasos se deciden con una política optimizada.”

### Diapositiva 4. Objetivos verificables — 1:15–1:50

“El objetivo general es evaluar esa política sobre costo total, servicio y ventas
perdidas. Seguimos cuatro pasos: representar el sistema, optimizar los
parámetros, comparar escenarios con las mismas semillas y contrastar con ventas
reales. El costo es el objetivo principal, pero revisamos los otros indicadores
para no confundir un ahorro con una mejora en todo.”

### Diapositiva 5. Fuentes y alcance — 1:50–2:25

[Señalar las dos tarjetas y enfatizar que tienen funciones diferentes.]

“Usamos dos conjuntos. El sintético tiene diez tiendas, tres productos y ciento
veinte días; sirve para entrenar y comparar en condiciones controladas. M5 son
ventas públicas reales de Walmart: tres tiendas y tres productos, con cincuenta y
seis días de contraste. Esas ventas son observadas, pero sus inventarios y
costos no.”

### Diapositiva 6. Entradas del modelo — 2:25–3:00

[Recorrer las tres tarjetas de izquierda a derecha.]

“El simulador recibe tres tipos de entrada. Primero, datos: ubicación y tipo de
cada tienda, y la demanda media por tienda, producto y día de la semana. Segundo,
parámetros: cuánto cuesta guardar, mover y perder una venta, y cómo se repone;
por ejemplo, la tienda tarda dos días en recibir de bodega. Tercero, los once
genes que ajusta el genético y las semillas que separan cada etapa.”

## Bloque 2 — Modelo, pasos de un día, costos, implementación e inventario

### Diapositiva 7. Modelo diario — 3:00–3:35

[Recorrer el diagrama desde proveedor hasta tiendas; después señalar los movimientos laterales.]

“El sistema tiene un proveedor, una bodega central y tiendas. La bodega repone a
las tiendas con una regla (s, S): si el inventario baja hasta s, se pide hasta S.
Además, las tiendas pueden enviarse unidades entre sí. La demanda es aleatoria y
lo que no se atiende se pierde.”

### Diapositiva 8. Pasos de un día simulado — 3:35–4:20

[Señalar los cinco pasos en orden y después la fila de multiplicadores.]

“Cada día ocurre en cinco pasos. Uno: llegan los pedidos y traspasos en camino.
Dos: ocurre la demanda y se vende lo disponible. Tres: la política estima el
valor de mover unidades y elige la carga de cada viaje. Cuatro: se aplica la
reposición. Cinco: se registran costos y se verifica que no se creen ni pierdan
unidades.

Ciento veinte días forman una réplica; diez réplicas dan el fitness de un
candidato del genético. Y un detalle clave: un traspaso llega al día siguiente,
mientras que un pedido a bodega tarda dos días.”

### Diapositiva 9. Costos e indicador económico — 4:20–5:00

“El costo total suma mantener inventario, hacer traslados y perder margen. Para
decidir un viaje calculamos un valor V: las ventas extra esperadas en la
receptora, menos el riesgo para la donante, el costo del viaje y una
penalización por tráfico. El viaje cuesta sesenta quetzales más cuatro por
kilómetro, cobrado una vez aunque lleve varios productos.”

### Diapositiva 10. Implementación y restricciones — 5:00–5:30

“Implementamos todo en Python. Con NetworkX resolvemos un flujo de costo mínimo
que elige la carga de cada ruta; después escogemos de forma voraz el viaje de
mayor valor. Controlamos exceso, exhibición, capacidad y conservación. La
selección de rutas no garantiza un óptimo global.”

### Diapositiva 11. Cómo evoluciona el inventario — 5:30–6:00

[Señalar los ejes y una caída seguida de una llegada.]

“Aquí vemos el inventario al cierre de un producto en dos tiendas. Las caídas
son ventas y las subidas, llegadas. Base y mejorada coinciden muchos días y
luego se separan. Es una sola réplica: para concluir necesitamos muchas.”

## Bloque 3 — Genético, evaluación, convergencia y salidas

### Diapositiva 12. Genético de 11 genes — 6:00–6:50

“El genético no decide cada movimiento. Ajusta once parámetros de la política:
seis de reserva por tipo de tienda, dos de reposición de bodega y tres de
decisión: umbral económico, peso del tráfico y hora de despacho.

Usa torneo, cruce uniforme, mutación gaussiana y elitismo. Cada hijo se repara
para respetar rangos y restricciones. No suponemos que el resultado sea un
óptimo global.”

### Diapositiva 13. Fitness y semillas — 6:50–7:30

[Señalar primero la fórmula y después los tres conjuntos de semillas.]

“El fitness es el costo promedio más una penalización si el servicio queda bajo
noventa y cinco por ciento. Menor es mejor. Entrenamos con las semillas uno a
diez, reevaluamos cinco finalistas con once a cuarenta y medimos al ganador con
mil uno a mil treinta, que nunca participan en la selección.”

### Diapositiva 14. Convergencia y ganador — 7:30–8:25

[Recorrer la curva izquierda hasta la generación 8 y después señalar el objetivo del 95% en la derecha.]

“Con treinta individuos, el mejor candidato apareció en la generación ocho y la
búsqueda paró en la dieciocho, tras diez generaciones sin mejora. El fitness baja
y se estabiliza, y el servicio se mantiene sobre el objetivo.

Eso muestra progreso en la búsqueda, pero no ahorro frente a la base. Además, el
ganador cambia la bodega junto con los traspasos; por eso necesitamos controles.”

### Diapositiva 15. Salidas del modelo — 8:25–9:00

[Recorrer las tres tarjetas.]

“De cada corrida obtenemos tres tipos de salida. Por réplica: costo total y sus
tres componentes, servicio, unidades perdidas y viajes. Series diarias de
inventario, ventas y pérdidas. Y evidencia guardada: el ganador, los resultados
por semilla, intervalos, pruebas y un manifiesto para reproducir cada cifra.
Con estas salidas construimos los experimentos.”

## Bloque 4 — Diseño, resultados, atribución, sensibilidad y condiciones

### Diapositiva 16. Diseño experimental — 9:00–9:25

“Comparamos ocho condiciones con treinta réplicas cada una: base, regla simple,
mejorada, dos controles de bodega y tres sensibilidades. Todas usan la misma
demanda por semilla y pruebas pareadas con ajuste de Holm.”

### Diapositiva 17. Ahorro y contraparte — 9:25–9:50

“La mejorada reduce el costo de unos treinta y un mil a veintitrés mil quetzales:
veinticinco punto sesenta y ocho por ciento. Pero las unidades perdidas suben seis
por ciento. No es una mejora simultánea, sino un intercambio favorable en costo.”

### Diapositiva 18. Comparación de políticas — 9:50–10:15

[Señalar costo a la izquierda y servicio a la derecha.]

“La regla simple atiende más demanda, pero sus viajes la hacen cinco por ciento
más cara que la base. La mejorada tiene el menor costo con servicio algo menor.
El eje de servicio empieza en noventa y cinco.”

### Diapositiva 19. Atribución del ahorro — 10:15–10:40

[Señalar el componente de inventario y comparar las dos últimas barras.]

“El control de bodega ajustada, sin traspasos, ya obtiene casi todo el ahorro.
Agregar traspasos ahorra ciento cincuenta quetzales más, pero el intervalo incluye
cero. En el escenario base, el ahorro viene de la bodega.”

### Diapositiva 20. Sensibilidad — 10:40–11:00

“Una demanda veinte por ciento mayor sube el costo diecinueve punto cinco por
ciento. Tráfico pesado y un solo vehículo no cambian el resultado de forma
significativa.”

### Diapositiva 21. ¿Cuándo convienen los traspasos? — 11:00–11:25

[Señalar las dos tarjetas.]

“Entonces nos preguntamos en qué condiciones sí convienen. Repetimos la
comparación con y sin traspasos en dos tipos de cadena: con menos reserva en las
tiendas y con entregas más lentas desde bodega. En cada nivel fijamos la bodega
y reentrenamos el genético solo con los genes de traspasos.”

### Diapositiva 22. Cuándo sí ahorran — 11:25–12:00

[Señalar la línea ámbar y después la verde.]

“La línea ámbar muestra que quitar reserva aumenta los faltantes hasta once por
ciento, pero el ahorro sigue en cero. La verde muestra que, si la reposición
tarda cinco o siete días, los traspasos ahorran uno punto nueve y tres punto uno
por ciento y mejoran el servicio, con significancia estadística.

La explicación: un traspaso solo gana si llega bastante antes que la
reposición normal. Con entregas de dos días, adelanta apenas un día y no paga el
viaje.

Hasta aquí, resultados sintéticos. Ahora, el contraste externo.”

## Bloque 5 — Validación, comparación real y cierre

### Diapositiva 23. Validación externa M5 — 12:00–12:35

“Pasar ciento cincuenta y cinco pruebas respalda el código, pero no demuestra que
represente una empresa. En M5 calibramos con ciento veinticuatro días y reservamos
los cincuenta y seis siguientes. Comparamos veinticuatro observaciones reales con
treinta réplicas por política, sin reajustar al ganador.”

### Diapositiva 24. Comparación real — 12:35–13:05

“M5 registra cuatrocientas veintiséis ventas; la base simula unas trescientas
treinta y ocho. El error absoluto relativo ronda el treinta y uno por ciento y el
servicio de la mejorada baja a noventa y cuatro punto cinco. No hubo traspasos,
así que esto no mide una mejora por traslados.”

### Diapositiva 25. Ventas reales y simuladas — 13:05–13:40

[Señalar un pico observado y las curvas medias más suaves.]

“La línea oscura son ventas observadas; las otras, medias de simulación, por eso
son más suaves. También hay una diferencia de nivel: la base subestima el total
real en veinte punto siete por ciento. Son ventas de California, no inventarios
de una cadena guatemalteca.”

### Diapositiva 26. Error por tienda — 13:40–14:00

“El MAE es de cinco a seis unidades por tienda y semana. El treinta y uno por
ciento suma errores sin cancelarlos; no es lo mismo que el error neto. La
correspondencia es limitada.”

### Diapositiva 27. Limitaciones — 14:00–14:20

“Respaldamos el código, la reproducibilidad y el ahorro de traspasos con entregas
lentas. No demostramos un óptimo global, costos reales ni beneficio de traspasos
en el escenario base. El análisis de condiciones es exploratorio.”

### Diapositiva 28. Contribuciones del equipo — 14:20–14:40

“El trabajo integra simulación, costos y traspasos, genético, experimentación,
contraste externo y el análisis de condiciones. El uso de inteligencia
artificial está declarado en el informe.”

### Diapositiva 29. Conclusiones y referencias — 14:40–15:00

“Concluimos que optimizar exige explicar el mecanismo. En el escenario base el
ahorro viene de la bodega; los traspasos convienen cuando la reposición es lenta,
no simplemente cuando hay faltantes. Muchas gracias; quedamos atentos a sus
preguntas.”

## Apoyo breve para preguntas

Estas respuestas no forman parte de los quince minutos programados.

**¿El proyecto demuestra que los traspasos no sirven?**
No. En el escenario base no hay ahorro incremental demostrable, pero el análisis
de condiciones muestra ahorros de 1.88% y 3.12% cuando la entrega desde bodega
tarda 5 y 7 días.

**¿Por qué quitar reserva no hace rentables los traspasos?**
Porque la bodega sigue abastecida y repone en dos días. Un traspaso tarda al
menos uno, así que solo adelanta un día una reposición que llega de todos modos.
Además, si todas las tiendas tienen poca reserva, hay pocos donantes.

**¿El análisis de condiciones cambia el escenario base o el ganador?**
No. Es un análisis adicional y exploratorio, diseñado después de ver los
resultados principales. La bodega se fija en sus valores originales y el
genético se reentrena por nivel solo con los genes de traspasos.

**¿Por qué llaman “mejorada” a una política con más pérdidas?**
Es el nombre del escenario ajustado por el genético. Tiene menor costo bajo el
objetivo definido, pero no mejora todos los indicadores.

**¿El genético garantiza un servicio de 95%?**
No. Penaliza el incumplimiento promedio; en M5 el promedio mejorado quedó bajo 95%.

**¿Qué validaron con M5?**
Calibración temporal y correspondencia de ventas fuera de muestra, con resultado
limitado. No se validaron inventarios, costos, reposición ni traspasos reales.

**¿Qué significan las semillas?**
Identifican las realizaciones aleatorias. Permiten repetir experimentos y comparar
políticas bajo condiciones comunes; no son datos reales adicionales.

**¿Cuál sería el siguiente paso?**
Obtener inventarios, tiempos de reposición y costos observados de una cadena
concreta; si sus entregas son lentas, es donde más vale la pena evaluar traspasos.
También estudiar interacciones entre reserva y entrega, y repetir el genético con
otras semillas.
