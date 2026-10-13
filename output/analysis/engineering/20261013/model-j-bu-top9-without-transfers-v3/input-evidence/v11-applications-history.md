# Historia verificable de solicitudes del playbook

Modo `presentation`. Se revalida applications, la fuente real del V11, junto con la vista alternativa.

Pregunta: Hay eventos y marcas temporales utilizables antes del corte y el feed alcanza la ventana actual.

Motivo: Determinar si el conteo de seis meses puede probarse sin convertir falta de feed en cero.

Tipo: `derived_feature`. Población: Eventos cand_applied=1; enlace agregado a quienes fueron Engineering elegibles en 2020–2026. Grain: fuente de eventos.

Conocimiento: Fecha de aplicación y fechas técnicas observadas; ninguna de ellas por sí sola demuestra completitud o fecha del enlace.. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Debe haber eventos antes del corte y en la última ventana de seis meses, además de registros con fechas técnicas anteriores. Son condiciones necesarias; si pasan todavía falta validar completitud y enlace temporal. SQL: `queries/audits/engineering_b_v11_applications_history_20261011.sql`.

Resultado: **fail**. Métricas completas en [v11-applications-history.json](v11-applications-history.json).

Conclusión: Se requiere resolver missing_current_window.

Limitación: Las fechas técnicas no prueban primera disponibilidad y la ausencia de solicitud no equivale a cero.

Acción: Si no se cumplen las condiciones necesarias, excluir del experimento temporal con la brecha concreta.. Impacto en score: ninguno.

Ejecución: 2026-10-12T15:16:15.306878+00:00. SHA256 SQL: `08fd5ef373291cf3290dc51053265fc0784452ea7093428f8937757e28119dd3`.
