# Observaciones al plan alterno de presentación: B → C → C + QVoice

## 1. Contexto del encargo

El usuario necesita una presentación para líderes y Recursos Humanos que explique los avances del proyecto de attrition voluntaria de Engineering: qué teníamos con B, qué probamos con C y QVoice, cómo llegamos a C + QVoice y por qué las pruebas posteriores, incluido D, no cambiaron esa elección.

La referencia es el deck de Julia del 5 de octubre de 2026. Se acordaron **9 diapositivas, incluida la agenda, 18 minutos de exposición y 2 minutos de preguntas**, texto proyectado en inglés, guion en español y lenguaje comprensible para una audiencia sin especialización técnica. Las tablas, imágenes explicativas y animaciones deben ayudar a entender la selección.

El modelo elegido continúa siendo **CQ, versión `engineering-c-qvoice-20261008-v1`, sin calibración posterior adicional del riesgo a seis meses**. La decisión se confirmó el 10 de octubre de 2026. El artefacto final usa un corte de datos al 7 de septiembre de 2026; sus coeficientes todavía requieren una evaluación posterior a su ajuste. El piloto no ha comenzado.

Este documento reúne los comentarios para compartir con el analista que preparó el plan alterno. Incluye lo que conviene conservar, las correcciones de contenido, los ajustes de narrativa y las decisiones que deben quedar claras para implementar la presentación.

| Campo | Referencia |
|---|---|
| Fecha de las observaciones | 10 de octubre de 2026 |
| Estado | Observaciones para revisión del plan alterno |
| Documento revisado | [Plan alterno](20261010-presentacion-evolucion-b-cq-alterno.md) |
| Plan de partida | [Plan original](20261010-presentacion-evolucion-b-cq.md) |
| Clasificación de la futura presentación | `presentation` |
| Criterios aplicados | `build-html-presentation` y `morgan-vis` |
| Alcance de la revisión | Narrativa, interpretación de evidencia archivada, diseño e implementación propuesta |

Las referencias H1–H8 y los números de diapositiva corresponden al plan alterno. Las fuentes E01–E12 se detallan al final del documento.

## 2. Valoración general

**Usaría el plan alterno como base, incorporando los ajustes siguientes.** Mejora la explicación para líderes y RH, conserva la extensión acordada y conecta mejor las pruebas realizadas con los avances del proyecto.

La historia central debe seguir siendo: **qué teníamos con B, qué aportaron C y QVoice, por qué CQ permanece elegido y qué falta comprobar antes de usarlo**. El seguimiento de compromisos ayuda a esa historia; también debe quedar suficiente espacio para explicar el punto de partida y la selección.

Las principales cifras contrastadas coinciden con los resultados archivados. Las correcciones más importantes afectan al alcance de algunas afirmaciones y a la forma de presentar las medidas, especialmente la sobreestimación media, el error por grupo y la declaración sobre puntuaciones individuales.

## 3. Lo que mantendría

1. **El seguimiento a los pendientes del deck anterior.** Ayuda a mostrar avances concretos: nuevas señales, métodos alternativos, estimaciones y comprobaciones pendientes.

2. **La referencia de selección al azar.** Explicar que un 30% elegido al azar concentraría aproximadamente el 30% de las salidas ayuda a interpretar el 43.1% de CQ.

3. **La identificación visible de los periodos.** Es necesaria para entender por qué C aparece con 45.4% en una comparación y con 42.4% en otra. La comparación B–C usa cuatro periodos y la comparación C–CQ–D usa dos periodos comunes.

4. **Los nombres comprensibles para los modelos.** “Core HR”, “Expanded HR” y “HR + employee feedback” facilitan la lectura. Mantendría también B, C y CQ como etiquetas secundarias para conservar la conexión con la documentación.

5. **La explicación equilibrada de las alternativas.** D mejora ligeramente una medida, pero pierde concentración de salidas en el periodo reciente. El bosque tiene una concentración similar y mayor error por grupo. Esa explicación sustenta la elección.

6. **La separación entre resultados históricos y versión final.** Es correcto aclarar que las evaluaciones históricas emplearon los modelos disponibles en cada fecha y que la versión final todavía requiere una evaluación posterior.

7. **Los siguientes pasos como propuestas.** Comprobar nuevos datos, revisar diferencias entre grupos, confirmar el uso de QVoice y preparar un piloto son pasos razonables. Sus fechas, alcance y responsables deben establecerse cuando corresponda.

8. **La construcción reproducible y la trazabilidad.** Conservaría la lectura directa de resultados, el registro de evidencia, las comprobaciones de cifras, los cuatro temas y el funcionamiento sin conexión.

## 4. Correcciones importantes de contenido

### O01. Corregir la afirmación sobre puntuaciones individuales

**Dónde:** H6, diapositiva 7 y respuesta preparada sobre el uso de QVoice.

La frase “No individual scores are produced or shared” afirma más de lo que acreditan las fuentes citadas. Estas indican que no se publican puntuaciones individuales y que no se guardan filas de empleados. El procesamiento interno autorizado utiliza información individual en memoria.

Las banderas `individual_scores_published: false` y `employee_level_rows_persisted: false` no demuestran que nunca se calculen puntuaciones individuales internamente.

**Redacción propuesta para la diapositiva:**

> Only group-level results are reported; no individual scores are published.

**Respuesta propuesta para el guion en español:**

> Durante el análisis autorizado se procesan respuestas a nivel individual en memoria. Los resultados compartidos son agregados por grupo; no se publican puntuaciones individuales.

**Criterio de cierre:** la diapositiva y el guion distinguen procesamiento interno, almacenamiento y publicación, usando afirmaciones respaldadas por las fuentes.

**Fuentes:** E01, E03 y E11.

### O02. Conservar el 20% como resultado complementario

**Dónde:** H2, portada, diapositiva 6 y conclusión general.

La reducción de aproximadamente **20% en sobreestimación media es correcta**, pero debe identificarse su alcance:

- Compara CQ frente a C.
- Corresponde a los grupos priorizados que cubren el 30% de la población.
- Es una reducción relativa de la diferencia media entre estimado y observado.
- El error por grupo y mes mejora **2.3%**.

Mantendría visible el **2.3%**, porque esa medida también se utiliza para comparar las alternativas. Dar protagonismo al 20% y después descartar modelos por otra medida puede hacer que la selección parezca inconsistente.

La distinción tiene una consecuencia práctica: el bosque presenta una diferencia media menor entre estimado y observado, pero su error por grupo es **10.3% mayor** que el de CQ. Al promediar diferencias con signo, las sobreestimaciones y subestimaciones pueden compensarse. Por eso una diferencia media cercana a cero no garantiza estimaciones cercanas en cada grupo o periodo.

**Cambio propuesto:** mantener el 20% en el respaldo o como explicación secundaria, con el comparador y el alcance explícitos. La selección debe seguir apoyándose en la concentración de salidas, el error por grupo y la estabilidad entre periodos.

Además, el observado cambia entre C y CQ porque pueden priorizar grupos diferentes. Esa explicación debe acompañar cualquier tabla de estimado frente a observado. La reducción porcentual debe calcularse antes de redondear los valores visibles.

**Criterio de cierre:** ningún título o indicador presenta el 20% como mejora general del modelo; el 2.3% conserva su significado de reducción relativa del error por grupo y mes.

**Fuentes:** E01, E03 y E05.

### O03. Precisar qué significa «el peor grupo»

**Dónde:** tabla de §5.3 y diapositiva 6.

Los valores **2.1 y 2.2** corresponden al promedio entre periodos del indicador de mayor error de grupo publicable, `worst_publishable_group_error_pp`. No siguen necesariamente al mismo grupo.

La frase “The worst-estimated group did not improve” resulta demasiado general. En el último periodo, ese indicador baja aproximadamente de **2.4 a 2.3**. El aumento del promedio entre periodos no equivale a afirmar que el indicador empeoró en cada periodo.

**Redacción propuesta para la diapositiva:**

> Some group estimates still need improvement.

En el respaldo sí explicaría exactamente cómo se calcula el indicador, los valores por periodo y la población a la que corresponde.

También distinguiría esta evidencia del pendiente del deck anterior: la comparación C–CQ sobre grupos priorizados no demuestra por sí sola qué ocurrió con el grupo específico de mayor riesgo mostrado anteriormente para B.

**Criterio de cierre:** se conserva la limitación sobre errores en grupos concretos, sin presentar un promedio de indicadores como seguimiento de un único grupo.

**Fuente:** E05, campos de `summary` y `periods`.

### O04. Separar la utilidad del modelo completo del aporte de QVoice

**Dónde:** H3, portada y diapositiva 6.

La referencia aleatoria explica la utilidad del modelo completo. Para explicar qué añadió QVoice, la comparación pertinente es:

| Comparación en los dos periodos comunes | Proporción de salidas en los grupos priorizados |
|---|---:|
| Referencia de un 30% elegido al azar | Aproximadamente 30% |
| C | 42.4% |
| CQ | 43.1% |

El aporte incremental de QVoice frente a C es de aproximadamente **0.7 puntos porcentuales**. La portada debe permitir reconocer esa diferencia. De otro modo, podría atribuirse a QVoice toda la distancia entre el 30% aleatorio y el 43.1%.

**Cambio propuesto:** mantener ambos comparadores, cada uno con su función. En la diapositiva 6, conservar las barras de C y CQ y la línea de referencia aleatoria, sobre una escala que comience en cero.

**Criterio de cierre:** se puede distinguir el desempeño del modelo completo de la mejora incremental por añadir QVoice. El 43.1% se describe como proporción de salidas observadas dentro de grupos que cubren el 30%, sin convertirlo en probabilidad personal o en salidas evitadas.

**Fuentes:** E01, E03 y E05.

### O05. Precisar el resultado del ajuste adicional a seis meses

**Dónde:** diapositiva 4, tercer paso, y §5.5.

La frase “Did not hold in later periods” amplía demasiado la evidencia de esta prueba.

En agosto–diciembre de 2025 no hubo historia suficiente para estimar ese ajuste; se mantuvo la versión sin corrección. La corrección efectiva se evaluó en enero–febrero de 2026 y no mejoró el balance. El artefacto final no añade otra evaluación posterior.

**Redacción propuesta:**

> The added adjustment did not improve the January–February 2026 test.

Conservaría en las notas la falta de historia del primer periodo. Esto evita presentar dos comprobaciones efectivas de la corrección donde sólo hubo una.

El resultado describe esa prueba. No permite concluir que cualquier calibración o ajuste posterior sea inútil.

**Criterio de cierre:** el guion diferencia un periodo sin ajuste por historia insuficiente del periodo en el que sí se evaluó una corrección estimada.

**Fuente:** E10.

### O06. Evitar que «≈» sugiera equivalencia demostrada

**Dónde:** diapositiva 8 y su regla de símbolos.

El criterio visual de marcar como aproximadamente iguales diferencias de hasta ±0.5 puntos puede ocultar información relevante. D quedaría cerca de CQ en el promedio, aunque pierde más en el periodo reciente de lo permitido por su regla de selección.

**Cambio propuesto:** conservar los valores con un decimal y usar una explicación breve. Si se mantiene «≈», aclarar que representa cercanía numérica y que no constituye una prueba de equivalencia ni una regla de adopción.

Mantendría estas distinciones en la tabla y el guion:

- D reduce el error por grupo y mes aproximadamente **0.8%** frente a CQ, por debajo del 10% requerido por su ruta de precisión.
- En enero–febrero de 2026, CQ concentra **42.8%** de las salidas y D **42.1%**; D no cumple el límite permitido de pérdida por periodo.
- El bosque tiene una concentración similar a CQ al redondear, con **10.3% más error por grupo y mes**.
- Las preguntas fijas con promedio revisado conservan el **43.1%**, con **4.1% más error por grupo y mes** que CQ.

**Criterio de cierre:** los símbolos complementan las cifras y no ocultan el motivo por el que una alternativa no sustituye a CQ.

**Fuentes:** E03, E05 y E06.

### O07. Mantener los límites de la evidencia estadística

**Dónde:** H7, diapositiva 6 y preguntas preparadas.

Es útil conservar en el guion el intervalo de la mejora de CQ frente a C. Debe acompañarse de su alcance: depende de los modelos ajustados, las prioridades y los periodos observados; no incorpora toda la incertidumbre de selección y entrenamiento. Las ventanas y personas se comparten entre periodos.

No convertiría ese intervalo en una afirmación de superioridad general. La explicación principal sigue siendo:

> CQ mejoró en un periodo y empató en el otro, con una mejora promedio modesta.

La elección vigente combina la magnitud de la mejora, el error de estimación y la utilidad de los grupos. La regla histórica más estricta que exigía ganar en ambos periodos debe conservarse como antecedente, tal como se documenta en la decisión vigente.

Las nueve variantes iniciales de QVoice deben describirse como **nueve variantes evaluadas**, evitando que parezcan nueve estudios o periodos independientes. El mensaje «9 de 9 mejoraron el ordenamiento; 0 de 9 pasaron todas las comprobaciones» es válido con ese alcance.

También debe mantenerse la distinción entre los modelos ajustados antes de cada periodo y el artefacto final con corte de datos al 7-sep-2026. Las métricas históricas no constituyen una evaluación posterior de sus coeficientes finales.

**Criterio de cierre:** las mejoras se presentan como retrospectivas y modestas, con el resultado por periodo visible y sin afirmar que se ha comprobado el desempeño futuro de la versión final.

**Fuentes:** E01, E03, E04 y E08.

### O08. Acotar las afirmaciones sobre pendientes

**Dónde:** H1, H6, diapositiva 9 y respuestas preparadas.

Para fairness, la evidencia revisada permite decir:

> No se encontró una evaluación archivada en los estudios revisados.

Eso es más preciso que afirmar que nunca se ha evaluado en el proyecto. En la presentación puede mantenerse como revisión pendiente de documentar o completar, según el estado que confirme el equipo.

Aplicaría el mismo criterio al acuerdo de uso de QVoice: confirmar y documentar su alcance vigente. Si existe un acuerdo, citarlo; si falta, mantenerlo como siguiente paso propuesto. La autorización de procesamiento interno no sustituye por sí sola la definición del uso en un futuro piloto.

**Criterio de cierre:** el plan no transforma la falta de una fuente entre los documentos revisados en una afirmación absoluta sobre todo el proyecto. Los siguientes pasos se identifican como propuestas y respetan las autorizaciones existentes que resulten aplicables.

**Fuentes:** H1 y H6 del plan alterno; E11 para el alcance del procesamiento interno.

## 5. Ajustes de narrativa

### 5.1. Conservar una explicación suficiente de B

La nueva diapositiva 3 dedica casi todo el espacio a compromisos. El objetivo original incluye explicar de dónde partimos.

Mantendría un diagrama breve que muestre cómo B organiza grupos mediante antigüedad, salidas previas del equipo y nivel. La audiencia debe entender esa base antes de escuchar que C y CQ conservan sus definiciones.

Tampoco asumiría que todos vieron el deck anterior. La presentación debe poder entenderse por sí misma. Una transición como «Empecemos por el modelo de partida y los puntos que queríamos mejorar» funciona para ambas audiencias.

El componente gráfico original puede servir como referencia. La elección de conservarlo o simplificarlo debe basarse en lo que necesita comprender la audiencia y en la verificación de su funcionamiento.

### 5.2. Cambiar «3 of 4 commitments addressed»

La tabla muestra dos actividades terminadas, una parcial y una pendiente. Aunque “addressed” puede incluir trabajo parcial, el título puede leerse como tres compromisos cumplidos.

**Título propuesto:**

> What we completed and what remains.

Además, las cuatro filas mostradas reorganizan los compromisos originales: separan la sobreestimación y fairness, y llevan la condición de adopción a otras diapositivas. Evitaría convertir esa reorganización en un porcentaje de cumplimiento.

### 5.3. Mantener visibles las definiciones de grupo

Preferiría **“Same group definitions”** frente a “Same groups”. Las definiciones se conservan, pero las personas incluidas, los grupos elegibles y el orden de prioridad pueden cambiar entre fechas y modelos.

Los nombres B, C y CQ deben acompañar a sus descripciones sencillas de forma consistente. «Level / 8 groups» se refiere a las categorías de nivel del deck de referencia; no al número de diapositivas ni al número total de grupos de riesgo.

### 5.4. Explicar D como un conjunto de pruebas

“Extra history test” describe una parte del trabajo de D. También hubo pruebas de representación de QVoice y controles de método.

**Etiqueta propuesta:**

> Additional signals and model tests (D)

En las notas aclararía que las nuevas señales históricas se probaron, pero no quedaron seleccionadas en la versión final. D conservó Q4, Q12 y Career en su corrección sobre C.

Para el título de la diapositiva 8, “Further tests did not justify replacing CQ” evita que tres filas de alternativas se interpreten como un inventario exhaustivo de sólo tres ejecuciones.

## 6. Ajustes propuestos para las nueve diapositivas

Se conserva el reparto de tiempos del plan alterno: **1080 segundos de exposición, equivalentes a 18 minutos**, más 2 minutos de preguntas.

| Diapositiva | Tiempo | Ajuste propuesto |
|---|---|---|
| 1. Decisión | 1:00 | Mostrar claramente que CQ permanece elegido. Conservar el 43.1%, identificar la mejora frente a C y reducir el protagonismo del 20%. |
| 2. Recorrido | 0:45 | Mantener B → C → CQ, con las pruebas relacionadas como ramas. Explicar una sola vez por qué existen dos conjuntos de periodos. |
| 3. Punto de partida y avances | 2:00 | Dar espacio suficiente al diagrama de B y conservar el estado de los pendientes. Retirar «3 of 4». |
| 4. Primeras pruebas de QVoice | 2:00 | Mantener los tres pasos y el dato 9 de 9 / 0 de 9. Explicar qué impedía adoptar las variantes y precisar el alcance del ajuste a seis meses. |
| 5. B frente a C | 2:15 | Mantener la tabla de dos medidas. Explicar “gap” como diferencia entre estimado y observado. Identificar el 11% como reducción relativa del error de grupo. |
| 6. C frente a CQ | 3:00 | Priorizar barras, referencia aleatoria, mejora del 2.3% y resumen de los dos periodos. Llevar la tabla completa de estimado frente a observado al guion. |
| 7. Funcionamiento | 2:00 | Mostrar cómo la información de RH y QVoice contribuye a estimar y priorizar grupos. Corregir la afirmación sobre puntuaciones individuales. |
| 8. Alternativas | 3:00 | Conservar cifras redondeadas y una explicación del balance. Mostrar el periodo reciente de D. Evitar que los símbolos de similitud sustituyan la evidencia. |
| 9. Cierre | 2:00 | Repetir la elección de CQ y los cuatro pasos propuestos. Incluir la revisión de errores por grupo dentro de la comprobación con nuevos datos. |

La diapositiva 6 requiere especial cuidado: las barras, la referencia aleatoria, la tarjeta de estimación, la tabla por periodo, la franja temporal y varias notas pueden competir por atención. El gráfico principal, una medida de error y el resumen por periodo deben formar una lectura clara. El detalle restante se desarrolla en el guion.

## 7. Detalles que cerraría para implementar sin ambigüedad

### 7.1. Franja de periodos

En cada diapositiva mostrar sólo el conjunto que corresponde:

- Diapositiva 5: “4 historical periods · Feb 2024–Jan 2026”.
- Diapositivas 6 y 8: “2 historical periods · Aug 2025–Feb 2026”.

La explicación extensa sobre ambos conjuntos puede aparecer una vez en la agenda y quedar desarrollada en el guion. Los periodos de QVoice están limitados por la historia utilizable y el seguimiento disponible.

Los porcentajes B 45.2%, C 45.4% y CQ 43.1% no deben conectarse como una única serie de desempeño. Un diagrama conceptual B → C → CQ sí ayuda a explicar la evolución del trabajo.

### 7.2. Comportamiento de las animaciones

La propuesta mezcla avance por clic con `Play` y una secuencia completa de seis segundos. Recomendaría definir este comportamiento:

1. `Play` reproduce la secuencia completa, con una duración máxima de seis segundos.
2. `Replay` reinicia la secuencia.
3. `Show all` muestra el resultado completo.
4. Cambiar de diapositiva cancela la reproducción.
5. Con movimiento reducido se muestra el estado final.
6. Las flechas conservan su función de navegación entre diapositivas.

Si se desea avance por pasos, debe definirse un control específico y actualizar la especificación para que no queden dos comportamientos distintos descritos como si fueran el mismo.

Al menos una animación debe ayudar a comprender cómo se forman o priorizan los grupos. Revelar filas de una tabla ayuda al ritmo, pero aporta poca explicación por sí mismo.

### 7.3. Fuentes visibles y evidencia cualitativa

Recuperaría la instrucción explícita de incluir en cada visual cuantitativo una fuente breve, fecha, población y ventana. El archivo `evidence.json` complementa esa información con campos, fórmulas y rutas exactas.

También deben registrarse las fuentes de afirmaciones cualitativas como:

- Se conservan las definiciones de grupo.
- No se encontró evaluación de fairness entre las ejecuciones revisadas.
- Las señales históricas de D no quedaron seleccionadas.
- La versión final requiere una evaluación posterior.

Conservar el mínimo de cohortes establecido por el proyecto y revisar que los datos embebidos en HTML y JavaScript sean agregados permitidos.

### 7.4. Cálculos, redondeo y campos faltantes

- Calcular diferencias y reducciones con los valores originales, antes de formatear.
- Mantener enteros sin decimales y el resto con un decimal como máximo en elementos visibles.
- No recalcular una reducción relativa desde los valores ya redondeados que ve la audiencia.
- Mantener separadas las definiciones de `group_mae_pp` y `group_snapshot_mae_pp`. El registro de evidencia debe indicar cuál usa cada comparación.
- Identificar los promedios por periodo y evitar sumar exposiciones mensuales como personas o salidas únicas.
- Permitir “n/a” en información secundaria cuando resulte apropiado. Si falta una cifra central para justificar la decisión, resolverla antes de entregar.
- Las comprobaciones deben verificar la correspondencia con las fuentes y las fórmulas; conviene evitar validaciones que sólo comparen dos copias del mismo valor introducido manualmente.

### 7.5. Verificador, base y revisión visual

Mantendría el inglés solicitado y la excepción documentada para el verificador que exige `lang="es"`. La mejora opcional del verificador puede realizarse por separado y no necesita convertirse en una dependencia de esta presentación.

Conservar la base vigente de Julia, los cuatro temas y la construcción sobre una copia nueva. El registro de validación debe reflejar los resultados reales del verificador y la revisión del navegador.

Comprobar legibilidad, navegación, animaciones, fuentes y funcionamiento sin conexión. La revisión del plan todavía no demuestra que todo el contenido quepa correctamente en el HTML final.

## 8. Matices sobre las observaciones al plan original

Coincido con las mejoras propuestas en H3 y H4, pero ajustaría su diagnóstico:

- **H3:** comparar con C ya proporciona una referencia explícita. Añadir la referencia aleatoria mejora la interpretación del resultado absoluto; no implica que cualquier comparación sin ella incumpla necesariamente el método. Su utilidad debe justificarse por lo que ayuda a comprender.
- **H4:** el plan original ya diferenciaba los periodos en subtítulos, notas visibles y especificaciones. La franja propuesta mejora su consistencia y visibilidad. Describiría el cambio de esa manera, en lugar de afirmar que la distinción sólo estaba en el guion de preguntas.

Estos matices permiten registrar con precisión qué se corrige y qué se mejora en la comunicación.

## 9. Lista de cierre para revisar el plan actualizado

- [ ] O01: corregida la frase sobre producción de puntuaciones individuales y alineada la respuesta del guion.
- [ ] O02: el 20% tiene comparador y alcance explícitos; el 2.3% permanece identificado como reducción relativa del error por grupo y mes.
- [ ] O03: el promedio del indicador de mayor error no se presenta como seguimiento del mismo grupo.
- [ ] O04: se distingue el aporte incremental de QVoice del desempeño del modelo completo frente al azar.
- [ ] O05: la prueba del ajuste a seis meses diferencia el periodo sin historia suficiente del periodo con corrección efectiva.
- [ ] O06: los símbolos de similitud no sustituyen cifras ni reglas de selección.
- [ ] O07: se conserva el resultado de mejora en un periodo y empate en el otro, junto con los límites de la evaluación histórica.
- [ ] O08: los pendientes se describen con el alcance de la evidencia revisada y se confirma cualquier acuerdo existente que deba citarse.
- [ ] La diapositiva 3 explica B y usa un título de avances sin un conteo ambiguo de cumplimiento.
- [ ] La diapositiva 6 tiene una lectura principal clara y el detalle adicional pasa al guion.
- [ ] La identificación de CQ, su corte de datos y el alcance de su elección coinciden con la referencia vigente.
- [ ] Se conservan las 9 diapositivas y los 18 minutos de exposición más 2 de preguntas.
- [ ] Los periodos, las fuentes visibles, los cálculos y los controles de animación tienen una especificación única y verificable.

## 10. Fuentes de respaldo

Las observaciones se basan en documentación y resultados agregados ya archivados. Las fechas de ejecución, población, ventanas y campos utilizados se conservan en esas fuentes y en los contratos de los planes.

| ID | Fuente | Uso en estas observaciones |
|---|---|---|
| E01 | [Decisión vigente de selección](../docs/context/model-selection-current.md) | Identidad de CQ, argumentos, alcance de la elección, modelos históricos y versión final |
| E02 | [Comparación B–C con cortes de B](../output/analysis/engineering/20261008/c-group-selection-v1/results.json) | Captura y error de grupo en los cuatro periodos; `summary["30"].B_cuts` y `C_Bcuts` |
| E03 | [Resultados de CQ y mezclas fijas de encuesta](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/results.json) | Comparaciones de C, CQ y preguntas fijas; intervalos y banderas de publicación y persistencia |
| E04 | [Informe de las mezclas de encuesta](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/informe.md) | Alcance de intervalos, periodos compartidos y procesamiento en memoria |
| E05 | [Resultados del experimento D](../output/analysis/engineering/20261010/model-d-v1/results.json) | C, CQ, D y RSF_Q; `summary.<modelo>.scenarios["30"]` y `periods[].evaluation.<modelo>.scenarios["30"].metrics` |
| E06 | [Decisión del experimento D](../output/analysis/engineering/20261010/model-d-v1/selection-decision.json) | Reglas de adopción, pérdida por periodo y motivos para conservar CQ |
| E07 | [Informe del experimento D](../output/analysis/engineering/20261010/model-d-v1/informe.md) | Alcance de las pruebas y señales seleccionadas |
| E08 | [Informe de las nueve variantes iniciales de B + QVoice](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/informe-modelo-b-qvoice.md) | Mejora de ordenamiento en las nueve variantes y resultado de las comprobaciones conjuntas |
| E09 | [Informe de B + QVoice calibrado](../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/informe-modelo-b-qvoice-calibrado.md) | Aporte de QVoice y limitaciones de la calibración general |
| E10 | [Informe del ajuste adicional a seis meses](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/informe.md) | Primer periodo sin ajuste por historia insuficiente y resultado de la corrección en enero–febrero de 2026 |
| E11 | [Autorización de procesamiento interno en memoria](../config/attrition_model_in_memory_training_authorization_20261001.json) | Distinción entre procesamiento interno, persistencia y resultados publicados |
| E12 | [Base de Julia del 5 de octubre con ajuste de grupos de nivel](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html) | Estilo, nueve diapositivas y pendientes del deck de referencia |

## 11. Recomendación final

Conservaría la estructura del plan alterno y corregiría las afirmaciones señaladas. La presentación debe permitir defender esta conclusión:

> B proporcionó una base comprensible. C acercó las estimaciones a lo observado. QVoice añadió una mejora modesta en la priorización y en el error promedio. Las pruebas posteriores no ofrecieron un balance suficientemente mejor para sustituir CQ. La siguiente etapa es comprobar la versión final con datos posteriores y completar las revisiones necesarias para un piloto.
