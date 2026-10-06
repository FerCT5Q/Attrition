# Implementación del modelo de People Analytics para Critical Tech

Fecha de ejecución: 2026-09-07  
Estado: población validada para análisis exploratorio; mapping pendiente de resolver por una family sin correspondencia.

## Objetivo

El modelo no busca producir una lista de personas que supuestamente van a
renunciar. Busca encontrar cohortes dentro de Critical Tech que presenten
attrition voluntario elevado, describir las señales asociadas y priorizar
acciones de retención que puedan ser evaluadas.

```text
Critical Tech filter
        -> hazard de attrition
        -> descubrimiento de cohortes
        -> drivers asociados
        -> palanca y acción candidata
        -> métrica de seguimiento
```

## Población y grain

La población primaria es:

- `worker_type = 'Employee'`;
- `employee_type = 'Regular'`;
- `active_status = 1`;
- `job_family` con coincidencia normalizada en `hrda.critical_tech`.

El filtro Critical Tech es una definición de población. No es un target que el
modelo deba aprender. `seg` sirve para reportar, comparar y probar hipótesis;
no convierte a una family en una variable modificable.

El grain de exposición es un employee-snapshot mensual. El grain del catálogo
es `extended_job_family`-`seg`.

## Evidencia ejecutada

### Acceso y mapping

| Evidencia | Resultado | Estado |
|---|---:|---|
| Columnas requeridas en `critical_tech` y `critical_tech_archive` | 7 de 7 encontradas | Pass |
| Families del catálogo comparables | 62 | Pass parcial |
| Contradicciones family-segment | 0 | Pass |
| Valores vacíos en el catálogo | 0 | Pass |
| Families con coincidencia en `job_family` | 61 de 62 | Review |
| Match rate normalizado | 98.3871% | Review |
| Archive con fechas efectivas no nulas | 135 filas | Contexto |

La evidencia no permite elevar Definition o Join a score 2 porque una key del
catálogo no coincide con `job_family`. El assessment conservador queda con
blocker `tbd` y debe repetirse después de resolver esa key.

Además, el preflight de la llave histórica confirmó que
`hrda.critical_tech_archive` no tiene la columna `extended_job_family`: tiene
`tech` y `dept_id`, mientras que el catálogo vigente usa
`extended_job_family` y `seg`. Por eso no es válido asumir que `tech` o
`dept_id` son equivalentes a una job family. La membership histórica queda
bloqueada hasta obtener un crosswalk autoritativo o una fuente archive con la
llave común. La consulta es
`queries/audits/critical_tech_archive_join_key_preflight_20260907.sql` y el
resultado fue `blocked_missing_common_family_key`.

SQL trazable:

- `queries/audits/critical_tech_source_access_20260907.sql`
- `queries/audits/critical_tech_mapping_definition_join_20260907.sql`
- `queries/audits/critical_tech_temporal_reconciliation_20260907.sql`

### Cobertura histórica

El profile de `critical_tech` devuelve 76 snapshots mensuales entre
2020-07-26 y 2026-09-27. La cobertura observable del `job_family` es 100% en
las fechas publicadas, después de aplicar el join al catálogo. Esta métrica
describe la población que sí pudo ser unida; no demuestra que la family sin
match esté correctamente clasificada.

SQL y artefactos:

- `queries/profiles/critical_tech_mapping_coverage_20260907.sql`
- `output/assessments/critical-tech-job-families-20260907-profile/profile.json`
- `output/assessments/critical-tech-job-families-20260907-profile/critical-tech-job-families_assessment_20260907-111937.xlsx`

### Hazard mensual por segmento

El preflight de hazard utiliza la misma lógica temporal del outcome aprobado:
eventos `Voluntary` deduplicados por empleado y fecha, unidos a snapshots
activos anteriores al evento. El periodo de evaluación termina en el límite de
conocimiento 2026-09-07.

Diez segmentos tienen al menos 30 eventos positivos y 24 intervalos completos
para un diagnóstico agregado independiente. Dos segmentos quedan
`pooled_or_suppressed`: participan en el modelo común, pero no se publican como
diagnósticos separados por volumen insuficiente.

La tasa observada sirve para screening, no es todavía un modelo ajustado ni una
causa. El resultado completo se conserva en la consulta y los conteos pequeños
se suprimen.

SQL: `queries/audits/critical_tech_hazard_preflight_20260907.sql`. El resultado
empaquetado está en `output/analysis/critical-tech/20260907/hazard-preflight-report.md`
y su manifest conserva los hashes del SQL y del resultado.

## Primer screen de cohortes ejecutado

Se ejecutó un screen agregado con target directo a seis meses para generar las
primeras hipótesis de grupos. El preflight específico encontró 68 snapshots
completos entre `2020-07-26` y `2026-02-22`, 2,038,274 exposiciones
employee-snapshot, cero duplicados en el grain y 100% de observabilidad en
tenure, manager change, promotion y transfer dentro de la ventana analizada.

La consulta `queries/audits/critical_tech_cohort_discovery_20260907.sql`
devuelve 428 cohortes publicables después de exigir al menos 30 empleados y 30
eventos positivos. El baseline Critical Tech fue 3.1588% de salida voluntaria
a seis meses. Bajo el filtro inicial de lift >= 1.25, al menos 100 empleados y
consistencia entre dos periodos, 54 cohortes quedaron como
`prioritaria_para_validacion` y 35 como `hipotesis_accionable`. Las categorías
`unknown` de eventos se clasificaron como `review_data_quality` y no se usaron
como drivers.

Los artefactos agregados son:

- `output/analysis/critical-tech/20260907/cohort-screen-results.json`;
- `output/analysis/critical-tech/20260907/cohort-screen-report.md`;
- `output/analysis/critical-tech/20260907/action-register.md`;
- `output/analysis/critical-tech/20260907/manifest.json`.

El patrón inicial se concentra en combinaciones de segmento o job family con
tenure y nivel. El resultado es un mapa para seleccionar cohortes de la
siguiente fase; no es todavía evidencia de que una acción concreta reduzca
attrition. La siguiente validación debe ajustar un hazard discreto pooled,
comparar cada señal contra el baseline y probar estabilidad out-of-time.

La especificación ejecutable de esta fase está en
`config/critical_tech_model_spec_v1_20260907.yaml`. Define el outcome mensual,
el rollup a seis meses, los bloques de features, los splits temporales, las
métricas de selección, la política de privacidad y la regla para que un
challenger no lineal pueda superar al hazard interpretable.

## Modelo estadístico

El modelo principal será supervivencia discreta mensual con enlace `cloglog`:

```text
h(i,t) = P(salida voluntaria entre el snapshot t y el siguiente snapshot)
```

El riesgo de seis meses se calcula acumulando los hazards mensuales. Se
comparará contra:

1. baseline histórico;
2. regresión logística directa a seis meses;
3. challenger no lineal, como Random Survival Forest o gradient boosting.

Se utilizará un modelo común para Critical Tech con `seg` y `job_family` como
contexto y posibles interacciones. Sólo se justificaría un modelo separado si
una family tiene volumen, comportamiento y estabilidad suficientes.

## Descubrimiento de grupos

Los grupos no están predeterminados. Se buscarán combinaciones interpretables
de:

- segmento y job family;
- level y management level;
- company tenure y time in role;
- manager change y manager leaving;
- team turnover;
- promoción, transferencia y movilidad;
- work arrangement y labor market;
- engagement e intent to stay de QVoice;
- bandas de compensación relativa.

El descubrimiento usará interacciones regularizadas y árboles de segmentación
pequeños con validación temporal. No se usará clustering como método principal,
porque un cluster puede ser estadísticamente coherente pero no accionable.

Un grupo será prioritario cuando tenga al menos 30 empleados para compartirlo,
preferentemente 100 o más, lift mínimo recomendado de 1.25, estabilidad en
periodos futuros y una palanca posible. Los grupos pequeños o inestables se
tratarán como hipótesis.

## Drivers y acciones

Cada driver se clasificará como:

- señal asociada;
- palanca potencialmente modificable;
- acción candidata;
- control de contexto no modificable.

La salida recomendada será:

```text
cohorte + tamaño + attrition + lift + driver
+ palanca + acción + owner + métrica + fecha de revisión
```

Ejemplos de palancas candidatas son revisión de carrera, movilidad interna,
manager enablement, apoyo después de cambios de manager, revisión de staffing,
seguimiento de engagement, revisión de compensación relativa y ajuste de work
arrangement.

Un driver predictivo no demuestra que cambiarlo reduzca attrition. La acción
se debe probar posteriormente con un piloto, análisis causal o diseño cuasi
experimental.

## Limitaciones y siguientes acciones

1. Resolver la family no mapeada en `critical_tech`.
2. Reconciliar `critical_tech_archive` con `extended_job_family` para construir
   membership histórica con fechas efectivas.
3. Construir el dataset employee-snapshot dentro del entorno controlado, sin
   guardar filas employee-level.
4. Ejecutar el modelo pooled y el benchmark directo de seis meses.
5. Descubrir cohortes con reglas estables y supresión de grupos pequeños.
6. Documentar drivers y acciones candidatas por cohorte.
7. Medir el efecto de las acciones antes de presentarlas como soluciones.

## Artefactos de assessment

- Spec v4: `config/critical_tech_job_families_v4_20260907.yaml`.
- Run request: `config/critical_tech_job_families_run_request_20260907.yaml`.
- Plan explícito: `config/critical_tech_job_families_analysis_plan_v1_20260907.yaml`.
- Preflight: `output/assessments/critical-tech-job-families-20260907-preflight3/`.
