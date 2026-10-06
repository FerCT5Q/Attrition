# Plan de continuidad — candidata 44: Above-average team turnover

Estado al 2026-09-10: **implementación incompleta; no presentar todavía como
entregable final**. La definición, SQL y el flujo v4 ya están creados. Falta
cerrar el assessment ejecutado, congelar la evidencia, documentar la variable
y actualizar/validar el deck de distribución.

## Objetivo aprobado

Crear la candidata 44 `Above-average team turnover`, una señal binaria de
contexto de manager separada de `High risk manager` y `High turnover under this
person`.

Para cada snapshot mensual `t`:

- `1`: el manager vigente del reporte directo es elegible y su tasa histórica
  de salidas `Voluntary`, equivalente a seis meses, es `>= 1.4 ×` el benchmark
  ponderado de managers elegibles.
- `0`: el manager es elegible y queda debajo del umbral.
- `Unknown`: falta historia o exposición suficiente. Nunca convertir este
  estado en `0`.

Reglas fijas:

- Ventana: 18 intervalos mensuales cerrados anteriores a `t` (19 cierres).
- Población: `worker_type='Employee'`, `employee_type='Regular'`,
  `active_status=1` y `manager_employee_id` no nulo.
- Evento: `term_type = 'Voluntary'` exactamente. Excluir `Voluntary Exception`,
  involuntarias y nulos.
- Atribución: manager del empleado en el inicio del intervalo que contiene
  `term_date`.
- Elegibilidad del manager: 18 intervalos consecutivos observables, promedio
  mensual de equipo `>=4`, y `>=2` salidas voluntarias distintas.
- Benchmark: promedio de tasas de managers elegibles ponderado por tamaño medio
  de equipo. Con 18 intervalos fijos equivale a
  `salidas elegibles / exposición elegible * 6`.
- Señal sensible/restringida, asociativa. No es evaluación individual de
  managers ni feature productiva sin validación temporal y gobierno.

## Artefactos ya creados

Configuración y planes:

- `config/above_average_team_turnover_v4_20260910.yaml`
- `config/above_average_team_turnover_run_request_20260910.yaml`
- `config/above_average_team_turnover_analysis_plan_v1_20260910.yaml`
- `config/above_average_team_turnover_analysis_plan_v2_20260910.yaml`
- `config/above_average_team_turnover_analysis_plan_v3_20260910.yaml`

Usar siempre el plan v3; v1 y v2 se conservan inmutables como historia de las
revisiones técnicas.

SQL agregado:

- `queries/audits/above_average_team_turnover_source_access_20260910.sql`
- `queries/audits/above_average_team_turnover_18m_audit_20260910.sql`
- `queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql`
- `queries/profiles/above_average_team_turnover_18m_profile_20260910.sql`

Adaptador técnico para el runner:

- `tools/read_only_redshift_query_helper.py`

El adaptador reutiliza el validador SELECT/WITH del skill de Redshift y el
modo `autocommit` del cliente oficial. Se creó porque el driver de Redshift
rechazaba `SET TRANSACTION READ ONLY` para el plan analítico, aun cuando el
validador bloquea cualquier operación no read-only. No añadir DDL/DML ni rutas
de escritura a este archivo.

## Evidencia ya observada (agregada, presentation-safe)

La consulta de perfil se ejecutó correctamente de forma directa mediante el
helper read-only. Para el cierre `2026-09-27`:

| Estado | Reportes directos actuales |
| --- | ---: |
| 0 o 1 (manager elegible) | 4,445 |
| 1 | 902 |
| Unknown | 45,761 |
| Total | 50,206 |

La alta proporción `Unknown` es el resultado de los mínimos de 18 intervalos,
promedio de equipo y dos salidas; debe reportarse como limitación de cobertura,
no como cero.

La auditoría de seis cierres produjo antes de la corrección de precisión:

- `evaluated_snapshot_count=6`
- `expected_interval_count=18`
- `minimum_eligible_interval_count=18`
- `minimum_eligible_average_team_size=4.000000`
- `minimum_eligible_voluntary_exit_count=2`
- `duplicate_count=0`
- `conflicting_manager_count=0`
- `event_multiple_interval_assignment_count=0`
- `event_multiple_manager_assignment_count=0`
- `future_event_usage_count=0`
- `eligible_count=295,100`, `matched_count=295,100`, `unmatched_count=0`,
  `multi_match_count=0`
- `rule_implementation_failure_count=0`

Contexto que debe documentarse, sin ocultarlo:

- Hay `53,865` filas repetidas del evento en los snapshots fuente, por lo que
  el SQL deduplica por `employee_id + term_date` antes de atribuir.
- Hay `4` llaves de evento voluntario con más de un tipo normalizado registrado.
  Esto contribuye a que `Consistency` sea como máximo 1.
- La versión previa de benchmark tenía
  `benchmark_reconciliation_failure_count=6` por redondear la tasa individual
  antes de ponderar. El SQL y el plan v3 usan la forma exacta por exposición;
  falta ejecutar y congelar esta revalidación v3.

## Estado y bloqueo actual

No existe aún un run publicado de assessment para esta candidata. Se crearon
varios directorios de trabajo fallidos bajo `output/assessments/`:

- `.above-average-team-turnover-v4-20260910.working`
- `.above-average-team-turnover-v4-20260910-r2.working`
- `.above-average-team-turnover-v4-20260910-r3.working`
- `.above-average-team-turnover-v4-20260910-r4.working`
- `.above-average-team-turnover-v4-20260910-r5.working`
- `.above-average-team-turnover-v4-20260910-r6.working`
- `.above-average-team-turnover-v4-20260910-r8.working`
- `.above-average-team-turnover-v4-20260910-r9.working`

Conservarlos como diagnóstico hasta publicar un run válido. No sobrescribir un
run publicado. Los fallos importantes ya corregidos fueron:

1. el validador rechazó un `;` dentro de texto SQL;
2. rechazó `alias.*` aunque fuera dentro de un CTE;
3. Redshift no aceptó `CONCAT` con tipos `unknown` y `varchar`;
4. el runner exigió rationale para validaciones con `max_score: 1`;
5. el validador narrativo pidió español en una regla del plan v3.

El último cambio corrige el punto 5. Se ejecutó `--print-sql` con plan v3 sin
error. Falta ejecutar de nuevo el assessment completo y revisar el resultado.

## Siguiente paso inmediato

Ejecutar este comando desde la raíz. Requiere Redshift con permiso de red y es
read-only por el guard del helper:

```powershell
& .venv\Scripts\python.exe -B `
  '.codex\skills\evaluate-attrition-variable\scripts\run_assessment.py' `
  --request 'config\above_average_team_turnover_run_request_20260910.yaml' `
  --catalog-spec 'config\above_average_team_turnover_v4_20260910.yaml' `
  --analysis-plan 'config\above_average_team_turnover_analysis_plan_v3_20260910.yaml' `
  --strict-analysis-plans `
  --continue-conservative `
  --skip-report-data `
  --query-helper 'tools\read_only_redshift_query_helper.py' `
  --run-id 'above-average-team-turnover-v4-20260910-r10' `
  --reporting-mode presentation
```

Si el servidor vuelve a cerrar la conexión durante la auditoría, no cambiar
los resultados manualmente. Reintentar una vez, revisar que no haya procesos
Python huérfanos y reducir sólo la implementación manteniendo las mismas
reglas. Si una nueva brecha material aparece, crear `analysis_plan_v4` antes
de la siguiente consulta.

## Cierre del assessment v4

Una vez que el run se publique:

1. Revisar `manifest.json`, `evidence-ledger.json`, los SQL copiados y hashes.
   Confirmar que las consultas dicen `executed_redshift_sql` y no resultados
   inventados/manuales.
2. Revisar el workbook. Debe conservar exactamente las hojas `Variable
   assessment`, `Coverage` y `Score rationale`.
3. Verificar que cada score 0/1 tenga comment y fila de rationale, y que no
   exista rationale para scores 2.
4. Mantener `Definition <=1` incluso si todas las reglas técnicas pasan: falta
   lineage oficial/reconciliación aprobada entre la fuente primaria y
   `all_terminations`.
5. Crear `docs/variables/above-average-team-turnover/README.md` en español.
   Debe explicar la definición, la proporción Unknown, la diferencia con las
   tres señales de manager existentes, la discrepancia de fuentes, límites y
   acciones. Citar rutas SQL, fecha, población, grain y métricas agregadas.

## Evidencia JSON para el deck

Después del run válido, generar un JSON congelado bajo:

`output/distribution/above-average-team-turnover-18m-evidence-20260910.json`

Debe contener sólo agregados, hashes de SQL/resultados y como mínimo:

- fecha de corte;
- conteos y porcentajes de 0, 1 y Unknown para reportes directos actuales;
- benchmark equivalente a seis meses y regla `1.4×` (no tasas por manager);
- 18 intervalos, 19 cierres, mínimos `>=4` y `>=2`;
- resultados de deduplicación, leakage, join y benchmark;
- comparación agregada con `all_terminations`;
- clasificación `presentation`, política `n >=30` y limitación no causal.

No mostrar IDs, nombres, manager IDs, rankings ni tasas individuales. Si algún
bucket 0/1/Unknown no cumple `n >=30`, suprimirlo o agruparlo de forma segura.

## Actualización pendiente del deck

Archivo principal: `tools/build_distribution_html_v2.py`.

Cambios requeridos:

1. Agregar constante para el JSON de evidencia, ruta SQL y validación estricta
   del contrato congelado.
2. Agregar función que cargue y reconcilie la evidencia (0 + 1 + Unknown =
   total; todos los buckets publicables >=30; flags/benchmark/límites pasan).
3. Agregar una función de slide en inglés visible titulada
   `Above-average team turnover` con:
   - distribución de 0, 1 y Unknown;
   - benchmark y regla `1.4×`;
   - 18 intervalos, promedio >=4, >=2 salidas;
   - caveat: contextual/associative, restricted, not manager performance.
4. Insertarla inmediatamente después de `High turnover under this person`.
   Es la nueva slide 40; `Manager leaving` y todas las posteriores pasan una
   posición.
5. Cambiar constantes e invariantes de 45 a 46 slides, agenda `38–46`, sección
   final y navegación/pills. El deck pasa de 43 a 44 candidatas visibles.
6. Incluir la nueva evidencia en `attrition-43-variable-distributions-v2-manifest.json` sin romper la ruta
   HTML existente `output/distribution/attrition-43-variable-distributions-v2.html`.
7. Validar 46 `slide-stage`, 46 pills, ubicación de la nueva slide, manifest,
   cero identidades y render en los cuatro temas.

## Pruebas finales

- Ejecutar validadores de ambos skills después de cualquier cambio en reglas,
  scripts o contratos.
- Renderizar la nueva slide en `light-soft`, `light-classic`, `dark-royal` y
  `dark-carbon`; revisar legibilidad y ausencia de clipping.
- Ejecutar pruebas existentes del deck y añadir una prueba focalizada de la
  evidencia/slide si el repositorio ya tiene ese patrón.
- Confirmar que la agenda, manifest, stages y pills reportan exactamente 46.

## Límites de interpretación que deben persistir

- La señal no demuestra causalidad ni desempeño de manager.
- El umbral 1.4 es inicial; requiere estabilidad temporal y prueba out-of-time.
- La señal no se usa operacionalmente hasta completar gobierno, privacidad,
  fairness, lineage y reconciliación de terminaciones.
- `Unknown` comunica falta de historia/exposición suficiente; no equivale a
  turnover bajo.
