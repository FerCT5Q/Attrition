# Revisión conjunta de la historia y el plan del modelo de attrition

Fecha de revisión: 2026-08-18

## Propósito

Este documento reúne los hallazgos para revisar en conjunto la narrativa, el
alcance y las fases del proyecto. No sustituye decisiones de negocio aún
pendientes ni modifica por sí mismo el target configurado en ejecuciones
anteriores.

Fuentes revisadas:

- `references/presentations/source/Attrition model story.pptx`
- `references/presentations/source/Attrition model steps.pptx`
- `docs/context/model-overview.md`
- `output/assessments/attrition-43-monthly-fiscal-20260816/run-request.yaml`
- Comentarios de Brigitte y Bhavya incorporados en `Attrition model steps.pptx`

## Conclusión general

La presentación propone una secuencia correcta para el proyecto:

1. definir attrition y el horizonte;
2. definir el universo o población;
3. construir evidencia y modelos por cohortes o segmentos;
4. acordar qué output se compartirá y con quién;
5. desarrollar, validar y mantener el modelo;
6. ampliar el alcance por fases.

Los comentarios nuevos no invalidan las 43 variables ni el trabajo de
assessment realizado. Complementan el plan al hacer explícitos los supuestos,
restricciones, criterios de selección del modelo, mantenimiento y posible uso
futuro de datos externos.

Antes de presentar el plan como definitivo deben resolverse tres decisiones:

- el horizonte objetivo, porque actualmente aparecen 1, 6 y 12 meses en
  distintos artefactos;
- la población del MVP, porque se alterna entre todos los empleados regulares
  activos y Critical Tech Jobs;
- la diferencia entre generar predicciones employee-level dentro de un entorno
  controlado y compartir únicamente resultados agregados por grupo.

## Base del proyecto que permanece vigente

- Outcome principal: attrition voluntario.
- Población base: empleados regulares activos al cierre de cada snapshot.
- Grain analítico: empleado-snapshot mensual.
- Regla temporal: utilizar exclusivamente información conocida al cierre del
  snapshot; ninguna señal futura puede entrar a una feature.
- Validación principal: entrenar con periodos anteriores y probar en periodos
  posteriores.
- Reporting: resultados por cohortes suficientemente grandes; no compartir
  listas ordenadas ni scores individuales con managers.
- Compensación: usar medidas relativas, bandas o percentiles; no publicar
  compensación exacta.
- Gender y otros atributos protegidos: reservarlos para fairness autorizado,
  no para targeting operativo.
- QVoice: tratarlo como encuesta por wave, no como una medición mensual nueva.
- Resultados observacionales: describir asociaciones e hipótesis, no causas
  demostradas.

## Tema central por resolver: frecuencia y horizonte

Actualmente se mezclan conceptos diferentes:

| Concepto | Propuesta recomendada |
|---|---|
| Grain de entrenamiento | Una observación por empleado y snapshot mensual |
| Frecuencia de features internas | La disponible al cierre de cada snapshot mensual |
| Horizonte del target | Attrition voluntario dentro de los siguientes 6 meses, sujeto a aprobación |
| QVoice | Última wave publicada y disponible al snapshot |
| Datos externos | Cadencia propia, posiblemente trimestral |
| Scoring | Mensual o según la cadencia operativa aprobada |
| Reporting | Resumen trimestral y por año fiscal |
| Monitoreo | Periódico y por alertas; frecuencia final según uso y estabilidad |

La presentación narrativa dice 12 meses en la lámina de definición y 6 meses en
la propuesta final. El run utilizado para evaluar las 43 variables se configuró
con un target de un mes. La documentación general del modelo propone seis
meses.

La recomendación para discusión es mantener snapshots mensuales y adoptar un
horizonte inicial de seis meses. Esto conserva señales actualizadas, acumula
más eventos que un target de un mes y deja tiempo para una intervención. No
debe considerarse decisión cerrada hasta que negocio confirme la ventana y se
compare empíricamente su prevalencia, estabilidad y utilidad frente a ventanas
alternativas.

Problem statement propuesto:

> Estimate, at each monthly employee snapshot, the probability that an active
> regular employee will voluntarily leave within the next six months, using
> only information known at the snapshot. Results will be shared only as
> approved cohort-level insights.

## Cómo se incorporan los comentarios nuevos

### Supuestos, restricciones e hipótesis no son equivalentes

Conviene separar los comentarios en cuatro categorías:

| Categoría | Ejemplos |
|---|---|
| Restricciones | No publicar raw compensation; QVoice tiene waves limitadas; proteger datos employee-level; respetar tamaños mínimos de cohorte |
| Decisiones pendientes | Horizonte; población inicial; audiencia; cadencia de scoring; acciones permitidas |
| Hipótesis por probar | Dos o tres ítems de QVoice podrían ser suficientes; la compensación relativa podría capturar la señal necesaria; ciertas aplicaciones internas podrían anticipar movilidad |
| Hechos por validar | Disponibilidad histórica; significado del missing; fecha de publicación; cobertura; join temporal; frecuencia real de actualización |

No se debe declarar como supuesto que “2-3 QVoice items will be useful” o que
“relative compensation is good enough”. Son hipótesis que deben competir con
alternativas mediante validación temporal.

### QVoice

QVoice ya está incluido entre las variables candidatas y debe conservarse como
fuente de encuesta:

- sólo puede utilizarse después de que una wave esté disponible;
- no se debe presentar como una señal que cambia cada mes;
- deben distinguirse persona no invitada, no respuesta, respuesta faltante y
  ausencia de una wave aplicable;
- la selección de 2-3 ítems debe basarse en definición, cobertura, estabilidad,
  validez temporal y desempeño fuera de muestra;
- arrastrar el último valor conocido puede ser una opción, pero debe definirse
  su vigencia y medirse su antigüedad.

### Compensación relativa

La restricción de no utilizar o compartir compensación cruda está alineada con
el proyecto. Aun así, “relative compensation” requiere definir:

- grupo de comparación: job family, nivel, ubicación, moneda y periodo;
- población elegible;
- cálculo por percentil o banda;
- tamaño mínimo del grupo;
- vigencia temporal y tratamiento de grupos pequeños;
- diferencia entre una feature para el modelo y una cifra permitida en el
  reporte.

### Datos faltantes y certeza del missing

El comentario aporta una mejora importante al assessment. No basta con medir el
porcentaje nulo; debe identificarse, cuando sea posible, si el dato significa:

- no aplica;
- el evento no ocurrió;
- la persona no era elegible o no fue invitada;
- la fuente todavía no existía;
- el dato no fue recolectado;
- el dato es verdaderamente desconocido;
- el dato fue suprimido por privacidad.

La “certeza del missing” puede transformarse en una propiedad documentada de
cada variable y, cuando sea apropiado, en una señal separada. No debe imputarse
un mismo valor a causas distintas sin validación.

### Señales mensuales

La pregunta sobre variables que predigan cambios mensuales complementa el
portafolio. Ya existen candidatos de este tipo, por ejemplo:

- solicitudes internas recientes;
- transferencias, promociones y cambios de manager;
- cambios de ubicación, job family o cost center;
- eventos organizacionales y movimientos del equipo.

Cada feature debe cerrar su ventana en el snapshot, definir fronteras y
deduplicación y evitar incorporar eventos futuros.

### Datos externos y pull factors

El comentario confirma que los factores externos no deben bloquear el MVP.
Constituyen un workstream separado por la dificultad de mapear mercado,
ubicación, periodo, job family y skillset.

Para medir su valor de forma limpia:

- Phase 1 y Phase 2 deben conservar la misma población y target;
- el challenger externo añade únicamente las señales externas;
- la comparación debe realizarse en los mismos periodos futuros;
- su uso puede comenzar con Critical Tech Jobs si allí existe suficiente
  cobertura, volumen de eventos y utilidad de negocio;
- scraping o identity matching no se consideran rutas aprobadas por defecto.

## Segmentación y población

“Model by segments” no debería significar automáticamente un modelo distinto
para cada segmento. La ruta recomendada es:

1. construir un baseline común e interpretable;
2. analizar desempeño y calibración por cohortes;
3. agregar interacciones o features cuando exista una hipótesis;
4. crear un modelo separado sólo si el segmento tiene suficientes empleados y
   eventos, comportamiento distinto y mejora estable en periodos futuros.

Un segmento no se justifica sólo porque sea relevante para el negocio. Debe
tener volumen suficiente, una acción diferenciada y capacidad de mantenimiento.

### Población del MVP pendiente

La lámina de definición propone empleados regulares, mientras la tabla de fases
comienza con Critical Tech Jobs. Ambas opciones son válidas, pero responden a
decisiones distintas:

- todos los empleados regulares permiten un baseline corporativo más amplio;
- Critical Tech Jobs reduce heterogeneidad y alinea mejor una fase futura de
  external pull factors;
- si se elige Critical Tech, debe existir una definición versionada del grupo y
  mantenerse constante al comparar baseline y challenger.

## Output y uso del modelo

La presentación acierta al separar el trabajo interno employee-level del output
compartido. La formulación recomendada es:

```text
Entrenamiento: empleado-snapshot mensual
Predicción interna: probabilidad de attrition voluntario en la ventana aprobada
Output compartido: insights agregados de cohortes aprobadas
```

Cada insight debería contener:

```text
cohorte + evidencia + driver hipotético + acción permitida + owner + métrica + cadencia
```

El modelo puede identificar asociaciones que ayudan a priorizar cohortes. No
demuestra que una acción específica retendrá a una persona. La efectividad de
acciones debe evaluarse mediante pilotos o diseños causales posteriores.

“Manager is the biggest push factor” debería expresarse como “manager-related
signals showed the strongest association or contribution for this cohort”,
salvo que exista evidencia causal independiente.

## Selección y defensa del modelo

El esquema base, challenger y champion es consistente con el proyecto:

- Baseline: modelo sencillo, interpretable y reproducible.
- Challenger: alternativa de features, parámetros o algoritmo evaluada con el
  mismo target, población y periodos.
- Champion: candidato que mejora el baseline y cumple requisitos de negocio,
  privacidad, estabilidad y operación.

No debe elegirse sólo por accuracy, precision, recall o KS. Para un evento poco
frecuente deben considerarse conjuntamente:

- lift y precision/recall en los percentiles o deciles priorizados;
- PR-AUC y discriminación;
- calibración global y por cohortes;
- estabilidad en meses y años fiscales futuros;
- fairness y tamaños suficientes de grupo;
- interpretabilidad y action-readiness;
- costo y capacidad de mantenimiento.

## Correcciones metodológicas recomendadas

### Snapshots superpuestos

Crear snapshots mensuales aumenta las observaciones longitudinales, pero no es
bootstrapping: varias filas corresponden a la misma persona y las ventanas de
outcome pueden superponerse. Por ello:

- no deben mezclarse snapshots de la misma ventana entre train y test;
- la validación principal debe ser temporal;
- se debe considerar el efecto de ventanas de outcome superpuestas;
- los intervalos de confianza o pruebas deben reconocer dependencia entre
  observaciones cuando corresponda.

### Data cleaning y train/test

El train/test split no es una actividad de limpieza. Debe definirse antes de
seleccionar variables, crear bins, imputar o ajustar transformaciones. Todo
parámetro aprendido debe ajustarse con train y aplicarse sin recalibración a
validation/test.

### Feature engineering

Probar percentiles, thresholds o bins es válido, pero la selección no debe
hacerse viendo todo el histórico. Las alternativas deben generarse con train y
compararse en periodos futuros para evitar overfitting.

## Fases recomendadas

| Fase | Población | Datos | Objetivo |
|---|---|---|---|
| 1. Internal baseline | Población MVP fija | Datos internos y QVoice seleccionado | Crear benchmark interpretable y gobernado |
| 2. External challenger | La misma población de Phase 1 | Baseline más señales externas aprobadas | Medir el valor incremental de pull factors |
| 3. Scale | Poblaciones adicionales aprobadas | Señales internas y externas que hayan demostrado valor | Ampliar cobertura sin perder estabilidad ni gobernanza |

No conviene cambiar simultáneamente población, datos y algoritmo entre fases,
porque ya no podría atribuirse la mejora a un componente específico.

## Cambios recomendados a `Attrition model story.pptx`

### Slide 2 — Decision storyline

Agregar explícitamente una decisión de medición: unidad de análisis, horizonte y
cadencia. Actualmente la secuencia Define / Focus / Act no hace visible la
decisión temporal.

### Slide 3 — Attrition definition and study population

- eliminar el placeholder repetido;
- reemplazar 12 meses por la ventana finalmente aprobada;
- declarar `employee-month snapshot` como unidad de análisis;
- mantener empleados regulares activos como población base o explicar por qué
  Critical Tech sería el MVP;
- mover detalle secundario a notas para reducir densidad.

### Slide 4 — Analytical cuts and governed outputs

- conservar cohortes y outputs agregados;
- añadir asociación versus causalidad;
- añadir mínimo de cohorte y aclarar que People Analytics puede trabajar con
  employee-level en un entorno controlado, pero no compartir scores;
- revisar el elemento detectado fuera del canvas.

### Slide 5 — Workplan

- corregir numeración y wording;
- incluir validación temporal, calibración, fairness, privacidad y readiness de
  las acciones;
- separar construcción del modelo de piloto de intervención.

### Slide 6 — Proposal / phases

- simplificar o dividir la tabla, porque actualmente concentra demasiadas filas
  y usa texto pequeño;
- agregar footer legal y número de slide;
- mantener fija la población entre internal baseline y external challenger;
- separar la expansión de población en una fase posterior;
- completar la cadencia de refresh o marcarla como decisión pendiente.

## Uso recomendado de `Attrition model steps.pptx`

El deck de steps contiene brainstorming valioso, pero es demasiado denso para
la narrativa ejecutiva. Debe usarse como fuente de trabajo o apéndice. Sus
comentarios deben sintetizarse en las láminas principales o trasladarse a
speaker notes, conservando trazabilidad.

## Decisiones para revisar en conjunto

1. ¿El horizonte inicial será 1, 3, 6 o 12 meses?
2. ¿El MVP cubre a todos los empleados regulares activos o comienza con
   Critical Tech Jobs?
3. ¿Con qué frecuencia se recalculará el score y con qué frecuencia se
   compartirán resultados?
4. ¿Cuál es el tamaño mínimo de cohorte para análisis y para reporting
   ejecutivo?
5. ¿Qué acciones están permitidas para cada familia de señal?
6. ¿Qué 2-3 constructos de QVoice se probarán primero y cuál será la vigencia de
   cada wave?
7. ¿Cuál será el peer group para compensación relativa?
8. ¿Qué causas de missingness pueden distinguirse de manera confiable?
9. ¿Critical Tech tiene una definición estable, suficientes eventos y un owner?
10. ¿Qué métricas y umbrales debe superar un challenger para reemplazar al
    baseline?

## Criterio recomendado para cerrar decisiones

Una decisión debería incorporarse al MVP cuando:

- responde a una necesidad de negocio concreta;
- puede reproducirse con información conocida al snapshot;
- tiene cobertura y volumen de eventos suficientes;
- puede validarse en periodos futuros;
- produce un output permitido y accionable;
- tiene owner, cadencia y regla de mantenimiento;
- no crea un riesgo desproporcionado de privacidad, fairness o interpretación
  causal incorrecta.

