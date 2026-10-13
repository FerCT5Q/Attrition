# Ciudad laboral

Modo `presentation`. Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta.

Pregunta: La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.

Motivo: Distinguir ciudades dentro de países o códigos de oficina amplios.

Tipo: `direct_field`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto mensual.

Conocimiento: valor registrado en la misma foto; no rellenar con una foto posterior. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza. SQL: `queries/audits/engineering_b_v11_city_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-city.json](v11-city.json).

Conclusión: Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce.

Limitación: La ciudad registrada es laboral; no representa domicilio ni movilidad real.

Acción: Agrupar categorías raras sólo con el entrenamiento y probar como B + X. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:20:36.938860+00:00. SHA256 SQL: `fb9487e2878ef51a443d6aed19f58104feb5927be967a686bfb53219a1ef6b7f`.
