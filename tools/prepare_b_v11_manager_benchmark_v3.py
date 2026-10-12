"""Conserva doble precisión en el control del benchmark; no cambia el score."""
from pathlib import Path
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence'
old=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v2.sql'
source=old.with_name(old.stem.replace('_v2','_v3')+'.sql')
path=ROOT/'config/b_playbook_v11_contracts/manager18-v3.json'
if source.exists() or path.exists():
    raise RuntimeError('La revisión ya existe.')
before='SUM(rate18*(exposure18/18.0))/NULLIF(SUM(exposure18/18.0),0)'
after='SUM(rate18*(exposure18::DOUBLE PRECISION/18))/NULLIF(SUM(exposure18::DOUBLE PRECISION/18),0)'
text=old.read_text(encoding='utf-8')
assert text.count(before)==1
source.write_text(text.replace(before,after),encoding='utf-8')
contract=json.loads((ROOT/'config/b_playbook_v11_contracts/manager18-v2.json').read_text(encoding='utf-8'))
queries=[]
for year in range(2020,2027):
    prior=ROOT/f'queries/audits/engineering_b_v11_manager18_v2_{year}_20261011.sql'
    if year<2024:
        # No había ventana elegible en estos años. Se preserva fecha y resultado
        # original de la consulta inalterada, sin declarar una nueva ejecución.
        query=prior
        cached=OUT/'v11-manager18-v2-parts'/(prior.stem+'.json')
        destination=OUT/'v11-manager18-v3-parts'/cached.name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(cached,destination)
    else:
        query=prior.with_name(prior.stem.replace('_v2_','_v3_')+'.sql')
        sql=prior.read_text(encoding='utf-8')
        assert sql.count(before)==1
        query.write_text(sql.replace(before,after),encoding='utf-8')
    queries.append(query.relative_to(ROOT).as_posix())
contract.update(id='manager18-v3',query=queries[0],queries=queries,source_query=source.relative_to(ROOT).as_posix())
contract['history']+=' El benchmark principal reconcilió con pesos de exposición; el control perdía precisión al dividir por 18.0 como decimal. Se corrige sólo el control a doble precisión y se mantiene la tolerancia de 1e-8.'
contract['supersedes']='manager18-v2: el benchmark principal no cambia; el control independiente debe conservar precisión.'
path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Control del benchmark corregido; cálculo principal y features sin cambios.')
