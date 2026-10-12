"""Aplica la primera observación de eventos verificada; evita ceros sin feed."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
old_source=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011.sql'
source=old_source.with_name(old_source.stem+'_v2.sql')
if source.exists():
    raise RuntimeError('La revisión ya existe.')
sql=old_source.read_text(encoding='utf-8')
first_seq="(SELECT seq FROM calendar WHERE snapshot_date=DATE '2022-10-23')"
sql=sql.replace('e.expected6,p.rate AS prior_rate,p.intervals AS global_intervals6,',
    'e.expected6,p.rate AS prior_rate,p.intervals AS global_intervals6,\n'+
    f' CASE WHEN h.seq>={first_seq}+6 THEN 1 ELSE 0 END AS feed_complete6,\n'+
    f' CASE WHEN h.seq>={first_seq}+18 THEN 1 ELSE 0 END AS feed_complete18,')
sql=sql.replace('CASE WHEN h.exposure6>0 AND p.intervals=6',f'CASE WHEN h.seq>={first_seq}+6 AND h.exposure6>0 AND p.intervals=6')
sql=sql.replace('CASE WHEN h.intervals18=18',f'CASE WHEN h.seq>={first_seq}+18 AND h.intervals18=18')
sql=sql.replace('v.global_intervals6,v.oe6,v.latest_known_date,','v.global_intervals6,v.oe6,v.latest_known_date,v.feed_complete6,v.feed_complete18,')
sql=sql.replace('CASE WHEN v.exposure6 IS NULL OR v.exposure6<=0 OR v.global_intervals6<>6',
                'CASE WHEN v.exposure6 IS NULL OR v.exposure6<=0 OR v.global_intervals6<>6 OR v.feed_complete6<>1')
source.write_text(sql,encoding='utf-8')
prefix=sql.split('-- MODEL_OUTPUT')[0]
for name in ['manager6','manager18']:
    path=ROOT/f'config/b_playbook_v11_contracts/{name}-v2.json'
    contract=json.loads((ROOT/f'config/b_playbook_v11_contracts/{name}.json').read_text(encoding='utf-8'))
    old_audit=(ROOT/contract['query']).read_text(encoding='utf-8')
    suffix='\n, integrity AS ('+old_audit.split('\n, integrity AS (',1)[1]
    if name=='manager6':
        suffix=suffix.replace("e.prior_rate<=0)","e.prior_rate<=0 OR e.feed_complete6<>1)")
        suffix=suffix.replace('AS independent_formula_mismatches\n',"AS independent_formula_mismatches,\n SUM(CASE WHEN e.feed_complete6<>1 AND e.manager_team_exits6_v11<>'(historia no confirmada)' THEN 1 ELSE 0 END) AS zero_without_feed\n")
        contract['zero_fields'].append('zero_without_feed')
    else:
        suffix=suffix.replace('e.exposure18<=0)', 'e.exposure18<=0 OR e.feed_complete18<>1)')
    queries=[]
    for year in range(2020,2027):
        first='2020-07-26' if year==2020 else f'{year}-01-01'
        last='2026-09-07' if year==2026 else f'{year}-12-31'
        query=ROOT/f'queries/audits/engineering_b_v11_{name}_v2_{year}_20261011.sql'
        query.write_text(prefix.replace('__PERIOD_START__',first).replace('__PERIOD_END__',last)+suffix,encoding='utf-8')
        queries.append(query.relative_to(ROOT).as_posix())
    contract.update(id=name+'-v2',query=queries[0],queries=queries,source_query=source.relative_to(ROOT).as_posix())
    contract['history']+=' La primera foto con eventos Voluntary observados es 2022-10-23 (auditoría manager-feed); se exige además una ventana completa posterior a esa fecha.'
    contract['acceptance_rule']+=' No convertir ausencia del feed anterior a 2022-10-23 en cero salidas; exigir seis o dieciocho intervalos posteriores completos, respectivamente.'
    contract['supersedes']=name+': la revisión anterior no distinguía explícitamente el inicio de observación del feed.'
    path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Contexto del manager v2: ventanas completas posteriores al inicio observado del feed.')
