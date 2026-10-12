"""Congelar configuración y planes del nuevo modelo B + QVoice."""
from pathlib import Path
import argparse
import copy
import json
import shutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1'
CONFIG = ROOT / 'config/qvoice_model_calibrated_20261008.yaml'
PLANS = ROOT / 'config/qvoice_model_plans_20261008_full'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['config', 'plans'])
    args = parser.parse_args()
    if args.phase == 'config':
        if CONFIG.exists():
            raise FileExistsError(CONFIG)
        config = yaml.safe_load((ROOT / 'config/qvoice_model_experiment_20261008.yaml').read_text(encoding='utf-8'))
        historical = yaml.safe_load((ROOT / 'config/qvoice_model_experiment_20261006.yaml').read_text(encoding='utf-8'))
        config['experiment_id'] = 'engineering-b-plus-qvoice-calibrated-20261008-v1'
        config['paths'] = dict(query_suffix='20261008_full', model_query='queries/profiles/engineering_qvoice_person_month_20261008_full.sql', portfolio_metadata_query='queries/audits/qvoice_model_portfolio_metadata_20261008.sql', plan_root=str(PLANS.relative_to(ROOT)).replace('\\', '/'))
        config['candidates'] = [c for c in historical['candidates'] if c['id'] != 'heartbeat']
        mean = next(c for c in config['candidates'] if c['id'] == 'mean33')
        mean['variants'].append(dict(id='pca_items', components=[f'M{i:02}' for i in range(1,34)], representation='binary_components'))
        config['combinations'] = historical['combinations']
        config['search'] = {
            'blocks': {'q4':['qv_Q4'], 'q12':['qv_Q12'], 'career':['qv_career'], 'mean33':['qv_mean33'], 'engagement':['qv_Q1','qv_Q2','qv_Q3'], 'connection':['qv_Q5','qv_Q7'], 'wellbeing':['qv_Q8','qv_Q10','qv_Q11'], 'confidence':['qv_Q13','qv_Q17']},
            'method':'exhaustive_subsets', 'nonempty_subsets':255,
            'extension':'cloglog additive QVoice correction with fitted B as fixed offset',
            'l2_grid':[0.1,1,10], 'criterion':'monthly_brier',
            'selection_intervals':2, 'calibration_intervals':2,
            'pca_components':[1,2,3,5,10],
            'pca_items':[f'qv_M{i:02}' for i in range(1,34)],
            'pca_imputation':'training item means; explicit missingness indicators',
            'calibration':{'method':'cloglog_intercept_positive_slope','slope_bounds':[0.25,4.0],'slope_l2':10},
            'refit_after_calibration':False,
            'evaluation_caveat':'Los periodos retrospectivos ya fueron inspeccionados en el desarrollo anterior; no son un holdout externo virgen.',
            'excluded':{'heartbeat':'No se reconstruyen los 53 ítems ordinales en 2024/2025; 2026 corresponde a snapshots 2027.', 'q6_q9':'Ausentes en la wave 2024 usada para entrenamiento previo a enero 2026; no tienen historia en ambos periodos.', 'comments':'Texto libre excluido.'},
            'career_status':'Sensibilidad exploratoria por diferencia de redacción 2024; si se selecciona, el modelo conserva esta limitación.'
        }
        CONFIG.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding='utf-8')
        RUN.mkdir(parents=True, exist_ok=False)
        shutil.copy2(CONFIG, RUN / 'experiment-config.yaml')
        print(CONFIG.relative_to(ROOT))
        return
    PLANS.mkdir(parents=True, exist_ok=False)
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    for candidate in config['candidates']:
        ident = candidate['id']
        source_root = ROOT / ('config/qvoice_model_plans_20261008' if ident in ('intent','career','mean33') else 'config/qvoice_model_plans')
        sources = list(source_root.glob(f'*-{ident}-v*.yaml'))
        source = max(sources, key=lambda p:int(p.stem.rsplit('-v',1)[1]))
        plan = yaml.safe_load(source.read_text(encoding='utf-8'))
        plan['plan_version'] = 1
        plan['variable'] = candidate['name']
        plan.pop('plan_revision_reason', None)
        plan['knowledge_date'] = 'Política anual aprobada: wave Y exclusivamente en snapshots Y+1, continuidad del episodio; frontera 2026-09-07.'
        plan['prior_evidence_policy'] = 'Los antecedentes orientan las preguntas; las nuevas métricas se ejecutan bajo esta política. No se elevan scores por asociación predictiva.'
        for story in plan['validation_story']:
            story['sql_reference'] = story['sql_reference'].replace(f'qvoice_model_{ident}_20261006.sql', f'qvoice_model_{ident}_20261008_full.sql').replace(f'qvoice_model_{ident}_20261008.sql', f'qvoice_model_{ident}_20261008_full.sql')
            if story['criterion'] == 'history':
                story['question'] = f'¿La historia de {ident} respeta la asignación anual aprobada y la versión de cada componente?'
                story['why'] = 'La política fija el año de uso y no constituye una fecha real de publicación; tampoco completa preguntas ausentes.'
                story['method'] = 'Comprobación de asignación Y a Y+1, caducidad anual y componentes por wave.'
                story['acceptance_rule'] = 'Cero waves sin fecha efectiva asignada por la política aprobada; los componentes ausentes quedan identificados.'
        target = PLANS / f'{source.name.split("-")[0]}-{ident}-v1.yaml'
        target.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding='utf-8')
    # Se reutilizan assessments de la misma sesión, definición, población, fuentes y corte.
    # Se conserva su fecha y resultado, sin emitir scores nuevos para esos tres conceptos.
    previous = ROOT / 'output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2'
    for ident in ('intent','career','mean33'):
        destination = RUN / 'variables' / ident
        destination.mkdir(parents=True)
        ref = json.loads((previous / 'variables' / ident / 'assessment-reference.json').read_text(encoding='utf-8'))
        ref['reuse_scope'] = 'Misma sesión y política, fuente, población, representación y corte. PCA se valida por separado; no se extiende el score del promedio a PCA.'
        (destination / 'assessment-reference.json').write_text(json.dumps(ref,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Planes preparados; los cuatro conceptos adicionales se ejecutarán secuencialmente.')

if __name__ == '__main__':
    main()
