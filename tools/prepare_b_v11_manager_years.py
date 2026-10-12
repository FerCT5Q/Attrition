"""Divide la auditoría de manager por año sin cambiar el lookback por foto."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

for name in ['manager6','manager18']:
    old=ROOT/f'config/b_playbook_v11_contracts/{name}.json'
    target=old.with_stem(name+'-annual')
    if target.exists():
        raise RuntimeError('La revisión anual ya existe.')
    contract=json.loads(old.read_text(encoding='utf-8'))
    text=(ROOT/contract['query']).read_text(encoding='utf-8')
    queries=[]
    for year in range(2020,2027):
        first='2020-07-26' if year==2020 else f'{year}-01-01'
        last='2026-09-07' if year==2026 else f'{year}-12-31'
        query=ROOT/f'queries/audits/engineering_b_v11_{name}_{year}_20261011.sql'
        query.write_text(text.replace("DATE '2020-07-26'",f"DATE '{first}'").replace("DATE '2026-09-07'",f"DATE '{last}'"),encoding='utf-8')
        queries.append(query.relative_to(ROOT).as_posix())
    contract.update(id=name+'-annual',query=queries[0],queries=queries)
    contract['history']+=' La ejecución conserva agregados por año; cada foto mantiene sus intervalos previos completos.'
    target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Auditorías de manager divididas por año, con contexto histórico completo.')
