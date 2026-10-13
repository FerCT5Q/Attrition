# Modalidad de trabajo del V11

Modo `presentation`. Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta. La primera implementación no identificaba el rótulo completo; esta revisión usa la correspondencia explícita de tools/build_distribution_html_v7.py y la contrasta con un patrón independiente.

Pregunta: La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.

Motivo: Probar la agrupación de tres modalidades que se revisó en el playbook.

Tipo: `grouped_mapping`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto mensual.

Conocimiento: valor registrado en la misma foto; no rellenar con una foto posterior. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza. Se exige además presencia del grupo de remoto temporal y cero diferencias frente al patrón independiente. SQL: `queries/audits/engineering_b_v11_arrangement_20261011_v2.sql`.

Resultado: **pass**. Métricas completas en [v11-arrangement-v2.json](v11-arrangement-v2.json).

Conclusión: Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce.

Limitación: La etiqueta de la foto no demuestra asistencia física ni resuelve las discrepancias de fechas de vigencia. No se extraen motivos sensibles.

Acción: Agrupar categorías raras sólo con el entrenamiento y probar como B + X. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:22:12.824920+00:00. SHA256 SQL: `d98b6a2ea24d8e5418bf73b81c021d7672fd8695f788723f6d0417cd9c8d9b97`.
