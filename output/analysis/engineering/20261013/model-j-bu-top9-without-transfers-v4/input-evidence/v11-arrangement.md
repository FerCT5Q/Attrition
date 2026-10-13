# Modalidad de trabajo del V11

Modo `presentation`. Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta.

Pregunta: La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.

Motivo: Probar la agrupación de tres modalidades que se revisó en el playbook.

Tipo: `grouped_mapping`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto mensual.

Conocimiento: valor registrado en la misma foto; no rellenar con una foto posterior. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza. SQL: `queries/audits/engineering_b_v11_arrangement_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-arrangement.json](v11-arrangement.json).

Conclusión: Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce.

Limitación: La etiqueta de la foto no demuestra asistencia física ni resuelve las discrepancias de fechas de vigencia. No se extraen motivos sensibles.

Acción: Agrupar categorías raras sólo con el entrenamiento y probar como B + X. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:21:24.182426+00:00. SHA256 SQL: `0f5ff6638b68a29d549a397e01a899b9b77f2e55ba9bd29331d2be5fd5cfff91`.
