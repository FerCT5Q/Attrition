# Inicio observado de salidas para contexto del manager

Modo `presentation`. La auditoría previa encontró ausencia de O/E observable antes de 2022; se comprueba la causa antes de finalizar.

Pregunta: ¿El cero histórico representa un feed observado o un periodo anterior a su primera observación?

Motivo: Evitar que falta de historia se convierta en cero salidas.

Tipo: `derived_feature`. Población: Fuente de eventos usados para contexto agregado del manager; las asignaciones finales son Engineering. Grain: evento deduplicado; resultado agregado global.

Conocimiento: Primera foto con tipo Voluntary y fecha efectiva ya ocurrida. Ventana: Contexto desde 2018-10-26 hasta 2026-09-07.

Método y regla: Obtener fechas extremas y recuentos de historia tardía; el inicio observado se usará para codificar historia incompleta, sin asumir ceros. SQL: `queries/audits/engineering_b_v11_manager_feed_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-manager-feed.json](v11-manager-feed.json).

Conclusión: Existe evidencia agregada para decidir el inicio admisible de las ventanas.

Limitación: Primera observación no acredita que un evento no existiera antes en otros sistemas.

Acción: Exigir una ventana completa posterior al inicio observado del feed. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:12:41.377007+00:00. SHA256 SQL: `dd6ace7e52dd100bb0964d03fe11104d6b43b9f45e470757060068d297903da2`.
