"""Indicadores locales de comentarios V11; texto y llaves nunca se persisten."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re

import pandas as pd

import build_qvoice_comment_evidence as comments_source
import build_qvoice_retention_concerns_evidence as retention
import build_qvoice_open_text_request_concern_evidence as requests_source
from qvoice_model_data import ROOT,availability_date,iter_structured_rows,parse_key,sha256_file


RETENTION = {
    'qv_comment_rewards':('Rewards','Recompensas'),
    'qv_comment_career':('Career growth and promotion','Carrera y promoción'),
    'qv_comment_leadership':('Manager, leadership and respect','Manager, liderazgo y respeto'),
    'qv_comment_workload':('Workload, staffing and work-life','Carga de trabajo y equilibrio personal'),
    'qv_comment_arrangement':('Work arrangement/RTO/commute','Modalidad y traslado'),
    'qv_comment_processes':('Tools, processes and bureaucracy','Herramientas, procesos y burocracia'),
    'qv_comment_confidence':('Organizational confidence/job security','Confianza y estabilidad laboral')}
WORKPLACE = {
    'qv_comment_remote':('Remote / WFH','Mención de trabajo remoto'),
    'qv_comment_hybrid':('Hybrid','Mención de trabajo híbrido'),
    'qv_comment_office':('RTO / office attendance','Mención de asistencia a oficina')}
LABELS={'qv_comment_presence':'QVoice: presencia de algún comentario',
    'qv_improvement_comment_presence':'QVoice: presencia de comentario de mejora',
    **{key:'QVoice: comentario sobre '+label.lower() for key,(_,label) in RETENTION.items()},
    **{key:'QVoice: '+label.lower() for key,(_,label) in WORKPLACE.items()},
    'qv_remote_hybrid_request':'QVoice: petición de flexibilidad remota o híbrida',
    'qv_onsite_policy_concern':'QVoice: inquietud de política presencial'}
FEATURES=list(LABELS)


def compiled(patterns):
    return re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(p.casefold()) for p in patterns)+r')(?!\w)')


RET_PATTERNS={f:compiled(retention.TAXONOMY[name]['patterns']) for f,(name,_) in RETENTION.items()}
WORK_PATTERNS={f:compiled(comments_source.TAXONOMY[name]['patterns']) for f,(name,_) in WORKPLACE.items()}
REQUEST_TARGET=compiled(requests_source.REMOTE_OR_HYBRID_TARGETS)
REQUEST_ACTION=compiled(requests_source.REQUEST_ACTIONS)
ONSITE_TARGET=compiled(requests_source.ONSITE_TARGETS)
ONSITE_ACTION=compiled(requests_source.ONSITE_CONCERN_ACTIONS)


def text_parts(values):
    normalized={role:retention._norm_text(text) for role,text in values.items()}
    all_text=' '.join(text for text in normalized.values() if text)
    improvement=' '.join(normalized.get(role,'') for role in ['can_improve','processes_to_improve']).strip()
    request_text='. '.join(text for text in normalized.values() if text)
    return all_text,improvement,request_text


def classify(values,reference=False):
    all_text,improvement,request_text=text_parts(values)
    result={'qv_comment_presence':'v1' if all_text else 'v0',
        'qv_improvement_comment_presence':'v1' if improvement else 'v0'}
    missing_improvement=not any(role in values for role in ['can_improve','processes_to_improve'])
    if missing_improvement:
        result['qv_improvement_comment_presence']='question_absent'
    original=retention.classify_themes(improvement) if reference else None
    for feature,(name,_) in RETENTION.items():
        if missing_improvement:
            result[feature]='question_absent'
        elif not improvement:
            result[feature]='no_comment'
        else:
            found=name in original if reference else bool(RET_PATTERNS[feature].search(improvement))
            result[feature]='v1' if found else 'v0'
    for feature,(name,_) in WORKPLACE.items():
        tested=requests_source.onsite_text(all_text) if name=='RTO / office attendance' else all_text
        found=comments_source._classify_theme(all_text,name) if reference else bool(WORK_PATTERNS[feature].search(tested))
        result[feature]=('v1' if found else 'v0') if all_text else 'no_comment'
    if reference:
        remote=requests_source.is_remote_hybrid_request(request_text)
        onsite=requests_source.is_onsite_policy_concern(request_text)
    else:
        clauses=requests_source.clauses(request_text)
        remote=any(REQUEST_TARGET.search(c) and REQUEST_ACTION.search(c) for c in clauses)
        onsite=any(ONSITE_TARGET.search(requests_source.onsite_text(c)) and ONSITE_ACTION.search(requests_source.onsite_text(c)) for c in clauses)
    result['qv_remote_hybrid_request']=('v1' if remote else 'v0') if all_text else 'no_comment'
    result['qv_onsite_policy_concern']=('v1' if onsite else 'v0') if all_text else 'no_comment'
    return result


def mapping_for(wave,metadata):
    spec=next(w for w in comments_source.WAVES if w['wave']==f"Jan-{wave['year']}")
    headers=[retention._norm_header(h) for h in metadata['headers']]
    key=retention._find_column(headers,[wave['key_column']])
    roles={role:retention._find_column(headers,choices) for role,choices in spec['prompt_candidates'].items() if choices}
    if key is None or any(header is None or headers.count(header)!=1 for header in roles.values()):
        raise RuntimeError('Los encabezados de comentarios son ausentes o ambiguos.')
    if headers.count(key)>1:
        audit=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-qvoice-comment-keys.json'
        check=json.loads(audit.read_text(encoding='utf-8'))
        positions=[i for i,h in enumerate(headers) if h==key]
        if (check['outcome']!='pass' or check['year']!=wave['year']
                or check['source_sha256']!=metadata['sha256']
                or positions!=check['positions_zero_based']
                or headers.index(key)!=check['selected_position_zero_based']):
            raise RuntimeError('La repetición de la llave no tiene reconciliación vigente.')
    if set(roles)!=({'doing_well','can_improve'} if wave['year']==2024 else {'doing_well','can_improve','processes_to_improve'}):
        raise RuntimeError('Cambió la disponibilidad de prompts.')
    response=retention._norm_header('Response Type') if 'Response Type' in headers else None
    return headers,key,roles,response


def scan(wave,metadata,salt,verify=False):
    if wave['year'] not in {2024,2025}:
        raise RuntimeError('Esta ronda sólo admite waves 2024 y 2025.')
    path=ROOT/wave['file']
    if sha256_file(path)!=metadata['sha256']:
        raise RuntimeError('Cambió la fuente QVoice respecto del preflight.')
    headers,key,roles,response=mapping_for(wave,metadata)
    required={key,*roles.values()}|({response} if response else set())
    quality=Counter(source_rows=0,invalid_key_rows=0,excluded_response_type_rows=0,duplicate_rows=0,
        independently_checked_records=0,independent_mismatches=0)
    rows,seen,duplicates={},set(),set()
    for indexes,record in iter_structured_rows(path,wave['sheet'],headers,required):
        quality['source_rows']+=1
        if quality['source_rows']%10000==0:
            print(f"Comentarios {wave['year']}: {quality['source_rows']} filas inspeccionadas sólo en RAM.",flush=True)
        if response:
            value=str(record.get(indexes[response]) or '').strip().upper()
            if value and value!='EX':
                quality['excluded_response_type_rows']+=1
                continue
        parsed=parse_key(record.get(indexes[key]))
        if parsed is None:
            quality['invalid_key_rows']+=1
            continue
        transient_key=hashlib.md5((str(parsed)+salt).encode()).hexdigest()
        values={role:record.get(indexes[header]) for role,header in roles.items()}
        result=classify(values)
        # Selección determinista ajena al outcome y estable ante cambios del salt.
        if verify and int(hashlib.sha256(str(parsed).encode()).hexdigest()[:8],16)%97==0:
            quality['independently_checked_records']+=1
            quality['independent_mismatches']+=int(result!=classify(values,reference=True))
        if transient_key in seen:
            quality['duplicate_rows']+=1
            duplicates.add(transient_key)
            rows.pop(transient_key,None)
        else:
            seen.add(transient_key)
            rows[transient_key]=result
        del values,result,record,parsed
    if quality['independent_mismatches']:
        raise RuntimeError('La clasificación no reproduce los helpers originales.')
    if verify and quality['independently_checked_records']<30:
        raise RuntimeError('Muestra independiente insuficiente.')
    quality['unique_usable_keys']=len(rows)
    quality['distinct_duplicate_keys']=len(duplicates)
    quality['keys_with_comment']=sum(r['qv_comment_presence']=='v1' for r in rows.values())
    quality['keys_with_improvement_comment']=sum(r['qv_improvement_comment_presence']=='v1' for r in rows.values())
    return rows,duplicates,{'year':wave['year'],'source':wave['file'],'sha256':metadata['sha256'],
        'prompt_roles':list(roles),'quality':dict(quality)}


def attach_lookup(frame,lookup,duplicates,year):
    selected=frame.person_key.astype(object).map(lookup)
    duplicate=frame.person_key.isin(duplicates)
    same=frame[f'same_episode_{year}'].eq(1)
    output=pd.DataFrame(index=frame.index)
    for feature in FEATURES:
        values=selected.map(lambda x:x[feature] if isinstance(x,dict) else 'no_linked_row')
        values.loc[duplicate]='duplicate'
        values.loc[~same]='different_employment_episode'
        output[feature]=values
    return output


def attach(frame,qconfig,metadata,salt,verify=False):
    result=frame.copy()
    for feature in FEATURES:
        result[feature]='no_available_wave'
    sources=[]
    for wave in qconfig['sources']['waves']:
        if wave['year'] not in {2024,2025}:
            continue
        known=availability_date(wave)
        expiry=known+pd.DateOffset(months=qconfig['temporal_rules']['maximum_age_months'])
        mask=result.snapshot_date.ge(known)&result.snapshot_date.lt(expiry)
        if not mask.any():
            continue
        meta=next(m for m in metadata['waves'] if m['year']==wave['year'])
        lookup,duplicates,source=scan(wave,meta,salt,verify)
        values=attach_lookup(result.loc[mask],lookup,duplicates,wave['year'])
        result.loc[mask,FEATURES]=values
        source['model_years']=sorted(int(y) for y in result.loc[mask,'snapshot_date'].dt.year.unique())
        source['linked_person_snapshots']=int((result.loc[mask,'person_key'].isin(lookup)&result.loc[mask,f"same_episode_{wave['year']}"].eq(1)).sum())
        sources.append(source)
        del lookup,duplicates,values
    for feature in FEATURES:
        result[feature]=result[feature].astype('category')
    return result,{'reporting_mode':'presentation','sources':sources,'outcome':'pass','employee_level_rows_persisted':False,
        'comment_text_persisted':False,'wave_2026_read':False,'assessment_score_changed':False}
