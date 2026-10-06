---
name: morgan-vis
description: >-
  Metodología de visualización y storytelling con datos de Julia para el
  proyecto Attrition: aclarar el mensaje, elegir el gráfico, simplificar,
  amplificar y revisar críticamente. Úsalo al diseñar, crear o revisar
  cualquier gráfico, KPI, tabla o narrativa visual del proyecto (slides,
  decks HTML, notebooks, reportes, matplotlib o Plotly), o al redactar
  títulos, anotaciones y limitaciones de un hallazgo. Para construir una
  presentación HTML usa build-html-presentation, que aplica este skill.
---

# Visualización con la metodología de Julia

Crea visualizaciones que ayuden a una audiencia concreta a entender un hallazgo
y a decidir o actuar. Optimiza claridad, honestidad, interpretabilidad y
consistencia; no decoración ni novedad visual.

Fuente: [skill original de Julia](../../../docs/julia/SKILL.md), derivado de un
curso de visualización. Este skill conserva su método y lo adapta a un agente
que analiza, construye y revisa el gráfico. No modifiques el original.

## Alcance y precedencia

- Aplica las reglas del usuario y de [AGENTS.md](../../../AGENTS.md) antes que
  este método: privacidad, modo de entrega, cohortes, idioma español y
  formato de cifras.
- Este skill decide **qué** mostrar y **cómo** debe leerse. La herramienta de
  construcción (por ejemplo `html-slide-generator`, matplotlib o Plotly)
  decide cómo implementarlo, sin anular estos criterios.
- Si el trabajo requiere consultar Redshift o evaluar una variable, carga
  primero `attrition-redshift-db` y, cuando aplique,
  `evaluate-attrition-variable`. Presentar evidencia existente no reevalúa
  scores.
- Lee [extensiones de Attrition](references/extensiones-attrition.md) siempre
  que el gráfico muestre tasas, cohortes, poblaciones o datos de RH.

## Principio central

> Un gráfico, un mensaje.

Cada gráfico comunica una conclusión. Si hay varios hallazgos, decide si forman
una historia **vertical** (cada uno profundiza en el anterior) o **horizontal**
(hallazgos relacionados que no se contienen) y usa varios gráficos coordinados.

Recorre los cuatro pasos en orden. No empieces eligiendo el tipo de gráfico;
empieza por el hallazgo.

## Paso 1: aclarar el mensaje

Convierte un resultado en un mensaje específico y relevante para la audiencia.

Investiga el número que llamó la atención desde tres ángulos:

- **Concentración:** ¿dónde es más fuerte el patrón? Desagrega por dimensiones
  con sentido (equipo, ubicación, nivel, rol, tenure, segmento).
- **Comparación:** ¿contra qué? Otro grupo, un benchmark, una meta, un periodo
  previo o un valor esperado.
- **Cambio:** ¿cómo se ha movido en el tiempo? Distingue saltos de tendencias.

«El valor total es 72%» es un **resultado**. «El valor bajó a 72%,
principalmente entre empleados senior, y ya está por debajo del benchmark» es
un **mensaje**.

Comprueba que sea accionable: ¿a quién afecta?, ¿qué cambió?, ¿comparado con
qué?, ¿por qué le importa a la audiencia?, ¿qué decisión, investigación o
acción puede apoyar?

### Precisión sobre la evidencia

No conviertas asociación en causalidad. Usa lenguaje acorde con los datos:

- Prefiere: «se concentra en», «se asocia con», «coincide con», «es el tema
  dominante entre», «podría estar contribuyendo a».
- Evita sin evidencia causal: «causó», «impulsó», «provocó», «está detrás de»,
  «driving». Esto incluye títulos de ejemplo: «Los empleados senior explican
  la mayor parte de la caída» es una afirmación de concentración que requiere
  una descomposición; «impulsan la caída» exige además evidencia causal.

Declara las limitaciones que cambien la lectura: historia faltante, muestras
pequeñas, cobertura incompleta, cambios de metodología o la diferencia entre
un nivel actual y un cambio en el tiempo.

Si hace falta un cruce nuevo para sostener el mensaje, formula primero la
hipótesis específica. No explores combinaciones hasta encontrar una historia.

### ¿Merece un gráfico?

- **Cifra grande:** cuando un valor es todo el mensaje y no se necesita
  tendencia ni comparación.
- **Gráfico:** cuando la audiencia necesita ver tendencia, comparación,
  distribución o relación.
- **Tabla:** como detalle, valores exactos o complemento accesible; rara vez
  como pieza principal de la historia.
- **Diagrama:** para procesos, relaciones o decisiones conceptuales. No
  inventes datos para justificar un gráfico en contenido conceptual.

## Paso 2: elegir el gráfico

### Tendencia en el tiempo: líneas

- Representa los intervalos con honestidad: espacios iguales, tiempos iguales.
- Deja huecos en periodos faltantes; nunca los conectes como si fueran
  conocidos.
- No suavices por defecto; el suavizado sugiere cambios no observados.
- Resalta la serie clave y atenúa las de contexto.
- Con pocos periodos, usa barras si importa más la comparación que la
  trayectoria.

### Comparación entre categorías: barras

- **Verticales** para pocas categorías, etiquetas cortas u orden natural.
- **Horizontales** para etiquetas largas o muchas categorías.
- Ordena con lógica cuando no exista un orden natural.
- El eje de barras empieza en cero; recortarlo distorsiona la magnitud.
- Evita etiquetas diagonales y densidad innecesaria.

### Parte-todo

Usa barra apilada cuando importan el total y la composición.

- Decide si el mensaje es de magnitud absoluta o de composición porcentual.
- Incluye el total o explica qué se agrupó o excluyó.
- Limita las subcategorías; agrupa las menores en «Otros» con una nota.
- Sólo se comparan bien los segmentos que comparten línea base; usa paneles si
  hay que comparar segmentos intermedios.

Usa pie o donut sólo cuando el foco es **una** proporción del total, hay pocas
porciones (idealmente cinco o menos, siete como máximo), la porción clave
empieza a las 12 cuando sea práctico y no hay efectos 3D ni porciones
separadas. Que una plantilla traiga un donut no justifica usarlo.

### Elegir entre alternativas

Cuando la elección sea ambigua, describe dos o tres bocetos (tipo de gráfico,
codificación, orden, énfasis) y compáralos por: alineación con el mensaje,
velocidad de lectura, riesgo de mala interpretación, accesibilidad y
complejidad. Elige uno y registra por qué se descartaron los demás. Los
bocetos pueden ser descripciones; no hace falta construirlos todos.

## Paso 3: simplificar

Cada elemento por defecto es opcional; sólo se queda si ayuda a entender el
mensaje.

Reduce o elimina: bordes, sombras, gradientes y efectos 3D dentro del gráfico;
títulos de gráfico y de eje redundantes; cuadrículas pesadas; marcas de eje y
fechas repetidas; leyendas cuando sea posible etiquetar directamente; colores
innecesarios y énfasis que compitan.

En líneas, usa un rango de eje informativo: suficiente para ver el movimiento,
sin exagerar diferencias pequeñas ni ocultar el patrón, con un margen modesto.

### Etiquetado directo

- Coloca las etiquetas junto a los datos en lugar de una leyenda.
- Etiqueta sólo los valores que importan: último, inicio y fin, máximo,
  mínimo o un valor atípico relevante.
- Etiqueta todos los valores sólo cuando la precisión sea central y haya
  espacio.

### Color con intención

- Un color de énfasis para la serie o categoría clave; gris o tono atenuado
  para el contexto.
- Uno o dos colores clave por gráfico salvo que el mensaje exija más.
- Mantén el significado del color en toda la historia.
- No dependas sólo de rojo/verde; combina con etiquetas, marcadores o estilos
  de línea, o usa azul/naranja.
- Revisa convenciones del proyecto u organización antes de asignar
  significado a un color (ver extensiones de Attrition).

## Paso 4: amplificar el mensaje

Un gráfico limpio también necesita interpretación. Haz que la conclusión se
encuentre aunque el gráfico se reenvíe sin contexto.

### Título activo

El título dice la conclusión, no describe los datos.

- Prefiere: «La attrition voluntaria de Critical Tech se concentra en los
  primeros dos años de tenure», «Los ingresos crecieron cada trimestre hasta
  un máximo en Q4».
- Evita: «Attrition por tenure», «Ingresos por trimestre».
- Empieza por la conclusión, con verbos activos y específicos (creció, cayó,
  superó, se estancó, se recuperó, se concentra).
- Una línea si es posible; dos como máximo.
- Añade subtítulo sólo si la audiencia necesita la medida, población, ventana
  o unidad de análisis. En este proyecto casi siempre la necesita.
- Una pregunta abierta o una hipótesis se titula como tal; no como hallazgo.

### Contexto útil

Usa sólo el contexto que fortalezca el mensaje: línea de meta, benchmark
interno, benchmark externo con fuente citada o rango de referencia. No
agregues referencias sólo porque existen.

### Anotaciones

Anota cuando ayude a explicar **por qué** (posible explicación de un cambio),
**qué pasó** (lanzamiento, política, reorganización, cambio de metodología) o
**qué es inusual** (atípico, periodo faltante, ruptura de serie). Distingue
coincidencia temporal de causalidad: «Entran nuevos criterios de promoción» es
más seguro que «Los nuevos criterios causaron la caída».

## Historias con varios gráficos

- Mantén colores, fuentes, posición de títulos, notas de fuente y formato.
- Conserva el significado de los colores de énfasis y de contexto.
- Usa rangos de eje comparables en hallazgos paralelos cuando corresponda.
- No cambies de tipo de gráfico sólo para variar.
- Agrupa en una misma diapositiva los gráficos que sólo se entienden juntos.
- En historias verticales, avanza del patrón general a la explicación
  específica.

La audiencia debe sentir que recorre una historia, no una colección de
gráficos sueltos.

## Revisión crítica propia

El método original usaba una IA como analista junior y como revisora. Aquí el
agente analiza y construye, así que debe hacer esa revisión sobre su propio
trabajo antes de entregar:

1. **Explorar con ángulos, no respuestas:** patrones, hipótesis alternativas,
   evidencia a favor y en contra, datos que faltan y limitaciones.
2. **Poner a prueba el mensaje:** intenta refutarlo; identifica afirmaciones
   demasiado fuertes o amplias y propone una redacción más defendible.
3. **Revisar el gráfico terminado** con la
   [guía de autocrítica](references/autocritica.md), idealmente sobre una
   captura renderizada y no sólo sobre el código.

Reglas:

- Trata como no verificados los números, patrones y sugerencias generados;
  valida cálculos, totales y denominadores contra la fuente.
- No inventes valores, fuentes, benchmarks ni explicaciones causales para
  fortalecer un título.
- Justifica cada cambio con su motivo y sus costos; no apliques una sugerencia
  sólo porque apareció en la revisión.
- Pide al usuario bocetos o decisiones sólo si cambian materialmente el
  resultado y no pueden inferirse.

## Checklist y formato de respuesta

Antes de entregar, recorre el [checklist de calidad](references/checklist.md).

Al crear o mejorar un gráfico, documenta en este orden (brevemente cuando el
encargo sea pequeño):

1. **Audiencia y decisión:** quién lo usará y qué decisión o acción apoya.
2. **Mensaje central:** conclusión en una frase.
3. **Evidencia y limitaciones:** valores clave, comparación, tendencia,
   población, n, ventana y limitaciones.
4. **Elección del gráfico:** tipo elegido y por qué se descartaron otros.
5. **Especificación de diseño:** título, subtítulo, ejes, etiquetas, colores,
   anotaciones, benchmark y accesibilidad.
6. **Validación:** comprobaciones contra la fuente.
7. **Revisión final:** trade-offs o riesgos de interpretación pendientes.
