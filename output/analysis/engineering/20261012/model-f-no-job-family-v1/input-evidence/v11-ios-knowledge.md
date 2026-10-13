# Fecha de conocimiento de motivos IOS

Modo `presentation`. V11 dispone de una preparación descriptiva por fecha efectiva. Antes de reutilizarla para predicción se comprueba el historial de carga y modificación.

Pregunta: ¿Hay eventos con motivo y fecha de conocimiento verificable para las ventanas de modelado?

Motivo: Preparar seis indicadores de movilidad previa como B + X, sin adelantar eventos retrospectivos.

Tipo: `derived_feature`. Población: Eventos de personas con alguna foto Employee, Regular, activa, Engineering y sin RF360 en el periodo. Grain: Evento deduplicado por persona, fecha efectiva y motivo; salida agregada por año.

Conocimiento: Para un evento utilizable se exige fecha efectiva, modificación y carga no posteriores a t; date_initiated sólo acredita el inicio del proceso. Ventana: Fotos 2020-07-26 a 2026-09-07; eventos efectivos hasta 2026-09-07.

Método y regla: La consulta debe recuperar eventos de los motivos V11 sin contradicción de inicio. La posibilidad de entrenamiento depende además de eventos conocidos antes de los cortes; se decide al revisar los agregados. SQL: `queries/audits/engineering_b_v11_ios_knowledge_20261011.sql`.

Resultado: **fail**. Métricas completas en [v11-ios-knowledge.json](v11-ios-knowledge.json).

Conclusión: Se requiere resolver conflicting_initiation.

Limitación: La fecha efectiva o el inicio de un proceso no prueban cuándo se conoció su resolución final. Una tabla vigente puede haber reescrito eventos antiguos.

Acción: Revisar las fechas agregadas y conservar desconocido cuando no se demuestre historia disponible. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:23:53.605365+00:00. SHA256 SQL: `057772e6b400ac0079f7812230718d7750ec4b8de72a7f91146b7d77e6514456`.
