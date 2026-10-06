# Tamaño de equipo directo (span)

## Estado y uso

Este concepto respalda únicamente el slide 33 de V7 como
`internal_analysis`. Es una visual exploratoria agregada, no un assessment v4,
no modifica un score de producción y no debe interpretarse como evidencia de
causalidad.

El uso es describir la distribución de empleados activos Regular según el
tamaño reconstruido del equipo directo de su manager y comparar su attrition
voluntaria prospectiva a 12 meses.

## Flujo histórico y límite temporal

1. Se fija el snapshot de pertenencia al **24-ago-2025**.
2. Se deduplica la relación `manager_employee_id` dentro de ese mismo snapshot.
3. Se conserva una relación solo si el manager se resuelve como Employee,
   Regular y activo en el snapshot. El span es el conteo de empleados
   elegibles que reportan directamente a ese manager.
4. Se sigue al mismo cohorte para una terminación estricta `VOLUNTARY` con
   `term_date` en `(2025-08-24, 2026-08-23]`.

No se usan `reg_non_intern_dir_reports`, `reg_non_intern_total_reports`,
`all_dir_reports` ni `all_total_reports` como definición primaria.

## Validación ejecutada

| Elemento | Resultado |
| --- | --- |
| Pregunta | ¿Cómo se distribuyen los empleados por tamaño de equipo directo y cuál es su attrition voluntaria anual? |
| Motivo | Un conteo almacenado no confirma por sí mismo la población, el momento ni el tratamiento de relaciones no resolubles. |
| Método | Consulta agregada read-only que reconstruye los equipos directos desde `manager_employee_id` y enlaza salidas futuras del mismo cohorte base. |
| Regla de aceptación | `45,003 = 44,737` elegibles + `266` exclusiones; seis bandas suman 44,737 empleados, 9,665 equipos y 2,480 salidas; tamaños exactos 5 y 20 reconcilian a 7,160/1,432 y 80/4 respectivamente. |
| Resultado | La regla pasó el 23-sep-2026. Cobertura: 99.41%. |
| Conclusión | El tamaño de equipo es una categoría derivada de relaciones del snapshot. Las tasas son descriptivas; no prueban que el span cause attrition. |
| Impacto en score | No aplica: no se creó ni actualizó un assessment o score de producción. |
| Acción | Volver a ejecutar la consulta si cambian la fecha de snapshot, población Regular o definición de manager resoluble. |

## Cobertura y privacidad

Las 266 personas sin manager resoluble se reportan como exclusión de
cobertura, no como una séptima banda. Las seis bandas visibles tienen al menos
30 empleados. La comparación exacta de 20 reportes representa cuatro equipos;
se marca exploratoria bajo la autorización V7 de análisis interno. La excepción
no permite filas, identidades, nombres, acceso a managers, redistribución,
uso operativo ni un cambio de score.

No se guardan ni muestran empleados, managers, identificadores, nombres,
correos ni filas individuales.

## Evidencia reproducible

- SQL agregado: `queries/audits/direct_team_span_annual_attrition_20260923.sql`
- Evidencia congelada: `output/distribution/json/direct-team-span-annual-attrition-evidence-20260923.json`
- Autorización: `config/attrition_v7_internal_analysis_authorization_20260917.json`
- Fecha de ejecución: 23-sep-2026

La evidencia congelada registra los SHA-256 de SQL y resultado agregado, la
reconciliación de cobertura/salidas y las verificaciones de privacidad.
