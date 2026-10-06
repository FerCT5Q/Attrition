# Documentación de Attrition

La documentación está separada entre contexto general y explicaciones técnicas por concepto.

## Contexto

- [Visión del modelo](context/model-overview.md): objetivo, target, gobierno, modelado y formato de salida.
- [Variables candidatas](context/candidate-variables.md): inventario de las 43 ideas del brainstorming.
- [Metodología de evaluación](context/assessment-methodology.md): criterios, umbrales, blockers y fuentes oficiales.

## Planes y revisiones

- [Revisión de la historia y el plan del modelo](plans/attrition-model-story-review-20260818.md): contraste de las presentaciones, comentarios del equipo, decisiones pendientes y criterios recomendados para el MVP.
- [Propuesta detallada del modelo](plans/attrition-model-recommendation-20260907.md): arquitectura estadística, target, selección de variables, validación temporal, gobierno y fases de implementación.
- [Implementación Critical Tech](plans/critical-tech-people-analytics-implementation-20260907.md): población, evidencia de mapping, descubrimiento de cohortes, drivers y acciones.
- [Screen agregado de cohortes Critical Tech](../output/analysis/critical-tech/20260907/cohort-screen-report.md): primer resultado ejecutado con baseline, lift, estabilidad y acciones candidatas.
- [Preflight del hazard Critical Tech](../output/analysis/critical-tech/20260907/hazard-preflight-report.md): volumen, intervalos completos y segmentos publicables.
- [Especificación ejecutable Critical Tech](../config/critical_tech_model_spec_v1_20260907.yaml): contrato del hazard, target, features, validación y gobierno.

## Investigación bibliográfica

- [Índice de literatura de attrition y People Analytics](research/attrition-literature/README.md)

## Variables revisadas

- [Índice de conceptos](variables/README.md)
- [Job family](variables/job-family/README.md)
- [Job level](variables/job-level/README.md)
- [Organizational layers](variables/organizational-layers/README.md)
- [Compensation](variables/compensation/README.md)
- [Rehire](variables/rehire/README.md)
- [Work arrangement](variables/work-arrangement/README.md)
- [Gender](variables/gender/README.md)
- [Backlog de revisión](variables/review-backlog.md)

## Regla de mantenimiento

Los documentos conceptuales explican qué significa una variable y cómo debería usarse. El inventario y workbook actuales son v2 y se conservan como referencia histórica. Un puntaje vigente requiere un spec v4 y evidencia calculada en `output/assessments/<run-id>/`; no se mantiene una segunda matriz de scoring en Markdown.
