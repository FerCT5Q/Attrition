"""Carga autorizada en RAM y contratos de entrada para B incremental."""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import secrets
import time

import numpy as np
import pandas as pd

import engineering_b_incremental as inc
import engineering_model_c as base
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config, sha256_file

ROOT = base.ROOT


def check_authorization(config):
    auth = base.read(ROOT/config['authorization'])
    if auth.get('status')!='approved':
        raise RuntimeError('Falta autorización de procesamiento en RAM.')
    controls = auth['non_negotiable_controls']
    for flag in ['employee_rows_persisted','employee_ids_selected_or_persisted','names_emails_free_text',
                 'exact_compensation','individual_scores_published','individual_explanations_published',
                 'protected_attributes_as_features','disk_cache_of_rows','logs_contain_rows']:
        if controls.get(flag) is not False:
            raise RuntimeError('Cambió un control de privacidad de la autorización.')
    if config.get('reporting_mode')!='presentation' or config['employee_level_rows_persisted'] or config['individual_scores_published']:
        raise RuntimeError('Configuración fuera del modo autorizado.')
    inc.mandatory_features([],config)


def input_ledger(config,out):
    contracts = base.read(ROOT/config['input_contracts'])['contracts']
    names = list(contracts)+['metadata','region','comp_ratio_band','grade_family','acquisition_recorded','transfer_12m','transfer_history']
    names += ['history-'+name for name in ['manager_recency','team_recency','manager_span','team_intensity']]
    names += config.get('extra_evidence',[])
    entries = []
    for name in names:
        path = out/f'input-evidence/{name}.json'
        entry = base.read(path)
        if entry.get('outcome')!='pass' or base.sha(ROOT/entry['query'])!=entry['sql_sha256']:
            raise RuntimeError(f'Contrato de entrada pendiente: {name}.')
        for execution in entry.get('executions',[]):
            if base.sha(ROOT/execution['query'])!=execution['sql_sha256']:
                raise RuntimeError(f'Cambió SQL ejecutado de {name}.')
        if entry.get('contract_path') and base.sha(ROOT/entry['contract_path'])!=entry['contract_sha256']:
            raise RuntimeError(f'Cambió el contrato de {name}.')
        if entry.get('transformer_source') and base.sha(ROOT/entry['transformer_source'])!=entry['transformer_sha256']:
            raise RuntimeError(f'Cambió la transformación validada de {name}.')
        entries.append({'concept':name,'result':path.relative_to(ROOT).as_posix(),
                        'result_sha256':base.sha(path),'sql':entry['query'],
                        'sql_sha256':entry['sql_sha256'],'executed_at':entry['executed_at'],
                        'executions':entry.get('executions',[]),'outcome':'pass'})
    # La revisión de conteo debe reproducir el recálculo independiente, no sólo sus rangos.
    direct = base.read(out/'input-evidence/team-pay-independent.json')['rows'][0]
    corrected = base.read(out/'input-evidence/team-pay-distinct.json')['rows'][0]
    if any(direct[k]!=corrected[k] for k in ['peer_groups_ge2','peer_groups_ge5']):
        raise RuntimeError('No reconcilia compensación con el cálculo independiente.')
    if corrected['exact_spread_matches']<=0:
        raise RuntimeError('La corrección de dispersión sigue vacía.')
    ledger = {'reporting_mode':'presentation','entries':entries,'assessment_score_changed':False,
              'authorization':config['authorization'],'employee_level_rows_persisted':False}
    inc.write(out/'evidence-ledger.json',ledger)
    return ledger


def year_windows(config):
    start,end = pd.Timestamp(config['training_start']),pd.Timestamp(config['knowledge_boundary'])
    for year in range(start.year,end.year+1):
        yield max(start,pd.Timestamp(year=year,month=1,day=1)), min(end,pd.Timestamp(year=year,month=12,day=31))


def read_frame(template_path, expected, categories, config, salt, label, transform=None):
    template = (ROOT/template_path).read_text(encoding='utf-8')
    parts = []
    with base.db.connect() as connection:
        connection.set_session(readonly=True,autocommit=True)
        for start,end in year_windows(config):
            tick = time.perf_counter()
            sql = base.db.validate_readonly(template.replace('__PERIOD_START__',str(start.date()))
                    .replace('__PERIOD_END__',str(end.date())).replace('__RUN_SALT__',salt))
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql)
                except base.db.psycopg2.Error as exc:
                    raise RuntimeError(f'Carga {label} incompleta ({type(exc).__name__}); no se muestra SQL expandido.') from None
                columns = [c[0] for c in cursor.description]
                if set(columns)!=set(expected) or set(columns)&base.db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('Columnas fuera de la lista autorizada de modelado.')
                year_rows = 0
                while True:
                    rows = cursor.fetchmany(50000)
                    if not rows:
                        break
                    part = pd.DataFrame(rows,columns=columns)
                    if transform is not None:
                        part = transform(part)
                        if set(part.columns)!={'snapshot_date','person_key',*categories}:
                            raise RuntimeError('La transformación retuvo componentes fuera del contrato.')
                    for f in categories:
                        part[f] = part[f].astype('category')
                    parts.append(part)
                    year_rows += len(part)
                    del rows
            base.log(f'{label} {start.year}: {year_rows} filas sólo en RAM; {time.perf_counter()-tick:.1f} s.')
    result = pd.concat(parts,ignore_index=True)
    del parts,sql
    result['snapshot_date'] = pd.to_datetime(result.snapshot_date)
    result['person_key'] = result.person_key.astype('category')
    for f in categories:
        result[f] = result[f].astype('category')
    if result.duplicated(['snapshot_date','person_key']).any():
        raise RuntimeError(f'Grain duplicado en {label}.')
    return result


def join_frame(frame, additional, name):
    before = len(frame)
    result = frame.merge(additional,on=['snapshot_date','person_key'],how='left',validate='one_to_one',indicator=True)
    unmatched = int(result._merge.ne('both').sum())
    if len(result)!=before or unmatched or len(additional)!=before:
        raise RuntimeError(f'La unión de {name} no reconcilia 1:1 con B.')
    return result.drop(columns='_merge'), {'name':name,'base_rows':before,'additional_rows':len(additional),
                                          'merged_rows':len(result),'missing_matches':0,'duplicate_keys':0,'outcome':'pass'}


def regional_qvoice(frame, config):
    """Referencia contemporánea de la misma foto; nunca usa una foto futura."""
    columns = [f'qv_M{i:02d}' for i in range(1,34)]
    numeric = np.column_stack([frame[f].astype(str).map({'v0':0.,'v1':1.}).to_numpy() for f in columns])
    complete = np.isfinite(numeric).all(axis=1)
    mean = np.where(complete,np.nan_to_num(numeric).sum(axis=1)/33,np.nan)
    valid = frame['qv_mean33'].astype(str).isin(inc.VALID_Q)
    if not np.array_equal(complete,valid.to_numpy()):
        raise RuntimeError('No coincide la completitud independiente del promedio QVoice.')
    work = pd.DataFrame({'snapshot':frame.snapshot_date.to_numpy(),'region':frame.region.astype(str).to_numpy(),'value':mean})
    grouped = work.groupby(['snapshot','region'],observed=True)['value']
    count = grouped.transform('count').to_numpy()
    center = grouped.transform('mean').to_numpy()
    sd = grouped.transform('std',ddof=0).to_numpy()
    z = np.divide(mean-center,sd,out=np.zeros(len(frame)),where=sd>1e-12)
    usable = complete & (count>=config['qvoice']['minimum_people_region_snapshot']) & (sd>1e-12)
    values = frame.qv_mean33.astype(str).to_numpy(copy=True)
    values[complete & (count<config['qvoice']['minimum_people_region_snapshot'])] = '(region too small)'
    values[complete & (count>=config['qvoice']['minimum_people_region_snapshot']) & ~(sd>1e-12)] = '(zero region variance)'
    values[usable & (z < -1)] = 'below -1 sd'
    values[usable & (z >= -1) & (z < 0)] = '-1 to 0 sd'
    values[usable & (z >= 0) & (z <= 1)] = '0 to 1 sd'
    values[usable & (z > 1)] = 'above 1 sd'
    frame['qv_region_relative'] = pd.Categorical(values)
    frame['qv_availability'] = pd.Categorical(np.where(valid,'available',frame.qv_mean33.astype(str)))
    # Reconciliación por momentos con referencia independiente.
    work['squared'] = work.value**2
    second = work.groupby(['snapshot','region'],observed=True)['squared'].transform('mean').to_numpy()
    independently = np.sqrt(np.maximum(second-center**2,0))
    difference = float(np.max(np.abs(independently[usable]-sd[usable]))) if usable.any() else 0.
    if difference>1e-9:
        raise RuntimeError('No reconcilia la normalización regional de QVoice.')
    return {'outcome':'pass','complete_person_snapshots':int(complete.sum()),'relative_score_person_snapshots':int(usable.sum()),
            'minimum_region_snapshot_people':config['qvoice']['minimum_people_region_snapshot'],
            'maximum_sd_recalculation_difference':difference,
            'temporal_rule':'Media y desviación sólo de la misma foto y región, con wave anual ya disponible.'}


def feature_support(frame,features):
    rows = []
    for feature in features:
        for year,part in frame.groupby(frame.snapshot_date.dt.year,observed=True):
            values = part[feature].astype(str)
            observed = ~values.isin(inc.MISSING)
            rows.append({'feature':feature,'year':int(year),'person_snapshots':len(part),
                'observable_person_snapshots':int(observed.sum()),
                'observable_snapshots':int(part.loc[observed,'snapshot_date'].nunique()),
                'observed_categories':int(values[observed].nunique()),
                'first_observed_snapshot':str(part.loc[observed,'snapshot_date'].min().date()) if observed.any() else None})
    return rows


def load(config,out):
    check_authorization(config)
    input_ledger(config,out)
    source = base.read(ROOT/config['source_c_config'])
    raw = base.raw_features(source)
    expected = {'snapshot_date','person_key','label_end','y_next','y_6m',
                'company_tenure_band','tenure_julia_band','same_episode_2024','same_episode_2025','same_episode_2026'}|set(raw)
    salt = secrets.token_hex(32)
    frame = read_frame(config['base_query'],expected,raw,config,salt,'B y entradas C')
    frame = frame.drop(columns=['company_tenure_band','tenure_julia_band'])
    frame['label_end'] = pd.to_datetime(frame.label_end)
    frame['r6_end'] = frame.snapshot_date+pd.DateOffset(months=6)
    frame['calendar_month'] = frame.snapshot_date.dt.month.astype(str).astype('category')
    for target in ['y_next','y_6m']:
        if not frame[target].dropna().isin([0,1]).all():
            raise RuntimeError('Etiqueta no binaria.')
    boundary = pd.Timestamp(config['knowledge_boundary'])
    if frame.loc[(frame.label_end.isna())|(frame.label_end>boundary),'y_next'].notna().any():
        raise RuntimeError('Etiqueta mensual sin madurez.')
    if frame.loc[frame.r6_end>boundary,'y_6m'].notna().any():
        raise RuntimeError('Etiqueta R6 sin madurez.')
    if ((frame.label_end<=frame.snapshot_date)&frame.label_end.notna()).any():
        raise RuntimeError('Intervalo de entrenamiento inválido.')
    joins = []
    blocks = [{'name':key,'query':config[key],'features':features}
              for key,features in [('history_query',config['history_features']),('pending_query',config['pending_features'])]]
    blocks += config.get('extra_hr_queries',[])
    for block in blocks:
        features = block['features']
        transformer = None
        if block.get('transform'):
            from b_v11_geography import transformer_for
            transformer = transformer_for(block['transform'])
        expected = {'snapshot_date','person_key'}|set(block.get('input_columns',features))
        extra = read_frame(block['query'],expected,features,config,salt,block['name'],transformer)
        if transformer is not None:
            inc.write(out/'input-evidence'/f"model-{block['name']}-transform.json",transformer.evidence())
        frame,check = join_frame(frame,extra,block['name'])
        joins.append(check)
        del extra,transformer
        gc.collect()
    inc.write(out/'input-evidence/model-joins.json',{'outcome':'pass','checks':joins,'employee_level_rows_persisted':False})
    # Las cohortes fuente se contrastan con una consulta agregada separada.
    expected_annual = base.read(out/'input-evidence/job-family.json')['rows']
    annual = []
    for year,part in frame.groupby(frame.snapshot_date.dt.year,observed=True):
        expected_row = next(r for r in expected_annual if r['year']==year)
        if len(part)!=expected_row['person_snapshots'] or part.person_key.nunique()!=expected_row['employee_count']:
            raise RuntimeError('La población modelada no reproduce el agregado independiente.')
        annual.append({'year':int(year),'person_snapshots':len(part),'distinct_people':int(part.person_key.nunique()),
                       'snapshots':int(part.snapshot_date.nunique()),'monthly_event_exposures':int(part.y_next.sum()),
                       'mature_six_month_exposures':int(part.y_6m.notna().sum())})
    inc.write(out/'population.json',{'reporting_mode':'presentation','annual':annual,'outcome':'pass',
                                    'aggregate_population_reconciled':True,'employee_level_rows_persisted':False})
    inc.write(out/'input-evidence/hr-feature-support.json',{'reporting_mode':'presentation',
        'method':'Comprobación en RAM del diseño derivado por el SQL guardado; sólo soporte agregado anual.',
        'queries':[config[k] for k in ['base_query','history_query','pending_query']]+[b['query'] for b in config.get('extra_hr_queries',[])],
        'rows':feature_support(frame,inc.hr_candidates(config)),'assessment_score_changed':False})
    qconfig = load_config(ROOT/config['source_qvoice_config'])
    metadata = base.read(ROOT/config['source_qvoice_metadata'])
    if sha256_file(ROOT/qconfig['sources']['dictionary'])!=metadata['dictionary_sha256']:
        raise RuntimeError('Cambió el diccionario QVoice.')
    qframe = frame.loc[frame.snapshot_date>=pd.Timestamp(config['qvoice']['start'])].copy().reset_index(drop=True)
    qsource_features = [f'qv_M{i:02d}' for i in range(1,34)]+['qv_career','qv_mean33']
    timing = {}
    qframe = horizon.attach_selected(qframe,qconfig,metadata,salt,qsource_features,timing)
    if config.get('qvoice_comments_contract'):
        import b_v11_qvoice_comments as comments
        contract = base.read(ROOT/config['qvoice_comments_contract'])
        for path,digest in contract['source_hashes'].items():
            if base.sha(ROOT/path)!=digest:
                raise RuntimeError('Cambió una fuente de clasificación de comentarios.')
        qframe,comment_check = comments.attach(qframe,qconfig,metadata,salt)
        inc.write(out/'input-evidence/model-qvoice-comments.json',comment_check)
    del salt
    if (qframe.qvoice_wave.astype(str)=='2026').any():
        raise RuntimeError('La wave 2026 no puede entrar a este corte.')
    regional = regional_qvoice(qframe,config)
    inc.write(out/'input-evidence/qvoice-regional.json',regional)
    inc.write(out/'input-evidence/qvoice-feature-support.json',{'reporting_mode':'presentation',
        'source_metadata':config['source_qvoice_metadata'],'source_metadata_sha256':base.sha(ROOT/config['source_qvoice_metadata']),
        'source_config_sha256':base.sha(ROOT/config['source_qvoice_config']),'timings':timing,
        'rows':feature_support(qframe,inc.q_candidates(config)),
        'common_items_counted_once':33,'wave_2026_included':False,
        'temporal_policy':config['qvoice']['annual_lag_policy'],'employee_level_rows_persisted':False,
        'assessment_score_changed':False,'career_wording_limit':qconfig['source_rules']['career_modeling_limit']})
    return frame,qframe
