# Rotación del equipo sobre benchmark a dieciocho intervalos

Modo `presentation`. Se reutiliza la definición V11, agregando la puerta explícita de conocimiento del evento para cada fecha. Historia insuficiente sigue desconocida. La primera foto con eventos Voluntary observados es 2022-10-23 (auditoría manager-feed); se exige además una ventana completa posterior a esa fecha.

Pregunta: Los eventos se asignan al equipo del inicio del intervalo y sólo se cuentan una vez conocidos en t.

Motivo: Contrastar las definiciones históricas del V11 manteniendo todos los términos de B.

Tipo: `derived_feature`. Población: Employee, Regular, activo y sin RF360 para exposición y benchmark; Engineering para la asignación final. Grain: persona-foto; historia agregada del manager actual.

Conocimiento: Exposición en inicio del intervalo; primera observación del evento <= t, sin conflicto de tipo conocido en t. Ventana: 2020-07-26 a 2026-09-07, con 21 meses anteriores de contexto.

Método y regla: Dieciocho intervalos contiguos, equipo medio >=4, al menos dos salidas; tasa >=1.3 veces benchmark ponderado, reconciliado con suma de tasas por pesos. Cero duplicados, contradicciones, eventos futuros y diferencias de fórmula. No convertir ausencia del feed anterior a 2022-10-23 en cero salidas; exigir seis o dieciocho intervalos posteriores completos, respectivamente. SQL: `queries/audits/engineering_b_v11_manager18_v2_2020_20261011.sql`.

Resultado: **fail**. Métricas completas en [v11-manager18-v2.json](v11-manager18-v2.json).

Conclusión: Se requiere resolver independent_formula_mismatches.

Limitación: Describe exposición histórica, no causalidad ni evaluación del manager. Se excluyen eventos sin exposición inicial única y tipos conflictivos; no se publican identidades.

Acción: Probar cada representación por separado y mantener estados desconocidos. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:27:45.267262+00:00. SHA256 SQL: `abd08eddacaf40fae48af747a1f4e950f28b18ec25d0356b2e3f28c600a89cd8`.
