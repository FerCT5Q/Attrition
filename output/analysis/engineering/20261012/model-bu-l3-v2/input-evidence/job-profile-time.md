# job-profile-time: entrada del experimento B incremental

Modo `presentation`. Se explicita el inicio de observación; no se sustituye una fecha ausente por antigüedad total.

Pregunta: ¿se sostiene esta entrada? Meses desde el máximo entre la fecha registrada de entrada al perfil y service_date; sólo fechas presentes y no futuras.

Motivo: Distinguir permanencia en perfil de permanencia en nivel y antigüedad total.

Tipo semántico: `derived_feature`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_job_profile_time_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells, invalid_dates_encoded_as_known, band_recalculation_mismatches; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `job-profile-time.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: service_date mantiene la convención de episodio de B. La fórmula operativa no demuestra lineage del campo fuente.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:08:07.899414+00:00. SHA256 del resultado: `d8cd9758e712b4ecacab87281e7364d007305c25ee780ae220182711c56f0b67`.
