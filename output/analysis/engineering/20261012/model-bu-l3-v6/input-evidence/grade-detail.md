# grade-detail: entrada del experimento B incremental

Modo `presentation`. Se revisa el código original de las fotos de 2020-2026; no se reetiqueta retrospectivamente.

Pregunta: ¿se sostiene esta entrada? Código completo de grado almacenado en cada foto; no es un importe ni una traducción a nivel.

Motivo: Probar si el detalle del grado aporta más que el nivel y el prefijo R/T.

Tipo semántico: `direct_field`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_grade_detail_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `grade-detail.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: No se afirma que todos los grados sean ordinales o comparables entre países.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:07:47.102012+00:00. SHA256 del resultado: `496c1aa16dae2922607232ec00ea1cf3cb8a6d40e082d75cecc81937a8f8412d`.
