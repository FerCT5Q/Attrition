# Historia: team_recency

Se amplía la revisión de la entrada de D a 2020–2026.

Pregunta: ¿la reconstrucción conserva el contrato? Salidas voluntarias del equipo a tres y seis meses y fecha de última salida; mismo manager previo al evento.

Motivo: probar su aporte individual sobre B.

Método y regla: `queries\audits\engineering_b_incremental_team_recency_20261011.sql`; cero en monotonicity_violations, last_event_consistency_violations, band_consistency_violations.

Observado: `{'person_snapshots': 2209264, 'snapshots': 74, 'monotonicity_violations': 0, 'last_event_consistency_violations': 0, 'band_consistency_violations': 0, 'future_events_excluded': 1803302, 'late_known_events_excluded': 214920, 'covered_person_snapshots': 356887, 'covered_percent': Decimal('16.1541'), 'maximum_3m': 6, 'maximum_6m': 9, 'maximum_12m': 10}`.

Conclusión: **pass**.

Impacto en score: ninguno. Acción: admitir como candidata experimental.

Ejecución: 2026-10-12T02:18:45.986506+00:00. Población Engineering, Employee, Regular, activo, sin RF360; grain persona-snapshot.
