# Commute distance

## Actualizacion global y comparacion Onsite - 2026-09-11

La distribución base de la slide 19 dejó de presentar la distancia como si toda la población fuera
`Onsite`. La evidencia se recalculo en el snapshot `2026-09-27` para grupos de
empleados regulares activos: `50,207` en total, de los cuales `45,433` tienen
`UPPER(TRIM(work_arrangement)) = 'ONSITE'` (`90.5%`) y `4,774` son otros valores
o desconocidos.

La grafica compara cinco bandas agregadas -`0-<10 km`, `10-<20 km`,
`20-<30 km`, `30+ km` y `No calculable`- entre toda la poblacion y el subconjunto
`Onsite`. La evidencia subyacente conserva el detalle de 1 km. La cobertura de
distancia es `41,760` (`83.2%`) para toda la poblacion y `39,536` (`87.0%`) para
`Onsite`; quedan `8,447` y `5,897` casos `No calculable`, respectivamente.

Esto responde a la observacion de que la distancia de personas `Offsite` no
debe interpretarse automaticamente como exposicion al traslado. La medida
sigue siendo un proxy Haversine entre centroide postal y coordenada de oficina;
no es distancia por carretera, tiempo de viaje ni commute observado. La
comparacion es descriptiva y no define todavia un umbral operativo.

Evidencia y consultas de esta actualizacion:

- `output/distribution/json/commute-distance-global-evidence-20260911-onsite.json`
- `queries/profiles/commute_distance_global_zip_hash_distribution_20260911_work_arrangement.sql`
- `queries/audits/commute_distance_global_input_coverage_20260911_work_arrangement.sql`
- `queries/audits/commute_distance_work_arrangement_onsite_20260911.sql`

## Cálculo exploratorio de distancia geográfica para Mexico City — 2026-09-08

Se construyó una distribución agregada para el snapshot `2026-09-27` usando 90
empleados regulares activos de `Mexico City`. `postal_code` se trató como ZIP
residencial del empleado, no como ZIP de oficina. El destino se tomó de la
página oficial de oficinas de Qualcomm: la oficina de Mexico City registra ZIP
`11000` y coordenadas `19.4287845, -99.207451`.

La distancia es Haversine entre el centroide del ZIP residencial y la
coordenada de la oficina. Es un proxy geográfico; no representa distancia por
carretera, tiempo de viaje ni el commute real. El catálogo público de
centroides se consultó localmente y los ZIP residenciales se cruzaron mediante
hashes; no se guardaron códigos postales de empleados en la evidencia.

Resultado agregado: 89 de 90 empleados tuvieron centroid matching (98.8889%).
La distribución publica sólo las bandas `0–<10 km` y `10+ km`, con conteos 38 y
51; ambas cumplen `n >= 30`. Un ZIP sin match se omitió y no se imputó.

Evidencia congelada:

- `output/distribution/json/commute-distance-mexico-city-evidence-20260908.json`
- `output/distribution/json/qualcomm-office-locations-evidence-20260908.json`
- `queries/profiles/commute_distance_mexico_city_zip_hash_distribution_20260908.sql`
- `queries/audits/commute_distance_mexico_city_input_coverage_20260908.sql`
- `queries/audits/commute_distance_mexico_city_postal_format_20260908.sql`

La salida es `internal_analysis` y no debe interpretarse como una feature
validada globalmente ni como distancia de trayecto.

## Tasa de attrition Voluntary por distancia estimada Onsite — 2026-09-17

La presentación V4 ahora reemplaza la comparación de distribución de la slide
19 por una pregunta más útil para attrition: **entre empleados `Onsite` con
distancia calculable, ¿cómo varía la tasa de salida `Voluntary` durante los
seis meses posteriores al snapshot en cada banda estimada de 1 km?** Esta
actualización no cambia el assessment ni convierte la distancia en una feature
aprobada para producción.

### Flujo histórico y población

La vista anterior usaba un solo snapshot global y comparaba la distribución de
distancia de toda la población elegible contra el subconjunto `Onsite`. El
nuevo resultado conserva sólo la población cuya exposición al traslado es más
plausible: employee-snapshots de empleados regulares activos con
`UPPER(TRIM(work_arrangement)) = 'ONSITE'` en 24 snapshots mensuales, desde
`2024-03-24` hasta `2026-02-22`. Para cada snapshot se observan salidas
`term_type = 'VOLUNTARY'` en el intervalo posterior de seis meses; se excluyen
`Voluntary Exception`, tipos nulos o ambiguos e involuntarias.

### Validación: población, temporalidad y unicidad

- **Pregunta:** ¿la población y el outcome están alineados en cada fecha?
- **Motivo:** una tasa por distancia no es interpretable si mezcla empleados no
  Onsite, usa una salida anterior al snapshot o duplica employee-snapshots.
- **Método:** auditoría agregada por employee-snapshot y salida posterior,
  con regla temporal `(snapshot_date, snapshot_date + 6 meses]`.
- **Regla de aceptación:** exactamente 24 snapshots maduros, cero duplicados
  Onsite y cero registros de ubicación conflictivos.
- **Métricas observadas:** 775,105 employee-snapshots Onsite elegibles;
  766,814 con entradas de ubicación completas y no conflictivas; 0 duplicados
  y 0 conflictos.
- **Conclusión:** la cohorte y la ventana cumplen la regla para describir tasas
  agregadas; no demuestran causalidad.

### Validación: cobertura y cálculo de distancia

- **Pregunta:** ¿hay cobertura suficiente y una definición explícita de la
  distancia?
- **Motivo:** la ausencia de match no debe convertirse en una distancia de
  cero ni mezclarse con una banda visible.
- **Método:** distancia Haversine entre el centroide del código postal
  residencial y la coordenada resuelta del `office_site`. El código postal se
  consulta sólo como hash; no se persiste ni se muestra en la evidencia.
- **Regla de aceptación:** cobertura de distancia calculable de al menos 70%
  de los employee-snapshots Onsite elegibles y reconciliación con la auditoría
  agregada.
- **Métricas observadas:** 675,101 employee-snapshots con distancia calculable,
  equivalentes a 87.1% de la población elegible; 20,010 salidas `Voluntary` en
  esa cohorte.
- **Conclusión:** la cobertura permite una comparación descriptiva de las
  bandas publicadas. La medida sigue siendo un proxy geográfico: no mide ruta,
  tiempo de traslado ni commute observado.

### Validación: publicación de bandas y resultado

- **Pregunta:** ¿cada tasa visible tiene volumen suficiente?
- **Motivo:** las bandas de 1 km son más útiles para la lectura solicitada,
  pero no deben revelar cohortes pequeñas.
- **Método:** bandas de `0–<1 km` a `29–<30 km` y una cola `30+ km`; se
  reconcilian exposiciones y salidas contra el baseline de distancia calculable.
- **Regla de aceptación:** cada banda publicada debe tener al menos 30
  employee-snapshots y 30 salidas `Voluntary`; la suma de bandas debe coincidir
  con el baseline.
- **Métricas observadas:** 31 bandas publicables; 675,101 employee-snapshots y
  20,010 salidas reconciliadas; tasa baseline de seis meses 2.96%.
- **Conclusión:** la slide V4 puede mostrar las tasas agregadas por 1 km, una
  línea baseline de 2.96% y el detalle emergente de volumen. Por ejemplo,
  `0–<1 km` registra 3.48%, `1–<2 km` 1.88% y `30+ km` 3.56%; estos valores no
  prueban que la distancia haya causado una salida.

### Impacto y acción

El resultado respalda una visualización compartible de análisis agregado
(`presentation`) y mejora la autoexplicación de la slide. No eleva los scores
del assessment: la variable continúa siendo una fuente externa y geográfica
sensible, sin autorización como feature de producción, umbral operativo,
predicción individual ni intervención. Cualquier uso futuro debe obtener una
fuente aprobada, una definición de negocio de commute y una revisión de
privacidad adicional.

Consultas y evidencia reproducible:

- `output/distribution/json/commute-distance-onsite-six-month-attrition-evidence-20260917.json`
- `queries/audits/commute_distance_onsite_six_month_attrition_audit_20260917.sql`
- `queries/profiles/commute_distance_onsite_six_month_attrition_hash_profile_20260917.sql`
- `queries/profiles/commute_distance_onsite_six_month_attrition_country_partitions_20260917.sql`

<!-- BEGIN evaluate-attrition-variable:commute-distance -->
## Conocimiento acumulado: Commute distance

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:33:17-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Location / workplace
- **Relevancia:** La carga de traslado puede interactuar con modalidad laboral y asistencia.

### Definición y fuente evaluadas

- **Definición vigente:** Distancia de traslado entre un proxy aprobado de ubicación del empleado y el sitio de trabajo efectivo.
- **Tipo semántico:** external_source
- **Tabla / fuente:** Fuente no validada o externa: No existe una fuente aprobada de distancia y la ubicación de domicilio es sensible.
- **Columnas:** homeaddresswithcountry, postal_code, office_site, external coordinates or distance
- **Grain:** Ubicación del empleado

### Relaciones con el portafolio

- Comparten office_site (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (2 puntos).
- **Scores:** Source=1, Definition=0, Coverage=0, Missingness=0, Consistency=0, History=0, Join=1, Effort=0
- **Coverage reciente:** None%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- No existe una ruta confiable y validada para construir la definición solicitada.
- No existe evidencia validada de coverage reciente.
- Missingness no puede cuantificarse sin observaciones validadas.

**Acciones recomendadas**

- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Identificar una fuente aprobada o excluir la variable del conjunto candidato.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- No existe SQL ejecutable para esta fuente.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:commute-distance -->
