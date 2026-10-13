# Documentación de Attrition

La documentación está separada entre contexto general, explicaciones por concepto y evidencia de cada ejecución de modelado.

## Contexto

- [Modelo elegido y estado de las comparaciones](context/model-selection-current.md): CQ confirmado el 10-oct-2026 y experimentos posteriores; consultar antes de identificar una versión como vigente.
- [Ronda B + playbook V11 y documentación por variable](context/b-playbook-v11-documentacion-variables.md): experimento terminado el 12-oct-2026, con enlaces a fichas, resultados y verificaciones; no sustituye a CQ.
- [Visión del modelo](context/model-overview.md): objetivo, target, gobierno, modelado y formato de salida.
- [Variables candidatas](context/candidate-variables.md): inventario histórico de las 43 ideas del brainstorming; no sustituye el alcance del playbook V11.
- [Metodología de evaluación](context/assessment-methodology.md): criterios, umbrales, blockers y fuentes oficiales.

## Resumen y detalle de la ronda V11

- [Resumen para Julia](../planes/modelo_c/43_variables_playbook_modelo_final_20261012.md): tabla de 43 filas con uso final, codificación y motivo de inclusión o exclusión.
- [Diccionario y fichas completas](../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.md): fuente, valores, transformaciones, faltantes, pruebas y decisiones por representación y corte.
- [Diccionario en Excel](../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.xlsx): consulta filtrable de la documentación de esa ejecución.

Las fichas de implementación están en `output/analysis/.../documentacion/fichas/`,
junto con los resultados del experimento. `docs/variables/` conserva la preparación
y explicación conceptual. El resumen para Julia no reemplaza ninguno de esos detalles.

## Planes y revisiones

- [Revisión conjunta implementada: CQ, FQ y BU L3](context/julia-rh-review-20261012.md): comparación común, 44 variables, capacidades, calibración, fichas RH y presentación corregida de **9 slides**; CQ sigue elegido.
- [C + BU L3 con/sin QVoice](context/c-bu-isolation-20261013.md): prueba específica con control C reajustado al mismo corte; BU sin encuesta no supera a CQ, y ciudad mejora la combinación con encuesta.
- [Plan de revisión conjunta: salida para RH](plans/revision-julia-brian-salida-rh-20261012.md): acciones, QVoice ausente, ficha de grupos, capacidad, calibración, estabilidad y límites de las validaciones actuales.
- [Plan y cierre de BU L3](plans/attrition-model-bu-l3-20261012.md): auditoría del mapping histórico, efecto predictivo en B/CQ/FQ y prueba de grupos.

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
