# Ingreso por adquisición

<!-- BEGIN evaluate-attrition-variable:ingreso-por-adquisici-n -->
## Conocimiento acumulado: Ingreso por adquisición

_Actualizado por el assessment v4 `acquisition-entry-v4-20260929-r4` el 2026-09-29T20:56:27-06:00._

### Contexto del problema

- **Problema:** Incorporar «Adquisiciones y attrition» entre las variables prioritarias con una distribución actual y una comparación anual de attrition voluntaria que no convierta valores vacíos en una afirmación sobre el origen de ingreso.
- **Decisión / caso de uso:** Determinar si el campo acquisition dispone de evidencia suficiente para una visual descriptiva agregada y documentar sus límites antes de cualquier uso analítico posterior.
- **Outcome:** Salida voluntaria posterior al snapshot basal y hasta 2026-08-23.
- **Población:** Empleados Regular activos (worker_type='Employee', employee_type='Regular', active_status=1) en el snapshot aplicable.
- **Límite de conocimiento:** acquisition se toma del snapshot de clasificación; ningún valor posterior al baseline puede reclasificar la cohorte de attrition.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Mostrar distribución y attrition voluntaria anual por presencia de adquisición registrada, con un desglose de las principales adquisiciones actuales y limitaciones explícitas de semántica.

### Definición y fuente evaluadas

- **Definición vigente:** Campo textual acquisition del snapshot mensual. La publicación distingue únicamente presencia o ausencia de registro normalizado y conserva los nombres almacenados sin unificar aliases no documentados.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** acquisition
- **Grain:** Empleado-snapshot mensual

### Relaciones con el portafolio

- Los reingresos pueden requerir una regla de vigencia distinta para interpretar acquisition.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (6 puntos).
- **Scores:** Source=2, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 15.3911%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple parcialmente.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple parcialmente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- El coverage observable reciente está por debajo del mínimo de 70% para score 1.
- Missingness reciente supera el máximo de 30% para score 1.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.
- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.

**SQL y evidencia trazable**

- `queries\profiles\acquisition-entry-v4-20260929-r4_01_ingreso-por-adquisici-n_coverage.sql`
- `queries/audits/acquisition_entry_source_access_20260929.sql`
- `queries/audits/acquisition_entry_semantic_audit_20260929.sql`
- `queries/audits/acquisition_entry_related_source_metadata_20260929.sql`
- `queries/audits/acquisition_entry_termination_label_audit_20260929.sql`
- `queries/audits/acquisition_entry_termination_event_grain_audit_20260929.sql`
- `queries/audits/acquisition_entry_termination_population_filter_audit_20260929.sql`
- `queries/audits/acquisition_entry_distribution_attrition_20260929.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 5.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:ingreso-por-adquisici-n -->

<!-- BEGIN evaluate-attrition-variable-run:ingreso-por-adquisici-n:acquisition-entry-v4-20260929-r4 -->

### Historial de decisión — run `acquisition-entry-v4-20260929-r4`

_Registrado el 2026-09-29T20:56:27-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (6 puntos).

**Evolución del plan**

- Plan v5: La ejecucion v4 llego a generar evidencia agregada y el notebook, pero el validador de narrativa marco el metodo de la historia 4 por no contener un marcador linguistico en espanol. Esta revision solo aclara esa redaccion y conserva la misma poblacion, SQL, ventanas y reglas de aceptacion v4 antes de repetir la ejecucion completa.

**Validaciones y efecto observado**

- **source:** ¿La tabla mensual y los campos requeridos existen y son accesibles por la ruta read-only? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Cada empleado tiene un registro no contradictorio por snapshot y el dominio admite normalizacion acotada? — resultado Cumple parcialmente; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **source:** ¿Las fuentes relacionadas exponen columnas para servir solo como contraste agregado? — resultado Informativa; impacto: Evidencia contextual para Source; sin capacidad de aumentar el score.
- **join:** ¿La normalizacion de term_type recupera solo la etiqueta VOLUNTARY? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La tasa selecciona una sola salida Voluntary por persona aunque el feed mensual repita filas? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La elegibilidad se fija en el baseline sin reclasificar a la persona por una fila posterior? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Que rango historico y contraste agregado ofrecen acquisition, new_hires y el snapshot historico? — resultado Informativa; impacto: Evidencia contextual para History; sin capacidad de aumentar el score.
- **join:** ¿Los segmentos, Top 10 mas Otras y salidas deduplicadas reconcilian con las poblaciones? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Que diferencias agregadas quedan entre la tabla principal y all_terminations para la cohorte? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\acquisition-entry-v4-20260929-r4_01_ingreso-por-adquisici-n_coverage.sql`
- `queries/audits/acquisition_entry_source_access_20260929.sql`
- `queries/audits/acquisition_entry_semantic_audit_20260929.sql`
- `queries/audits/acquisition_entry_related_source_metadata_20260929.sql`
- `queries/audits/acquisition_entry_termination_label_audit_20260929.sql`
- `queries/audits/acquisition_entry_termination_event_grain_audit_20260929.sql`
- `queries/audits/acquisition_entry_termination_population_filter_audit_20260929.sql`
- `queries/audits/acquisition_entry_distribution_attrition_20260929.sql`

<!-- END evaluate-attrition-variable-run:ingreso-por-adquisici-n:acquisition-entry-v4-20260929-r4 -->

## Revisión de la lámina para uso interno — 2026-10-05

Se recalcularon las cuatro tasas omitidas por el umbral de eventos en V8 a partir de los mismos agregados ejecutados el 2026-09-29. La [nota de revisión interna](internal-attrition-review-20261005.md) documenta la autorización para el solicitante y Julia, los numeradores y denominadores, las comprobaciones y las cinco categorías sin cohorte anual. La corrección se entrega en V9 y no cambia el assessment ni sus scores.

El [diagnóstico de las bases cero](zero-baseline-diagnosis-20261005.md), consultado el 5 de octubre de 2026, confirma las primeras fechas observadas de las cinco etiquetas y distingue su ausencia en la cohorte de la posible historia anterior de sus empleados actuales. No cambia scores ni demuestra fechas legales de adquisición.

La [ampliación por período observado](observed-period-attrition-20261005.md) completa V10 con las tasas desde el primer corte disponible para Aqua, NAPS, Arduino y Augentix Inc., identificadas con asterisco y duración. NAPS conserva la advertencia de su cohorte inicial de 4; Moonshot permanece sin tasa porque aún no hay seguimiento posterior. La fórmula es la misma proporción de salidas de una cohorte fija y no se anualiza.
