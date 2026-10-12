# Talent index: búsqueda de fuente histórica fechada

Modo `presentation`. La fuente real del V11 es master_talent_index; las revisiones previas sólo describen disponibilidad actual.

Pregunta: Se inspeccionan fuentes y columnas de Talent index sin inferir vigencia desde timestamps técnicos.

Motivo: Comprobar si puede reconstruirse el valor disponible antes de cada predicción.

Tipo: `precomputed_metric`. Población: Metadata de tablas HRDA con talent en el nombre; objetivo Engineering 2020–2026. Grain: tabla-columna; sin datos de personas.

Conocimiento: Requiere fecha de negocio o snapshot histórico; los timestamps técnicos no la acreditan. Ventana: 26-jul-2020 a 7-sep-2026.

Método y regla: La consulta debe devolver metadata; pass sólo acredita inspección, no historia ni selección de la variable. SQL: `queries/audits/engineering_b_v11_talent_metadata_20261012.sql`.

Resultado: **pass**. Métricas completas en [v11-talent-metadata.json](v11-talent-metadata.json).

Conclusión: Metadata disponible para revisar temporalidad.

Limitación: Fórmula, elegibilidad y fecha de publicación deben verificarse separadamente.

Acción: Si sólo existen timestamps técnicos, conservar la limitación temporal sin cambiar scores.. Impacto en score: ninguno.

Ejecución: 2026-10-12T15:23:09.395020+00:00. SHA256 SQL: `96e2cd68e2c0bbd9580c00a7db7b7110fc97e61ea226658f75a1bd060370a8a3`.
