"""Reutiliza documentación V11; no consulta datos ni modifica scores."""
from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/analysis/engineering/20261012/julia-rh-review-v1'
DOC = ROOT / 'output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion'
CQ = ROOT / 'output/analysis/engineering/20261008/model-c-plus-qvoice-v1'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


# Relación explícita de las 43 filas de Julia, sin sustituirlas por otro inventario.
FEATURES = [
    ['ios_12m','transfer_12m'], ['region'], ['labor_market_detail'],
    ['work_arrangement_group','work_arrangement_v11'], [], ['rehire'],
    ['acquisition_recorded','acquisition_detail'], ['prior_experience_band'],
    ['commute_distance_onsite_v11'], [], ['qv_Q4','qv_Q12'], ['qv_career'],
    ['qv_mean33','qv_availability','qv_region_relative'],
    ['time_at_level_band','time_in_job_profile_band','time_in_role_stored_v11'],
    ['tenure_playbook_band'], ['time_since_promotion_band','current_grade_entry_path','time_since_grade_entry_band'],
    ['time_since_promotion_band','grade_family','pay_track_detail','compensation_grade_detail'],
    ['layers_band','hierarchy_depth_band'], ['direct_reports_band'], ['comp_ratio_band'],
    ['team_exits_12m','team_exits_6m','manager_team_exits6_v11'], ['manager_left_6m'], [],
    ['work_country','work_site','work_city'], ['work_site','work_city'],
    ['team_exits_3m','team_exits_6m','team_exit_recency_12m'],
    ['manager_team_size_band','team_exit_intensity_12m'], ['job_family_detail','job_family_group'], [], [], [],
    ['level_grouped'], ['grade_family','pay_track_detail','compensation_grade_detail'],
    ['hierarchy_depth_band','compensation_grade_detail'], ['compensation_grade_detail'],
    ['within_team_pay_position','manager_pay_spread_band'], ['manager_timezone_relation'],
    ['manager_location_relation','manager_colocation_v11'], ['manager_observed_expected6_band'],
    ['manager_above_average18'], ['manager_changes_12m'],
    ['manager_changes_12m','manager_changes_3m','manager_changes_6m'], [], ['bu_l3']]

ACTION_GROUPS = [
    ({1,14,16,17,23}, 'Revisar acceso a movilidad y desarrollo', 'RH y Desarrollo', 'Criterios de movilidad, cobertura histórica y conversaciones de carrera', 'Conversaciones completadas y acceso a oportunidades'),
    ({4,9,30,37,38}, 'Validar coordinación y condiciones de trabajo', 'RH y Operaciones', 'Modalidad efectiva, tiempos de coordinación y escucha agregada', 'Acuerdos de coordinación revisados'),
    ({10,11,12,13,31}, 'Contrastar temas con escucha estructurada', 'RH y equipo de Encuestas', 'Respuestas suficientes, redacción comparable y fecha de publicación', 'Cobertura de escucha y acciones con seguimiento'),
    ({18,19,21,22,26,27,39,40,41,42}, 'Revisar continuidad, vacantes y soporte del equipo', 'RH y liderazgo operativo', 'Historial de reorganización, carga y vacantes; sin atribuir culpa al manager', 'Vacantes y acuerdos de soporte revisados'),
    ({20,33,34,35,36}, 'Revisar criterios de compensación por cohorte', 'Compensación y RH', 'Comparabilidad de grado, moneda y bandas; no usar salarios individuales', 'Cohortes con revisión de criterios completada'),
    ({2,3,5,6,7,8,15,24,25,28,32,44}, 'Localizar población y validar necesidades organizacionales', 'RH de la población o unidad', 'Contexto local, antigüedad, reorganizaciones y comparabilidad', 'Grupos con responsable y conversación documentados'),
    ({29,43}, 'Resolver alcance y definición antes de cualquier uso', 'Gobierno de datos y RH', 'Autorización, definición y disponibilidad histórica', 'Brechas documentadas y resueltas')]


def action(number):
    return next(x[1:] for x in ACTION_GROUPS if number in x[0])


def main():
    destination = OUT / 'documentacion'
    destination.mkdir(parents=True, exist_ok=True)
    original = (ROOT / 'planes/modelo_c/43_variables_playbook_modelo_final_20261012.md').read_text(encoding='utf-8')
    refs = dict(re.findall(r'^\[([^]]+)\]: (.+)$', original, re.M))
    dictionary = {v['feature']:v for v in read(DOC/'diccionario.json')['variables']}
    rows = []
    for line in original.splitlines():
        if re.match(r'^\| \d+ \|', line):
            parts = [s.strip() for s in line.strip('|').split('|')]
            n = int(parts[0])
            rows.append({'numero': n, 'variable': re.sub(r'\[([^]]+)\]\[[^]]+\]', r'\1', parts[1]),
                         'representaciones': FEATURES[n-1], 'preparacion_v11': parts[3],
                         'resultado_historico_B_V11_no_CQ': parts[4],
                         'detalle': sorted(set(refs[k] for k in re.findall(r'\]\[([^]]+)\]', line) if k in refs))})
    assert len(rows) == 43
    rows.append({'numero':44,'variable':'BU L3','representaciones':['bu_l3'],
                 'preparacion_v11':'Join as-of con d_department; desconocido separado; BU con menos de 300 personas de entrenamiento → (other). Indicadores nominales.',
                 'resultado_historico_B_V11_no_CQ':'No pertenece al playbook V11. La corrida BU v7 respalda mejora modesta de log-loss. Su REST selectivo no es comparable y se recalculará.',
                 'detalle':['../../docs/variables/bu-l3/README.md']})
    models = {p:read(CQ/'folds'/p/'model.json') for p in ['aug_dec_2025','jan_feb_2026']}
    for row in rows:
        n = row['numero']
        act, owner, evidence, indicator = action(n)
        row.update(accion_candidata=act, responsable_funcion=owner, evidencia_RH=evidence,
                   indicador=indicator, plazo_sugerido='30 días para contraste; 90 días para seguimiento',
                   clasificacion={'potencialmente_accionable': n in {1,4,9,10,11,12,14,16,17,19,20,21,22,23,26,27,30,36,37,38,39,40,41,42},
                                  'util_para_priorizar':n not in {29,43}, 'inadecuada_para_explicacion_individual':True,
                                  'requiere_cautela':True},
                   limitacion='Asociación retrospectiva; la acción es una hipótesis organizacional, sin efecto causal estimado.',
                   uso_por_modelo_corte={}, tratamientos_existentes=[])
        for f in row['representaciones']:
            alias = {'qv_Q4':'qv_M16','qv_Q12':'qv_M14'}.get(f,f)
            if alias in dictionary:
                row['tratamientos_existentes'].append({k:dictionary[alias].get(k) for k in
                    ['feature','source_fields','input_type','source_values','transformation','missing_and_default','known_at','sources','considerations']})
        for period, artifact in models.items():
            for name in ['CQ','FQ','FQ_BU_L3']:
                used = set(artifact['base_model']['features'] + artifact['selected']['features'])
                if name != 'CQ': used.add('work_city')
                if name == 'FQ_BU_L3': used.add('bu_l3')
                predictors = [f for f in row['representaciones'] if f in used]
                groups = [f for f in row['representaciones'] if f in ['tenure_playbook_band','team_exits_12m','level_grouped']]
                diagnostics = [f for f in row['representaciones'] if f in ['region','tenure_playbook_band','level_grouped']]
                row['uso_por_modelo_corte'][period+'/'+name] = {
                    'predictor':predictors, 'definicion_grupos':groups,
                    'diagnostico':diagnostics, 'subdivision_experimental':n==44,
                    'excluidas_de_esta_comparacion':[f for f in row['representaciones'] if f not in used],
                    'filtro_poblacion':n==5,
                    'motivo':'Composición congelada por el plan; no hay nueva búsqueda ni prueba de eliminación.' if predictors else
                             'Fuera de la composición congelada; el resultado histórico de B no estima un efecto sobre CQ/FQ.'}
        if n == 1:
            row['limitacion'] += ' IOS permanece en C histórico, aunque V11 lo excluyó por falta de acreditación temporal. Reproducir CQ no resuelve esta brecha.'
        if n == 28:
            row['limitacion'] += ' job_family_detail se excluye expresamente de los tres modelos por historia no confiable.'
    write(destination/'variables-44.json', {'reporting_mode':'presentation','assessment_score_changed':False,'rows':rows})
    lines = ['# Las 44 filas para Julia y RH', '',
             'Modo `presentation`. Revisión documental previa al cálculo. 43 filas del resumen V11 más BU L3; no son 44 predictores independientes.', '',
             'CQ es la referencia elegida. FQ añade ciudad; FQ + BU L3 añade también unidad. Se conservan las selecciones de cada corte. Las propuestas son hipótesis organizacionales; todas requieren cautela y son inadecuadas para explicaciones individuales.', '',
             'La preparación y el resultado de B V11 se conservan como contexto en el JSON y en las fichas enlazadas. No se atribuyen a CQ ni a FQ. Las referencias/categorías exactas de los modelos restaurados y ajustados se entregan en `codificaciones-modelos.json` al terminar el cálculo.', '',
             '| # | Variable y representaciones | Uso en CQ / FQ / FQ + BU L3 | Acción y responsable | Contraste RH / seguimiento | Detalle |',
             '|---|---|---|---|---|---|']
    for row in rows:
        n=row['numero']
        use=[]
        for period in models:
            parts=[]
            for model in ['CQ','FQ','FQ_BU_L3']:
                d=row['uso_por_modelo_corte'][period+'/'+model]
                text=', '.join(d['predictor']) or ('filtro' if d['filtro_poblacion'] else 'sin predictor')
                parts.append(model+': '+text)
            use.append(period+': '+'; '.join(parts))
        links=[]
        for i, p in enumerate(row['detalle']):
            absolute=(ROOT/'planes/modelo_c'/p).resolve()
            import os
            links.append(f'[Ficha {i+1}]({Path(os.path.relpath(absolute,destination)).as_posix()})')
        lines.append('| '+ ' | '.join([str(n),row['variable']+'; '+', '.join(row['representaciones']), '<br>'.join(use),
            row['accion_candidata']+' — '+row['responsable_funcion'], row['evidencia_RH']+'; '+row['indicador'], ', '.join(links)])+' |')
    lines += ['', 'QVoice histórico también contiene Engagement (Q1/Q2/Q3) y, en 2026, Confidence (Q13/Q17); son representaciones del bloque de encuesta, no filas nuevas del inventario. En 2025 entran Q4, Q12, Career y Engagement; en 2026 Q4, Career, Engagement y Confidence. El promedio no entra en estos dos cortes.', '',
              'Hallazgo de preparación: IOS forma parte del C histórico y por eso se conserva para reproducirlo. V11 documentó falta de prueba de conocimiento histórico de IOS. Esta revisión no acredita ausencia total de información futura; el límite debe acompañar cualquier recomendación.', '',
              'Calendario e interacción nivel × antigüedad se documentan en los modelos guardados; no se cuentan como filas adicionales del playbook.']
    (destination/'variables-44.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    matrix = [
        ('Salida comprensible y accionable','Revisión Julia/Brian y marco de acciones','Fichas históricas con tema, responsable e indicador','Investigar necesidades de cohortes; no etiquetar personas.'),
        ('Personas sin QVoice utilizable','Encoder distingue ausencia y episodio; CQ guarda coeficientes','Completa/parcial/ausente, error y contraste RH en las mismas personas','Ausencia no implica descontento ni retorno automático a RH.'),
        ('Clasificar variables','43 filas V11 y fichas; BU L3 documentada','Cruzar composición por corte y categorías de uso','44 filas documentales; no 44 predictores independientes.'),
        ('Personas, salidas e incertidumbre','CQ conserva resúmenes parciales','Headcount/foto, personas distintas, exposiciones y eventos únicos','IC observado e IC aproximado del riesgo medio tienen métodos distintos.'),
        ('Capacidades 10/20/30','FQ resume 30%; CQ tiene 20/30/40','Exacta ponderada e inclusión/exclusión de frontera','Capacidad describe atención; no probabilidad de salida.'),
        ('Calibración','CQ usa identidad; FQ sin curvas completas','Sesgo por fecha, grupo y cinco bandas previas; R6 condicionado','Aplicar corrección sólo con historia y mejora posterior.'),
        ('Estabilidad mensual','Ganancia en bloques no mide continuidad','Riesgo, ranking y prioridad entre personas comunes; composición aparte','Señalar cambio de wave, modelo y grupo.'),
        ('Concentración por segmento','Métricas globales insuficientes','Región, nivel, antigüedad y QVoice con soporte y error','Diferencia descriptiva no demuestra sesgo injustificado.'),
        ('Grupos BU más específicos','REST v7 mezcla no prioridad con residual','Partición exhaustiva; mínimos 100/150/200; guardas','Conservar padres cuando la subdivisión no es viable.'),
        ('Uso organizacional','Autorización de entrenamiento sólo en RAM','Supresión de tasas y campos reconstruibles; agregados','No publicar scores, listas ni explicaciones individuales.')]
    write(destination/'matriz-comentarios.json',{'stage':'documental_antes_del_calculo','created_at':datetime.now(timezone.utc).isoformat(),
          'source':'docs/plans/revision-julia-brian-salida-rh-20261012.md','rows':[dict(zip(['comentario','evidencia_existente','comprobacion_pendiente','respuesta_RH'],x)) for x in matrix]})
    (destination/'matriz-comentarios.md').write_text('# Comentarios de Julia: evidencia y comprobación\n\nModo `presentation`. Primera entrega documental; las pruebas pendientes no se presentan como ejecutadas. Fuente: [revisión previa](../../../../../../docs/plans/revision-julia-brian-salida-rh-20261012.md).\n\n| Comentario | Evidencia existente | Comprobación pendiente | Respuesta propuesta para RH |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(x)+' |' for x in matrix)+'\n',encoding='utf-8')
    write(destination/'verification-documental.json',{'rows':len(rows),'unique_rows':len({r['numero'] for r in rows}),
          'model_period_roles':sum(len(r['uso_por_modelo_corte']) for r in rows),'all_actions_present':all(r['accion_candidata'] for r in rows),
          'assessment_score_changed':False,'status':'pass'})
    print('Primera entrega documental: 44 filas y 10 comentarios; 264 usos por modelo/corte.')


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT)
    OUT=parser.parse_args().output.resolve()
    main()
