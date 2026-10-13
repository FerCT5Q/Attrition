# Reconciliación de compensación antes de entrenar

La auditoría inicial no detectó violaciones de rango, pero devolvió cero grupos
de dispersión pese a encontrar posiciones relativas comparables. Ese resultado
se trató como una brecha; el `pass` de las comprobaciones iniciales no habilita
por sí solo esta entrada. La evidencia activa es `team-pay-v2.json`.

En enero-agosto de 2026 el recálculo directo independiente encontró 353077
filas completas, 87531 grupos de al menos dos integrantes y 5653 de al menos
cinco. El SQL con agregaciones anidadas y `COUNT(*)` en `peer_stats` devolvía
cero al filtrar el tamaño; no se atribuye una causa del motor sin demostrarla.

Se sustituyó el conteo por `COUNT(DISTINCT employee_id)` en el grain ya
deduplicado y por `COUNT(min_pay)` para los grupos de importes positivos.
La revisión reconcilia exactamente los 87531 y 5653 grupos del recálculo
independiente y encuentra 257539 coincidencias de dispersión en Engineering.
Sólo se adoptará la revisión después de repetir la auditoría anual completa.

Consultas: `engineering_b_incremental_team_pay_followup_20261011.sql`,
`engineering_b_incremental_team_pay_independent_20261011.sql` y
`engineering_b_incremental_team_pay_distinct_20261011.sql`, guardadas en
`queries/audits/`. Sus resultados y fechas están en los JSON homónimos de
esta carpeta. Se conservan las consultas y los resultados iniciales.

Población: Engineering, Employee, Regular, activo, sin RF360; los pares de
compensación pueden incluir compañeros regulares de otras áreas con el mismo
manager, país, grado y moneda. No se exportaron importes ni identificadores.
Impacto en score: ninguno.
