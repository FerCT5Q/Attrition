"""Conciliar promedios del RSF con periodos recuperados, conservando procedencia."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import engineering_random_survival_forest as rsf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/analysis/engineering/20261008/random-survival-forest-v1'
history = rsf.base.read(OUT/'historical-results.json')
updated = rsf.summarize_periods(history['periods'])
changes = []
for name,row in updated.items():
    for metric,value in row['global'].items():
        before = history['summary'][name]['global'][metric]
        if abs(value-before)>1e-12:
            changes.append({'model':name,'metric':metric,'before':before,'after':value,'difference':value-before})
if any(c['metric']!='pr_auc' or abs(c['difference'])>1e-6 for c in changes):
    raise RuntimeError('La conciliacion requiere revisar metricas adicionales.')
revision = OUT/'revisions/before-summary-reconciliation'
revision.mkdir(parents=True,exist_ok=False)
for name in ['historical-results.json','results.json','frozen-sources.json']:
    shutil.copy2(OUT/name,revision/name)
shutil.copy2(OUT/'source/tools/engineering_random_survival_forest.py',revision/'engineering_random_survival_forest.py')
history['summary'] = updated
rsf.write(OUT/'historical-results.json',history)
results = rsf.base.read(OUT/'results.json')
results['historical']['summary'] = updated
rsf.write(OUT/'results.json',results)
sources = rsf.base.read(OUT/'frozen-sources.json')
runner = ROOT/'tools/engineering_random_survival_forest.py'
key = next(k for k in sources if Path(k).name==runner.name)
sources[key] = rsf.base.sha(runner)
shutil.copy2(runner,OUT/'source'/key)
rsf.write(OUT/'frozen-sources.json',sources)
rsf.write(OUT/'summary-reconciliation.json',{'date':datetime.now(timezone.utc),'outcome':'pass',
    'reason':'Al reanudar, el periodo se recalculo desde parametros exportados y el promedio PR-AUC conservaba la version anterior. Se recalculan los promedios desde los periodos persistidos.',
    'changes':changes,'model_parameters_changed':False,'bootstrap_intervals_changed':False,
    'bootstrap_note':'Los intervalos son de captura, log-loss y Brier; PR-AUC no forma parte de esos intervalos.',
    'original_training_source':'revisions/before-summary-reconciliation/engineering_random_survival_forest.py',
    'current_source_change':'Recalcular promedios al reanudar; no modifica ajuste, seleccion, calibracion ni predictor.'})
shutil.copy2(Path(__file__),OUT/'source/tools'/Path(__file__).name)
manifest = rsf.base.read(OUT/'manifest.json')
manifest['files'] = {str(p.relative_to(OUT)):rsf.base.sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
rsf.write(OUT/'manifest.json',manifest)
print(json.dumps({'outcome':'pass','changes':changes}))
