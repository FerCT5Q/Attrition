# Historia: manager_recency

Se amplía la revisión de la entrada de D a 2020–2026.

Pregunta: ¿la reconstrucción conserva el contrato? Cambios de manager observados a tres y seis meses; fechas efectivas y conocidas no posteriores a cada foto.

Motivo: probar su aporte individual sobre B.

Método y regla: `queries\audits\engineering_b_incremental_manager_recency_20261011.sql`; cero en monotonicity_violations, negative_count_violations.

Observado: `{'person_snapshots': 2209264, 'snapshots': 74, 'monotonicity_violations': 0, 'negative_count_violations': 0, 'future_events_excluded': 1531785, 'late_known_events_excluded': 0, 'covered_person_snapshots': 557977, 'covered_percent': Decimal('25.2562'), 'maximum_3m': 3, 'maximum_6m': 4, 'maximum_12m': 6}`.

Conclusión: **pass**.

Impacto en score: ninguno. Acción: admitir como candidata experimental.

Ejecución: 2026-10-12T02:18:40.791036+00:00. Población Engineering, Employee, Regular, activo, sin RF360; grain persona-snapshot.
