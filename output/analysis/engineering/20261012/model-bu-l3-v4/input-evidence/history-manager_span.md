# Historia: manager_span

Se amplía la revisión de la entrada de D a 2020–2026.

Pregunta: ¿la reconstrucción conserva el contrato? Tamaño reconstruido del equipo del manager actual en la misma foto; no es el campo de reportes del empleado.

Motivo: probar su aporte individual sobre B.

Método y regla: `queries\audits\engineering_b_incremental_manager_span_20261011.sql`; cero en negative_span_violations.

Observado: `{'person_snapshots': 2209264, 'snapshots': 74, 'manager_known_rows': 2209263, 'reconstructed_rows': 2209263, 'negative_span_violations': 0, 'stored_field_rows': 2209264, 'exact_matches': 63076, 'mean_absolute_difference': Decimal('5'), 'band_1_4': 716467, 'band_5_9': 1217230, 'band_10_14': 218731, 'band_15_19': 39037, 'band_20_29': 15012, 'band_30_plus': 2786, 'maximum_reconstructed_span': 74}`.

Conclusión: **pass**.

Impacto en score: ninguno. Acción: admitir como candidata experimental.

Ejecución: 2026-10-12T02:18:51.697604+00:00. Población Engineering, Employee, Regular, activo, sin RF360; grain persona-snapshot.
