# Company tenure

<!-- BEGIN evaluate-attrition-variable:company-tenure -->
## Conocimiento acumulado: Company tenure

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:35:15-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Tenure
- **Relevancia:** Company tenure es un control central del ciclo laboral para modelos de attrition.

### Definición y fuente evaluadas

- **Definición vigente:** Tiempo de servicio completado desde la fecha de contratación aprobada hasta cada snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** original_hire_date, max_hire_rehire_date
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten max_hire_rehire_date (shared_source_column).
- Comparten original_hire_date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_26_company-tenure_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_26_company-tenure_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_26_company-tenure_report_column_profile.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:company-tenure -->

## Revisión descriptiva para la lámina 27 — 2026-09-10

### Flujo histórico y alcance

La evaluación v4 de 2026-08-16 dejó `Company tenure` como una feature derivada
pendiente de una definición de negocio. Esta revisión no cambia ese score ni
elige una definición HRIS. Sólo publica, para análisis interno, dos
distribuciones de los campos almacenados en el snapshot mensual fijo del
2026-08-23: `original_hire_date` y `max_hire_rehire_date`.

- **Modo de entrega:** `internal_analysis`.
- **Población y grain:** empleados regulares activos; empleado-snapshot único.
- **Corte de conocimiento:** 2026-08-23.
- **Regla de privacidad:** cada banda visible debe tener `n >= 30`; no se
  retienen IDs, filas de empleados, fechas individuales ni resultados crudos.

### Validaciones ejecutadas

#### 1. Unicidad y reconciliación de población

- **Pregunta y motivo:** ¿la población que alimenta ambos campos es un único
  snapshot por empleado? Sin este control, una distribución podría duplicar o
  mezclar valores de una misma persona.
- **Método y evidencia:** consulta agregada
  `queries/audits/company_tenure_stored_date_integrity_20260823.sql`, ejecutada
  el 2026-09-10 sobre `hrda.post_hire_monthly_worker_dtls`.
- **Regla de aceptación:** cero IDs faltantes, duplicados o conflictos, y los
  renglones fuente deben reconciliar exactamente con empleados únicos.
- **Métricas observadas:** 50,043 renglones fuente, 50,043 empleados únicos;
  0 IDs faltantes, 0 empleados duplicados, 0 renglones excedentes y 0
  conflictos.
- **Conclusión e impacto:** la población es apta para describir los dos
  campos; esto no prueba cuál de ellos es la definición HRIS de tenure.
- **Acción:** conservar el filtro fijo y volver a ejecutar la auditoría ante
  cualquier refresh de corte.

#### 2. Integridad de las dos fechas almacenadas

- **Pregunta y motivo:** ¿existen nulos, fechas futuras u orden temporal
  imposible que invaliden las bandas por aniversario?
- **Método y evidencia:** misma auditoría agregada, con los contadores de nulos
  y fechas futuras por campo y la regla `original_hire_date <=
  max_hire_rehire_date` cuando ambos están presentes.
- **Regla de aceptación:** cero fechas futuras y cero órdenes imposibles; los
  nulos se separan de forma explícita como no calculables, sin imputación.
- **Métricas observadas:** 0 nulos en `original_hire_date`, 0 nulos en
  `max_hire_rehire_date`, 0 fechas futuras en ambos campos y 0 órdenes
  imposibles.
- **Conclusión e impacto:** ambas distribuciones son calculables para los
  50,043 empleados. La evidencia es definitoria para la integridad descriptiva
  del snapshot, no para la semántica de negocio de los campos.
- **Acción:** no aplicar una fecha sobre la otra; una decisión de uso para el
  modelo requiere gobernanza HRIS separada.

#### 3. Reconciliación de bandas compartidas y privacidad

- **Pregunta y motivo:** ¿las mismas seis bandas por aniversario reconcilian a
  cada denominador calculable y cumplen el mínimo de cohorte?
- **Método y evidencia:** profile fijo
  `queries/profiles/company_tenure_stored_date_distribution_20260823.sql`,
  ejecutado el 2026-09-10. Las bandas son `<1`, `1–<2`, `2–<3`, `3–<5`,
  `5–<10` y `10+ years`.
- **Regla de aceptación:** cada campo debe sumar 50,043 empleados calculables,
  cada porcentaje debe sumar 100% y cada banda publicada debe tener `n >= 30`.
- **Métricas observadas:**
  - `original_hire_date`: 6,784; 4,978; 3,024; 8,502; 14,595; 12,160
    empleados (100.0% en total).
  - `max_hire_rehire_date`: 7,644; 5,312; 3,201; 8,577; 14,314; 10,995
    empleados (100.0% en total).
- **Conclusión e impacto:** las dos gráficas son publicables sólo como
  descripciones agregadas de sus propios campos. No se requiere una
  confirmación HRIS para este resultado descriptivo y no se eleva ningún score
  cualitativo a 2.
- **Acción:** si se selecciona una sola feature de attrition, solicitar la
  definición gobernada, la regla de rehire y la validación time-safe antes de
  cambiar la evaluación v4.

La evidencia congelada, sus hashes SQL/resultados y los controles de privacidad
están en `output/distribution/json/company-tenure-distribution-evidence-20260910.json`.
