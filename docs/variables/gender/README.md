# Gender

## Separación técnica y de gobierno

La calidad técnica del campo y el permiso para utilizarlo son decisiones independientes. Un campo puede ser consistente y aun así permanecer `Sensitive / restricted` por ser un atributo protegido.

## Revalidación agregada al 2026-08-17

La validación usó empleados regulares activos y snapshots cerrados entre
2020-07-26 y 2026-07-26. No expuso etiquetas, distribuciones por categoría ni
registros individuales.

- El tipo físico es `character varying`, no un booleano.
- En los 73 snapshots cerrados existen exactamente dos códigos normalizados no
  vacíos; también hay dos en el último snapshot.
- La cardinalidad raw es tres únicamente porque la cadena vacía aparece como
  una forma adicional. Se observaron 6,326 blanks y cero `NULL`; el blank se
  clasifica como missing, no como tercera categoría.
- No existen aliases por mayúsculas/minúsculas, whitespace residual,
  contradicciones dentro de una llave empleado-snapshot ni llaves duplicadas.
- Coverage global: 99.7872%; mínimo mensual: 97.4626%; último snapshot:
  99.9960%.
- Se observaron ocho cambios de código normalizado correspondientes a siete
  empleados. Sin una política gobernada no puede determinarse si son
  correcciones, actualizaciones legítimas o anomalías.
- Ninguna cohorte código-snapshot quedó por debajo del umbral compartido de 30.

Conclusión técnica: el campo está **codificado con dos valores observados**, pero
eso no prueba que el concepto de género sea intrínsecamente binario ni confirma
qué significado de negocio tiene cada código. La definición y los cambios
longitudinales requieren confirmación del data owner; la restricción de
privacidad permanece.

SQL trazable:

- `queries/audits/gender_domain_stability_audit_20260817.sql`
- `queries/audits/gender_normalization_transition_followup_20260817.sql`

## Seguimiento del pico de missingness — 2026-08-17

Este seguimiento respondió a la duda visible en el gráfico histórico sin
publicar etiquetas ni registros individuales. Se ejecutó sobre empleados
regulares activos al grain empleado-snapshot, desde 2020-07-26 hasta el último
snapshot disponible (2026-08-23).

- En todo el período, faltaron **6,328 de 3,023,199** employee-snapshots:
  **0.209315%** ponderado.
- En FY2026 faltaron **5,982 de 525,623**: **1.138078%**. El bloque de cinco
  meses de dic-2025 a abr-2026 explica **5,958** de esos casos (**99.598796%**
  del missingness de FY2026).
- Todas las ausencias del seguimiento fueron **cadenas en blanco**, no `NULL`;
  no hubo llaves empleado-snapshot duplicadas ni ausencias sin clasificar.

| Snapshot | Missing employee-snapshots | Missingness |
|---|---:|---:|
| 2025-12-28 | 1,196 | 2.537446% |
| 2026-01-25 | 1,198 | 2.535021% |
| 2026-02-22 | 1,202 | 2.521714% |
| 2026-03-29 | 1,186 | 2.478579% |
| 2026-04-26 | 1,176 | 2.447756% |
| 2026-05-24 | 13 | 0.026896% |

La continuidad agrega evidencia de que fue un solo bloque temporal: 1,156
empleados estuvieron faltantes en los cinco snapshots. Sólo uno pertenecía a
la población del snapshot previo; 1,131 volvieron a estar poblados al cierre de
mayo. El patrón es consistente con una cohorte que entró al universo analítico
con el atributo pendiente de carga y después recibió un backfill, pero no
demuestra la causa raíz. Debe confirmarlo el data owner o el proceso de carga.

El pico no cambia el score de **Missingness=2** bajo la regla vigente (cada mes
permanece por debajo de 5%), pero se conserva como limitación temporal para
auditorías de fairness.

SQL trazable de este seguimiento:

- `queries/audits/gender_missingness_followup_20260817.sql`
- `queries/audits/gender_missingness_continuity_followup_20260817.sql`
- `queries/audits/gender_missingness_population_entry_followup_20260817.sql`

## Uso recomendado

- No usar Gender para targeting ni como driver operativo de retención.
- Si existe aprobación, utilizarlo en un entorno restringido para auditorías de fairness y desempeño diferencial.
- No mostrar categorías ni cortes pequeños en outputs generales.
- Repetir periódicamente la auditoría agregada de nulls, blanks, cardinalidad y estabilidad.

<!-- BEGIN evaluate-attrition-variable:gender -->
## Conocimiento acumulado: Gender

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:30:59-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Demographics
- **Relevancia:** Se limita a monitoreo de fairness; su uso predictivo requiere aprobación formal.

### Definición y fuente evaluadas

- **Definición vigente:** Atributo demográfico protegido registrado en el snapshot; su uso requiere aprobación de gobernanza independiente.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** gender
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 99.9966%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_09_gender_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_09_gender_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_09_gender_report_column_profile.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:gender -->
