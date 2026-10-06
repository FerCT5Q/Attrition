# Business-unit-level relationship between employee satisfaction, employee engagement, and business outcomes: A meta-analysis

## Ficha

- Autores: James K. Harter, Frank L. Schmidt y Theodore L. Hayes
- Año: 2002
- Revista: *Journal of Applied Psychology*, 87(2), 268–279
- DOI: `10.1037/0021-9010.87.2.268`
- URL oficial: https://doi.org/10.1037/0021-9010.87.2.268
- Fuente consultada: OpenAlex work `W2005673510`, PubMed y metadatos editoriales
- Fecha de consulta: 2026-09-24
- Estado de acceso: abstract y metadatos visibles; texto completo cerrado
- Etiquetas: `engagement`, `satisfacción`, `unidad-de-negocio`, `meta-análisis`, `outcomes-agregados`

## Abstract y resumen

### Abstract original

El abstract visible describe un meta-análisis de 7,939 unidades de negocio en
36 compañías. Examina, a nivel de unidad, la relación entre
satisfacción-engagement y satisfacción de clientes, productividad, ganancia,
turnover y accidentes.

### Resumen en español

La contribución central es el nivel de análisis: no modela a una persona que
sale, sino relaciones entre agregados de unidades de negocio y resultados de
negocio. Eso es relevante para QVoice porque evita inferir que una respuesta o
un promedio individual es una predicción individual de attrition. El abstract
reporta relaciones generalizables con valor práctico, pero no aporta la
definición de turnover, temporalidad ni tamaños de efecto necesarios para
trasladar un resultado a Critical Tech.

## Pregunta y datos

- Pregunta: cuál es la relación, a nivel de unidad de negocio, entre satisfacción-engagement de empleados y resultados de negocio.
- Población: 7,939 unidades de negocio pertenecientes a 36 compañías; no se describe una población de empleados individuales.
- Tamaño: 7,939 unidades y 36 compañías.
- Grain: unidad de negocio agregada.
- Target y horizonte: customer satisfaction, productividad, ganancia, turnover y accidentes; el abstract no confirma que turnover sea voluntario ni una ventana prospectiva.
- Censura o competing risks: no aplica al diseño agregado descrito.

## Método y validación

- Método: meta-análisis de relaciones a nivel de unidad de negocio.
- Variables: satisfacción-engagement agregado y los cinco outcomes de negocio indicados en el abstract.
- Split temporal: no se confirma un split temporal ni una evaluación out-of-time de un modelo predictivo.
- Métricas: relaciones meta-analíticas; no se usan tamaños de efecto ni métricas de attrition porque el acceso actual sólo permite el abstract.
- Resultados: el abstract reporta relaciones generalizables con valor práctico y plantea que cambios en prácticas de management que aumenten satisfacción pueden mejorar outcomes de unidad. No se interpreta como prueba causal ni como efecto individual sobre attrition.

## Limitaciones

- Leakage: no se pudieron verificar fechas de encuesta, fecha de outcome ni si las mediciones precedían al turnover de cada unidad.
- Sesgos: el grain agregado puede producir falacia ecológica si se aplica a personas; industrias, instrumentos y definición de unidad no están disponibles en el abstract.
- Generalización: no valida QVoice, attrition voluntario observado ni un modelo de Critical Tech.
- Fairness/privacidad: el uso correcto en Attrition es por cohortes agregadas y reportables; no autoriza segmentar o intervenir sobre empleados por su respuesta de encuesta.

## Aplicabilidad a Attrition

- Relación con Critical Tech: apoya analizar QVoice/engagement como una señal de cohorte, siempre separada del score individual y con población/fecha explícitas.
- Variables disponibles relacionadas: temas de QVoice, participación de survey, segmento, equipo y periodo pueden ser candidatos de agregación; su cobertura, tamaño de cohorte y fecha de wave deben comprobarse antes.
- Qué adoptar: distinguir explícitamente el grain de una señal: persona, equipo, segmento o unidad; no mezclar sus conclusiones en una misma feature sin diseño previo.
- Qué probar como challenger: añadir, si existe cobertura suficiente, un agregado rezagado y excluyente del propio empleado contra el baseline temporal, con cohortes de reporte adecuadas.
- Qué posponer: usar un promedio de engagement como score individual, afirmar que reduce attrition voluntario o trasladar los efectos meta-analíticos.

## Acción y decisión

- Señal asociada: estado agregado de satisfacción-engagement de una cohorte, no intención ni riesgo de una persona.
- Palanca potencial: diagnóstico de equipo/unidad, escucha agregada y seguimiento de acciones con owner.
- Acción candidata: definir para QVoice el grain, la fecha de corte y la regla de exclusión antes de comparar su información agregada con attrition posterior.
- Métrica de seguimiento: cobertura, tamaño de cohorte, estabilidad temporal, Brier/PR-AUC/lift del modelo y tasa agregada de salida voluntaria.
- Decisión: `referencia conceptual`; `probar como challenger` sólo como señal agregada, rezagada y validada temporalmente.

## Trazabilidad

- Evidencia consultada: OpenAlex, PubMed y abstract indexado; revista, volumen y paginación verificados por metadatos.
- Sección/página si el texto completo fue revisado: no aplica; sólo abstract y metadatos visibles.
- Limitaciones de acceso: no se conservó un PDF cerrado. No se usaron resultados cuantitativos ni afirmaciones causales no visibles en la evidencia consultada.
