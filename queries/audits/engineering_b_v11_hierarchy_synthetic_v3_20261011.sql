/* Datos enteramente sintéticos; ninguna fila de empleados. */
WITH RECURSIVE nodes AS (
SELECT DATE '2024-01-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,2::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,2::BIGINT AS employee_id,99::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,2::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,2::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,4::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,2::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,3::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,0::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,1::BIGINT AS employee_id,0::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,2::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,4::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,5::BIGINT AS employee_id,4::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,6::BIGINT AS employee_id,5::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,7::BIGINT AS employee_id,6::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,8::BIGINT AS employee_id,7::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,9::BIGINT AS employee_id,8::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,10::BIGINT AS employee_id,9::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,11::BIGINT AS employee_id,10::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,12::BIGINT AS employee_id,11::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,13::BIGINT AS employee_id,12::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,14::BIGINT AS employee_id,13::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,15::BIGINT AS employee_id,14::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,16::BIGINT AS employee_id,15::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,17::BIGINT AS employee_id,16::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,18::BIGINT AS employee_id,17::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,19::BIGINT AS employee_id,18::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,20::BIGINT AS employee_id,19::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,21::BIGINT AS employee_id,20::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,22::BIGINT AS employee_id,21::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,23::BIGINT AS employee_id,22::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,24::BIGINT AS employee_id,23::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,25::BIGINT AS employee_id,24::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,26::BIGINT AS employee_id,25::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,27::BIGINT AS employee_id,26::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,28::BIGINT AS employee_id,27::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,29::BIGINT AS employee_id,28::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,30::BIGINT AS employee_id,29::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
),
tree(snapshot_date,employee_id,ancestor,depth) AS (
 SELECT snapshot_date,employee_id,employee_id AS ancestor,0::INTEGER AS depth
 FROM nodes WHERE manager_id IS NULL AND source_rows=1 AND manager_variants=1
 UNION ALL
 SELECT n.snapshot_date,n.employee_id,t.ancestor,t.depth+1
 FROM nodes n JOIN tree t ON t.snapshot_date=n.snapshot_date AND t.employee_id=n.manager_id
 WHERE t.depth<25 AND n.source_rows=1 AND n.manager_variants=1
),
unresolved AS (
 SELECT n.snapshot_date,n.employee_id,n.manager_id
 FROM nodes n LEFT JOIN tree t ON t.snapshot_date=n.snapshot_date AND t.employee_id=n.employee_id
 WHERE t.employee_id IS NULL
),
probe(snapshot_date,origin,current_id,next_id,depth,cycle,path) AS (
 SELECT snapshot_date,employee_id,employee_id,manager_id,0::INTEGER,0::INTEGER,
 CAST('|'||employee_id::VARCHAR||'|' AS VARCHAR(1024))
 FROM unresolved
 UNION ALL
 SELECT p.snapshot_date,p.origin,n.employee_id,n.manager_id,p.depth+1,
 CASE WHEN POSITION('|'||n.employee_id::VARCHAR||'|' IN p.path)>0 THEN 1 ELSE 0 END,
 CAST(p.path||n.employee_id::VARCHAR||'|' AS VARCHAR(1024))
 FROM probe p JOIN nodes n ON n.snapshot_date=p.snapshot_date AND n.employee_id=p.next_id
 WHERE p.depth<25 AND p.cycle=0 AND n.source_rows=1 AND n.manager_variants=1
),
probe_summary AS (
 SELECT snapshot_date,origin,MAX(cycle) AS cycle,MAX(depth) AS steps
 FROM probe GROUP BY 1,2
),
walked AS (
 SELECT n.snapshot_date,n.employee_id,n.manager_id,n.stored_level,n.eligible,n.source_rows,n.manager_variants,n.level_variants,
 t.depth,t.ancestor,COALESCE(p.cycle,0) AS cycle,
 CASE WHEN p.steps=25 AND p.cycle=0 THEN 1 ELSE 0 END AS depth_cap,
 CASE WHEN n.source_rows<>1 OR n.manager_variants<>1 THEN 1 ELSE 0 END AS ambiguous_chain
 FROM nodes n LEFT JOIN tree t ON t.snapshot_date=n.snapshot_date AND t.employee_id=n.employee_id
 LEFT JOIN probe_summary p ON p.snapshot_date=n.snapshot_date AND p.origin=n.employee_id
),
root_counts AS (
 SELECT snapshot_date,COUNT(DISTINCT ancestor) AS roots,COUNT(*) AS resolved_rows
 FROM walked WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1
),
root_sizes AS (
 SELECT snapshot_date,ancestor,COUNT(*) AS members FROM walked
 WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1,2
),
convergence AS (SELECT snapshot_date,MAX(members) AS largest_root_rows FROM root_sizes GROUP BY 1),
encoded AS (
 SELECT w.snapshot_date,w.employee_id,w.manager_id,w.stored_level,w.source_rows,w.manager_variants,w.level_variants,
 w.depth,w.ancestor,w.cycle,w.depth_cap,w.ambiguous_chain,
 COALESCE(r.roots,0) AS roots,COALESCE(r.resolved_rows,0) AS resolved_rows,
 COALESCE(c.largest_root_rows,0) AS largest_root_rows,
 CASE WHEN w.depth IS NULL OR w.cycle=1 OR w.ambiguous_chain=1 OR COALESCE(r.roots,0)<>1 THEN '(historia no confirmada)'
 WHEN w.depth<=2 THEN '0-2' WHEN w.depth>=10 THEN '10+' ELSE w.depth::VARCHAR END AS hierarchy_depth_band
 FROM walked w LEFT JOIN root_counts r ON r.snapshot_date=w.snapshot_date
 LEFT JOIN convergence c ON c.snapshot_date=w.snapshot_date WHERE w.eligible=1
)
, expected AS (
SELECT DATE '2024-01-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,2::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,3::BIGINT AS node,2 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,4::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,2::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,3::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,0::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,1::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,2::BIGINT AS node,2 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,3::BIGINT AS node,3 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,4::BIGINT AS node,4 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,5::BIGINT AS node,5 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,6::BIGINT AS node,6 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,7::BIGINT AS node,7 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,8::BIGINT AS node,8 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,9::BIGINT AS node,9 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,10::BIGINT AS node,10 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,11::BIGINT AS node,11 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,12::BIGINT AS node,12 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,13::BIGINT AS node,13 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,14::BIGINT AS node,14 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,15::BIGINT AS node,15 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,16::BIGINT AS node,16 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,17::BIGINT AS node,17 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,18::BIGINT AS node,18 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,19::BIGINT AS node,19 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,20::BIGINT AS node,20 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,21::BIGINT AS node,21 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,22::BIGINT AS node,22 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,23::BIGINT AS node,23 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,24::BIGINT AS node,24 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,25::BIGINT AS node,25 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,26::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,27::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,28::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,29::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,30::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
)
SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN COALESCE(e.depth,-1)<>COALESCE(x.expected_depth,-1) THEN 1 ELSE 0 END) AS depth_mismatches,
 SUM(CASE WHEN e.cycle<>x.expected_cycle THEN 1 ELSE 0 END) AS cycle_mismatches,
 SUM(CASE WHEN (CASE WHEN e.hierarchy_depth_band='(historia no confirmada)' THEN 0 ELSE 1 END)<>x.expected_known THEN 1 ELSE 0 END) AS known_mismatches
FROM encoded e JOIN expected x ON x.snapshot_date=e.snapshot_date AND x.node=e.employee_id;
