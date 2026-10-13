# Reconciliación de precisión del benchmark de 18 intervalos

Modo `presentation`. La comparación de suma de eventos/exposición con promedio ponderado no cumplió la tolerancia de 1e-8.

Pregunta: ¿La discrepancia proviene del redondeo de pesos decimales o de un error en el benchmark principal?

Motivo: Resolver la auditoría fallida sin relajar la tolerancia arbitrariamente.

Tipo: `derived_feature`. Población: Managers con historia elegible; resultados agregados, sin identidades. Grain: foto agregada.

Conocimiento: Historia conocida al 23-ago-2026. Ventana: Dieciocho intervalos previos al 23-ago-2026.

Método y regla: Medir las dos fórmulas independientes con pesos de exposición y pesos en doble precisión, además del redondeo de pesos original. SQL: `queries/audits/engineering_b_v11_manager_benchmark_precision_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-manager-benchmark-precision.json](v11-manager-benchmark-precision.json).

Conclusión: Se dispone de magnitudes para identificar la causa de la discrepancia.

Limitación: Este diagnóstico no habilita por sí solo el uso del indicador; debe cerrar la reconciliación.

Acción: Corregir la implementación que no conserve precisión y repetir la regla original. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:30:34.189211+00:00. SHA256 SQL: `8fb678dec5d6b39b884b3c9665351780fad105814994ecc015534c16b58ff2ba`.
