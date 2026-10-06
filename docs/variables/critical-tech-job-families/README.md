# Critical Tech job families

## Propósito

`Critical Tech job families` define la población del MVP de People Analytics
para attrition. El catálogo se usa como filtro de población y no como outcome.

La pregunta analítica es:

> ¿Qué cohortes dentro de Critical Tech tienen attrition voluntario elevado,
> qué señales están asociadas y qué acciones pueden evaluarse?

## Fuente y mapping

- Catálogo: `hrda.critical_tech`.
- Detalle del catálogo: `extended_job_family`.
- Segmento: `seg`.
- Snapshot observado: `hrda.post_hire_monthly_worker_dtls.job_family`.
- Grain del catálogo: family-segment.
- Grain para el modelo: empleado-snapshot mensual.
- Población: `worker_type='Employee'`, `employee_type='Regular'`,
  `active_status=1`.

La unión se hace por `TRIM(LOWER(extended_job_family)) =
TRIM(LOWER(job_family))`. No se deben inferir families críticas por nombres
parecidos si el catálogo no las contiene.

## Resultado de la validación 2026-09-07

La fuente tiene todas las columnas requeridas. El catálogo contiene 62 keys y
12 segmentos, sin valores vacíos ni contradicciones family-segment. 61 keys
coinciden exactamente con el dominio de `job_family`; una no coincide y queda
pendiente de resolución.

La cobertura del scope unido es 100% por snapshot desde 2020-07-26 hasta
2026-09-27. Esta cobertura no prueba que la key sin match sea correcta ni que
el catálogo actual sea históricamente válido.

El archive contiene fechas efectivas, pero usa un grain distinto. Por eso la
membership histórica permanece pendiente hasta reconciliar `tech` con
`extended_job_family`.

## Uso en el modelo

Critical Tech es el primer filtro. Dentro de esa población se descubrirán
cohortes mediante combinaciones de family, segmento, level, tenure, manager,
movilidad, engagement, work arrangement y otras variables aprobadas.

Los grupos pequeños se poolen en el modelo común y no se publican
individualmente. El mínimo compartido es 30 empleados; se prefieren 100 o más
para reporting ejecutivo.

## Evidencia y artefactos

- `queries/audits/critical_tech_source_access_20260907.sql`
- `queries/audits/critical_tech_mapping_definition_join_20260907.sql`
- `queries/audits/critical_tech_temporal_reconciliation_20260907.sql`
- `queries/audits/critical_tech_hazard_preflight_20260907.sql`
- `queries/profiles/critical_tech_mapping_coverage_20260907.sql`
- `output/assessments/critical-tech-job-families-20260907-profile/profile.json`

## Acción pendiente

Resolver la key no mapeada y aprobar si el catálogo actual puede aplicarse a
todo el historial de entrenamiento. Hasta entonces, Definition y Join no se
consideran completamente confirmados.
