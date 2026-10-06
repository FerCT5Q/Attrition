# Hours away from manager

## Descubrimiento de fuentes para distancia — 2026-08-17

La búsqueda de metadata de Redshift confirmó que `postal_code` en la tabla
mensual de empleados pertenece a datos de domicilio sensibles. No debe enviarse
a una API pública ni usarse para calcular distancia entre empleado y manager.

También aparecieron `location_latitude` y `location_longitude` en
`esd_backup` y `exit_survey_data`; la estructura de esas tablas contiene
metadatos y contenido de exit-survey, por lo que las coordenadas no son una
fuente gobernada de sitios de oficina y además presentan riesgo de leakage.

No se encontró una tabla aprobada y efectiva en el tiempo que haga el mapping
`office_site -> latitud/longitud/zona horaria`. La ruta correcta sería obtener
una referencia de Facilities/Real Estate con ese mapping, vigencia y dueño. Con
ella se podría calcular distancia geodésica entre **sitios de oficina** en
bandas; “horas” requeriría adicionalmente una definición de ruta, modo y tráfico.
Una API pública sólo sería evaluable para un catálogo pequeño de oficinas,
desidentificado y aprobado; nunca para domicilios o códigos postales de empleados.

SQL trazable:

- `queries/audits/manager_proximity_source_discovery_20260817.sql`
- `queries/audits/manager_proximity_candidate_tables_20260817.sql`
- `queries/audits/manager_proximity_coordinate_schema_20260817.sql`

## Validación de ZIP y candidato de sitio de trabajo — 2026-08-17

Se probó de forma agregada si `postal_code` del snapshot mensual puede ser el
ZIP de `office_site`. La regla de aceptación era que, para cada combinación de
sitio y mes con al menos dos empleados, hubiese un único ZIP. Falló de forma
concluyente: 3,652 de 3,653 grupos comparables (99.9726%) tenían más de un ZIP
y el máximo fue 4,926. Por lo tanto, `postal_code` no es un mapping
`office_site → ZIP` y no se utilizará para distancia ni se expondrán sus
valores.

La búsqueda de metadata no encontró una tabla HRDA nombrada como catálogo de
oficinas, sitios, ubicaciones o facilities. Sí apareció
`hrda.vndly_assignment`, con `tdw_wo_work_site_code`, nombre, ciudad/estado y
ZIP de sitio de trabajo. Su mapping interno parece prometedor para su propio
origen (238 de 248 códigos tienen un ZIP; uno tiene dos; nueve no tienen ZIP).
Que no incluya `employee_id` no la invalida como posible catálogo de sitios;
esa llave no es necesaria para una dimensión de ubicaciones. La brecha real es
el crosswalk: el snapshot mensual de empleados sólo expone `office_site` y
`office_location`, no `office_code`, `site_id` ni `location_id`. Ninguno de
los 68 `office_site` coincide literalmente con un nombre o código VNDLY, y
`office_location` tampoco proporciona una llave directa: 110 de 65,912
valores distintos coinciden con un nombre VNDLY. Hace falta un mapping
gobernado entre esos descriptores de empleado y `tdw_wo_work_site_code`.

Esto no es una fuente aprobada para la feature. La siguiente ruta válida sigue
siendo un catálogo efectivo en el tiempo de Facilities/Real Estate o de
Workday que relacione el identificador de oficina usado por empleados con
coordenadas, zona horaria o ZIP de oficina.

SQL trazable adicional:

- `queries/audits/office_site_employee_postal_dispersion_audit_20260817.sql`
- `queries/audits/office_reference_table_metadata_20260817.sql`
- `queries/audits/vndly_work_site_mapping_audit_20260817.sql`
- `queries/audits/office_site_vndly_name_crosswalk_audit_20260817.sql`
- `queries/audits/employee_location_vndly_crosswalk_audit_20260817.sql`
- `queries/audits/employee_snapshot_location_identifier_metadata_20260817.sql`
- `queries/audits/hrda_employee_location_code_crosswalk_metadata_20260817.sql`

<!-- BEGIN evaluate-attrition-variable:hours-away-from-manager -->
## Conocimiento acumulado: Hours away from manager

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:39:29-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Manager / workplace
- **Relevancia:** La separación horaria o de viaje puede representar carga de coordinación.

### Definición y fuente evaluadas

- **Definición vigente:** Distancia aprobada en tiempo de viaje o zona horaria entre sitios efectivos de empleado y manager.
- **Tipo semántico:** external_source
- **Tabla / fuente:** Fuente no validada o externa: HRDA contiene sitios, pero no una referencia aprobada de travel time o distancia de zona horaria.
- **Columnas:** employee_id, manager_employee_id, office_site, country, external travel-time or time-zone fields
- **Grain:** Par empleado-manager

### Relaciones con el portafolio

- Hours away from manager depende de Location.
- Comparten country (shared_source_column).
- Comparten employee_id (shared_source_column).
- Comparten manager_employee_id (shared_source_column).
- Comparten office_site (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Externa / tercero (4 puntos).
- **Scores:** Source=1, Definition=0, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** None%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Pendiente.
- No existe una racha estable que califique como historia utilizable. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- No existe una ruta confiable y validada para construir la definición solicitada.
- No existe evidencia validada de coverage reciente.
- Missingness no puede cuantificarse sin observaciones validadas.

**Acciones recomendadas**

- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Identificar una fuente aprobada o excluir la variable del conjunto candidato.

**SQL y evidencia trazable**

- No existe SQL ejecutable para esta fuente.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:hours-away-from-manager -->
