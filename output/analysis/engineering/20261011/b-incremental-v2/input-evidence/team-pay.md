# team-pay: entrada del experimento B incremental

Modo `presentation`. Cada conjunto comparable se reconstruye en su propia foto; no se usan sueldos actuales para el pasado.

Pregunta: ¿se sostiene esta entrada? Posición relativa en pago FTE almacenado con mismo manager, país, grado y moneda (mínimo cinco); y proporción de grupos del manager con max/min >=1.10 (mínimo dos por grupo).

Motivo: Probar contexto relativo de compensación sin extraer importes ni identificar equipos.

Tipo semántico: `derived_feature`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_team_pay_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells, rank_bound_violations, rank_midpoint_violations, spread_violations, small_group_position_violations; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `team-pay.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: Banda experimental de valores almacenados; no acredita equidad salarial ni lineage de normalización FTE. No comparable es una categoría separada.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:10:23.050800+00:00. SHA256 del resultado: `109f4553a02e756dc28c15e4d25cc44410ad9ed671b7ea49c2252102da50cdf3`.
