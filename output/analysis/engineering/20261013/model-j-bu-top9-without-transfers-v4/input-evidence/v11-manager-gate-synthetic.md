# Casos sintéticos de conocimiento y ventana de eventos

Modo `presentation`. Prueba enfocada, independiente de los agregados históricos.

Pregunta: El filtro excluye eventos aún no conocidos, conflictos de tipo ya conocidos e intervalos futuros o fuera de ventana.

Motivo: Verificar el filtro temporal exacto usado por las señales del manager.

Tipo: `derived_feature`. Población: Eventos y managers ficticios; ninguna fila HR. Grain: equipo ficticio-fecha.

Conocimiento: Fechas explícitas de conocimiento, conflicto e intervalo en cada fixture. Ventana: Dos fechas ficticias y cinco escenarios.

Método y regla: Cero diferencias entre el SQL real y el conteo independiente por fechas explícitas. SQL: `queries/audits/engineering_b_v11_manager_gate_synthetic_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-manager-gate-synthetic.json](v11-manager-gate-synthetic.json).

Conclusión: El filtro temporal se comporta como se definió en los casos probados.

Limitación: No sustituye las auditorías de exposición, suavizado y benchmark sobre el histórico completo.

Acción: Conservar los dos tipos de evidencia. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:21:46.608893+00:00. SHA256 SQL: `68e657c2c5bd218b117fca84c217a4c2e319d45b98576645ac63d477dec1e9d2`.
