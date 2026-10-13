# Profundidad reconstruida de la jerarquía

Modo `presentation`. El campo precalculado empieza en 2023; la reconstrucción usa la historia real de managers que exista desde 2020, sin trasladar la jerarquía actual a fechas anteriores. Se ejecuta por año con joins acotados tras una interrupción de conexión en la consulta monolítica; ninguna métrica del intento incompleto se usa. El recorrido desde la raíz visita una sola vez cada nodo resuelto, manteniendo la foto como partición y verificando ciclos en los no resueltos.

Pregunta: ¿Cuántos enlaces separan a cada persona de la raíz técnica de su jerarquía en la misma foto?

Motivo: Contrastar la profundidad literal que motiva V11, además de la capa organizacional precalculada de C.

Tipo: `hierarchy`. Población: Engineering, Employee, Regular, activo, sin RF360; nodos de soporte: todos los workers activos de la misma foto. Grain: persona-foto mensual.

Conocimiento: Todos los enlaces y la raíz se toman exclusivamente de la misma foto. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Cero nodos duplicados o conflictivos. La raíz reconstruida tiene profundidad cero y cada enlace resuelto cumple profundidad_hijo=profundidad_manager+1 y misma raíz. Ciclos, enlaces ausentes, más de 25 capas y fechas sin una sola raíz para la población objetivo se codifican desconocidos. SQL: `queries/audits/engineering_b_v11_hierarchy_v3_2020_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-hierarchy-v3.json](v11-hierarchy-v3.json).

Conclusión: La profundidad técnica puede probarse como incorporación; no se usa la capa almacenada como sustituto.

Limitación: La referencia de CEO aprobada del análisis de agosto no permite acreditar todas las raíces históricas. La nueva feature se denomina profundidad hasta la raíz, sin afirmar semántica histórica de CEO.

Acción: Probar bandas de profundidad y conservar desconocidos; informar raíces, convergencia, ciclos y diferencias con el campo almacenado. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:04:58.121310+00:00. SHA256 SQL: `a9f34044d1dca37af781167c6210c078b82357d49fd5bcb413541bb29ad636cb`.
