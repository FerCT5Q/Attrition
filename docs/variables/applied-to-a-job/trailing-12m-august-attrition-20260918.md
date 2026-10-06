# Attrition observado trailing-12m a corte de agosto

**Modo de entrega:** `internal_analysis` para el requester y Julia, desarrolladores del proyecto. Sólo incluye agregados; no contiene filas, IDs, nombres ni requisiciones. La excepción interna para buckets inferiores a 30 está registrada en `config/application_intensity_internal_analysis_authorization_20260913.json`.

## Flujo histórico y decisión de visualización

La fuente de aplicaciones se puede reconstruir para cinco cortes de agosto disponibles: 2022 a 2026. Cada corte toma las aplicaciones de los doce meses que terminan en la fecha de snapshot de agosto, por lo que no depende de esperar doce meses adicionales después de un cierre fiscal.

El slide 3 muestra únicamente Ago-2025 y Ago-2026. Ago-2022 a Ago-2024 se mantienen en el artefacto de evidencia para trazabilidad, no como histórico visual. La decisión evita mezclar los cortes rolling con la antigua comparación de años fiscales y conserva el foco en las dos ventanas más recientes.

## Definición validada

- **Concepto y uso:** distribución de intensidad de aplicaciones internas y attrition voluntario descriptivo de cada bucket para revisión interna; no es una feature aprobada para modelo ni una afirmación causal.
- **Tipo semántico:** `derived_feature`.
- **Población y grain:** aplicantes vinculados distintos por corte de agosto y bucket `1`, `2`, `3` o `4+` requisiciones únicas; un renglón agregado por corte y bucket.
- **Ventana de conocimiento:** `(corte de agosto - 12 meses, corte de agosto]`.
- **Resultado:** terminación `VOLUNTARY` estricta posterior a la primera aplicación calificable y en o antes del corte. La tasa es `100 × salidas voluntarias / aplicantes distintos`.
- **Límite temporal:** es attrition observado en los últimos doce meses al corte de agosto. No es attrition prospectivo de doce meses después de un endpoint fiscal y no imputa resultados futuros.

## Validaciones y evidencia

### 1. Disponibilidad de componentes

- **Pregunta:** ¿las fuentes tienen exactamente los campos necesarios para derivar la ventana y el resultado?
- **Motivo:** sin fecha de aplicación, requisición, vínculo de empleado y terminación no es posible reproducir la tasa.
- **Método:** metadata agregada sobre `information_schema.columns`.
- **Regla de aceptación:** cada columna requerida existe exactamente una vez en su tabla.
- **Resultado al 2026-09-18:** `job_applications_vw` devolvió `employee_id`, `req_id`, `application_date` y `cand_applied` una vez cada una; `post_hire_monthly_worker_dtls` devolvió `employee_id`, `term_date` y `term_type` una vez cada una. **Resultado: pasa.**
- **SQL:** `queries/audits/application_trailing_12m_august_attrition_metadata_20260918.sql`.

### 2. Reconstrucción rolling y reconciliación de tasas

- **Pregunta:** ¿la derivación devuelve los cinco cortes por los cuatro buckets, y cada tasa coincide con sus agregados?
- **Motivo:** la fecha de borde, la deduplicación por requisición y el numerador post-aplicación pueden alterar tanto la distribución como attrition.
- **Método:** se reconstruyeron requisiciones únicas por empleado en cada ventana; se deduplicaron las salidas voluntarias por empleado y se validó cada denominador, numerador y porcentaje.
- **Regla de aceptación:** 20 renglones (`5 × 4`); la suma de buckets debe igualar el total de aplicantes de cada corte; `0 ≤ salidas ≤ denominador`; y la tasa redondeada debe igualar `100 × salidas / denominador`.
- **Resultado al 2026-09-18:** 20 de 20 renglones presentes y reconciliados. Los totales de aplicantes distintos fueron 1,029 (2022), 915 (2023), 3,079 (2024), 1,966 (2025) y 2,167 (2026). **Resultado: pasa.**
- **SQL:** `queries/audits/application_trailing_12m_august_attrition_20260918.sql`.
- **Artefacto congelado:** `output/distribution/json/attrition-43-variable-distributions-v7.application-trailing-12m-august-attrition-evidence-20260918.json`.

## Métricas que se publican en el slide

| Corte | Bucket | Distribución | n aplicantes | Attrition voluntario trailing-12m |
| --- | --- | ---: | ---: | ---: |
| Ago-2025 | 1 | 92.07% | 1,810 | 0.94% (17 salidas) |
| Ago-2025 | 2 | 7.48% | 147 | 2.04% (3 salidas) |
| Ago-2025 | 3 | 0.41% | 8 | 0.00% (0 salidas) |
| Ago-2025 | 4+ | 0.05% | 1 | 0.00% (0 salidas) |
| Ago-2026 | 1 | 83.25% | 1,804 | 1.05% (19 salidas) |
| Ago-2026 | 2 | 15.87% | 344 | 0.29% (1 salida) |
| Ago-2026 | 3 | 0.65% | 14 | 14.29% (2 salidas) |
| Ago-2026 | 4+ | 0.23% | 5 | 0.00% (0 salidas) |

La proporción de aplicantes con 2+ requisiciones pasa de 7.93% (156 de 1,966) en Ago-2025 a 16.75% (363 de 2,167) en Ago-2026, una diferencia descriptiva de +8.82 pp.

## Limitaciones y acción

Los buckets 3 y 4+ de los dos cortes visibles están por debajo de 30 en parte o en su totalidad. Los porcentajes se muestran con su `n` y están permitidos sólo bajo la autorización interna registrada; no se deben redistribuir ni usar para decisiones operativas, clasificación individual o cambio de score. Las diferencias entre buckets describen cohortes observadas y no demuestran que aplicar a más requisiciones cause attrition. Para uso compartible se debe suprimir o agrupar los buckets bajo umbral y acordar una definición de población de empleados activa para la finalidad concreta.
