"""Recorrido de jerarquía por duplicación de saltos, sin SQL recursivo ilimitado."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def query():
    sql="""/* Jerarquía de la misma foto. Seis duplicaciones alcanzan 63 enlaces.
Se admiten como feature hasta 25; el resto conserva estado desconocido.
IDs y caminos sólo dentro de SQL; nunca son columnas de salida. */
WITH nodes AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date,employee_id,
        MAX(manager_employee_id::BIGINT) AS manager_id,
        MAX(worker_supervisory_organization_level_from_top) AS stored_level,
        MAX(CASE WHEN worker_type='Employee' AND employee_type='Regular' AND is_rf360_yes_no=0
                  AND TRIM(eng_or_noneng)='Engineering' THEN 1 ELSE 0 END) AS eligible,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(manager_employee_id::VARCHAR,'<NULL>')) AS manager_variants,
        COUNT(DISTINCT COALESCE(worker_supervisory_organization_level_from_top::VARCHAR,'<NULL>')) AS level_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
 AND active_status=1 AND employee_id IS NOT NULL GROUP BY 1,2
),
p0 AS (
 SELECT snapshot_date,employee_id,employee_id AS ancestor,manager_id AS next_id,
        0::INTEGER AS depth,0::INTEGER AS cycle,
        CASE WHEN source_rows<>1 OR manager_variants<>1 THEN 1 ELSE 0 END::INTEGER AS broken,
        CAST('|'||employee_id::VARCHAR||'|' AS VARCHAR(4096)) AS path
 FROM nodes
)"""
    for i in range(1,7):
        previous=f'p{i-1}'
        active='a.next_id IS NOT NULL AND a.broken=0 AND a.cycle=0'
        joined=f'{active} AND b.employee_id IS NOT NULL'
        merged="a.path||SUBSTRING(b.path,2)"
        sql+=f""",
p{i} AS (
 SELECT a.snapshot_date,a.employee_id,
 CASE WHEN {joined} THEN b.ancestor ELSE a.ancestor END AS ancestor,
 CASE WHEN {joined} THEN b.next_id WHEN {active} THEN NULL ELSE a.next_id END::BIGINT AS next_id,
 CASE WHEN {joined} THEN a.depth+b.depth+1 ELSE a.depth END::INTEGER AS depth,
 CASE WHEN a.cycle=1 OR ({joined} AND (b.cycle=1 OR POSITION('|'||a.employee_id::VARCHAR||'|' IN SUBSTRING({merged},2))>0)) THEN 1 ELSE 0 END::INTEGER AS cycle,
 CASE WHEN a.broken=1 OR ({active} AND (b.employee_id IS NULL OR b.broken=1)) THEN 1 ELSE 0 END::INTEGER AS broken,
 CAST(CASE WHEN {joined} THEN {merged} ELSE a.path END AS VARCHAR(4096)) AS path
 FROM {previous} a LEFT JOIN {previous} b ON b.snapshot_date=a.snapshot_date AND b.employee_id=a.next_id
)"""
    sql+=""",
root_counts AS (
 SELECT p.snapshot_date,COUNT(DISTINCT p.ancestor) AS roots,
        COUNT(*) AS resolved_rows
 FROM p6 p JOIN nodes n ON n.snapshot_date=p.snapshot_date AND n.employee_id=p.employee_id
 WHERE n.eligible=1 AND p.broken=0 AND p.cycle=0 AND p.next_id IS NULL AND p.depth<=25
 GROUP BY 1
),
root_sizes AS (
 SELECT p.snapshot_date,p.ancestor,COUNT(*) AS members
 FROM p6 p JOIN nodes n ON n.snapshot_date=p.snapshot_date AND n.employee_id=p.employee_id
 WHERE n.eligible=1 AND p.broken=0 AND p.cycle=0 AND p.next_id IS NULL AND p.depth<=25 GROUP BY 1,2
),
convergence AS (SELECT snapshot_date,MAX(members) AS largest_root_rows FROM root_sizes GROUP BY 1),
encoded AS (
 SELECT p.snapshot_date,p.employee_id,p.ancestor,p.next_id,p.depth,p.cycle,p.broken,
        n.manager_id,n.stored_level,n.source_rows,n.manager_variants,n.level_variants,
        COALESCE(r.roots,0) AS roots,COALESCE(r.resolved_rows,0) AS resolved_rows,
        COALESCE(c.largest_root_rows,0) AS largest_root_rows,
        CASE WHEN p.broken=1 OR p.cycle=1 OR p.next_id IS NOT NULL OR p.depth>25 OR COALESCE(r.roots,0)<>1 THEN '(historia no confirmada)'
             WHEN p.depth<=2 THEN '0-2'
             WHEN p.depth>=10 THEN '10+'
             ELSE p.depth::VARCHAR END AS hierarchy_depth_band
 FROM p6 p JOIN nodes n ON n.snapshot_date=p.snapshot_date AND n.employee_id=p.employee_id
 LEFT JOIN root_counts r ON r.snapshot_date=p.snapshot_date
 LEFT JOIN convergence c ON c.snapshot_date=p.snapshot_date
 WHERE n.eligible=1
)
"""
    return sql


def main():
    source=ROOT/'queries/profiles/engineering_b_v11_hierarchy_person_month_20261011.sql'
    audit=ROOT/'queries/audits/engineering_b_v11_hierarchy_20261011.sql'
    if source.exists() or audit.exists():
        raise RuntimeError('La preparación ya existe.')
    prefix=query()
    source.write_text(prefix+"-- MODEL_OUTPUT\nSELECT snapshot_date,MD5(employee_id::VARCHAR||'__RUN_SALT__') AS person_key,hierarchy_depth_band FROM encoded\n",encoding='utf-8')
    suffix=""",
node_issues AS (
 SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
        SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_nodes,
        SUM(CASE WHEN manager_variants<>1 OR level_variants<>1 THEN 1 ELSE 0 END) AS contradictory_nodes
 FROM nodes GROUP BY 1
),
annual AS (
 SELECT EXTRACT(year FROM e.snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT e.employee_id) AS employee_count,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' THEN 1 ELSE 0 END) AS observable_rows,
 SUM(CASE WHEN e.broken=1 THEN 1 ELSE 0 END) AS unresolved_rows,
 SUM(e.cycle) AS cycle_rows,
 SUM(CASE WHEN e.next_id IS NOT NULL AND e.cycle=0 AND e.broken=0 THEN 1 ELSE 0 END) AS depth_cap_rows,
 MIN(e.roots) AS minimum_roots,MAX(e.roots) AS maximum_roots,
 MIN(100.0*e.largest_root_rows/NULLIF(e.resolved_rows,0)) AS minimum_convergence_percent,
 MAX(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' THEN e.depth END) AS maximum_depth,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' AND e.stored_level IS NOT NULL THEN 1 ELSE 0 END) AS stored_comparable_rows,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' AND e.stored_level<>e.depth+1 THEN 1 ELSE 0 END) AS stored_depth_difference_rows,
 SUM(CASE WHEN e.broken=0 AND e.cycle=0 AND e.next_id IS NULL AND
       ((e.manager_id IS NULL AND e.depth<>0) OR (e.manager_id IS NOT NULL AND
        (m.employee_id IS NULL OR m.broken<>0 OR m.cycle<>0 OR m.next_id IS NOT NULL OR e.depth<>m.depth+1 OR e.ancestor<>m.ancestor))) THEN 1 ELSE 0 END) AS edge_reconciliation_violations,
 SUM(CASE WHEN e.hierarchy_depth_band<>'(historia no confirmada)' AND (e.cycle<>0 OR e.broken<>0 OR e.next_id IS NOT NULL OR e.depth>25 OR e.roots<>1) THEN 1 ELSE 0 END) AS invalid_known_rows
 FROM encoded e LEFT JOIN p6 m ON m.snapshot_date=e.snapshot_date AND m.employee_id=e.manager_id
 GROUP BY 1
)
SELECT a.year,a.person_snapshots,a.employee_count,a.observable_rows,a.unresolved_rows,a.cycle_rows,a.depth_cap_rows,
 a.minimum_roots,a.maximum_roots,a.minimum_convergence_percent,a.maximum_depth,a.stored_comparable_rows,
 a.stored_depth_difference_rows,a.edge_reconciliation_violations,a.invalid_known_rows,
 n.duplicate_nodes,n.contradictory_nodes
FROM annual a JOIN node_issues n ON n.year=a.year WHERE a.employee_count>=30 ORDER BY 1;
"""
    audit.write_text(prefix.replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07')+suffix,encoding='utf-8')
    print('SQL de jerarquía y auditoría preparados; sin IDs ni rutas en resultados.')


if __name__=='__main__':
    main()
