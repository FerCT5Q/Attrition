"""Comprueba artefactos agregados de C y ejecuta las pruebas autorizadas del modelo."""
from pathlib import Path
import json
import subprocess
import shutil
import sys
import numpy as np
import pandas as pd

from engineering_model_c import read,write,sha,decision,Design,Model,ROOT


def main():
    config=read(ROOT/'config/engineering_model_c_20261008_fast.json');out=ROOT/config['output']
    result=read(out/'results.json');frozen=read(out/'frozen-config.json');checks=[]

    def check(name,condition):
        checks.append({'check':name,'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)

    check('configuración congelada intacta',config==frozen)
    for relative,digest in read(out/'frozen-sources.json').items():
        check('hash '+relative,sha(ROOT/relative)==digest)
        target=out/'source'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
        check('copia de fuente '+relative,sha(target)==digest)
    optimizer=read(out/'frozen-optimizer.json')
    check('optimizador congelado intacto',sha(ROOT/optimizer['script'])==optimizer['sha256'])
    for relative in [optimizer['script'],'tools/qvoice_model_validation.py','tools/build_engineering_model_c_report.py',
                     'tools/verify_engineering_model_c.py','tests/test_engineering_model_c.py',
                     'tools/finalize_engineering_model_c_evaluation.py',
                     'config/engineering_model_c_input_contracts_20261008.json']:
        target=out/'source'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
        check('fuente auxiliar '+relative,sha(target)==sha(ROOT/relative))
    inventory=read(ROOT/'config/engineering_model_c_inventory_20261008.json')
    check('43 conceptos y dos adiciones sin duplicados',len(inventory)==45 and len({x['order'] for x in inventory})==45)
    check('QVoice excluido',not result['qvoice_included'] and not any(x.startswith('qv_') for x in config['candidate_features']))
    check('sin filas ni scores individuales persistidos',result['employee_level_rows_persisted'] is False and result['individual_scores_published'] is False)
    for path in (out/'input-evidence').glob('*.json'):
        item=read(path)
        check('evidencia '+path.stem,item['outcome']=='pass' and sha(ROOT/item['query'])==item['sql_sha256'])
    for path in (out/'selection').glob('*.json'):
        trace=read(path);cutoff=pd.Timestamp(trace['cutoff'])
        for item in trace['dates']:
            check('etiqueta mensual previa '+path.stem+item['origin'],pd.Timestamp(item['train_latest_label'])<=pd.Timestamp(item['origin']))
            check('etiqueta interna R6 madura '+path.stem+item['origin'],pd.Timestamp(item['validation_latest_outcome'])<=cutoff)
        check('candidato elegido fue evaluado '+path.stem,any(t==trace['C'] for t in trace['trials']))
        check('convergencia candidata '+path.stem,not trace['C']['failed'] and len(trace['C']['folds'])==2)
        for model in ['B','C']:
            spec=trace[model]
            check('lista válida '+path.stem+model,set(spec['features'])<=set(config['candidate_features']))
            for inter,parents in config['interactions'].items():
                check('jerarquía '+path.stem+model+inter,inter not in spec['features'] or set(parents)<=set(spec['features']))
    for f in result['folds']:
        tag=str(f['fold'])
        check('corte externo '+tag,pd.Timestamp(f['train_latest_label'])<=pd.Timestamp(f['origin']))
        check('seguimiento externo '+tag,pd.Timestamp(f['latest_outcome'])<=pd.Timestamp(config['knowledge_boundary']))
        check('cohorte igual B y C '+tag,f['B']['exposures']==f['C']['exposures'] and f['B']['event_exposures']==f['C']['event_exposures'])
        check('fracción observada consistente '+tag,abs(f['B']['observed_percent']-100*f['B']['event_exposures']/f['B']['exposures'])<1e-10)
        rules=f['group_definition']['rules']
        check('máximo ocho grupos '+tag,len(rules)<=8)
        check('tres condiciones por grupo '+tag,all(len(r['conditions'])<=3 for r in rules))
        check('hojas entrenamiento grandes '+tag,all(r['training_people']>=300 for r in rules))
        for row in f['groups']['rows']:
            if row.get('suppressed'):
                continue
            check('cohorte publicada '+tag+str(row['node']),row['minimum_people_per_snapshot']>=30)
            if row['observed_percent'] is not None:
                check('eventos distintos suficientes '+tag+str(row['node']),row['distinct_people_with_event']>=30)
                for model in ['B','C']:
                    check('error en grupo '+tag+str(row['node'])+model,abs(row[model+'_error_pp']-abs(row[model+'_predicted_percent']-row['observed_percent']))<1e-9)
    repeated=decision(result['folds'],result['paired_loss_intervals'],config)
    check('decisión reproducible',repeated==result['decision'])
    for m,item in result['paired_loss_intervals'].items():
        check('intervalo finito '+m,np.isfinite(item['ci95']).all() and item['ci95'][0]<=item['ci95'][1])
    artifact=read(out/'trained-model/model-c.json');design=Design(**artifact['encoder'])
    model=Model(design,np.asarray(artifact['beta']),artifact['features'],artifact['l2'],artifact['iterations'])
    check('modelo final lista concordante',artifact['features']==result['final_features'])
    check('dimensión de coeficientes',len(artifact['beta'])==len(design.columns))
    check('coeficientes finitos',np.isfinite(artifact['beta']).all())
    sample={f:[design.references[f]]*2 for f in design.features if f not in design.interactions}
    sample['snapshot_date']=pd.to_datetime(['2026-08-23','2026-09-27'])
    if 'calendar_month' in sample:
        sample['calendar_month']=['8','9']
    p=model.risk(pd.DataFrame(sample))
    check('modelo exportado produce probabilidades finitas',np.isfinite(p).all() and ((p>0)&(p<1)).all())
    population=read(out/'population.json');last=max(population,key=lambda x:x['snapshot_date'])
    check('última foto carece de etiqueta mensual',last['monthly_labeled']==0)
    closure=read(out/'finalization.json')
    check('comparación completa',closure['four_external_periods_completed'] and len(result['folds'])==4)
    check('cierre sin promoción coherente',not result['decision']['passes_all'] and not result['final_model_refit'])
    check('no se presentan pronósticos actuales',result['forecast_groups']==[] and result['forecast_snapshot'] is None)
    check('fecha real del modelo archivado',artifact['training_cutoff']==result['folds'][-1]['origin'])
    source_model=read(out/'folds/fold-4-C-model.json')
    check('modelo archivado coincide con el evaluado',artifact['beta']==source_model['beta'] and artifact['encoder']==source_model['encoder'])
    check('informe y figura existen',all((out/p).exists() for p in ['informe.md','inventario.md','comparacion-b-c.png','comparacion-b-c.svg']))
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_engineering_model_c.py','-v'],cwd=ROOT,capture_output=True,text=True)
    (out/'model-tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    check('pruebas sintéticas',test.returncode==0)
    write(out/'verification.json',{'checks':checks,'passed':len(checks),'failed':0,
                                    'tests':'model-tests.txt','test_script_sha256':sha(ROOT/'tests/test_engineering_model_c.py'),
                                    'verifier_sha256':sha(Path(__file__))})
    with (out/'informe.md').open('a',encoding='utf-8') as f:
        f.write(f'\n## Verificación\n\nPasaron {len(checks)} comprobaciones de artefactos, fechas, cohortes, privacidad, fórmulas y exportación, además de las pruebas sintéticas adjuntas.\n')
    manifest=read(out/'manifest.json')
    manifest['files']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}
    manifest['report_builder_sha256']=sha(ROOT/'tools/build_engineering_model_c_report.py')
    manifest['verification_passed']=True
    write(out/'manifest.json',manifest)
    print(json.dumps({'passed':len(checks),'failed':0},ensure_ascii=False))


if __name__=='__main__':
    main()
