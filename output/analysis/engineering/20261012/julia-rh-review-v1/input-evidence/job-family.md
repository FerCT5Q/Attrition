# job-family: entrada del experimento B incremental

Modo `presentation`. Campos en la misma tabla mensual de B; se comprueba todo 2020-2026 antes del modelo.

Pregunta: ¿se sostiene esta entrada? Familia y grupo registrados en cada foto; conservar el mapping de la fecha, sin aplicar el mapping actual al pasado.

Motivo: Contexto ocupacional adicional al nivel y antigüedad de B.

Tipo semántico: `grouped_mapping`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_job_family_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells, ambiguous_mappings, null_misalignment; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `job-family.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: Coherencia de mapping no prueba su definición oficial. Las etiquetas raras se agrupan usando sólo entrenamiento.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:05:37.605896+00:00. SHA256 del resultado: `a94f57719b1e344e20ccef9516e0d0c930ff2134b24182de8a9e8f1e2811dc0e`.
