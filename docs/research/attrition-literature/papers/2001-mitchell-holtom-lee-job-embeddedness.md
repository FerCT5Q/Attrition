# P15 — Why People Stay: Using Job Embeddedness to Predict Voluntary Turnover

## Ficha y nivel de evidencia

- **Autores:** Terence R. Mitchell, Brooks C. Holtom, Thomas W. Lee, Chris J. Sablynski y Miriam Erez.
- **Publicación:** 2001; *Academy of Management Journal*, 44(6), 1102–1121, según Crossref.
- **DOI registrado:** [10.2307/3069391](https://doi.org/10.2307/3069391). La consulta de `10.5465/3069391` redirige al mismo registro de Crossref; no se cuenta otro trabajo.
- **Consulta:** iniciada 2026-09-29 y completada 2026-09-30, America/Mexico_City.
- **Clasificación:** `presentation`; investigación bibliográfica sin datos internos.
- **Evidencia:** texto completo de una copia autoral pública de 56 páginas en Technion, incluidos métodos, discusión y tablas. No es la maquetación editorial. La portada de la copia indica una página final distinta; se conserva la paginación editorial de Crossref y se citan páginas del PDF realmente leído.
- **Acceso:** [manuscrito en Technion](https://innovation.technion.ac.il/wp-content/uploads/2021/11/mitchell_embeddedness.pdf). Se leyó en memoria; no se guardó el PDF ni una transcripción íntegra. No se presupone licencia de redistribución.
- **Estado:** `Revisado`, con texto completo autoral.

## Resumen verificable del estudio

El constructo combina vínculos, compatibilidad y sacrificios percibidos, tanto
en la organización como en la comunidad. Se estudia con encuesta inicial y
salida voluntaria durante los 12 meses siguientes, en una cadena de
supermercados y un hospital.

Se recibieron 232 encuestas en cada organización, de 700 y 500 invitaciones.
Para vincular salida se identificaron 177 y 208 participantes. El instrumento
se modificó entre muestras. Las seis dimensiones se promediaron con igual
peso; varios indicadores se estandarizaron antes. La relación con salida se
evaluó mediante regresiones logísticas. En el contraste que incorpora todos
los competidores, el incremento de ajuste es marginal en supermercados y más
claro en el hospital. Se usan pruebas direccionales. No hay evaluación temporal
fuera de muestra ni métricas de calibración. Localizadores: PDF, pp. 20–29,
46–55.

## Análisis crítico

### Un índice formativo no es una actitud única

El propio trabajo describe una construcción **formativa**: los componentes
forman el índice; no se supone que todos sean manifestaciones intercambiables
de una misma actitud latente (pp. 25–26). Esto cambia la interpretación de su
confiabilidad y de cualquier intento de reproducirlo.

Para Attrition, un alfa alto no bastaría para demostrar que antigüedad, carrera,
relaciones y condiciones laborales pueden sumarse. Tampoco basta eliminar
componentes por correlación baja: en una construcción formativa podrían
representar contenidos diferentes. Se necesitaría justificar el dominio,
componentes, unidades y pesos antes de hablar de una medida de embeddedness.

Hay una diferencia adicional entre promediar todas las preguntas y promediar
seis dimensiones con el mismo peso. Cuando las dimensiones tienen distinto
número de preguntas, las dos fórmulas producen resultados diferentes. Por eso
el paper aporta un marco de interpretación, pero no una fórmula que podamos
aplicar a columnas disponibles por semejanza de nombre.

### Dos muestras aportan contraste; no constituyen validación externa de un modelo congelado

La comparación entre sectores es valiosa porque el resultado no procede de una
sola organización. Sin embargo, cambian partes del cuestionario, y los modelos
se estiman en cada muestra. No es una prueba de entrenar una especificación
congelada en una organización y comprobar sus probabilidades en la otra.

En una réplica predictiva se congelarían transformaciones, escalamiento y
selección de variables con datos de entrenamiento. La estabilidad se mediría
en cortes posteriores y, cuando sea pertinente, en segmentos externos al
ajuste. Esas son pruebas diferentes del contraste inferencial publicado.

### La selección de respuestas y la clasificación de salidas afectan el estimando

Los participantes que no podían vincularse con los registros de salida no
aportaron el mismo tipo de análisis que los identificables. Además, los autores
intentaron verificar la voluntariedad con quienes habían salido y excluyeron
casos ambiguos e involuntarios (pp. 21–25).

Son dos fortalezas y límites distintos: la validación de la causa mejora el
target, pero la selección puede cambiar a quién representan los resultados.
La nota de tamaño muestral de la tabla 2 no proporciona un diagrama completo
de denominadores tras cada exclusión. Esta revisión no reconstruye una tasa
final exacta ni un número de eventos por regresión a partir de porcentajes
redondeados.

Para nuestro trabajo, la lección es registrar por separado elegibilidad,
respuesta, posibilidad de vinculación, exclusión y evento; también fijar el
tratamiento de causas competidoras. Excluir a posteriori a quienes tienen otra
causa de salida no es automáticamente equivalente a un modelo longitudinal
con censura o riesgos competitivos.

### El resultado incremental es menos uniforme que la conclusión del abstract

Las tablas 3 y 4 permiten separar asociación simple, comparación parcial y
comparación con todos los predictores. En esta última, las mejoras publicadas
de razón de verosimilitud son `2.37` y `5.67` para supermercados y hospital.
Los autores explican que dividen por dos el valor p de chi-cuadrado para una
lectura direccional (pp. 28–29 y 54–55).

Recalculé las colas de una distribución chi-cuadrado con un grado de libertad,
usando `erfc(sqrt(x/2))`. Se obtienen aproximadamente `0.124` y `0.017`;
al dividirlas por dos, `0.062` y `0.009`. Es una verificación de la sensibilidad
al contraste elegido, **no una reestimación con los datos originales**. El
cálculo y sus entradas se conservan en
`output/research/attrition-literature/20260929-pending-review/P15/statistical-check.json`.

Así, el apoyo incremental en supermercados es débil incluso bajo la convención
direccional de los autores. La señal en el hospital es más consistente, pero
una mejora de verosimilitud dentro de muestra no establece mejor calibración,
lift ni utilidad futura. Los tamaños de muestra y el bajo volumen de salidas
también aconsejan revisar incertidumbre y sobreajuste antes de adoptar una
especificación de muchos términos.

### La relación entre antecedentes no debe confundirse con ganancia independiente

Embeddedness incluye contenido que puede solaparse con antigüedad, carrera,
compensación percibida, satisfacción y compromiso. Si el baseline ya representa
parte de ese contenido, la pregunta útil es qué información nueva añade cada
bloque. Un resultado del índice completo no establece el aporte aislado de una
columna ni de cada dimensión.

La comparación local propuesta mantendría bloques separados y documentaría el
solapamiento. Retirar contenido restringido y conservar sólo señales laborales
produciría una nueva operacionalización, que no debería llevar la etiqueta de
la escala original sin validación específica.

### Permanecer no identifica automáticamente una experiencia positiva

Un vínculo puede reflejar oportunidad y pertenencia, pero también costo de
cambio o restricciones. Desde el objetivo de People Analytics, optimizar la
permanencia sin definir bienestar, voluntariedad y propósito de una acción
sería una decisión incompleta.

Esta revisión propone priorizar hipótesis sobre claridad de carrera, ajuste
del rol y conexión laboral cuando exista una palanca aprobada. No propone
recopilar circunstancias familiares, vivienda, salud, beneficios individuales
ni relaciones privadas para reproducir el componente comunitario. La
compensación interna seguiría tratándose únicamente de acuerdo con las reglas
del proyecto. Las acciones candidatas exigirían evaluación propia: aquí no hay
asignación aleatoria ni efecto causal demostrado de una intervención.

## Decisión para Attrition

**Usar como fundamento conceptual y como guía de una prueba incremental por
bloques.** El aporte principal es ampliar la pregunta desde actitudes hacia
condiciones que favorecen permanencia, manteniendo separados sus componentes.

No adoptar un índice único ni importar pesos, odds ratios o escalas. La
evidencia no selecciona un algoritmo, no convierte el horizonte anual en seis
meses y no modifica scores de variables internas. Las prioridades de prueba
siguen sujetas a definición, fecha de conocimiento y validación temporal local.

## Trazabilidad y pendientes

- **Identidad:** [Crossref](https://api.crossref.org/works/10.2307%2F3069391) y [OpenAlex W1978245076](https://api.openalex.org/works/https://doi.org/10.2307/3069391).
- **Contenido:** manuscrito público de Technion; pp. 7–19, definición y comparación de constructos; pp. 20–27, muestras, target y medida; pp. 28–36, resultados y discusión; pp. 46–55, instrumentos y tablas.
- **Versión:** hash SHA-256 `16e45951f1dd50c506b46b204aeb6ed57e9a4881bc115de2874d7831e433bfb1`; metadatos de acceso en `output/research/attrition-literature/20260929-pending-review/P15/sources/`.
- **Pendientes residuales:** cotejar con la versión editorial final si se dispone de acceso; reconciliar denominadores después de exclusiones y obtener incertidumbre/reanálisis antes de usar magnitudes publicadas. Ninguno de estos puntos se completa por inferencia.
