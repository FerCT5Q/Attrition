# Metadata de aplicaciones internas

Modo `presentation`. El playbook tiene preparación en applications; se contrasta con la vista inspeccionada previamente.

Pregunta: Identificar las fuentes y fechas del conteo V11, sin equiparar aplicaciones con una vista distinta.

Motivo: Determinar si puede reconstruirse B más solicitudes internas.

Tipo: `derived_feature`. Población: Metadata de hrda.applications y job_applications_vw; sin filas de empleados. Grain: tabla-columna.

Conocimiento: Metadata actual; no demuestra fecha histórica de los eventos.. Ventana: Cortes previstos 2020-07-26 a 2026-09-07.

Método y regla: La metadata debe identificar las columnas para formular la comprobación temporal; sin asignar score. SQL: `queries/audits/engineering_b_v11_applications_metadata_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-applications-metadata.json](v11-applications-metadata.json).

Conclusión: Fuentes disponibles para revisión temporal específica.

Limitación: Los nombres de timestamps no prueban conocimiento ni completitud del feed.

Acción: Revisar agregados de fechas y enlace antes de habilitar una candidata.. Impacto en score: ninguno.

Ejecución: 2026-10-12T15:14:43.663625+00:00. SHA256 SQL: `da32413cdb73929825aa79f4a823b4c273ad07bdbd4f251e4e773c7752959619`.
