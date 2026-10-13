# Offsets históricos contrastados con zoneinfo

Modo `presentation`. V11 aporta una preparación geográfica descriptiva; se incorpora su proxy, con conflictos de zona explícitos y sin asumir vigencia histórica de direcciones.

Pregunta: La relación usa empleado y manager de la misma foto y respeta los offsets históricos IANA.

Motivo: Probar las representaciones geográficas del V11 sobre B completo.

Tipo: `external_source`. Población: Fechas y zonas de catálogo público; sin filas de RH. Grain: zona-fecha.

Conocimiento: Ubicación de la foto; geografía pública estática 2026, usada como proxy retrospectivo declarado.. Ventana: 2020-07-26 a 2026-09-07.

Método y regla: Cero diferencias en minutos entre Redshift y zoneinfo en enero, marzo, julio y noviembre de 2020–2026. SQL: `queries/audits/engineering_b_v11_timezone_dst_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-timezone-dst.json](v11-timezone-dst.json).

Conclusión: El proxy puede probarse con su limitación geográfica explícita.

Limitación: Sitio igual no prueba presencia física; catálogo 2026 sin vigencia histórica de direcciones. No cambia score.

Acción: Probar las dos representaciones y conservar missingness. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:40:28.863710+00:00. SHA256 SQL: `53aa003af533779ab0f6ba79156c2fc450f8719f1c34bc71e10a41d516fde5c9`.
