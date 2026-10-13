# team-pay-v2: entrada del experimento B incremental

Modo `presentation`. Cada conjunto comparable se reconstruye en su propia foto; no se usan sueldos actuales para el pasado.

Pregunta: ¿se sostiene esta entrada? Posición relativa en pago FTE almacenado con mismo manager, país, grado y moneda (mínimo cinco); y proporción de grupos del manager con max/min >=1.10 (mínimo dos por grupo).

Motivo: Probar contexto relativo de compensación sin extraer importes ni identificar equipos.

Tipo semántico: `derived_feature`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_team_pay_20261011_v2.sql`. Regla: cero en duplicate_keys, contradictory_cells, rank_bound_violations, rank_midpoint_violations, spread_violations, small_group_position_violations; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `team-pay-v2.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: Banda experimental de valores almacenados; no acredita equidad salarial ni lineage de normalización FTE. No comparable es una categoría separada.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:17:46.964869+00:00. SHA256 del resultado: `7b649e0ef0eb13a85244cc63458f2f90413d82c073c714d77b5610e8bad541f2`.
