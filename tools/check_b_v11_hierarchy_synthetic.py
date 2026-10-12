"""Casos sintéticos: compara SQL con un recorrido independiente en Python."""
from pathlib import Path
import json

from prepare_b_v11_hierarchy_v3 import prefix

ROOT=Path(__file__).resolve().parents[1]


def walk(graph,origin):
    seen=set()
    node=origin
    depth=0
    while node in graph and depth<=25:
        if node in seen:
            return None,1
        seen.add(node)
        parent=graph[node]
        if parent is None:
            return depth,0
        if parent in seen:
            return None,1
        node=parent
        depth+=1
    return None,0


def main():
    query=ROOT/'queries/audits/engineering_b_v11_hierarchy_synthetic_v3_20261011.sql'
    target=ROOT/'config/b_playbook_v11_contracts/hierarchy-synthetic-v3.json'
    if query.exists() or target.exists():
        raise RuntimeError('El fixture ya existe.')
    graphs=[{1:None,2:1,3:2},{1:None,2:99,3:2},{1:None,2:2,3:2},
            {1:None,2:3,3:2,4:3},{1:None,2:None,3:1},
            {i:None if i==0 else i-1 for i in range(31)}]
    source,expected=[],[]
    for month,graph in enumerate(graphs,1):
        date=f'2024-{month:02d}-01'
        rooted=[i for i in graph if graph[i] is None]
        for node,parent in graph.items():
            depth,cycle=walk(graph,node)
            known=int(depth is not None and len(rooted)==1)
            source.append(f"SELECT DATE '{date}' AS snapshot_date,{node}::BIGINT AS employee_id,"+
                 ('NULL::BIGINT' if parent is None else f'{parent}::BIGINT')+' AS manager_id,'+
                 'NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants')
            expected.append(f"SELECT DATE '{date}' AS snapshot_date,{node}::BIGINT AS node,"+
                 ('NULL::INTEGER' if depth is None else str(depth))+f' AS expected_depth,{cycle} AS expected_cycle,{known} AS expected_known')
    sql='/* Datos enteramente sintéticos; ninguna fila de empleados. */\nWITH RECURSIVE nodes AS (\n'+'\nUNION ALL\n'.join(source)
    sql+='\n),\ntree'+prefix().split('),\ntree',1)[1]
    sql+=', expected AS (\n'+'\nUNION ALL\n'.join(expected)+'\n)\n'
    sql+="""SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN COALESCE(e.depth,-1)<>COALESCE(x.expected_depth,-1) THEN 1 ELSE 0 END) AS depth_mismatches,
 SUM(CASE WHEN e.cycle<>x.expected_cycle THEN 1 ELSE 0 END) AS cycle_mismatches,
 SUM(CASE WHEN (CASE WHEN e.hierarchy_depth_band='(historia no confirmada)' THEN 0 ELSE 1 END)<>x.expected_known THEN 1 ELSE 0 END) AS known_mismatches
FROM encoded e JOIN expected x ON x.snapshot_date=e.snapshot_date AND x.node=e.employee_id;
"""
    query.write_text(sql,encoding='utf-8')
    contract={'schema_version':4,'id':'hierarchy-synthetic-v3','title':'Casos límite sintéticos de jerarquía',
       'claim':'El SQL distingue árbol válido, manager ausente, auto-ciclo, ciclo de dos nodos, varias raíces y profundidad mayor de 25.',
       'use':'Verificar la reconstrucción con un oráculo independiente antes de modelar.',
       'semantic_type':'hierarchy','population':'Grafos ficticios; no son datos de empleados',
       'grain':'nodo sintético','known_at':'Cada grafo se evalúa por separado en su fecha ficticia',
       'window':'Seis escenarios sintéticos','history':'Prueba de límites de la implementación, no evidencia HR.',
       'query':query.relative_to(ROOT).as_posix(),'zero_fields':['depth_mismatches','cycle_mismatches','known_mismatches'],
       'positive_fields':['synthetic_cases'],'expected_rows':1,
       'acceptance_rule':'Cero diferencias frente al recorrido independiente en Python.',
       'conclusion_if_pass':'Los casos límite probados se comportan como se definió',
       'limitation':'Los fixtures no sustituyen la auditoría agregada de datos históricos.',
       'action':'Conservar ambas evidencias con hashes'}
    target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(expected)} casos sintéticos preparados; sólo se consultarán conteos de diferencias.')


if __name__=='__main__':
    main()
