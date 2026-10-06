/*
  Determina la granularidad sin exponer claves.
  Se reporta la distribución de filas por requisición, no las requisiciones.
*/
WITH per_req AS (
    SELECT req_id, COUNT(*) AS rows_per_req
    FROM hrda.requisitions
    WHERE req_id IS NOT NULL
    GROUP BY req_id
), raw_bands AS (
    SELECT
        CASE
            WHEN rows_per_req = 1 THEN '1 fila por req'
            WHEN rows_per_req BETWEEN 2 AND 4 THEN '2-4 filas por req'
            WHEN rows_per_req BETWEEN 5 AND 9 THEN '5-9 filas por req'
            ELSE '10+ filas por req'
        END AS grain_band,
        COUNT(*) AS requisition_count,
        SUM(rows_per_req) AS source_rows
    FROM per_req
    GROUP BY 1
), view_per_req AS (
    SELECT req_id, COUNT(*) AS rows_per_req
    FROM hrda.requisitions_vw
    WHERE req_id IS NOT NULL
    GROUP BY req_id
), view_bands AS (
    SELECT
        CASE
            WHEN rows_per_req = 1 THEN '1 fila por req'
            ELSE '2+ filas por req'
        END AS grain_band,
        COUNT(*) AS requisition_count,
        SUM(rows_per_req) AS source_rows
    FROM view_per_req
    GROUP BY 1
)
SELECT
    'requisitions' AS source_table,
    grain_band,
    requisition_count,
    source_rows
FROM raw_bands
UNION ALL
SELECT
    'requisitions_vw' AS source_table,
    grain_band,
    requisition_count,
    source_rows
FROM view_bands
ORDER BY source_table, grain_band;
