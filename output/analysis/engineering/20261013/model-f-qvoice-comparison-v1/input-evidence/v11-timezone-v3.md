# Proximidad registrada y diferencia horaria del manager

Modo `presentation`. V11 aporta una preparación geográfica descriptiva; se incorpora su proxy, con conflictos de zona explícitos y sin asumir vigencia histórica de direcciones. v1 y v2 se cancelaron por coste. v3 procesa el mapping público y offsets en RAM; la consulta valida la unión y se complementa con la reconciliación de la transformación y el control DST de 1036 casos.

Pregunta: La relación usa empleado y manager de la misma foto y respeta los offsets históricos IANA.

Motivo: Probar las representaciones geográficas del V11 sobre B completo.

Tipo: `derived_feature`. Población: Employee, Regular, activo, Engineering, sin RF360. Grain: persona-foto.

Conocimiento: Ubicación de la foto; geografía pública estática 2026, usada como proxy retrospectivo declarado.. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Cero duplicados o uniones fuera de la foto; reconciliación posterior de categorías en RAM, sin guardar hashes de ubicaciones asociados a personas. SQL: `queries/audits/engineering_b_v11_timezone_20261011_v3.sql`.

Resultado: **pass**. Métricas completas en [v11-timezone-v3.json](v11-timezone-v3.json).

Conclusión: El proxy puede probarse con su limitación geográfica explícita.

Limitación: Sitio igual no prueba presencia física; catálogo 2026 sin vigencia histórica de direcciones. No cambia score.

Acción: Probar las dos representaciones y conservar missingness. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:47:04.164082+00:00. SHA256 SQL: `78c57912ba64795e9c9135083d77b1701ad0d1e76bc672f4376a01d25aeba8fa`.
