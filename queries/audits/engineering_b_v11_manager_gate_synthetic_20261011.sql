/* Sólo eventos sintéticos. Se prueba el filtro del SQL real. */
WITH targets AS (
 SELECT DATE '2024-04-23' AS snapshot_date,100 AS seq
 UNION ALL SELECT DATE '2024-05-23',101
), attributions AS (
SELECT 1 AS employee_id,98 AS seq,10 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2024-02-05' AS term_date,DATE '2024-04-23' AS known_date,NULL::DATE AS conflicting_known_date
UNION ALL
SELECT 2 AS employee_id,99 AS seq,10 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2024-03-03' AS term_date,DATE '2024-05-23' AS known_date,NULL::DATE AS conflicting_known_date
UNION ALL
SELECT 3 AS employee_id,98 AS seq,20 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2024-02-05' AS term_date,DATE '2024-04-23' AS known_date,DATE '2024-04-23' AS conflicting_known_date
UNION ALL
SELECT 4 AS employee_id,98 AS seq,30 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2024-02-05' AS term_date,DATE '2024-04-23' AS known_date,DATE '2024-05-23' AS conflicting_known_date
UNION ALL
SELECT 5 AS employee_id,102 AS seq,40 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2024-06-01' AS term_date,DATE '2024-04-23' AS known_date,NULL::DATE AS conflicting_known_date
UNION ALL
SELECT 6 AS employee_id,75 AS seq,50 AS manager_id,'fixture'::VARCHAR AS stratum,DATE '2022-03-03' AS term_date,DATE '2024-04-23' AS known_date,NULL::DATE AS conflicting_known_date
),
known_events AS (
 SELECT t.snapshot_date,t.seq AS target_seq,a.employee_id,a.term_date,a.known_date,
 a.seq,a.manager_id,a.stratum
 FROM targets t JOIN attributions a ON a.seq>=t.seq-18 AND a.seq<t.seq AND a.known_date<=t.snapshot_date
 AND (a.conflicting_known_date IS NULL OR a.conflicting_known_date>t.snapshot_date)
),
observed AS (
 SELECT snapshot_date,manager_id,COUNT(*) AS exits18,
 SUM(CASE WHEN seq>=target_seq-6 THEN 1 ELSE 0 END) AS exits6,
 MAX(known_date) AS latest_known_date
 FROM known_events GROUP BY 1,2
),
expected AS (
SELECT DATE '2024-04-23' AS snapshot_date,10 AS manager_id,1 AS expected_count
UNION ALL
SELECT DATE '2024-04-23' AS snapshot_date,20 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-04-23' AS snapshot_date,30 AS manager_id,1 AS expected_count
UNION ALL
SELECT DATE '2024-04-23' AS snapshot_date,40 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-04-23' AS snapshot_date,50 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-05-23' AS snapshot_date,10 AS manager_id,2 AS expected_count
UNION ALL
SELECT DATE '2024-05-23' AS snapshot_date,20 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-05-23' AS snapshot_date,30 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-05-23' AS snapshot_date,40 AS manager_id,0 AS expected_count
UNION ALL
SELECT DATE '2024-05-23' AS snapshot_date,50 AS manager_id,0 AS expected_count
)
SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN COALESCE(o.exits6,0)<>e.expected_count THEN 1 ELSE 0 END) AS knowledge_window_mismatches,
 SUM(CASE WHEN o.latest_known_date>e.snapshot_date THEN 1 ELSE 0 END) AS future_event_violations
FROM expected e LEFT JOIN observed o ON o.snapshot_date=e.snapshot_date AND o.manager_id=e.manager_id;
