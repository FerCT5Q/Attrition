/* Recorrido por foto desde las raíces; nodos no resueltos se auditan
por separado. Límite observado de recursión del servidor: 50,000,000 filas.
Cada árbol se aísla por snapshot_date. Ningún identificador sale de SQL. */
WITH RECURSIVE nodes AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date,employee_id,
 MAX(manager_employee_id::BIGINT) AS manager_id,
 MAX(worker_supervisory_organization_level_from_top) AS stored_level,
 MAX(CASE WHEN worker_type='Employee' AND employee_type='Regular' AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' THEN 1 ELSE 0 END) AS eligible,
 COUNT(*) AS source_rows,
 COUNT(DISTINCT COALESCE(manager_employee_id::VARCHAR,'<NULL>')) AS manager_variants,
 COUNT(DISTINCT COALESCE(worker_supervisory_organization_level_from_top::VARCHAR,'<NULL>')) AS level_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'
 AND active_status=1 AND employee_id IS NOT NULL GROUP BY 1,2
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

, node_issues AS (
 SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_nodes,
 SUM(CASE WHEN manager_variants<>1 OR level_variants<>1 THEN 1 ELSE 0 END) AS contradictory_nodes
 FROM nodes GROUP BY 1
), annual AS (
 SELECT EXTRACT(year FROM e.snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT e.employee_id) AS employee_count,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' THEN 1 ELSE 0 END) AS observable_rows,
 SUM(CASE WHEN e.depth IS NULL AND e.cycle=0 AND e.depth_cap=0 THEN 1 ELSE 0 END) AS unresolved_rows,
 SUM(e.cycle) AS cycle_rows,SUM(e.depth_cap) AS depth_cap_rows,
 MIN(e.roots) AS minimum_roots,MAX(e.roots) AS maximum_roots,
 MIN(100.0*e.largest_root_rows/NULLIF(e.resolved_rows,0)) AS minimum_convergence_percent,
 MAX(e.depth) AS maximum_depth,
 SUM(CASE WHEN e.depth IS NOT NULL AND e.stored_level IS NOT NULL THEN 1 ELSE 0 END) AS stored_comparable_rows,
 SUM(CASE WHEN e.depth IS NOT NULL AND e.stored_level<>e.depth+1 THEN 1 ELSE 0 END) AS stored_depth_difference_rows,
 SUM(CASE WHEN e.depth IS NOT NULL AND e.cycle=0 AND e.ambiguous_chain=0 AND
 ((e.manager_id IS NULL AND e.depth<>0) OR (e.manager_id IS NOT NULL AND
 (m.employee_id IS NULL OR m.depth IS NULL OR m.cycle<>0 OR m.ambiguous_chain<>0 OR e.depth<>m.depth+1 OR e.ancestor<>m.ancestor))) THEN 1 ELSE 0 END) AS edge_reconciliation_violations,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' AND (e.depth IS NULL OR e.cycle<>0 OR e.ambiguous_chain<>0 OR e.depth>25 OR e.roots<>1) THEN 1 ELSE 0 END) AS invalid_known_rows
 FROM encoded e LEFT JOIN walked m ON m.snapshot_date=e.snapshot_date AND m.employee_id=e.manager_id GROUP BY 1
)
SELECT a.year,a.person_snapshots,a.employee_count,a.observable_rows,a.unresolved_rows,a.cycle_rows,a.depth_cap_rows,
 a.minimum_roots,a.maximum_roots,a.minimum_convergence_percent,a.maximum_depth,a.stored_comparable_rows,
 a.stored_depth_difference_rows,a.edge_reconciliation_violations,a.invalid_known_rows,n.duplicate_nodes,n.contradictory_nodes
FROM annual a JOIN node_issues n ON n.year=a.year WHERE a.employee_count>=30 ORDER BY 1;
