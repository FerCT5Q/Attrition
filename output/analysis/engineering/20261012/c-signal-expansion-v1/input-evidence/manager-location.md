# manager-location: entrada del experimento B incremental

Modo `presentation`. Join histórico de las fotos de 2020-2026; manager no localizado se mantiene desconocido.

Pregunta: ¿se sostiene esta entrada? Relación de ubicación registrada entre persona y manager activo de la misma foto: sitio, ciudad, país o país distinto.

Motivo: Probar contexto de coordinación distribuida.

Tipo semántico: `derived_feature`. Conocimiento: snapshot t; unión sólo a manager de t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_manager_location_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells, ambiguous_manager_keys, relation_violations, join_count_difference; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `manager-location.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: Coincidir en etiquetas no prueba trabajo presencial, misma zona horaria ni proximidad residencial.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:09:42.279907+00:00. SHA256 del resultado: `dd3566a1b3bcccfc7b2c6a312e309893ece0251897d9df41b747b857b14b9271`.
