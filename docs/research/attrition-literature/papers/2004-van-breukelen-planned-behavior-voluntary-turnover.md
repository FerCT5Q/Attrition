# P14 — Voluntary employee turnover: combining variables from the ‘traditional’ turnover literature with the theory of planned behavior

## Ficha y alcance de la revisión

- **Autores:** Wim van Breukelen, René van der Vlist y Herman Steensma.
- **Publicación:** 2004; *Journal of Organizational Behavior*, 25(7), 893–914.
- **DOI:** [10.1002/job.281](https://doi.org/10.1002/job.281).
- **Consulta:** 2026-09-29, America/Mexico_City; registros técnicos en UTC.
- **Clasificación del entregable:** `presentation`; revisión bibliográfica sin datos internos de empleados.
- **Nivel de evidencia:** abstract editorial depositado en Crossref, corroborado por OpenAlex; metadatos de Semantic Scholar. **No se leyó el texto completo.**
- **Acceso:** Wiley devolvió HTTP 403 y una barrera automatizada en el navegador. OpenAlex y Semantic Scholar no localizaron una copia abierta. La búsqueda por título y autor no produjo una versión institucional verificable.
- **Estado:** `Revisado`, limitado a abstract y metadatos. La lectura integral queda abierta.
- **Corrección bibliográfica:** el inventario atribuía el trabajo a Hom et al.; Crossref y OpenAlex identifican a los tres autores indicados arriba.

## Qué se investigó y qué pudo comprobarse

El trabajo pregunta si la teoría del comportamiento planificado explica la
intención y la salida voluntaria, y si satisfacción, compromiso, edad y
antigüedad añaden información. El abstract describe 296 profesionales de la
Marina Real neerlandesa en la primera encuesta, repetida seis meses después;
202 completaron las preguntas relevantes en ambas ocasiones. Se registró la
permanencia o salida durante dos años desde la primera encuesta.

La intención fue el mejor predictor reportado de la salida. Satisfacción y
antigüedad aportaron explicación adicional de la intención tras considerar los
predictores del marco teórico. El abstract no informa número de salidas,
coeficientes, intervalos, escalas, estimador ni rendimiento predictivo fuera de
muestra. No permite afirmar que las variables tradicionales carezcan de valor
incremental para nuestro modelo ni que se haya demostrado mediación causal.

## Lectura crítica del diseño

### 1. Intención y evento observado son objetos diferentes

**Pregunta:** ¿aporta algo más que una encuesta de intención? **Sí:** existe
seguimiento de salida observada. Esta secuencia es más pertinente para
Attrition que predecir intención con otras respuestas de la misma encuesta.

**Límite:** dos años de seguimiento no equivalen a nuestro horizonte de seis
meses. El resumen tampoco confirma la fecha exacta de cada salida ni cómo se
tratan causas distintas de la renuncia. No sabemos si su análisis conserva el
tiempo al evento o reduce todo el seguimiento a un resultado binario.

**Consecuencia para el proyecto:** mantener `intent_to_stay` como posible señal
fechada y salida voluntaria observada como target. Esto es una hipótesis
bibliográfica; no confirma el contenido, la cobertura ni la validez de ningún
ítem interno.

### 2. La segunda encuesta exige revisar el origen del tiempo

El seguimiento comienza con la primera encuesta, mientras que la segunda se
aplica seis meses después. Antes de interpretar un análisis que use ambas
mediciones, se necesita saber qué ocurre con las salidas de los primeros seis
meses y quién puede contestar la segunda encuesta.

Hay dos diseños diferentes que conviene distinguir: predicción desde la primera
encuesta y predicción desde un nuevo corte tras la segunda. **No se afirma que
el artículo tenga leakage**; el abstract no permite resolver esta pregunta.
En una prueba local se debe fijar la fecha de conocimiento y empezar el
horizonte después del corte correspondiente. Una respuesta posterior nunca
debe explicar retrospectivamente un corte anterior.

### 3. La muestra repetida puede ser selectiva

Sólo 202 de los 296 participantes iniciales entran en la descripción de casos
con ambas encuestas completas. El resumen no explica los motivos de exclusión,
si participaron todas las personas elegibles ni cómo se trataron valores
faltantes. No corresponde llamar a los casos restantes «renunciantes» o
«desertores de la encuesta».

La pregunta pendiente es si la selección depende de intención, antigüedad o
salida temprana. Para nuestro diseño esto aconseja conservar estados de
observación y fechas de respuesta y comprobar estabilidad entre quienes tienen
y no tienen una encuesta utilizable, dentro de la política de cohortes. No
autoriza imputar una actitud a quienes no responden.

### 4. Explicación dentro de una muestra y predicción futura

Que una variable explique variación adicional en una regresión no establece
calibración, discriminación ni utilidad operativa en meses futuros. El acceso
disponible no acredita partición temporal, ajuste de hiperparámetros ni
validación externa. Tampoco permite recomendar un estimador concreto.

La lección transferible es comparar información incremental. La propuesta local
sería contrastar un bloque de actitudes/intención con el mismo baseline, la
misma población y el mismo holdout temporal; luego revisar calibración, Brier,
PR-AUC, lift y estabilidad. La inclusión de un bloque dependería de esa prueba,
no de la frase «mejor predictor» del abstract.

### 5. Predicción y acción requieren interpretaciones distintas

Una intención declarada puede estar cerca de una decisión de salida sin
identificar su causa ni la intervención adecuada. Si satisfacción o carrera
actúan antes de esa intención, condicionar todo el análisis a la intención
también puede cambiar la interpretación de las otras asociaciones.

Esto plantea una decisión de diseño, no una conclusión causal del artículo:
la comparación predictiva puede incluir intención; la evaluación de una acción
de carrera necesita además una pregunta causal y supuestos propios. No deben
convertirse importancias o asociaciones condicionadas en palancas demostradas.

## Transferencia a Critical Tech

| Elemento | Decisión de esta revisión | Condición o límite |
|---|---|---|
| Encuesta anterior a salida observada | Adoptar como principio temporal | Fechar wave, snapshot e inicio del horizonte. |
| Intención de permanecer | Probar como bloque candidato | Verificar primero significado y disponibilidad internos; no sustituye al target. |
| Satisfacción, compromiso y antigüedad | Mantener separados al formular hipótesis | El artículo no aporta pesos transferibles ni equivalencia de instrumentos. |
| Teoría del comportamiento planificado | Referencia conceptual | No hay evidencia suficiente para reproducir escalas ni construir un índice. |
| Generalización | Exige comprobación local | Una institución militar en 2004 difiere de talento técnico empresarial actual. |
| Uso operativo | Análisis agregado y revisión humana | La intención no habilita listas, explicaciones o decisiones por empleado. |

La clasificación de variables internas, sus scores y el modelo vigente no
cambian con esta ficha. No se evaluaron datos de HRDA.

## Qué falta para una revisión integral

Recuperar una copia autorizada y revisar: instrumentos y confiabilidad;
denominador elegible y exclusiones; número y causa de eventos; modelos para las
dos encuestas; tratamiento de salidas antes de la segunda wave; censura y
faltantes; coeficientes e incertidumbre; análisis de sensibilidad y existencia
de validación fuera de muestra. La evidencia actual cierra la identificación
y la revisión del abstract, no esas preguntas.

## Trazabilidad

- [Crossref: metadatos y abstract depositado por Wiley](https://api.crossref.org/works/10.1002%2Fjob.281), campo `message.abstract` y datos bibliográficos.
- [OpenAlex W2022395324](https://api.openalex.org/works/https://doi.org/10.1002/job.281), abstract indexado y localizaciones.
- [Semantic Scholar: búsqueda por DOI](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1002/job.281?fields=title,authors,year,abstract,openAccessPdf,url), sin copia abierta ni abstract redistribuido.
- [Página editorial consultada](https://onlinelibrary.wiley.com/doi/10.1002/job.281), acceso bloqueado; no se atribuyen páginas interiores como leídas.
- Registros de acceso con URL, fecha, estado HTTP y hash: `output/research/attrition-literature/20260929-pending-review/P14/sources/`.
- Los resúmenes automáticos y fragmentos del buscador sirvieron únicamente para descubrir posibles enlaces; no fundamentan hallazgos.
