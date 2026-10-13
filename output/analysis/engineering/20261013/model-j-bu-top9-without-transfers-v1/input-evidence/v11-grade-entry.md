# Entrada observada al grado actual y pay track

Modo `presentation`. La preparación V11 reconstruía la entrada al grado en una foto. Se extiende a cada foto, conservando gaps mayores de 45 días, falta de grado e inicios de episodio como historia desconocida.

Pregunta: ¿Puede reconstruirse la última entrada al grado dentro del episodio vigente sin utilizar promociones futuras?

Motivo: Distinguir promoción confirmada, cambio sin promoción registrada e historia no observable; contrastar tiempo desde entrada y track completo.

Tipo: `derived_feature`. Población: Employee, Regular, activo, Engineering, sin RF360 en cada foto objetivo; historia previa de esas personas sólo dentro del episodio vigente. Grain: persona-foto mensual.

Conocimiento: Cambio observado hasta t; promoción efectiva en la ventana de entrada y observada en una foto no posterior a t. Ventana: 2020-07-26 a 2026-09-07; historia anterior para detectar la entrada.

Método y regla: Cero duplicación/contradicción, entradas fuera del episodio o con gap mayor de 45 días, confirmaciones futuras y diferencias de bandas frente a aritmética independiente de meses. Track sólo en códigos letra+dígitos. SQL: `queries/audits/engineering_b_v11_grade_entry_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-grade-entry.json](v11-grade-entry.json).

Conclusión: La entrada observada y sus límites temporales pueden probarse como incorporaciones a B.

Limitación: No acredita el primer ingreso histórico al grado si falta historia. Ausencia de promoción registrada no equivale a promoción imposible; compensation_grade_old no entra a la fórmula.

Acción: Probar las representaciones por separado y mantener desconocido donde no hay transición observada. Impacto en score: ninguno.

Ejecución: 2026-10-12T03:26:06.676011+00:00. SHA256 SQL: `5067726701cc827e43207ac33807d24c88242b1a9ea47c5567dd25b98968ffaa`.
