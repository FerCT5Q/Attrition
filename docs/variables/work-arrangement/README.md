# Work arrangement

## Campos

- `work_arrangement`: categoría registrada en el snapshot.
- `work_arrangement_start_date`: inicio de vigencia disponible.
- `work_arrangement_end_date`: fin de vigencia disponible.

La intención es representar el estado onsite, hybrid o remote efectivo en cada mes, no solamente copiar la categoría más reciente.

## Hallazgos agregados

- La auditoría más reciente encontró 17 categorías crudas y 17 normalizadas.
- No se observaron anomalías de espacios ni colisiones al normalizar mayúsculas/espacios.
- La cobertura reciente fue aproximadamente 99.4%.
- La historia utilizable comienza el 2024-08-25. La revisión de 2026-08-18
  confirmó 25 snapshots mensuales utilizables, todos con cobertura del campo
  bruto superior a 95%.

## Por qué todavía requiere validación

Que los textos estén limpios no demuestra que las transiciones sean correctas. Por ejemplo, si un snapshot dice `Hybrid` pero la fecha de inicio comienza el mes siguiente, se necesita una regla que indique qué fuente tiene prioridad. También deben resolverse categorías equivalentes, cambios temporales y fechas de fin abiertas.

## Prueba recomendada de consistencia

Para cada mes, de forma agregada:

1. contar categorías crudas y normalizadas;
2. contar cambios de categoría entre snapshots consecutivos;
3. comprobar si cada cambio coincide con start/end dates;
4. medir transiciones imposibles o reversas en periodos muy cortos;
5. revisar estabilidad por país, site y source era sin exponer empleados.

La feature final debe aplicar una precedencia aprobada entre categoría y fechas y debe contar con pruebas de regresión para los edge cases.

## Revisión de semántica y grain — 2026-08-17

Se revalidó la variable para el caso de uso de attrition mensual sobre empleados
regulares activos. La auditoría no expuso filas de empleados ni etiquetas de
excepción sensibles.

### Definition

`work_arrangement` no es actualmente una clasificación directa y limpia de
**Remote / Hybrid / In office**. Se observaron 29 etiquetas históricas (tras
normalizar mayúsculas y espacios), de las cuales existe una categoría onsite
explícita y categorías que mencionan remote, pero no existe una categoría
hybrid explícita. Las restantes incluyen offsite y arreglos temporales o de
excepción; algunas codifican razones potencialmente sensibles. Por ello no se
deben usar los valores crudos como feature predictiva ni inferir que offsite o
interim equivale a hybrid.

Las fechas son parcialmente coherentes: ningún inicio poblado es posterior al
snapshot ni al fin, pero 1,684 registros con categoría tienen un fin anterior
al snapshot. En transiciones entre meses adyacentes hubo 11,571 cambios de
categoría; sólo 6,366 contaron con una frontera de inicio o fin que los
respaldara dentro del intervalo y 5,205 no la tuvieron. Esto impide considerar
las fechas como una definición efectiva completamente reconciliada.

Conclusión: **Definition permanece en 1**. Se requiere un mapping de negocio,
versionado y aprobado que produzca una categoría no sensible por snapshot y
defina el tratamiento de offsite, arreglos temporales, expiraciones y los casos
sin categoría. El campo bruto debe tratarse como restringido mientras contenga
razones sensibles.

### Join

El campo se encuentra en la misma fila que el snapshot de empleado, por lo que
no necesita un join externo. La comprobación de 3,023,320 llaves
`employee_id + fis_mo_end_dt` encontró cero llaves duplicadas y cero llaves con
más de una categoría normalizada. Las 1,915,962 llaves sin categoría son una
brecha histórica de coverage (el primer valor poblado es 2024-08-25), no una
ambigüedad de join.

Conclusión técnica: se adopta **Join = 2** para la proyección del campo directo
al grain empleado-snapshot. El workbook publicado conserva Join=1 únicamente
como registro histórico de la ejecución original; una reevaluación v4 futura
deberá incorporar estas consultas en su ledger congelado.

SQL trazable de esta revisión:

- `queries/audits/remote_hybrid_definition_join_audit_20260817.sql`
- `queries/audits/remote_hybrid_domain_history_audit_20260817.sql`
- `queries/audits/remote_hybrid_domain_semantics_audit_20260817.sql`
- `queries/audits/remote_hybrid_transition_effective_date_audit_20260817.sql`
- `queries/audits/remote_hybrid_related_field_metadata_20260817.sql`

### Corrección de historia mensual — 2026-08-18

El `History=1` del assessment histórico se originó porque el cálculo comparó
fechas de calendario: del 2024-08-25 al 2026-08-23 faltan dos días para dos
años calendario completos. Esa no es una base adecuada para un caso de uso con
snapshots mensuales.

La auditoría `queries/audits/remote_hybrid_raw_history_observation_audit_20260818.sql`
se ejecutó el 2026-08-18 con la población de empleados regulares activos y
contó 25 observaciones mensuales pobladas; las 25 tuvieron cobertura de
`work_arrangement` >=95% (mínimo 96.4373%, máximo 99.7991%). Con la regla del
skill de 24 o más observaciones mensuales utilizables, la calificación correcta
para la **historia del campo bruto** es **History=2**.

Esto no resuelve la definición de la feature solicitada de tres estados. El
mapping conservador a Remote / Hybrid / In office sigue sin clasificar de forma
explícita al menos 95% de todos los empleados en los snapshots recientes; esa
brecha afecta Definition, Coverage y Missingness de la feature derivada, no la
profundidad histórica del campo fuente. El bloque administrado que sigue se
conserva como registro histórico de la ejecución 2026-08-16.

<!-- BEGIN evaluate-attrition-variable:remote-hybrid-in-office-status -->
## Conocimiento acumulado: Remote / hybrid / in office status

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:31:28-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Work arrangement
- **Relevancia:** La modalidad puede relacionarse de forma distinta con retención según rol y ubicación.

### Definición y fuente evaluadas

- **Definición vigente:** Categoría de modalidad laboral efectiva para el empleado en cada snapshot mensual.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** work_arrangement, work_arrangement_start_date, work_arrangement_end_date
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (11 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=1, Join=1, Effort=1
- **Coverage reciente:** 99.4068%.
- **Historia utilizable:** 23.0 meses.

**Hallazgos principales**

- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La historia utilizable es menor al umbral de 24 meses para score 2.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.

**Acciones recomendadas**

- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Continuar la colección o backfill hasta completar al menos 24 meses.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_10_remote-hybrid-in-office-status_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_10_remote-hybrid-in-office-status_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_10_remote-hybrid-in-office-status_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_10_remote-hybrid-in-office-status_work-arrangement_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:remote-hybrid-in-office-status -->
