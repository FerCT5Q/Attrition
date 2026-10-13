# Mercado laboral registrado

Modo `presentation`. Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta.

Pregunta: La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.

Motivo: Contrastar diferencias entre mercados laborales más allá de la región.

Tipo: `direct_field`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto mensual.

Conocimiento: valor registrado en la misma foto; no rellenar con una foto posterior. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza. SQL: `queries/audits/engineering_b_v11_labor-market_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-labor-market.json](v11-labor-market.json).

Conclusión: Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce.

Limitación: Se modela la etiqueta registrada; no se acredita una delimitación económica externa.

Acción: Agrupar categorías raras sólo con el entrenamiento y probar como B + X. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:21:03.416898+00:00. SHA256 SQL: `e0fef7cab220fb4fa8a6f279d6d856db3c6102bd37478b51605e6356840d70fe`.
