# Tiempo en rol almacenado y bandas del V11

Modo `presentation`. V11 muestra time_in_role separado del perfil. Se revalida la historia de Engineering.

Pregunta: El campo de la misma foto tiene grain único y bandas V11 reproducibles.

Motivo: Probar su aporte a B con representación distinta del tiempo calculado en perfil.

Tipo: `precomputed_metric`. Población: Engineering, Employee, Regular, activo y sin RF360. Grain: persona-foto; salida agregada anual.

Conocimiento: Valor almacenado en la propia foto; no se reconstruye ni completa historia ausente. Ventana: 26-jul-2020 a 7-sep-2026.

Método y regla: Cero duplicados, conflictos, bandas diferentes o negativos/nulos codificados como observados. La selección exige además seis fotos observables de entrenamiento. SQL: `queries/audits/engineering_b_v11_stored_role_20261012.sql`.

Resultado: **pass**. Métricas completas en [v11-stored-role.json](v11-stored-role.json).

Conclusión: Bandas verificadas para el valor almacenado; revisar historia mínima por corte.

Limitación: El recálculo de bandas no acredita fórmula, unidad ni semántica de resets del campo precalculado.

Acción: Incorporar como valor almacenado explícito, sin cambiar scores ni equipararlo a tiempo en nivel.. Impacto en score: ninguno.

Ejecución: 2026-10-12T15:25:01.197898+00:00. SHA256 SQL: `4f0e2af7a53b2d148c22c9b173f113f5fddc36e0350123c498ae17cb48be39dc`.
