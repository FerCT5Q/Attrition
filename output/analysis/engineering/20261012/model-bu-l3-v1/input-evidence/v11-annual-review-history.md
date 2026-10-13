# Annual Review: ciclos y conocimiento histórico

Modo `presentation`. El V11 usa AR25 por track. No se equipara al flag is_promo del historial mensual.

Pregunta: Hay registros de ciclo utilizables antes del corte, sin conflictos de flag o grade.

Motivo: Determinar si promotion_yes_no puede probarse junto con B sin adelantar una revisión anual.

Tipo: `derived_feature`. Población: Ciclos de Annual Review y enlace agregado a Engineering elegible en 2020–2026. Grain: persona-ciclo, agregado por ciclo con al menos 30 personas.

Conocimiento: Fecha oficial de publicación o versión histórica requerida; timestamps técnicos son sólo condición necesaria. Ventana: 26-jul-2020 a 7-sep-2026.

Método y regla: Cero conflictos, duplicados o flags inválidos y algún registro con carga y modificación anteriores al corte; después sería necesario validar publicación y unión as-of. SQL: `queries/audits/engineering_b_v11_annual_review_history_20261012.sql`.

Resultado: **pass**. Métricas completas en [v11-annual-review-history.json](v11-annual-review-history.json).

Conclusión: Se cumple el requisito técnico necesario, pendiente de publicación y enlace temporal.

Limitación: El año del ciclo y la fecha de carga no demuestran cuándo se comunicó o entró en vigor la promoción.

Acción: Conservar promoción de B y entrada al grado; sólo habilitar Annual Review con conocimiento histórico acreditado.. Impacto en score: ninguno.

Ejecución: 2026-10-12T15:20:53.688965+00:00. SHA256 SQL: `e0475221a4abd7d04996ad4260589a4529d14d78395c4e8ee0c6ab80422647e9`.
