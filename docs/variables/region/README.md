# Region

<!-- BEGIN evaluate-attrition-variable:region -->
## Conocimiento acumulado: Region

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:30:31-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Demographics
- **Relevancia:** La región permite controles geográficos amplios y segmentación por mercado laboral.

### Definición y fuente evaluadas

- **Definición vigente:** Región de trabajo registrada para cada empleado activo en el snapshot.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** region
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- La normalización regional depende del composite de survey y de un mapping geográfico estable.
- Standardized / normalized within region depende de Region.
- Comparten region (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- Coverage reciente cumplió el threshold del score. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_08_region_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_08_region_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_08_region_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_08_region_region_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:region -->

## Decisión de visualización — 2026-09-08

La presentación interna conserva **Region** como el campo directo `region`; no
se modifica la definición de la feature ni sus scores del assessment v4. La
primera visual separa `United States of America` de `AMERICAS` sólo como
agrupación de display, para evitar que la escala de Estados Unidos quede oculta
dentro de Americas.

La segunda visual usa el campo distinto `labor_market` para **todos** los
empleados regulares activos, no sólo Estados Unidos. Los tres valores `USA -
Market 1`, `USA - Market 2` y `USA - Market 3` confirmaron el recuerdo del
comentario, pero son categorías dentro de la distribución global, no el alcance
del gráfico.

- **Corte y población:** snapshot mensual `2026-08-23`, grain de
  empleado-snapshot distinto, 50,043 empleados regulares activos.
- **Display Region:** India (20,814), United States (14,470), APAC (7,631),
  EMEA (5,558) y Americas excluding U.S. (1,570). Los cinco grupos reconcilian
  al total y superan `n >= 30`.
- **Display Labor Market:** 42 valores fuente observados; se muestran los 20
  más grandes y `Other Labor Markets` (892 empleados) para conservar la
  distribución de toda la población sin publicar categorías menores a `n=30`.
- **Cobertura:** `labor_market` tiene cobertura de 100.0% en este corte. No se
  sustituye por `workplace city`, que es otra variable y respondería una
  pregunta geográfica distinta.

La evidencia agregada se guarda en
`queries/audits/region_us_labor_market_display_snapshot_20260908.sql` y
`output/distribution/json/attrition-43-variable-distributions-v2.region-labor-market-evidence-20260908.json`.
La validación verificó cero duplicados o contradicciones por empleado-snapshot,
cero casos sin clasificar, Estados Unidos dentro de `AMERICAS`, India dentro de
`INDIA` y cobertura completa de `labor_market`. Esto confirma el display de
este corte; no demuestra estabilidad histórica del mapping ni eleva los
criterios pendientes del assessment.

## Revalidación de display global — 2026-09-09

**Flujo histórico.** El display del 2026-09-08 separaba Estados Unidos de
`AMERICAS` únicamente para visualización. Tras revisar el alcance con el
equipo, se retiró esa agrupación híbrida: Country sigue en su propia lámina y
Region debe mostrar exclusivamente las categorías almacenadas.

- **Pregunta:** ¿La lámina puede comparar Region y Labor Market sin limitar el
  segundo a Estados Unidos ni transformar la primera en una mezcla de país y
  región?
- **Motivo:** Country, Region y Labor Market responden preguntas geográficas
  distintas; separar Estados Unidos dentro de Region duplicaba la narrativa de
  Country.
- **Método:** consulta agregada del snapshot `2026-08-23` sobre empleados
  regulares activos, grain empleado-snapshot distinto. Se validaron duplicados
  de filas fuente, conflictos por empleado-snapshot, dominio almacenado de
  Region, cobertura de `labor_market`, reconciliación contra el denominador y
  `n >= 30` en cada bucket publicado.
- **Regla de aceptación:** los cuatro valores almacenados de Region y el top
  20 global de Labor Market más `Other Labor Markets` deben reconciliar a la
  población elegible; todas las validaciones deben ser cero y cada bucket debe
  cumplir `n >= 30`.
- **Métricas observadas:** 50,043 empleados; India 20,814 (41.59%), Americas
  16,040 (32.05%), APAC 7,631 (15.25%) y EMEA 5,558 (11.11%). Labor Market
  tiene 42 valores fuente, cobertura 100.0% y se publica como top 20 más Other.
  Duplicados, conflictos, Region sin clasificar y Labor Market faltante: 0.
- **Conclusión e impacto:** se aprobó el display global puro. Es un cambio de
  visualización; no cambia la definición de la feature, el alcance histórico ni
  los scores del assessment v4.

Trazabilidad: `config/region_labor_market_global_display_plan_v4_20260909.yaml`,
`queries/audits/region_labor_market_global_display_20260909.sql` y
`output/distribution/json/region-labor-market-global-evidence-20260909.json`.

## Display alternativo solicitado — 2026-09-09

Se conserva arriba la distribución de **Region** con sus cuatro categorías
almacenadas. Debajo se añade una segunda visualización, solicitada para la
revisión, que es una agrupación de display y no reemplaza el campo `region`:

- `United States` y `Americas excluding U.S.` sustituyen visualmente al grupo
  almacenado `AMERICAS`.
- `China` y `APAC excluding China` sustituyen visualmente al grupo almacenado
  `APAC`.
- `India` y `EMEA` conservan sus grupos almacenados.

La consulta agregada del mismo snapshot `2026-08-23` reconcilia los seis
buckets con los 50,043 empleados regulares activos: India 20,814; United
States 14,470; Americas excluding U.S. 1,570; China 3,389; APAC excluding
China 4,242; EMEA 5,558. Todos cumplen `n >= 30`. Las validaciones de filas
fuente, conflicto de Region/Country, región sin clasificar, Estados Unidos
fuera de Americas y China fuera de APAC resultaron en cero. No había Country
faltante en esta población.

Trazabilidad: `config/region_major_country_split_display_plan_v4_20260909.yaml`,
`queries/audits/region_major_country_split_display_20260909.sql` y
`output/distribution/json/region-major-country-split-evidence-20260909.json`.
