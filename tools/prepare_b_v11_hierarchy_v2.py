"""Jerarquía con 25 joins acotados; ejecución agregada por año."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def prefix():
    sql="""/* Misma foto; hasta 25 enlaces. Sin SQL recursivo ni caminos exportados. */
WITH nodes AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date,employee_id,
 MAX(manager_employee_id::BIGINT) AS manager_id,
 MAX(worker_supervisory_organization_level_from_top) AS stored_level,
 MAX(CASE WHEN worker_type='Employee' AND employee_type='Regular' AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' THEN 1 ELSE 0 END) AS eligible,
 COUNT(*) AS source_rows,
 COUNT(DISTINCT COALESCE(manager_employee_id::VARCHAR,'<NULL>')) AS manager_variants,
 COUNT(DISTINCT COALESCE(worker_supervisory_organization_level_from_top::VARCHAR,'<NULL>')) AS level_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
 AND active_status=1 AND employee_id IS NOT NULL GROUP BY 1,2
), walked AS (
 SELECT n0.snapshot_date,n0.employee_id,n0.manager_id,n0.stored_level,n0.eligible,
 n0.source_rows,n0.manager_variants,n0.level_variants,
 CASE
"""
    for i in range(26):
        sql+=f' WHEN n{i}.employee_id IS NOT NULL AND n{i}.manager_id IS NULL THEN {i}\n'
    sql+=' END AS depth,\n CASE\n'
    for i in range(26):
        sql+=f' WHEN n{i}.employee_id IS NOT NULL AND n{i}.manager_id IS NULL THEN n{i}.employee_id\n'
    sql+=' END AS ancestor,\n CASE WHEN '
    sql+=' OR '.join(f"n{i}.manager_id IN ({','.join(f'n{j}.employee_id' for j in range(i+1))})" for i in range(26))
    sql+=' THEN 1 ELSE 0 END AS cycle,\n CASE WHEN n25.manager_id IS NOT NULL THEN 1 ELSE 0 END AS depth_cap,\n'
    sql+=' CASE WHEN '+' OR '.join(f'(n{i}.source_rows<>1 OR n{i}.manager_variants<>1)' for i in range(26))+' THEN 1 ELSE 0 END AS ambiguous_chain\n'
    sql+=' FROM nodes n0\n'
    for i in range(1,26):
        seen=','.join(f'n{j}.employee_id' for j in range(i))
        sql+=f' LEFT JOIN nodes n{i} ON n{i}.snapshot_date=n0.snapshot_date AND n{i}.employee_id=n{i-1}.manager_id AND n{i}.employee_id NOT IN ({seen})\n'
    sql+='''), root_counts AS (
 SELECT snapshot_date,COUNT(DISTINCT ancestor) AS roots,COUNT(*) AS resolved_rows
 FROM walked WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1
), root_sizes AS (
 SELECT snapshot_date,ancestor,COUNT(*) AS members FROM walked
 WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1,2
), convergence AS (SELECT snapshot_date,MAX(members) AS largest_root_rows FROM root_sizes GROUP BY 1),
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
'''
    return sql


SUFFIX='''
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
'''


def main():
    source=ROOT/'queries/profiles/engineering_b_v11_hierarchy_person_month_20261011_v2.sql'
    path=ROOT/'config/b_playbook_v11_contracts/hierarchy-v2.json'
    if source.exists() or path.exists():
        raise RuntimeError('La revisión ya existe.')
    sql=prefix()
    source.write_text(sql+"-- MODEL_OUTPUT\nSELECT snapshot_date,MD5(employee_id::VARCHAR||'__RUN_SALT__') AS person_key,hierarchy_depth_band FROM encoded\n",encoding='utf-8')
    queries=[]
    for year in range(2020,2027):
        first='2020-07-26' if year==2020 else f'{year}-01-01'
        last='2026-09-07' if year==2026 else f'{year}-12-31'
        audit=ROOT/f'queries/audits/engineering_b_v11_hierarchy_v2_{year}_20261011.sql'
        audit.write_text(sql.replace('__PERIOD_START__',first).replace('__PERIOD_END__',last)+SUFFIX,encoding='utf-8')
        queries.append(audit.relative_to(ROOT).as_posix())
    contract=json.loads((ROOT/'config/b_playbook_v11_contracts/hierarchy.json').read_text(encoding='utf-8'))
    contract.update(id='hierarchy-v2',queries=queries,query=queries[0],source_query=source.relative_to(ROOT).as_posix())
    contract['history']+=' Se ejecuta por año con joins acotados tras una interrupción de conexión en la consulta monolítica; ninguna métrica del intento incompleto se usa.'
    path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Jerarquía v2 preparada por año.')


if __name__=='__main__':
    main()
