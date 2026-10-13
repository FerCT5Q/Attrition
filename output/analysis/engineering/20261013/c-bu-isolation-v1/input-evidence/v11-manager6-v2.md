# Contexto del manager a seis intervalos

Modo `presentation`. Se reutiliza la definición V11, agregando la puerta explícita de conocimiento del evento para cada fecha. Historia insuficiente sigue desconocida. La primera foto con eventos Voluntary observados es 2022-10-23 (auditoría manager-feed); se exige además una ventana completa posterior a esa fecha.

Pregunta: Los eventos se asignan al equipo del inicio del intervalo y sólo se cuentan una vez conocidos en t.

Motivo: Contrastar las definiciones históricas del V11 manteniendo todos los términos de B.

Tipo: `derived_feature`. Población: Employee, Regular, activo y sin RF360 para exposición y benchmark; Engineering para la asignación final. Grain: persona-foto; historia agregada del manager actual.

Conocimiento: Exposición en inicio del intervalo; primera observación del evento <= t, sin conflicto de tipo conocido en t. Ventana: 2020-07-26 a 2026-09-07, con 21 meses anteriores de contexto.

Método y regla: Seis intervalos globales, estratos con al menos 30 exposiciones o fallback global, prior de 60 exposiciones y reconciliación O/E por identidad algebraica independiente. Cero duplicados, contradicciones, eventos futuros y diferencias de fórmula. No convertir ausencia del feed anterior a 2022-10-23 en cero salidas; exigir seis o dieciocho intervalos posteriores completos, respectivamente. SQL: `queries/audits/engineering_b_v11_manager6_v2_2020_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-manager6-v2.json](v11-manager6-v2.json).

Conclusión: La representación respeta el contrato temporal y puede probarse como B + X.

Limitación: Describe exposición histórica, no causalidad ni evaluación del manager. Se excluyen eventos sin exposición inicial única y tipos conflictivos; no se publican identidades.

Acción: Probar cada representación por separado y mantener estados desconocidos. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:18:26.653368+00:00. SHA256 SQL: `f285b5d330fe0bb6e35697c5c2830b79999eaf4d2a1fbd59d22ebc3a5f70b75e`.
