"""Congela el alcance V11 y sus entradas verificadas antes de entrenar."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import engineering_model_c as base
import engineering_b_incremental as inc
from b_v11_commute import CommuteTransform
from b_v11_geography import TimezoneTransform
from b_v11_qvoice_comments import FEATURES, LABELS

ROOT = base.ROOT
OUT = ROOT / 'output/analysis/engineering/20261011/b-playbook-v11-v1'
CONFIG = ROOT / 'config/engineering_b_playbook_v11_20261012.json'
SCOPE = ROOT / 'config/b_playbook_v11_scope_20261012.json'


def main():
    if CONFIG.exists() or SCOPE.exists() or (OUT/'frozen-config.json').exists():
        raise RuntimeError('El alcance ya existe; conservarlo y usar una revisión nueva.')
    correspondence = base.read(OUT/'playbook-correspondence.json')
    for key in ['source', 'manifest']:
        if base.sha(ROOT/correspondence[key]) != correspondence[key+'_sha256']:
            raise RuntimeError('Cambió el playbook V11 o su manifest.')
    config = base.read(ROOT/'config/engineering_b_incremental_20261011_v2.json')
    for key in ['retry_of', 'retry_reason']:
        config.pop(key, None)
    config.update(run_id='engineering-b-playbook-v11-20261012-v1',
        output=OUT.relative_to(ROOT).as_posix(),
        plan='docs/plans/attrition-b-playbook-v11-20261011.md',
        playbook_scope=SCOPE.relative_to(ROOT).as_posix(),
        source_playbook=correspondence['source'], source_playbook_sha256=correspondence['source_sha256'],
        qvoice_comments_contract='config/b_playbook_v11_contracts/qvoice-comments.json')
    config['existing_hr_features'].remove('ios_12m')
    config['feature_labels'].pop('ios_12m', None)
    config['qvoice']['extra_features'] += FEATURES
    config['feature_labels'].update(LABELS)
    config['extra_hr_queries'] = [
        {'name':'v11-categories', 'query':'queries/profiles/engineering_b_v11_categories_person_month_20261011_v2.sql',
         'features':['work_city','labor_market_detail','work_arrangement_v11','acquisition_detail']},
        {'name':'v11-grade-entry', 'query':'queries/profiles/engineering_b_v11_grade_entry_person_month_20261011.sql',
         'features':['current_grade_entry_path','time_since_grade_entry_band','pay_track_detail']},
        {'name':'v11-hierarchy', 'query':'queries/profiles/engineering_b_v11_hierarchy_person_month_20261011_v3.sql',
         'features':['hierarchy_depth_band']},
        {'name':'v11-manager-history', 'query':'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql',
         'features':['manager_observed_expected6_band','manager_team_exits6_v11','manager_above_average18']},
        {'name':'v11-timezone', 'query':'queries/profiles/engineering_b_v11_timezone_person_month_20261011_v3.sql',
         'features':TimezoneTransform.features, 'transform':'timezone_v11', 'input_columns':TimezoneTransform.input_columns},
        {'name':'v11-commute', 'query':'queries/profiles/engineering_b_v11_commute_inputs_20261011.sql',
         'features':CommuteTransform.features, 'transform':'commute_v11', 'input_columns':CommuteTransform.input_columns},
        {'name':'v11-stored-role', 'query':'queries/profiles/engineering_b_v11_stored_role_person_month_20261012.sql',
         'features':['time_in_role_stored_v11']},
    ]
    config['feature_labels'].update({
        'work_city':'Ciudad laboral', 'labor_market_detail':'Mercado laboral registrado',
        'work_arrangement_v11':'Modalidad en tres grupos del V11',
        'acquisition_detail':'Adquisición registrada: detalle',
        'current_grade_entry_path':'Entrada observada al grado actual',
        'time_since_grade_entry_band':'Tiempo desde entrada observada al grado',
        'pay_track_detail':'Track de compensación',
        'hierarchy_depth_band':'Profundidad jerárquica reconstruida',
        'manager_observed_expected6_band':'Salidas observadas/esperadas del manager, 6 intervalos',
        'manager_team_exits6_v11':'Salidas bajo el manager actual, 6 intervalos',
        'manager_above_average18':'Salidas sobre benchmark del manager, 18 intervalos',
        'manager_colocation_v11':'Coincidencia de sitio y ciudad con el manager',
        'manager_timezone_relation':'Relación horaria con el manager',
        'commute_distance_onsite_v11':'Aproximación postal a oficinas de la ciudad (Onsite)',
        'time_in_role_stored_v11':'Tiempo en rol almacenado: bandas V11',
    })
    config['extra_evidence'] = [
        'v11-city','v11-labor-market','v11-arrangement-v2','v11-acquisition','v11-grade-entry',
        'v11-hierarchy-v3','v11-hierarchy-synthetic-v3','v11-manager-feed',
        'v11-manager6-v2','v11-manager18-v3','v11-manager-gate-synthetic',
        'v11-timezone-v3','v11-timezone-prepared','v11-timezone-dst',
        'v11-commute-inputs','v11-commute-prepared','v11-qvoice-comments','v11-stored-role',
    ]
    # Estado describe preparación, no utilidad predictiva; ésta se determina después.
    views = {
      3: ('Movimientos IOS','No seleccionable',[],
          'Los seis motivos existen descriptivamente, pero sus cargas actuales no acreditan conocimiento histórico. Se retira también ios_12m; B no contiene IOS.'),
      4: ('Región y mercado laboral','Preparada',['region','work_country','labor_market_detail'],
          'Se prueban por separado región, país y mercado registrado en la propia foto.'),
      5: ('Modalidad de trabajo','Preparada',['work_arrangement_group','work_arrangement_v11'],
          'Se contrasta la agrupación anterior con los tres grupos exactos del V11, incluido Short-Term Remote Work.'),
      6: ('Engineering y otras funciones','Constante',[],
          'Engineering define la población de esta ronda; no discrimina dentro de ella.'),
      7: ('Recontratación','Obligatoria en B',['rehire'],'Se conserva la variable de B.'),
      8: ('Adquisiciones','Preparada',['acquisition_recorded','acquisition_detail'],
          'Se prueba presencia y detalle registrado; sin registro no demuestra contratación orgánica.'),
      9: ('Experiencia previa','Preparada',['prior_experience_band'],'Se conservan las bandas y desconocidos de la fuente histórica.'),
      10: ('Distancia estimada','Preparada con limitación',['commute_distance_onsite_v11'],
           'Aproximación postal a oficinas de la ciudad para Onsite. Mapping público estático; distancia mínima cuando hay varias oficinas. No es commute real validado.'),
      11: ('Temas de retención en comentarios QVoice','Preparada',
           ['qv_improvement_comment_presence']+[f for f in FEATURES if f in {
               'qv_comment_rewards','qv_comment_career','qv_comment_leadership','qv_comment_workload',
               'qv_comment_arrangement','qv_comment_processes','qv_comment_confidence'}],
           'Se incorporan los siete temas de la taxonomía completa y presencia de comentario de mejora, con waves 2024/2025 y desfase anual.'),
      12: ('Intención de permanecer: preguntas','Preparada',['qv_M16','qv_M14'],
           'Cada pregunta se prueba separada; los aliases Q4/Q12 no duplican variables.'),
      13: ('Metas profesionales','Preparada con limitación',['qv_career'],
           'Se mantiene la limitación de cambio de redacción en 2024.'),
      14: ('Promedio de preguntas comparables QVoice','Preparada',
           ['qv_mean33','qv_availability','qv_region_relative'],
           'Promedio de 33 ítems comunes, sus 33 pruebas individuales y controles de disponibilidad. La media relativa es respecto a la región contemporánea.'),
      15: ('Tiempo en nivel, perfil y rol','Preparada con historia corta',
           ['time_at_level_band','time_in_job_profile_band','time_in_role_stored_v11'],
           'Tres medidas distintas. Perfil aparece en noviembre de 2025 y rol almacenado en agosto de 2025; cada corte exige seis fotos observables. La fórmula de rol no se declara confirmada.'),
      16: ('Antigüedad en Qualcomm','Obligatoria en B',['tenure_playbook_band'],'Se conservan las seis bandas de B.'),
      17: ('Tiempo desde la última promoción','Obligatoria en B',
           ['time_since_promotion_band','current_grade_entry_path','time_since_grade_entry_band'],
           'B conserva su promoción. Las incorporaciones contrastan la entrada observada al grado dentro del episodio, sin afirmar contratación directa.'),
      18: ('Promoción y salidas por track','Parcial',
           ['time_since_promotion_band','grade_family','compensation_grade_detail','pay_track_detail'],
           'Track y grado se prueban; el flag promotion_yes_no de Annual Review queda fuera por falta de publicación histórica verificada. No se equipara a is_promo.'),
      19: ('Capas de la jerarquía','Preparada con límite semántico',
           ['layers_band','hierarchy_depth_band'],
           'Se comparan capa almacenada y profundidad reconstruida en la misma foto; una raíz no se denomina CEO sin validación de negocio.'),
      20: ('Tamaño del equipo directo','Obligatoria en B',['direct_reports_band'],
           'Se conserva el tamaño directo de B; no se confunde con el equipo del manager.'),
      21: ('Compa-ratio','Preparada con límite semántico',['comp_ratio_band'],
           'Bandas de la razón almacenada; no se afirma que su fórmula de origen esté validada.'),
      22: ('Salidas recientes bajo el manager actual','Preparada',
           ['team_exits_6m','team_exits_12m','manager_team_exits6_v11'],
           'Se distingue el contexto de compañeros de B del conteo V11 bajo el manager actual. Seis intervalos completos después del inicio del feed.'),
      23: ('Salida del manager','Preparada',['manager_left_6m'],
           'Salida anterior a la foto, con evento conocido y episodio vigente.'),
      24: ('Solicitudes de empleo','No seleccionable',[],
           'applications termina en octubre de 2024. La vista alternativa tiene eventos recientes, pero falta historial del vínculo y observabilidad. Ausencia de feed no equivale a cero solicitudes.'),
      25: ('Ubicación laboral','Preparada',['work_country','work_site','work_city'],
           'País, sitio y ciudad de la foto; no se usan domicilios como categorías.'),
      26: ('Sitio y ciudad de oficina','Preparada',['work_site','work_city'],
           'Se incorpora ciudad; algunos códigos de sitio representan varias ciudades.'),
      27: ('Salidas anteriores del equipo','Preparada',
           ['team_exits_3m','team_exits_6m','team_exit_recency_12m'],
           'El estudio por evento orienta la hipótesis; sólo se usan salidas conocidas antes de t.'),
      28: ('Sensibilidad: equipos de seis o más','Contexto',
           ['manager_team_size_band','team_exit_intensity_12m'],
           'El umbral de equipo es una sensibilidad del estudio; tamaño e intensidad se prueban como representaciones adicionales.'),
      29: ('Familia de puesto','Preparada',['job_family_detail','job_family_group'],
           'Detalle y grupo se prueban por separado; categorías raras se agrupan sólo con entrenamiento.'),
      30: ('Género','Fuera de autorización',[],
           'Atributo protegido excluido de la autorización de predicción; no se usa como feature.'),
      31: ('Comentarios sobre modalidad','Preparada',
           ['qv_comment_presence','qv_comment_remote','qv_comment_hybrid','qv_comment_office',
            'qv_remote_hybrid_request','qv_onsite_policy_concern'],
           'Presencia, menciones y peticiones se prueban por separado. No comentario, no enlace y ausencia de pregunta son distintos; mención no demuestra sentimiento.'),
      32: ('Heartbeat de QVoice','No seleccionable',[],
           '2024 no tiene escalas ordinales; 2025 tiene 52 de 53 y falta Q42. No se cambia el denominador ni se adelanta la wave 2026, asignada a 2027.'),
      33: ('Nivel','Obligatoria en B',['level_grouped'],'Se conserva el nivel de B.'),
      34: ('Familia de grado','Preparada',['grade_family','compensation_grade_detail','pay_track_detail'],
           'Se prueban prefijo de grado, código completo y track V11 por separado.'),
      35: ('Grados en las capas 0–2','Contexto',['hierarchy_depth_band','compensation_grade_detail'],
           'Es un cruce descriptivo; usa las mismas representaciones de jerarquía y grado, sin duplicarlas.'),
      36: ('Grado de compensación','Preparada',['compensation_grade_detail'],'Se usa el código, sin importes individuales.'),
      37: ('Compensación relativa dentro del equipo','Preparada',
           ['within_team_pay_position','manager_pay_spread_band'],
           'Pares comparables de país, grado y moneda. Recálculo independiente; ningún importe sale de SQL.'),
      38: ('Diferencia horaria con el manager','Preparada con limitación',['manager_timezone_relation'],
           'Catálogo público estático y offsets de cada foto con DST, verificados en 1,036 casos. No se acredita vigencia histórica de direcciones.'),
      39: ('Coincidencia de ubicación con el manager','Preparada',
           ['manager_location_relation','manager_colocation_v11'],
           'Se contrasta relación país/sitio/ciudad con coincidencia V11 de sitio y ciudad. Registro igual no demuestra proximidad física.'),
      40: ('Salidas observadas y esperadas del manager','Preparada',['manager_observed_expected6_band'],
           'Ratio con exposición histórica, benchmark por estratos y seis intervalos completos; no es una calificación del manager.'),
      41: ('Salidas del manager sobre el benchmark','Preparada',['manager_above_average18'],
           'Dieciocho intervalos completos, equipo promedio de al menos cuatro, dos salidas y umbral 1.3 veces el benchmark; historia desde abril de 2024.'),
      42: ('Cambio de manager','Obligatoria en B',['manager_changes_12m'],
           'La presencia del evento está contenida en el conteo obligatorio de B.'),
      43: ('Cantidad y recencia de cambios de manager','Preparada',
           ['manager_changes_12m','manager_changes_3m','manager_changes_6m'],
           'B conserva doce meses y se contrastan tres y seis meses. Las definiciones de grupo no se fuerzan a 22.'),
      44: ('Talent index','No seleccionable',[],
           'La metadata actual sólo contiene timestamps técnicos en master_talent_index; no hay fecha de negocio ni snapshot del índice para un enlace as-of.'),
    }
    records = []
    for row in correspondence['rows']:
        title,state,features,note = views[row['slide_number']]
        records.append({'slide':row['slide_number'], 'vista':title, 'prioritaria':row['priority'],
                        'estado':state, 'representaciones':features, 'explicacion':note,
                        'source_stage_id':row['source_stage_id'], 'source_title':row['title']})
    assert set(views)=={r['slide_number'] for r in correspondence['rows']}
    candidates = inc.hr_candidates(config)+inc.q_candidates(config)
    allowed = set(candidates)|set(inc.B_TERMS)
    assert set(f for r in records for f in r['representaciones']) <= allowed
    assert len(inc.hr_candidates(config))==41 and len(inc.q_candidates(config))==51
    assert 'ios_12m' not in candidates
    inc.mandatory_features(inc.hr_candidates(config),config)
    notes = [
        'El nombre «43 variables» identifica el playbook; contiene 42 vistas analíticas además de portada y navegación. No equivale a 43 columnas independientes.',
        'Se prepararon 41 incorporaciones RH y 51 QVoice, conservando ocho predictores y dos interacciones de B. Las 33 preguntas comunes están incluidas una sola vez cada una.',
        'IOS, aplicaciones, Heartbeat exacto y Talent index quedan fuera por las brechas verificadas; Annual Review queda parcialmente representado por promoción y track, con su flag de ciclo pendiente.',
        'El tiempo en perfil comienza en noviembre de 2025 y el rol almacenado en agosto de 2025. La elegibilidad se determina dentro de cada entrenamiento; preparación no significa historia suficiente.',
        'La distancia es una aproximación postal a oficinas de la ciudad para Onsite: todo el mapping resolvió por ciudad, hay oficinas alternativas y no hay país de domicilio estructurado. En 2026, 38,044 persona-fotos calculables superan 500 km. No se presenta como commute real validado.',
        'El catálogo geográfico público de 2026 se usa como aproximación estática retrospectiva. DAL.B está excluido y TIJNA.Z corregido con una entrada válida del catálogo.',
        'Los catorce indicadores de comentarios usan taxonomías completas congeladas. El prompt de mejora de procesos sólo existe desde 2025; los controles distinguen contenido y disponibilidad.',
        'Los grupos conservan las dimensiones de B para aislar el aporte de variables. La cantidad se recalcula por foto; el diagnóstico agregado por predicción ayuda a valorar la restricción de esos grupos.',
        'La búsqueda evalúa todas las incorporaciones individuales y pares/tríos de los seis mejores candidatos internos. No demuestra un óptimo global ni cambia modelos publicados.',
    ]
    scope = {'schema_version':1, 'reporting_mode':'presentation',
             'created_at':datetime.now(timezone.utc).isoformat(),
             'source':correspondence['source'], 'source_sha256':correspondence['source_sha256'],
             'source_manifest':correspondence['manifest'], 'source_manifest_sha256':correspondence['manifest_sha256'],
             'views':records, 'notes':notes, 'assessment_score_changed':False}
    extra = [SCOPE.relative_to(ROOT).as_posix(), correspondence['source'], correspondence['manifest'],
             config['qvoice_comments_contract'], 'tools/finalize_b_playbook_v11_config.py',
             'tools/b_v11_geography.py','tools/b_v11_commute.py','tools/b_v11_qvoice_comments.py',
             'tools/build_v7_manager_timezone_annual_attrition_evidence.py',
             'tools/build_global_commute_distance_evidence.py',
             'tools/build_qvoice_comment_evidence.py','tools/build_qvoice_retention_concerns_evidence.py',
             'tools/build_qvoice_open_text_request_concern_evidence.py',
             'tests/test_b_v11_geography.py','tests/test_b_v11_qvoice_comments.py',
             config['authorization'], config['source_c_config'], config['source_qvoice_metadata']]
    for name in config['extra_evidence']:
        path = OUT/'input-evidence'/f'{name}.json'
        evidence = base.read(path)
        if evidence['outcome']!='pass' or base.sha(ROOT/evidence['query'])!=evidence['sql_sha256']:
            raise RuntimeError('Entrada pendiente: '+name)
        extra.append(path.relative_to(ROOT).as_posix())
        if evidence.get('contract_path'):
            extra.append(evidence['contract_path'])
    for name in ['v11-commute-mapping','v11-qvoice-comment-keys','v11-ios-knowledge',
                 'v11-applications-history','v11-annual-review-history','v11-heartbeat-headers','v11-talent-metadata']:
        extra.append((OUT/'input-evidence'/f'{name}.json').relative_to(ROOT).as_posix())
    commute = base.read(OUT/'input-evidence/v11-commute-prepared.json')
    extra.append(commute['catalog'])
    extra += [source['path'] for source in commute['centroid_sources'].values() if source.get('path')]
    qcontract = base.read(ROOT/config['qvoice_comments_contract'])
    extra += [entry['source'] for entry in qcontract['sources']]
    qmeta = base.read(ROOT/config['source_qvoice_metadata'])
    extra.append('data/QVoice/survey_structure.xlsx')
    if base.sha(ROOT/'data/QVoice/survey_structure.xlsx')!=qmeta['dictionary_sha256']:
        raise RuntimeError('Cambió el diccionario QVoice.')
    for entry in qcontract['sources']:
        if base.sha(ROOT/entry['source'])!=entry['sha256']:
            raise RuntimeError('Cambió un archivo QVoice.')
    config['additional_reproducibility_sources'] = sorted(set(extra))
    config['preparation_limitations'] = notes[2:7]
    base.write(SCOPE,scope)
    base.write(CONFIG,config)
    print(json.dumps({'config':CONFIG.relative_to(ROOT).as_posix(), 'views':len(records),
        'hr_candidates':len(inc.hr_candidates(config)), 'qvoice_candidates':len(inc.q_candidates(config)),
        'mandatory_predictors':8,'mandatory_interactions':2,'frozen_sources':len(set(extra)),
        'training_started':False},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
