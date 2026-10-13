# Historia: team_intensity

Se amplía la revisión de la entrada de D a 2020–2026.

Pregunta: ¿la reconstrucción conserva el contrato? Salidas del equipo a doce meses por cien personas-mes de exposición bajo ese manager; sólo fechas pasadas.

Motivo: probar su aporte individual sobre B.

Método y regla: `queries\audits\engineering_b_incremental_team_intensity_20261011.sql`; cero en nonpositive_denominator_violations, numerator_exposure_violations.

Observado: `{'person_snapshots': 2209264, 'snapshots': 74, 'nonpositive_denominator_violations': 0, 'numerator_exposure_violations': 0, 'future_events_excluded': 1803302, 'late_known_events_excluded': 214920, 'band_0': 1852376, 'band_gt0_lt05': 4925, 'band_05_lt1': 70894, 'band_1_plus': 281068, 'band_unknown': 1, 'maximum_person_months': 504, 'maximum_rate_per_100_person_months': Decimal('50.0000')}`.

Conclusión: **pass**.

Impacto en score: ninguno. Acción: admitir como candidata experimental.

Ejecución: 2026-10-12T02:19:45.921088+00:00. Población Engineering, Employee, Regular, activo, sin RF360; grain persona-snapshot.
