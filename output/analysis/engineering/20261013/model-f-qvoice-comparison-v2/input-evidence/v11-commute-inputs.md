# Componentes históricos de la distancia estimada

Modo `presentation`. La preparación descriptiva V11 se adapta a la historia mensual; oficinas ambiguas producen un proxy mínimo declarado.

Pregunta: La modalidad y ubicación pertenecen a la foto y no tienen duplicados o contradicciones.

Motivo: Probar la distancia del V11 sobre B, usando sólo bandas.

Tipo: `external_source`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto.

Conocimiento: Ubicación y modalidad en t; catálogos estáticos de 2026 sin vigencia histórica demostrada.. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Cero duplicados y conflictos de componentes; recálculo geográfico posterior con diferencia máxima de 0.0001 km y población anual reconciliada. SQL: `queries/audits/engineering_b_v11_commute_inputs_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-commute-inputs.json](v11-commute-inputs.json).

Conclusión: Componentes habilitados para la reconciliación en RAM.

Limitación: No acredita residencia histórica exacta, traslado real ni vigencia histórica del catálogo externo.

Acción: Transformar hashes en bandas sólo en RAM, conservar desconocidos y documentar cobertura. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:52:10.808517+00:00. SHA256 SQL: `430fa41e0142f90ca8e39025c5cf491d9b0b78cfbd27f7a16045dd0b3e18e8f4`.
