# work-location: entrada del experimento B incremental

Modo `presentation`. Se revisan las fotos de 2020-2026; faltantes son categorías explícitas.

Pregunta: ¿se sostiene esta entrada? País laboral y sitio registrado, con el país incluido en la llave del sitio.

Motivo: Distinguir contexto de mercado y centro laboral dentro de una región.

Tipo semántico: `direct_field`. Conocimiento: snapshot t.

Población: Employee, Regular, activo, Engineering, excluye RF360. Periodo: 2020-07-26 a 2026-09-07.

Método: `queries/audits/engineering_b_incremental_work_location_20261011.sql`. Regla: cero en duplicate_keys, contradictory_cells; siete años agregados.

Resultado: **pass**. Métricas anuales completas en `work-location.json`.

Conclusión y acción: habilitar la representación experimental.

Límite: El sitio registrado no acredita presencia física. No se usan domicilios ni distancias residenciales.

Impacto en score: ninguno.

Ejecución: 2026-10-12T02:07:35.061537+00:00. SHA256 del resultado: `581116948f6223cff34068180ee15e2b98aacd5d5b0a8e1d0e8e08e355cb6634`.
