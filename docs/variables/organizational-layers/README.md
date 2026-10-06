# Organizational layers

## Dos variables que no deben confundirse

### Supervisory organization level from top

- Campo directo: `worker_supervisory_organization_level_from_top`.
- Representa el nivel precalculado de la organización supervisora desde la parte superior.
- Los valores observados fueron 1 a 12.
- Restar uno cambia la base numérica, pero no lo convierte en un conteo exacto de managers.

### Manager layers to CEO

- Feature derivada: número de relaciones `manager_employee_id` entre el empleado y la raíz CEO en el mismo `fis_mo_end_dt`.
- La raíz tiene cero capas; cada subordinado tiene `capas_del_manager + 1`.
- Requiere `employee_id`, `manager_employee_id` y `fis_mo_end_dt` para reconstruir cada snapshot.

## Validación agregada

- Corte revisado: 50,043 empleados regulares activos, todos con cadena reconstruible.
- Todas las cadenas actuales convergieron en una raíz única cuyo cargo estaba clasificado como CEO.
- En 49,497 de 50,042 relaciones employee-manager, el nivel del empleado fue exactamente el del manager más uno: 98.91%.
- El campo directo coincidió con la profundidad reconstruida para 49,265 empleados: 98.45%.
- En 42 snapshots utilizables existió exactamente un CEO en nivel 1, pero también hubo otros registros de nivel 1.
- La cobertura del campo directo es estable desde 2023-03-26.

## Evidencia del dashboard Tableau

El workbook `references/tableau/organizational-csi-dashboard/Organizational CSI Dashboard.twb` mapea directamente el campo desde la tabla diaria. No contiene una fórmula activa que recorra `manager_employee_id`. El nombre `Level from CEO` aparece sólo como terminología informal en preferencias antiguas.

## Recomendación

- Si se usa el campo directo, llamarlo `Supervisory organization level from top`.
- Si el requisito es literalmente “Layers from CEO”, calcular la cadena recursiva por snapshot.
- Documentar reglas para managers faltantes, relaciones matriciales, ciclos y reorganizaciones.
- Revaluar la definición y consistencia del assessment antes de tratar ambos conceptos como equivalentes.

## Distribución para la lámina 32 — snapshot 2026-08-23

**Clasificación del entregable:** `internal_analysis`. La lámina sólo puede
mostrar conteos y porcentajes agregados de empleados regulares activos; no
incluye IDs, nombres, managers ni la identidad de la raíz.

### Método vigente

- **Concepto:** profundidad literal de la cadena de reporte directo hasta la
  raíz CEO aprobada por RH.
- **Población de visualización:**
  `worker_type='Employee'`, `employee_type='Regular'` y `active_status=1` en
  `fis_mo_end_dt = '2026-08-23'`.
- **Universo de nodos:** todos los workers activos del mismo snapshot, para que
  un manager activo que no pertenezca a la población de visualización siga
  estando disponible durante el recorrido.
- **Grain:** empleado regular activo por snapshot mensual. La profundidad es el
  número de enlaces `employee_id → manager_employee_id`: la raíz CEO es capa
  0 y un reporte directo es capa 1.
- **Aislamiento temporal:** cada enlace se resuelve únicamente dentro del
  snapshot 2026-08-23; nunca se toma un manager de otro snapshot.
- **Límite y fallas:** manager faltante, auto-manager, nodo repetido/ciclo,
  asignación conflictiva de manager o intento de recorrer más de 25 enlaces
  invalidan la publicación.
- **Raíz de negocio:** el proceso recibe la referencia CEO aprobada por RH a
  través de un mecanismo seguro no versionado al momento de ejecutar. El valor
  se vincula como parámetro de consulta en memoria; no aparece en SQL guardado,
  JSON, documentación, logs ni la lámina.
- **Reconciliación separada:**
  `worker_supervisory_organization_level_from_top` se compara con la profundidad
  reconstruida más uno, pero no se usa como valor del gráfico.

### Regla de aceptación y privacidad

La evidencia se publica sólo si existe el snapshot, todos los nodos activos
reconstruyen sin excepciones, hay una sola raíz, cada cadena converge 100% a la
referencia CEO aprobada y el total de profundidades de la población de
visualización reconcilia exactamente con su denominador. El SQL trazable es
`queries/audits/layers_from_ceo_snapshot_20260823_distribution.sql`.

Los conteos por profundidad permanecen en memoria hasta aplicar la política de
publicación. Cada barra final debe tener `n >= 30`; las capas escasas de los
extremos se agrupan de manera contigua (por ejemplo, `0–2 layers` o `9+ layers`).
La raíz/CEO nunca se muestra como barra singleton.

### Estado y resultado actual

Ejecución completada el 2026-09-10 con la referencia CEO aprobada suministrada
en memoria al proceso. La referencia no se conservó en el SQL, JSON,
documentación ni la lámina.

- **Población:** 50,043 empleados regulares activos en el snapshot 2026-08-23.
- **Reconstrucción y raíz:** 100.0% de convergencia a una sola raíz aprobada;
  no hubo cadenas no resueltas, ciclos, auto-managers, conflictos de manager ni
  recorridos superiores a 25 enlaces.
- **Publicación:** 10 bandas contiguas, de la más superficial a la más
  profunda; la banda mínima tiene `n=100`. La raíz singleton quedó agrupada en
  `0–2 layers` y no se muestra de forma individual.
- **Reconciliación separada:**
  `worker_supervisory_organization_level_from_top = profundidad + 1` coincidió
  para 98.6492% de los empleados regulares comparables. Ese campo no es el
  valor del gráfico.
- **Artefactos:**
  `output/distribution/json/layers-from-ceo-depth-distribution-evidence-20260910.json`
  y la lámina 32 del deck de distribuciones fueron actualizados. El JSON sólo
  contiene métricas agregadas y bandas que cumplen `n >= 30`.

### Evidencia congelada para regeneraciones

La referencia CEO aprobada se valido dentro de la auditoria del snapshot
2026-08-23 y se uso solo en memoria durante esa ejecucion. No se conserva en
Git, configuracion, SQL, JSON, HTML, documentacion ni el deck. La evidencia
congelada solo retiene el resultado agregado: una raiz aprobada, 100% de
convergencia y las bandas publicables.

Los rebuilds posteriores no necesitan recibir ni volver a consultar esa
referencia. Validan el contrato completo de la evidencia congelada: snapshot,
hash del SQL, controles de privacidad, una raiz, convergencia y reconciliacion
de totales, antes de volver a materializar la lamina 32. Si el snapshot, la
regla o la jerarquia fuente cambian, se requiere una nueva auditoria aprobada;
la referencia vuelve a usarse solo en memoria para esa revalidacion puntual.

Para repetir el proceso con una referencia aprobada en un entorno seguro:

```powershell
& .venv\Scripts\python.exe -B tools\build_distribution_html_v2.py
```

El comando habitual valida y reutiliza la evidencia agregada congelada de la
lamina 32. Para refrescar solo la lamina en el HTML, no reconsulta Redshift:

```powershell
& .venv\Scripts\python.exe -B tools\build_distribution_html_v2.py `
  --refresh-layers-from-ceo-slide
```

El generador rechaza la escritura del JSON y el refresco focalizado rechaza la
lámina si falla cualquier control. Este cambio es sólo de distribución y no
altera el score histórico v4.

## Revalidación de cadenas — 17 de agosto de 2026

Se reconstruyó la jerarquía con `employee_id` y `manager_employee_id` dentro del
mismo `fis_mo_end_dt`, usando como población objetivo empleados regulares
activos. Los identificadores se mantuvieron dentro de los joins y sólo se
publicaron métricas agregadas.

### Snapshot más reciente cerrado: 2026-07-26

- 49,652 empleados elegibles y 49,652 cadenas reconstruidas.
- Cero cadenas no resueltas y cero ciclos.
- Una sola raíz, con `job_title` clasificado como CEO.
- Convergencia a esa raíz: 100%.
- Profundidad máxima reconstruida: 11 relaciones de manager.
- El campo almacenado coincidió con `profundidad reconstruida + 1` para 48,829
  empleados; 823 no coincidieron. Match rate: 98.3425%.
- La regla local empleado-manager `nivel_empleado = nivel_manager + 1` coincidió
  en 49,144 de 49,651 relaciones: 98.9789%.

### Historial utilizable: 2023-03-26 a 2026-07-26

- 41 snapshots y 1,790,114 empleado-snapshots elegibles.
- 1,790,097 cadenas convergieron en la raíz con título CEO.
- Dieciséis cadenas quedaron no resueltas y una convergió en una raíz distinta
  del CEO; no se detectaron ciclos.
- Cuarenta de 41 snapshots tuvieron una sola raíz CEO. El snapshot 2024-03-24
  tuvo dos raíces entre las cadenas de la población objetivo.
- Las 16 cadenas no resueltas se concentran entre marzo y noviembre de 2023 y
  corresponden a rutas con manager faltante en el mismo snapshot.
- El campo almacenado coincidió con `profundidad reconstruida + 1` en 90.8915%
  del historial comparable: 1,627,043 coincidencias y 163,050 discrepancias.

### Decisión de evidencia

La derivación recursiva demuestra que puede construirse una feature literal de
capas hasta la raíz CEO. No demuestra que
`worker_supervisory_organization_level_from_top` sea esa misma feature: la
reconciliación histórica falla la regla de equivalencia exacta. Bajo la puerta
v4, `Definition` permanece en 1 mientras las 16 cadenas no resueltas, la raíz
alternativa y las discrepancias del campo almacenado no tengan una regla
aprobada o se seleccione formalmente la derivación recursiva con tratamiento de
excepciones.

### SQL trazable

- `queries/audits/layers_from_ceo_metadata_discovery_20260817.sql`
- `queries/audits/layers_from_ceo_active_snapshot_structure_20260817.sql`
- `queries/audits/layers_from_ceo_root_semantics_20260817.sql`
- `queries/audits/layers_from_ceo_latest_snapshot_reconstruction_20260817.sql`
- `queries/audits/layers_from_ceo_historical_reconstruction_20260817.sql`
- `queries/audits/layers_from_ceo_historical_structure_exceptions_20260817.sql`

## Revisión del dashboard Tableau — 17 de agosto de 2026

Se inspeccionó el XML de
`references/tableau/organizational-csi-dashboard/Organizational CSI Dashboard.twb`
para identificar el lineage utilizado por el dashboard.

- La fuente principal carga directamente el último `transaction_date` de
  `hrda.post_hire_daily_worker_dtls`, filtrando registros activos de tipo
  `Employee`.
- `worker_supervisory_organization_level_from_top` está mapeado como columna
  física del source. El workbook no contiene una fórmula que lo recalcule.
- El archivo contiene 549 campos calculados; ninguno utiliza
  `manager_employee_id` ni
  `worker_supervisory_organization_level_from_top`.
- Ninguno de los 23 worksheets utiliza `manager_employee_id`, el nivel desde la
  parte superior o un campo activo llamado `Level from CEO`.
- Ningún Custom SQL contiene `WITH RECURSIVE` ni otra reconstrucción de cadenas
  de manager.
- Los textos `Level from CEO (Max)` y `Sup_Org_Level_from_Top` sólo permanecen
  en metadata de estilo/color y ordenamiento del datasource. No existe en esta
  versión una definición de cálculo ni una referencia activa desde una hoja.

### Interpretación

El dashboard no calcula distancia al CEO. Como máximo aporta contexto de que
una versión o preferencia anterior presentó el campo upstream con terminología
de CEO. Por tanto, no valida la equivalencia entre el campo almacenado y el
número de relaciones de manager. La reconstrucción recursiva por snapshot sigue
siendo la validación adecuada para una feature literal `Layers from CEO`, y la
reconciliación de Redshift demuestra que el campo directo no es un sustituto
exacto.

<!-- BEGIN evaluate-attrition-variable:layers-from-ceo -->
## Conocimiento acumulado: Layers from CEO

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:37:27-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Organization structure
- **Relevancia:** La profundidad organizacional puede representar distancia de decisión y posición estructural.

### Definición y fuente evaluadas

- **Definición vigente:** Profundidad organizacional del snapshot desde la raíz superior de la jerarquía supervisora.
- **Tipo semántico:** hierarchy
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** worker_supervisory_organization_level_from_top
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 40.0 meses.

**Hallazgos principales**

- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Aprobar la definición y reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz; guardar SQL agregado, regla previa y métricas de reconciliación.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_30_layers-from-ceo_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_30_layers-from-ceo_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_30_layers-from-ceo_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_30_layers-from-ceo_worker-supervisory-organization-level-from-top_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:layers-from-ceo -->

<!-- BEGIN evaluate-attrition-variable:et-fields -->
## Conocimiento acumulado: ET fields

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:46:11-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Talent / expert track
- **Relevancia:** Una clasificación expert-track podría segmentar carrera, pero el acrónimo y mapping objetivo son ambiguos.

### Definición y fuente evaluadas

- **Definición vigente:** Clasificación expert-track por definir, por ejemplo engineering ET1/ET2 o non-engineering ET1.
- **Tipo semántico:** hierarchy
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** et_1_leader, et_2_leader, et_3_leader, et_4_leader, et_5_leader, et_6_leader, et_7_leader, et_8_leader, et_9_leader, et_10_leader, et_11_leader
- **Grain:** Empleado u organización por definir

### Relaciones con el portafolio

- Comparten group_category_level (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Por definir (9 puntos).
- **Scores:** Source=2, Definition=0, Coverage=2, Missingness=2, Consistency=0, History=2, Join=1, Effort=0
- **Coverage reciente:** 99.9609%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_43_et-fields_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_43_et-fields_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_43_et-fields_report_column_profile.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:et-fields -->
