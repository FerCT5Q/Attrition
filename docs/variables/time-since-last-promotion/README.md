# Time since last promotion

<!-- BEGIN evaluate-attrition-variable:time-since-last-promotion -->
## Conocimiento acumulado: Time since last promotion

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:35:43-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Career progression
- **Relevancia:** Un periodo largo sin promoción puede reflejar fricción de progresión.

### Definición y fuente evaluadas

- **Definición vigente:** Tiempo completado desde la promoción más reciente conocida al momento del snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** is_promo, promotion_date
- **Grain:** Historia empleado-evento

### Relaciones con el portafolio

- Comparten is_promo (shared_source_column).
- Comparten promotion_date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La historia utilizable cumplió el threshold del score. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_27_time-since-last-promotion_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_27_time-since-last-promotion_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_27_time-since-last-promotion_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_27_time-since-last-promotion_is-promo_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:time-since-last-promotion -->

## Actualización de distribución para la lámina (2026-09-10)

### Flujo histórico y decisión de fuente

Esta actualización conserva el assessment v4 histórico como contexto y no
modifica sus scores. Para la lámina se evaluó una distribución descriptiva con
corte fijo al **2026-08-23** y modo de entrega `presentation`.

- Se rechazó usar `promotion_date` del snapshot actual como si fuera la última
  promoción: la fecha sólo aparece en el snapshot del evento y no describe por
  sí sola todo el historial del empleado.
- Se aceptó reconstruir el evento más reciente desde
  `hrda.post_hire_monthly_worker_dtls`, usando sólo filas con `is_promo=1`,
  `promotion_date` no nula, no posterior al snapshot del evento y no posterior
  al corte.
- La feature publicada es la **última promoción registrada válida**, no una
  política de promociones aprobada ni una afirmación causal sobre attrition.

### Método reproducible

- **Población y grain:** `worker_type='Employee'`, `employee_type='Regular'`
  y `active_status=1`; un empleado regular activo en el snapshot mensual del
  corte.
- **Episodio laboral actual:** se usan únicamente eventos con
  `promotion_date >= max_hire_rehire_date`. Los eventos previos al rehire se
  excluyen, aunque sigan disponibles como auditoría agregada.
- **Deduplicación:** sólo el par idéntico `employee_id + promotion_date` se
  cuenta una vez. Duplicados o conflictos de empleado-snapshot, conflictos de
  flag/fecha, flags inválidos, fechas futuras y fechas posteriores a su
  snapshot bloquean la publicación.
- **Bandas:** aniversarios calendario `0–<1`, `1–<2`, `2–<3`, `3–<5` y `5+`
  años. El KPI `2+ years` es la suma de las últimas tres bandas y usa como
  denominador toda la población activa regular.
- **Ausencia de evento:** no se convierte en "never promoted" ni en una
  duración. Se muestran separadamente `No promotion recorded in current
  episode` y `History predates observed promotion events`. El segundo estado
  conserva el left-censoring cuando el episodio comenzó antes del inicio
  observado de historia de promociones (2016-10-23). Una fecha de inicio de
  episodio desconocida sólo podría entrar a un estado no calculable; en este
  corte su conteo fue cero.
- **Transferencias:** `is_transferred` y `transfer_date` están fuera de la
  fórmula. Se conservan sólo como auditoría para comprobar que una transferencia
  coincidente no altera la última promoción seleccionada.

### Validaciones, consultas y resultado agregado

| Pregunta | Método y regla de aceptación | Resultado al 2026-09-10 | Conclusión |
| --- | --- | --- | --- |
| ¿El evento es seguro para el corte y el episodio actual? | Audit agregado con snapshots únicos, flags binarios, fechas válidas y ninguna promoción seleccionada anterior al rehire. | 0 duplicados/conflictos de snapshot, flags inválidos, fechas faltantes para `is_promo=1`, fechas futuras o fechas posteriores al snapshot; 311 eventos previos al episodio fueron excluidos. | Pasa. |
| ¿Las transferencias cambian el cálculo? | La fórmula no referencia campos de transferencia; el audit cuenta coincidencias como diagnóstico. | 60 eventos válidos tuvieron `is_transferred=1`; 29 coincidieron exactamente en fecha con una transferencia. | Pasa: permanecen fuera de la fórmula. |
| ¿La distribución reconcilia? | Bandas temporales + estados no temporales = denominador; porcentajes no redondeados = 100%; `2+` = últimas tres bandas. | 50,043 activos regulares; 23,180 con última promoción registrada; 26,863 estados no temporales; 13,029 con 2+ años (26.04%). | Pasa. |
| ¿Se puede publicar? | Sólo agregados, sin identidades, fechas individuales ni categorías protegidas; cada bucket mostrado debe tener `n >= 30`. | El menor bucket mostrado es 1,695. | Pasa en modo `presentation`. |

Las consultas agregadas y la evidencia congelada son:

- `queries/audits/time_since_last_promotion_event_integrity_20260823.sql`
- `queries/profiles/time_since_last_promotion_distribution_20260823.sql`
- `output/distribution/json/time-since-last-promotion-distribution-evidence-20260910.json`

### Distribución congelada

| Categoría | Empleados | % de todos los activos regulares |
| --- | ---: | ---: |
| 0–<1 año | 5,514 | 11.02% |
| 1–<2 años | 4,637 | 9.27% |
| 2–<3 años | 4,107 | 8.21% |
| 3–<5 años | 7,227 | 14.44% |
| 5+ años | 1,695 | 3.39% |
| No promotion recorded in current episode | 23,001 | 45.96% |
| History predates observed promotion events | 3,862 | 7.72% |

### Limitaciones y acción

- La evidencia sólo representa eventos de promoción registrados dentro de la
  historia observada; no prueba que no haya promociones previas ni que el campo
  represente una política HR aprobada.
- La lámina no usa la ausencia de evento como una característica numérica. Si
  se quiere usar una feature distinta en un modelo, se debe acordar su
  tratamiento de no-evento, left-censoring y fecha de conocimiento antes de
  volver a evaluarla.
- El assessment v4 histórico conserva sus scores actuales. Esta actualización
  mejora la trazabilidad de una distribución de presentación, no eleva ningún
  score cualitativo.

## Rediseño del slide 26: cohortes temporales comparables (2026-09-23)

### Flujo histórico y decisión

La distribución histórica de la lámina separaba la última promoción registrada
de estados no temporales. Esa separación era correcta para no convertir la
ausencia de evento en “never promoted”, pero los dos paneles no describían la
misma cohorte temporal. Además, el texto declaraba la exclusión de RF360 sin
que el cálculo histórico la aplicara.

El rediseño fija una sola cohorte al **24-ago-2025**: empleados `Employee`,
`Regular`, activos y con `COALESCE(is_rf360_yes_no, 0)=0`. La categoría se
calcula sólo con información conocida en esa fecha y cada persona se sigue para
una salida estrictamente `VOLUNTARY` en **(2025-08-24, 2026-08-23]**. El nuevo
artefacto inicial fue `presentation`; no contiene identificadores, filas ni
etiquetas de categorías protegidas. La actualización interna del 2026-09-24
conserva exactamente el mismo cálculo y sólo cambia la política de visibilidad
de la celda pequeña autorizada.

### Definiciones publicadas

- **Time since latest recorded promotion:** máxima `promotion_date` válida en
  el episodio vigente (`promotion_date >= max_hire_rehire_date`), usando las
  bandas calendario `0–<1`, `1–<2`, `2–<3`, `3–<5` y `5+ years`.
- **People with no recorded promotion:**
  proxy estricto, no una afirmación de “never promoted”. Sólo incluye episodios
  que empiezan dentro de la historia observable, sin promoción válida desde
  hire/rehire, con `time_in_role` no negativo y donde
  `ROUND(time_in_role, 1)` coincide con la antigüedad calendario desde
  `max_hire_rehire_date`, también redondeada a una decimal.

### Validaciones y evidencia

| Pregunta | Motivo y método | Regla de aceptación | Resultado observado | Conclusión e impacto |
| --- | --- | --- | --- | --- |
| ¿La población es un empleado-snapshot único y realmente excluye RF360? | Auditoría agregada del snapshot baseline. | Cero duplicados, conflictos e integrantes RF360 después del filtro. | 41,757 empleados; 0 duplicados, 0 conflictos y 0 RF360 incluidos; 3,246 RF360 se excluyeron antes de clasificar. | Pasa. Corrige el desfase entre texto y cálculo sin cambiar scores v4. |
| ¿El evento de promoción es válido y time-safe? | Reconciliación agregada de `is_promo`, `promotion_date`, snapshot del evento y episodio laboral. | Cero flags inválidos, flags sin fecha, fechas sin flag, fechas posteriores al snapshot o futuras. | Todas esas métricas fueron 0; 195 eventos previos al episodio vigente se excluyeron. | Pasa. La banda superior representa sólo la última promoción registrada válida. |
| ¿El proxy inferior sigue siendo una cohorte temporal acotada? | Comparación agregada entre `time_in_role` y la duración calendario del episodio, redondeadas a una decimal. | Episodio observable, duración no negativa y coincidencia exacta al redondeo; el resto permanece declarado como exclusión. | 15,812 empleados cumplieron el proxy; 4,681 se excluyeron por historia previa no observable y 2,171 por no alinear rol y episodio. | Pasa para el proxy; no habilita una afirmación sobre todo el historial de promociones. |
| ¿Las cohortes y el outcome reconcilian? | Conteos agregados por panel y comparación de salidas con el join directo al outcome. | Base = promoción registrada + proxy + exclusiones; salidas clasificadas = salidas directas. | 41,757 = 19,093 + 15,812 + 6,852; ambos métodos dieron 2,377 salidas voluntarias. | Pasa. Los porcentajes se calculan dentro de cada panel independiente. |
| ¿Cómo se muestra la celda menor a n=30? | Autorización explícita de análisis interno, manteniendo sólo agregados y sin IDs. | Marcar la celda como exploratoria; mostrar su conteo, porcentaje, salidas y tasa descriptiva sin tratarla como estimación estable. | La banda registrada 5+ tiene n=7, 0 salidas y 0.0%; el proxy sin promoción registrada tiene n=790 en 5+ años. | Pasa para revisión interna; el asterisco y la nota impiden confundir el dato descriptivo con una tasa estable. |

### Resultado para la lámina

Ambos paneles publican cinco bandas con porcentaje, `n` y attrition voluntaria
anual descriptiva. En el panel de promoción registrada, la fila 5+ lleva un
asterisco porque n=7 está bajo el umbral compartido. El panel proxy usa el
encabezado corto **People with no recorded promotion**; la condición de
alineación entre rol y episodio queda en la nota metodológica. En ambos, la
barra expresa distribución dentro de su propio panel y la nota declara las
cohortes independientes, la historia previa no observable y los casos de rol
que no coincide con el episodio.

La evidencia y las consultas trazables son:

- `queries/audits/v7_time_since_last_promotion_comparable_cohorts_metadata_20260923.sql`
- `queries/audits/v7_time_since_last_promotion_comparable_cohorts_20260923.sql`
- `output/distribution/json/attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json`

Esta actualización está limitada al visual y su evidencia interna agregada. No
modifica los scores del assessment v4 ni otras láminas de promociones.

## Actualizacion de visual interno: banda 5+ y texto claro (2026-09-24)

Este cambio solo ajusta la visibilidad del artefacto exploratorio V7; no cambia
la definicion de la variable, los scores V4 ni la regla de clasificacion. El
modo de entrega ahora es `internal_analysis`, bajo la autorizacion
`attrition-v7-internal-aggregate-visibility-20260917`, para el solicitante y
Julia. Se mantienen controles no negociables: solo agregados, sin filas ni IDs
de empleados, y sin uso operativo o redistribucion.

- La banda `5+ years` de **Time since latest recorded promotion** se muestra
  aunque tiene `n=7`: se observaron 0 salidas voluntarias en la ventana anual
  y la tasa descriptiva es 0.0%. Lleva un asterisco y una nota explicita:
  `n<30` no es una estimacion estable de attrition.
- Este resultado no contesta cuantas personas llevan 5+ anos sin promocion. La
  cohorte proxy inferior de **People with no recorded promotion** si mide esa
  condicion restringida y contiene `n=790` en `5+ years`.
- El encabezado inferior se simplifica a **People with no recorded promotion**.
  La alineacion entre antiguedad de rol y episodio laboral permanece como una
  condicion metodologica de la nota, no como una afirmacion de "never
  promoted".

La evidencia nueva conserva los conteos, porcentajes, salidas y tasas agregadas
de ambas cohortes, y registra la excepcion autorizada:

- `output/distribution/json/attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json`

La auditoria agregada de calculo se mantiene en
`queries/audits/v7_time_since_last_promotion_comparable_cohorts_20260923.sql`.
La excepcion de visualizacion no cambia la formula ni vuelve estable una tasa
de cohorte pequena.
