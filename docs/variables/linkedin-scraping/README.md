# LinkedIn scraping

<!-- BEGIN evaluate-attrition-variable:linkedin-scraping -->
## Conocimiento acumulado: LinkedIn scraping

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:34:23-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** External pull factors
- **Relevancia:** La fuente solicitada no define una feature y presenta riesgos de consentimiento, términos de uso e identity matching.

### Definición y fuente evaluadas

- **Definición vigente:** Señal mensual de perfil profesional externo asociada a un empleado mediante un método de recopilación aprobado.
- **Tipo semántico:** external_source
- **Tabla / fuente:** Fuente no validada o externa: No existe feed aprobado ni crosswalk gobernado entre empleados y perfiles.
- **Columnas:** TBD employee/profile match, observation_date
- **Grain:** Empleado / perfil externo

### Relaciones con el portafolio

- Comparten index_score_average (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Externa / tercero (1 puntos).
- **Scores:** Source=1, Definition=0, Coverage=0, Missingness=0, Consistency=0, History=0, Join=0, Effort=0
- **Coverage reciente:** None%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Pendiente.
- No existe una racha estable que califique como historia utilizable. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- No existe una ruta confiable y validada para construir la definición solicitada.
- No existe evidencia validada de coverage reciente.
- Missingness no puede cuantificarse sin observaciones validadas.

**Acciones recomendadas**

- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Identificar una fuente aprobada o excluir la variable del conjunto candidato.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.

**SQL y evidencia trazable**

- No existe SQL ejecutable para esta fuente.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:linkedin-scraping -->
