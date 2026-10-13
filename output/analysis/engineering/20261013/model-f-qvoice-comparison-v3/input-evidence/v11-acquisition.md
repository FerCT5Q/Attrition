# Adquisición registrada, con detalle

Modo `presentation`. Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta.

Pregunta: La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.

Motivo: Contrastar adquisiciones concretas sin perder B ni usar valores posteriores a la foto.

Tipo: `direct_field`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto mensual.

Conocimiento: valor registrado en la misma foto; no rellenar con una foto posterior. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza. SQL: `queries/audits/engineering_b_v11_acquisition_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-acquisition.json](v11-acquisition.json).

Conclusión: Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce.

Limitación: Sin registro no equivale a contratación orgánica. No se consolidan aliases sin evidencia.

Acción: Agrupar categorías raras sólo con el entrenamiento y probar como B + X. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:22:34.129001+00:00. SHA256 SQL: `1c49a2914c433e012909b91670b94f23f9e98b83fc7bf0d12f75c14b98cc8952`.
