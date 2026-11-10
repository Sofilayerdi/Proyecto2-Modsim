# Proyecto 2: traspasos de inventario entre tiendas

## Informe técnico integrado

**Universidad del Valle de Guatemala**  
**Curso:** CC3074 — Modelización y Simulación  
**Integrantes y carnés:** pendiente de completar por el equipo.  
**Docente y fecha de entrega:** pendiente de completar por el equipo.

**Estado del documento:** borrador integrado. Contiene el problema, la
investigación, la formulación, la implementación y la evidencia de optimización
disponible. Las comparaciones experimentales y la validación real están
identificadas como pendientes. Este archivo es el documento maestro del informe.

## Resumen

Se desarrolló un modelo de simulación diaria de inventario para una cadena de
tiendas abastecida desde una bodega central. El modelo representa demanda
aleatoria, ventas perdidas, reposición mediante reglas (s, S) y traspasos entre
tiendas. La mejora propuesta ajusta los parámetros de una política de traspasos
mediante un algoritmo genético con reparación de restricciones, evaluación por
réplicas y reevaluación de candidatos. Un flujo de costo mínimo selecciona la
carga de cada viaje, mientras una heurística voraz selecciona las rutas.

La ejecución disponible utiliza datos sintéticos de 10 tiendas, una bodega,
3 productos y un horizonte de 120 días. El genético, con 30 individuos y hasta
50 generaciones, terminó en la generación 18 por estancamiento. El ganador
alcanzó un costo promedio de Q23,074.24 y un nivel de servicio promedio de
98.56% en 30 réplicas con semillas independientes de las usadas para seleccionarlo.

Estos resultados verifican la ejecución del método en el sistema sintético.
La reducción frente a la política base, la sensibilidad y la correspondencia
con una cadena real todavía deben establecerse mediante los experimentos y
la validación descritos en este documento.

**Palabras clave:** inventario, traspasos laterales, simulación, algoritmo
genético, restricciones, flujo de costo mínimo.

## Contenido

1. Problema y objetivos.
2. Investigación de la técnica adicional.
3. Formulación del modelo.
4. Implementación de la mejora.
5. Diseño experimental y verificación.
6. Comparación con la vida real.
7. Resultados disponibles y análisis pendiente.
8. Conclusiones provisionales y limitaciones.
9. Referencias.
10. Anexo de reproducibilidad y responsabilidades.

## 1. Problema y objetivos

### 1.1 Contexto y planteamiento

La demanda de un producto no es uniforme entre los puntos de venta de una
cadena. Una tienda puede agotar sus existencias mientras otra conserva unidades
que tardarán en venderse. Si cada tienda depende exclusivamente de reposiciones
desde bodega, el inventario disponible en otros establecimientos no se aprovecha
para responder a esos faltantes.

Los traspasos laterales trasladan unidades entre tiendas del mismo nivel de la
red. Pueden evitar ventas perdidas, pero introducen costos de viaje y el riesgo
de dejar sin existencias al donante. Por ello, no basta con mover productos de
una tienda con más inventario a otra con menos: debe evaluarse si llegarán a
tiempo y si el beneficio esperado compensa el costo y el riesgo.

El proyecto estudia esta decisión mediante simulación y optimización. La
referencia empresarial prevista es una cadena cuyos datos aportaría el equipo;
en la versión actual solo se dispone del contrato sintético de arranque. No
se atribuyen a una empresa real los parámetros ni resultados de ese contrato.

### 1.2 Pregunta de investigación

¿Cuánto se reducen el costo total y las ventas perdidas de la cadena si los
traspasos entre tiendas se deciden con una política optimizada, en lugar de
depender solo de la reposición desde bodega?

### 1.3 Objetivo general

Evaluar, mediante simulación, el efecto de una política de traspasos entre
tiendas cuyos parámetros se ajustan con un algoritmo genético sobre el costo
total y el nivel de servicio de una cadena con bodega central.

### 1.4 Objetivos específicos

1. Representar la dinámica diaria de inventario, demanda, ventas, faltantes y
   reposición de tiendas y bodega.
2. Formular un indicador económico que relacione el beneficio de atender
   demanda adicional con el costo del traslado y el riesgo para el donante.
3. Implementar políticas de traspasos que respeten exhibición, exceso disponible,
   capacidad de transporte, tránsito y conservación de unidades.
4. Ajustar los parámetros de la política mediante un genético con restricciones
   y evaluaciones replicadas bajo demanda común.
5. Comparar el escenario base, una regla simple y la política ajustada, y evaluar
   su sensibilidad con estadística sobre réplicas pareadas.
6. Contrastar el modelo base con datos reales antes de interpretar la mejora
   como una recomendación operativa.

Los objetivos 5 y 6 requieren trabajo experimental y datos que todavía no
están completos en el repositorio.

### 1.5 Alcance

Se incluyen una bodega, múltiples tiendas y productos, demanda semanalmente
estacional, pronóstico simple, reposición (s, S), transporte e inventario en
tránsito, costos y ventas perdidas. La ejecución disponible considera 10
tiendas, 3 productos y 120 días, dentro del tamaño sugerido en el plan.

No se modelan precios variables, sustitución entre productos, pedidos de
clientes pendientes, retornos de vehículos ni rutas con varias paradas. Cada
vehículo puede hacer como máximo un viaje directo por día. La reposición sigue
una regla (s, S); sus parámetros de bodega forman parte del cromosoma, por lo
que su ajuste debe distinguirse del efecto exclusivo de los traspasos.

## 2. Investigación de la técnica adicional

### 2.1 Selección de un algoritmo genético

Los parámetros de una política de inventario interactúan de forma no lineal:
una mayor reserva protege al donante, pero reduce la cantidad transferible;
un umbral económico alto evita viajes poco rentables, pero puede dejar demanda
sin atender. Las evaluaciones contienen ruido porque la demanda es aleatoria.

Un algoritmo genético permite explorar una representación mixta de enteros y
reales utilizando el simulador como evaluador, sin requerir derivadas del costo.
Eiben y Smith (2015) presentan la representación, selección, recombinación y
mutación como componentes configurables de los algoritmos evolutivos. En este
proyecto el cromosoma describe una política reutilizable y no una lista de
todos los movimientos diarios, lo que limita la dimensión de búsqueda.

### 2.2 Manejo de restricciones

Deb (2000) estudia el manejo de restricciones en algoritmos genéticos y la
distinción entre factibilidad y calidad. Nuestra implementación combina
reparación y penalización; no implementa las reglas específicas de selección
por factibilidad propuestas por ese autor.

Se distinguen dos niveles:

- **Política válida:** genes dentro de sus rangos, valores enteros donde
  corresponde, S de bodega mayor o igual que s y horizontes compatibles con
  el pronóstico.
- **Acciones válidas:** envíos limitados por exceso y capacidad, reserva de
  exhibición, inventario no negativo y conservación durante el tránsito.

El objetivo de 95% de servicio se trata como una restricción blanda sobre el
promedio de réplicas: incumplirlo aumenta el fitness, pero no invalida
automáticamente al candidato ni garantiza 95% por tienda o producto.

### 2.3 Optimización mediante simulación y evaluación ruidosa

Amaran et al. (2016) describen la optimización mediante simulación como la
búsqueda de decisiones cuyo desempeño se obtiene evaluando un modelo. Aquí
la función objetivo se estima con réplicas y no se conoce de forma cerrada.

Para un candidato $\theta$, se minimiza:

$$
\widehat F(\theta)=\frac{1}{R}\sum_{r=1}^{R}C_r(\theta)
+\lambda\max\left(0,0.95-\frac{1}{R}\sum_{r=1}^{R}NS_r(\theta)\right),
\qquad \lambda=100000.
$$

$C_r$ se expresa en quetzales y $NS_r$ como fracción entre cero y uno.
Un déficit de 0.01 en servicio promedio agrega Q1,000 al fitness. El valor de
la penalización es un supuesto del equipo, no una calibración económica real.

Se emplean las mismas semillas de demanda para comparar candidatos durante
el entrenamiento. Los cinco mejores genotipos distintos se reevalúan con
semillas adicionales y el ganador se evalúa con un tercer conjunto independiente.
Esto reduce el riesgo de seleccionar una política por una realización favorable.

### 2.4 Extensión y fundamento bibliográfico

La extensión del genético visto en clase combina reparación, evaluación con
réplicas y números aleatorios comunes, reevaluación de finalistas e integración
con el simulador y el flujo de costo mínimo. Según el plan, el equipo debe
confirmar con el docente su clasificación como técnica adicional válida.

| Fuente | Aporte al enfoque |
| --- | --- |
| Eiben y Smith (2015) | Representación, operadores y administración de población |
| Deb (2000) | Fundamento del manejo de restricciones y factibilidad |
| Amaran et al. (2016) | Marco de optimización con evaluaciones de simulación |

Estas referencias sustentan el enfoque general, no demuestran que la población,
rangos o penalización elegidos sean óptimos para esta aplicación.

## 3. Formulación del modelo

### 3.1 Conjuntos, estados y decisiones

Se consideran tiendas $i,j\in\{1,\ldots,N\}$, productos
$k\in\{1,\ldots,K\}$, una bodega $w$ y días
$t\in\{0,\ldots,T-1\}$. Cada tienda pertenece a una clase de demanda
$g(i)\in\{\text{alta},\text{media},\text{baja}\}$.

| Símbolo | Descripción | Unidad |
| --- | --- | --- |
| $I_{ik,t}$ | Inventario disponible en tienda | Unidades |
| $W_{k,t}$ | Inventario disponible en bodega | Unidades |
| $A_{ik,t}$ | Llegadas programadas a tiendas | Unidades |
| $A^w_{k,t}$ | Llegadas programadas a bodega | Unidades |
| $D_{ik,t}$ | Demanda real de una réplica | Unidades/día |
| $\widehat\mu_{ik,t+\ell}$ | Pronóstico de demanda futura | Unidades/día |
| $Y_{ik,t}$ | Unidades vendidas | Unidades/día |
| $P_{ik,t}$ | Unidades de demanda perdida | Unidades/día |
| $q_{ijk,t}$ | Cantidad enviada entre tiendas | Unidades |
| $d_{ij}$ | Distancia vial estimada | km |
| $m_k$ | Margen no obtenido por unidad perdida | Q/unidad |

La política observa inventario, llegadas comprometidas, pérdidas acumuladas y
pronóstico después de las ventas del día. No recibe las realizaciones futuras
de demanda utilizadas por el motor.

### 3.2 Datos, parámetros y procedencia

Los CSV sintéticos contienen 10 tiendas y 210 registros de demanda: una fila
por tienda, producto y día semanal. La clase de tienda se declara antes de
simular. El generador usa medias base de 6, 3 y 1.5 unidades/día por producto,
factores de clase 1.5, 1 y 0.6, heterogeneidad multiplicativa lognormal y un
perfil semanal normalizado. Las dispersiones por clase son 2, 4 y 6.

| Parámetro | Valor de referencia | Origen y función |
| --- | --- | --- |
| Horizonte | 120 días | Supuesto dentro del tamaño previsto |
| Tiendas, bodega y productos | 10, 1 y 3 | Diseño del contrato sintético |
| Márgenes P01, P02 y P03 | Q12, Q35 y Q90/unidad | Estimados; valoran ventas perdidas |
| Mantenimiento | Q0.08/unidad·día | Estimado; penaliza inventario al cierre |
| Viaje fijo | Q60/viaje | Estimado; activa un traslado |
| Costo variable | Q4/km | Estimado; depende de distancia |
| Vehículos | 2 | Supuesto; un viaje por vehículo y día |
| Capacidad por vehículo | 150 unidades | Supuesto; compartida por productos |
| Velocidad | 30 km/h | Estimada, antes del tráfico |
| Factor vial | 1.3 | Estimado; multiplica Haversine |
| Factores de tráfico | 1.0–1.9 | Estimados por franja de salida |
| Mínimo de exhibición | 2 unidades/producto | Supuesto; reserva del donante al enviar |
| Inventario inicial de tienda | 7 días de demanda media | Supuesto, redondeado a unidades |
| Inventario inicial de bodega | 21 días de demanda media de la cadena | Supuesto, redondeado a unidades |
| Entrega de bodega a tienda | 2 días | Estimada |
| Seguridad y objetivo de reposición en tienda | 3 y 12 días | Supuestos de la regla fija |
| Entrega de proveedor a bodega | 7 días | Estimada |
| s y S de bodega, base | 10 y 30 días | Supuestos; sustituibles por el candidato |
| Ventana de pronóstico | 4 semanas | Supuesto |
| Horizonte de pronóstico | 14 días | Supuesto; limita H + SS |
| Descuento diario $\delta$ | 0.98 | Supuesto de valoración temporal |

Las coordenadas son ficticias alrededor de (14.60, −90.52). La procedencia y
la semilla de generación se conservan en
[`procedencia.json`](../../data/synthetic/procedencia.json). Ninguna magnitud
de esta tabla debe citarse como medición real de una empresa.

### 3.3 Demanda aleatoria y pronóstico

La demanda usa una media por tienda, producto y día semanal. Si la dispersión
varianza/media es uno, se utiliza Poisson; si es mayor que uno, se usa binomial
negativa parametrizada para obtener la media y dispersión especificadas:

$$
E[D_{ik,t}]=\mu_{ik,t},\qquad
\operatorname{Var}(D_{ik,t})=\phi_{ik,t}\mu_{ik,t}.
$$

El motor pregenera la demanda de toda la réplica a partir de la semilla.
Con igual configuración de demanda y semilla, la secuencia no cambia al
modificar la política de traspasos.

El pronóstico promedia las ventas observadas del mismo día semanal en las
últimas cuatro semanas. Las semanas todavía no observadas se completan con
la media previa del archivo de entrada. Se producen 14 días de pronóstico.
Se utilizan ventas observadas, no demanda futura; cuando hubo agotamientos,
esta serie puede subestimar la demanda latente.

### 3.4 Dinámica diaria y reposición

El orden diario es el siguiente:

```text
para cada día:
    recibir llegadas programadas a tiendas y bodega
    atender demanda con el inventario disponible
    registrar ventas perdidas
    construir pronóstico y decidir traspasos
    descontar envíos del donante y programar su llegada
    aplicar reposición (s, S) de tiendas desde bodega
    aplicar compras (s, S) de bodega al proveedor
    registrar inventario de cierre, costos y balances
```

Después de recibir llegadas:

$$
Y_{ik,t}=\min(I_{ik,t},D_{ik,t}),\qquad
P_{ik,t}=D_{ik,t}-Y_{ik,t}.
$$

Las pérdidas no se acumulan como pedidos pendientes de clientes. Los envíos
se descuentan del inventario al despachar y se reciben cuando termina el tránsito.

La reposición utiliza la posición de inventario: existencias más unidades
ya en camino. Si la posición es menor o igual que s, se pide hasta S:

$$
Q=\begin{cases}
\max(0,\lceil S-\text{posición}\rceil),&\text{posición}\leq s,\\
0,&\text{en otro caso}.
\end{cases}
$$

Para tiendas, s equivale a demanda media diaria por tiempo de entrega más
seguridad, y S a demanda media diaria por días objetivo. Si la bodega no
alcanza, reparte proporcionalmente y redondea hacia abajo. Para la bodega se
usa la demanda media diaria agregada de la cadena y sus parámetros en días.
La regla se mantiene; el genético puede cambiar s y S de bodega.

### 3.5 Distancias, tráfico y tránsito

La distancia entre coordenadas se estima con Haversine, usando un radio
terrestre de 6371.0088 km, y se multiplica por el factor vial 1.3. No es una
distancia calculada sobre una red real de carreteras.

$$
\tau_{ij}(h_d)=\frac{d_{ij}}{v}\,f(h_d),\qquad
L_{ij}=\max\left(1,\left\lceil\frac{h_d+\tau_{ij}(h_d)}{24}\right\rceil\right).
$$

$\tau$ se expresa en horas y $L$ en días. Se aplica el factor de la
franja de salida; no se integra el cambio de tráfico durante el viaje.
El motor no admite que un traspaso llegue en el día del despacho. La distancia
y el costo corresponden a la ida, sin recorrido de retorno modelado.

### 3.6 Cobertura, exceso e indicador económico

La cobertura compara inventario con demanda media prevista. Demanda cero
implica cobertura infinita. Para un donante de clase g, el exceso transferible es:

$$
\operatorname{cob}_{ik}=\frac{I_{ik}}{\bar\mu_{ik}},\qquad
e_{ik}=\max\left(0,\left\lfloor I_{ik}-
\max\{I_{\min},\bar\mu_{ik}(H_g+SS_g)\}\right\rfloor\right).
$$

La media $\bar\mu$ se calcula sobre el horizonte de esa tienda. Las
llegadas pendientes ayudan a estimar faltantes y ventas futuras; no se cuentan
como unidades disponibles hoy para enviar.

Para un viaje consolidado de i a j con cantidades $\mathbf q$, el valor
de decisión se aproxima como:

$$
V_{ij}(\mathbf q)=\sum_k m_k\left[
\sum_{\ell=1}^{H_{g(j)}}\Delta\widehat Y_{jk,\ell}(\mathbf q)\delta^{\ell}
-\sum_{\ell=1}^{\lceil H_{g(i)}+SS_{g(i)}\rceil}
\Delta\widehat P_{ik,\ell}(\mathbf q)\right]
-c_{ij}-p_T\max(0,f(h_d)-1)c_{ij},
$$

$$
c_{ij}=c_f+c_{km}d_{ij}.
$$

Las ventas extra y pérdidas adicionales se obtienen comparando proyecciones
de inventario con y sin envío, usando el pronóstico como demanda esperada.
No se integra toda la distribución de demanda. Se consideran llegadas
comprometidas y una estimación del despacho de bodega de hoy, limitada por su
stock; no se anticipan todas las reposiciones futuras.

El costo fijo se resta una vez por viaje, aunque consolide productos. La
penalización por tráfico influye en la decisión, pero no es un gasto físico
añadido al costo total. La política económica acepta un viaje solo si
$V_{ij}>u_V$; si una reposición cubre las ventas antes de que llegue el
traspaso, el beneficio adicional disminuye o desaparece.

### 3.7 Costos, métricas y restricciones

El costo físico por réplica es:

$$
C=C_I+C_T+C_P,
$$

$$
C_I=h\sum_{t=0}^{T-1}\left(\sum_{i,k}I^{\mathrm{cierre}}_{ik,t}
+\sum_k W^{\mathrm{cierre}}_{k,t}\right),\qquad
C_T=\sum_{\text{viajes}}(c_f+c_{km}d_{ij}),\qquad
C_P=\sum_{t,i,k}m_kP_{ik,t}.
$$

El mantenimiento se cobra al stock de cierre en tiendas y bodega, no a las
unidades en tránsito. El costo de ventas perdidas representa margen no obtenido,
no el precio completo de venta. La implementación no incorpora costos de compra
ni fletes de proveedor o bodega dentro del costo de traspasos laterales.

$$
NS=\frac{\sum_{t,i,k}Y_{ik,t}}{\sum_{t,i,k}D_{ik,t}}.
$$

Si la demanda total es cero, se define servicio igual a uno. Se registran
también unidades perdidas, viajes consolidados y kilómetros recorridos.

Los envíos deben cumplir:

- Cantidades enteras positivas, tiendas distintas y llegada posterior al despacho.
- Inventario disponible no negativo y donante por encima del mínimo de exhibición.
- Envíos agregados de cada donante/producto no mayores que su exceso disponible.
- Un viaje por vehículo y día, con capacidad compartida entre productos.
- Conservación de unidades, incluyendo inventario que sigue en tránsito al terminar.

## 4. Implementación de la mejora

### 4.1 Arquitectura y políticas

```text
CSV + configuración
    → carga y validación
    → motor diario + demanda y pronóstico
    → política de traspasos
        → transporte y valoración económica
        → selección de carga por flujo y de rutas por heurística
    → métricas por réplica
    → evaluación y operadores del genético
    → ganador, historial y evaluación independiente
```

El escenario base no ejecuta traspasos. La regla simple usa umbrales fijos
de cobertura y reserva, y prioriza tiendas y productos por índice sin buscar
rentabilidad. Puede ejecutar viajes con V negativo, pero respeta las
restricciones físicas y evita cubrir dos veces faltantes ya atendidos por
envíos planificados.

La política económica calcula curvas de beneficio marginal por producto para
cada ruta. Un flujo de costo mínimo selecciona unidades con capacidad común
y una salida de costo cero para dejar capacidad sin usar. Después se resta
el costo real del viaje y se elige la ruta de mayor V aceptable. Se actualizan
inventario y llegadas antes de decidir el siguiente vehículo.

El flujo optimiza la carga de cada ruta; la selección de rutas es voraz y no
garantiza el óptimo global con cargos fijos. Los costos marginales se redondean
a microquetzales para el flujo; V se comprueba sin ese redondeo. Las líneas
de productos comparten un identificador de viaje y solo una contiene el costo
y los kilómetros, evitando duplicaciones en las métricas.

### 4.2 Cromosoma de 11 genes

$$
\theta=(s_w,S_w,H_a,SS_a,H_m,SS_m,H_b,SS_b,u_V,p_T,h_d).
$$

| Genes | Tipo y cantidad | Rango | Función |
| --- | --- | --- | --- |
| `bodega_s_dias` | Un entero | 5–20 | Umbral de bodega en días |
| `bodega_S_dias` | Un entero | 15–45 | Objetivo de bodega en días |
| `horizonte_dias_alta/media/baja` | Tres enteros | 1–7 | H por clase |
| `seguridad_dias_alta/media/baja` | Tres enteros | 0–7 | SS por clase |
| `umbral_valor_q` | Un real | 0–200 | Umbral por viaje, Q |
| `peso_trafico` | Un real | 0–2 | Penalización adicional de tráfico |
| `hora_despacho` | Un entero | 0–23 | Hora de salida |

La ampliación de siete genes globales a once permite diferenciar reservas
y horizontes por clase, conforme al rango de 10–20 genes previsto en el plan.
Los límites son supuestos de diseño y requieren análisis de sensibilidad.
La reparación acota los genes, redondea enteros y garantiza S ≥ s y
H + SS compatible con el horizonte de pronóstico configurado.

### 4.3 Operadores y control del algoritmo

| Componente | Configuración utilizada |
| --- | --- |
| Población | 30 individuos |
| Máximo de generaciones | 50 |
| Selección | Torneo de 3 |
| Cruce | Uniforme, probabilidad 0.85 |
| Mutación | Probabilidad 0.10 por hijo; modifica un gen elegido al azar |
| Perturbación | Gaussiana con σ igual a 10% del rango del gen |
| Elitismo | 2 individuos |
| Parada por estancamiento | 10 generaciones consecutivas sin mejora |
| Finalistas | Hasta 5 genotipos distintos |

Población y máximo de generaciones utilizan el extremo inferior del presupuesto
del plan. No se presentan como valores calibrados u óptimos. Cada hijo se
repara. Los genotipos repetidos reutilizan su evaluación dentro de la corrida,
porque configuración y semillas permanecen fijas.

### 4.4 Réplicas, integración y reproducibilidad

| Generador o etapa | Semilla o conjunto | Uso |
| --- | --- | --- |
| Datos sintéticos | 20261109 | Generador independiente de entradas |
| Operadores del genético | 20261109 | Instancia local `random.Random` |
| Entrenamiento | 1–10 | Fitness bajo demanda común |
| Reevaluación | 11–40 | Elección entre finalistas |
| Evaluación final | 1001–1030 | Medición posterior a la selección |

Los conjuntos de demanda son disjuntos. El final no participa en selección,
mutación, criterio de parada ni elección del ganador. El proceso principal
administra los operadores; los trabajadores evalúan candidatos con semillas
fijas y devuelven los resultados en orden, conservando la reproducibilidad.

El adaptador conecta el genético con el motor y la política económica. La
corrida conserva ganador, historial por generación, métricas por réplica,
gráfica y manifiesto con versiones, configuración y huellas SHA-256 de entradas
y código. Una instantánea de progreso no equivale a una reanudación completa
del algoritmo: no guarda el estado completo de su generador.

## 5. Diseño experimental y verificación

### 5.1 Verificación ya realizada

La última verificación registrada del proyecto obtuvo **122 pruebas aprobadas**.
La evidencia disponible cubre:

- Conservación en tiendas, bodega y sistema, incluyendo tránsito final.
- Demanda cero, inventario abundante y ausencia de inventario negativo.
- Semilla común independiente de la política.
- Distancias, tráfico, costo a distancia cero y consolidación de productos.
- Capacidad por viaje, exceso agregado y mínimo de exhibición.
- Selección de carga comparada con enumeración exhaustiva en un caso pequeño.
- Efecto real de parámetros por tipo, reparación y operadores del genético.
- Igualdad entre ejecución secuencial y paralela y aislamiento del RNG global.

Se verificaron las huellas del código y CSV de la corrida guardada. Una
reejecución de sus 30 semillas finales reprodujo exactamente las métricas
individuales y los agregados. Esto es verificación interna y reproducibilidad;
no demuestra correspondencia del modelo con una cadena real.

### 5.2 Comparación de escenarios prevista

**Pendiente de ejecución y análisis por la persona 4.**

| Condición | Política | Propósito |
| --- | --- | --- |
| Base | Sin traspasos, reposición de referencia | Punto de comparación |
| Regla simple | Cobertura y reserva fijas | Separar el efecto de introducir movimientos del de optimizarlos |
| Mejorada | Parámetros del ganador | Evaluar el desempeño de la política ajustada |
| Sensibilidad | Mejorada con condiciones modificadas | Examinar robustez |

Cada condición debe tener 30 réplicas con semillas registradas. Para las
condiciones con igual demanda se usarán 1001–1030, preservando el emparejamiento
por semilla. El CSV comparativo tendrá una fila por condición y semilla y
una columna por métrica, usando servicio como fracción antes de presentarlo.

La política ajustada cambia también s y S de bodega. Para atribuir una mejora
específicamente a los traspasos se necesita una comparación adicional que
mantenga esos parámetros constantes, o un análisis que separe ambos aportes.

### 5.3 Sensibilidad prevista

Se propone estudiar demanda +20%, tráfico pesado y menor disponibilidad de
vehículos, identificando qué parámetro cambia en cada condición. En el código
actual, `factor_demanda=1.2` también escala las medias usadas para inventario
inicial y umbrales de reposición; no representa un aumento aislado de demanda
con esas cantidades fijas. El diseño definitivo debe declarar si conserva
ese comportamiento o controla dichos factores por separado.

### 5.4 Tratamiento estadístico previsto

Se reportarán promedio, desviación estándar e intervalo de confianza del 95%
por condición. Para costos medios, un intervalo basado en t puede expresarse:

$$
\bar C\pm t_{0.975,29}\frac{s_C}{\sqrt{30}}.
$$

El método debe identificarse y sus supuestos revisarse. La comparación base
frente a mejorada debe analizar diferencias por semilla, mediante t pareada
o Wilcoxon según las características de esas diferencias. No corresponde
tratarlas como dos muestras independientes.

Se planifican gráficas de inventario temporal, costo y servicio por escenario
con intervalos, sensibilidad y convergencia. Solo la convergencia está
disponible actualmente. Los porcentajes de reducción se calcularán respecto
a la base; el cambio de nivel de servicio se expresará en puntos porcentuales.

## 6. Comparación con la vida real

**Pendiente de datos y validación por la persona 5.**

Se requieren ventas diarias por tienda/producto, ubicaciones y, si existen,
inventarios, reposiciones, traspasos y costos o márgenes. Los datos privados
no se incorporarán al repositorio público; deben proporcionarse instrucciones
de acceso o una referencia anonimizada conforme al acuerdo del equipo.

La validación prevista consiste en separar calibración y validación, ajustar
los parámetros de demanda con el primer período y simular la base sobre el
segundo con 30 réplicas. Se compararán ventas por tienda y semana mediante:

$$
MAE=\frac{1}{n}\sum_{a=1}^{n}|\widehat y_a-y_a|.
$$

También se reportará error relativo, explicitando su denominador y el
tratamiento de valores reales cero. Si existen datos de faltantes o inventario,
se contrastarán sus tasas o trayectorias. Las ventas observadas pueden estar
censuradas por agotamiento y no equivaler a demanda total.

La tabla final de referencia real, base y mejorada deberá incluir diferencias
absolutas y porcentuales. Actualmente no hay valores reales que permitan
completarla ni cuantificar la correspondencia del modelo.

## 7. Resultados disponibles y análisis pendiente

### 7.1 Ejecución sintética de la optimización

La corrida utilizó 10 tiendas, una bodega, 3 productos y 120 días. Con población
30, máximo 50 generaciones y paciencia 10, terminó en la generación 18. El
mejor de entrenamiento apareció en la generación 8 y se evaluaron 176
genotipos distintos.

Se realizaron 1,950 réplicas: 1,760 de entrenamiento de candidatos únicos,
150 de reevaluación de cinco finalistas, 30 finales y 10 para identificar el
fitness de entrenamiento del ganador definitivo. Las repeticiones de un
genotipo dentro del entrenamiento utilizaron la evaluación almacenada.

![Convergencia del algoritmo genético](../../results/optimizacion/semilla_20261109/convergencia.png)

**Figura 1. Convergencia y servicio en entrenamiento.** El mejor fitness
histórico descendió de Q23,536.98 a Q22,378.04. Las curvas de costo y fitness
coinciden porque los mejores históricos no reciben penalización. El descenso
describe progreso de la búsqueda, no una reducción contra la política base.
El servicio puede variar aun cuando el mejor fitness histórico no empeore.

### 7.2 Parámetros del ganador

| Parámetro | Valor seleccionado |
| --- | ---: |
| s y S de bodega | 6 y 15 días |
| H y SS, demanda alta | 4 y 6 días |
| H y SS, demanda media | 3 y 4 días |
| H y SS, demanda baja | 1 y 3 días |
| Umbral económico | Q129.661968 |
| Peso de tráfico | 0.746413 |
| Hora de despacho | 23 |

Los valores mostrados están redondeados; el
[`ganador.json`](../../results/optimizacion/semilla_20261109/ganador.json)
conserva la precisión utilizada. La hora de salida es un resultado del modelo
discreto y no debe interpretarse automáticamente como recomendación operativa.

### 7.3 Desempeño en las etapas de evaluación

| Etapa del ganador | Fitness promedio (Q) | Réplicas |
| --- | ---: | ---: |
| Entrenamiento | 22,378.04 | 10 |
| Reevaluación | 22,739.86 | 30 |
| Evaluación final | 23,074.24 | 30 |

Las diferencias entre etapas reflejan demanda de conjuntos distintos. En
general, el ganador de entrenamiento puede diferir del elegido al reevaluar;
en esta corrida ambos coinciden.

| Métrica de evaluación final | Promedio por período de 120 días |
| --- | ---: |
| Costo total | Q23,074.24 |
| Costo de inventario | Q12,255.13 |
| Costo de traslado | Q209.34 |
| Costo de ventas perdidas | Q10,609.77 |
| Nivel de servicio | 98.5556% |
| Unidades perdidas | 185.77 |
| Viajes consolidados | 2.63 |
| Kilómetros modelados | 12.84 |

Los costos de componentes se muestran redondeados. Los conteos tienen
decimales porque son promedios entre réplicas. Las 30 réplicas finales
superaron 95% de servicio; el promedio no recibe penalización, por lo que
fitness y costo total coinciden. Este resultado no garantiza servicio mínimo
en cada tienda ni bajo condiciones diferentes.

Las métricas por semilla se conservan en
[`evaluacion_final.csv`](../../results/optimizacion/semilla_20261109/evaluacion_final.csv).
La ejecución tomó aproximadamente 56.22 segundos con seis trabajadores en el
entorno registrado; ese tiempo no es una garantía para otros equipos.

### 7.4 Comparación pendiente

| Condición | Costo medio | Servicio medio | IC del 95% | Estado |
| --- | --- | --- | --- | --- |
| Base | Pendiente | Pendiente | Pendiente | Falta comparación experimental |
| Regla simple | Pendiente | Pendiente | Pendiente | Falta comparación experimental |
| Mejorada | Q23,074.24 | 98.5556% | Pendiente | Hay evaluación individual; falta integrarla al estudio |
| Sensibilidad | Pendiente | Pendiente | Pendiente | Falta ejecutar condiciones modificadas |

No se dispone todavía de una reducción porcentual respecto a la base, de
una prueba pareada ni de una comparación real/base/mejorada. La pregunta de
investigación no puede responderse cuantitativamente con la sola evaluación
del ganador.

## 8. Conclusiones provisionales y limitaciones

### 8.1 Conclusiones sustentadas por la evidencia disponible

1. Se implementó e integró una simulación de inventario con políticas de
   traspasos y un genético propio de 11 genes diferenciados por clase de tienda.
2. La corrida al tamaño previsto se ejecutó y dejó un ganador, historial,
   métricas por réplica y procedencia reproducible.
3. El ganador alcanzó un servicio promedio de 98.56% en la evaluación sintética
   final de 30 réplicas, con costo promedio de Q23,074.24 por 120 días.
4. Las pruebas y la reejecución de las réplicas finales respaldan la consistencia
   interna del código, no su validez como representación de una empresa real.

### 8.2 Limitaciones y conclusiones todavía no establecidas

- El genético y la selección voraz de rutas no garantizan el óptimo global.
  Una sola semilla del genético no permite estimar estabilidad de la búsqueda.
- La demanda, ubicaciones y clasificación son sintéticas; los costos y otros
  parámetros son estimaciones o supuestos sin calibración empresarial.
- El pronóstico basado en ventas puede subestimar demanda por faltantes; el
  indicador usa una proyección determinista de demanda esperada.
- La discretización diaria limita la representación de tráfico intradía y
  la logística omite retornos y rutas multitienda.
- El 95% se controla mediante una penalización promedio, no como garantía por
  tienda, producto o réplica.
- Ajustar reposición de bodega y traspasos simultáneamente exige separar ambos
  efectos al interpretar mejoras.
- Quedan pendientes los escenarios comparativos, intervalos, sensibilidad,
  prueba pareada y validación real. Las conclusiones definitivas y recomendaciones
  operativas se redactarán después de esos análisis.

## 9. Referencias

1. Eiben, A. E., & Smith, J. E. (2015). *Introduction to Evolutionary Computing*
   (2.ª ed.). Springer. https://doi.org/10.1007/978-3-662-44874-8
2. Deb, K. (2000). An efficient constraint handling method for genetic algorithms.
   *Computer Methods in Applied Mechanics and Engineering, 186*(2–4), 311–338.
   https://doi.org/10.1016/S0045-7825(99)00389-8
3. Amaran, S., Sahinidis, N. V., Sharda, B., & Bury, S. J. (2016).
   Simulation optimization: a review of algorithms and applications.
   *Annals of Operations Research, 240*, 351–380. Publicado en línea en 2015.
   https://doi.org/10.1007/s10479-015-2019-x

**Pendiente bibliográfico:** incorporar la referencia empresarial o pública
real y las fuentes que sustenten costos, márgenes, distancias y parámetros
cuando se reemplacen los supuestos. Las fichas editoriales anteriores se
consultaron para la investigación; no se atribuyen a sus autores los datos,
resultados ni valores calibrados de esta implementación.

## 10. Anexo de reproducibilidad y responsabilidades

### 10.1 Ejecutar la implementación

Desde la raíz del repositorio, con Python 3.10 o superior y dependencias instaladas:

```bash
python -m pytest -q
python -m experiments.optimizar --config config.yaml --salida results/optimizacion/nueva_ejecucion --trabajadores 6
```

La salida debe ser una carpeta vacía. Los CSV sintéticos ya están incluidos.
Las dependencias exactas de la ejecución de referencia y las huellas del
código constan en el
[`manifest.json`](../../results/optimizacion/semilla_20261109/manifest.json).
Las fechas, rutas y tiempos pueden cambiar al repetirla. Las semillas no
garantizan igualdad entre versiones distintas de las dependencias.

| Evidencia | Archivo o ubicación |
| --- | --- |
| Configuración de referencia | [`config.yaml`](../../config.yaml) |
| Datos y procedencia | [`data/synthetic/README.md`](../../data/synthetic/README.md) |
| Historial por generación | [`historial.csv`](../../results/optimizacion/semilla_20261109/historial.csv) |
| Resultados completos | [`resultado.json`](../../results/optimizacion/semilla_20261109/resultado.json) |
| Semillas y métricas de finalistas | [`reevaluacion.csv`](../../results/optimizacion/semilla_20261109/reevaluacion.csv) |

### 10.2 Distribución para completar y revisar el documento

| Responsable previsto | Secciones y cierre |
| --- | --- |
| Persona 1 | Revisar problema, objetivos, dinámica, demanda, pronóstico y reposición |
| Persona 2 | Revisar costos, transporte, indicador y traspasos; integrar formato y PDF final |
| Persona 3 | Revisar técnica, genético, reproducibilidad y evidencia de optimización |
| Persona 4 | Completar diseño ejecutado, estadística, comparación y sensibilidad |
| Persona 5 | Completar referencia real, validación, fuentes y conclusiones definitivas |

La distribución identifica responsabilidades del plan, no certifica autoría
individual ni aprobación humana de este borrador. Los nombres, carnés y
registro de contribuciones deben ser completados por el equipo. La revisión
cruzada de la persona 4 sigue pendiente de su entrega experimental.
