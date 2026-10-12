"""Informe y gráficos del experimento, exclusivamente desde resultados agregados."""
from __future__ import annotations

import csv
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

import engineering_b_incremental as inc
import engineering_model_c as base


def fmt(value,signed=False):
    if value is None:
        return '—'
    if 0<abs(float(value))<0.05:
        return ('+' if signed and value>0 else '−' if value<0 else '')+'<0.1'
    rounded = round(float(value),1)
    text = str(int(rounded)) if rounded.is_integer() else f'{rounded:.1f}'
    return ('+' if signed and rounded>0 else '')+text


def candidate_summary(result):
    rows = {}
    for period in result['periods']:
        for candidate in period['candidates']:
            anchor = candidate.get('anchor','B')
            key = (candidate['family'],anchor,candidate['feature'])
            row = rows.setdefault(key,{'family':key[0],'anchor':key[1],'feature':key[2],
                                       'comparisons':[],'failed_periods':[],'insufficient_history_periods':[]})
            if candidate['status']!='ok':
                row['failed_periods'].append(period['period']['id'])
                continue
            if candidate['family']=='RH' and not candidate['training_support']['eligible_for_selection']:
                row['insufficient_history_periods'].append(period['period']['id'])
                continue
            m,b = candidate['metrics'],period['metrics'][anchor]
            comparison = {'period':period['period']['id'],
                'brier_gain_relative_percent':100*(b['brier_score']-m['brier_score'])/b['brier_score'],
                'log_loss_gain_relative_percent':100*(b['log_loss']-m['log_loss'])/b['log_loss'],
                'capture_gain_pp':m['capture_percent']-b['capture_percent'],
                'group_error_reduction_pp':b['common_group_snapshot_mae_pp']-m['common_group_snapshot_mae_pp']}
            if candidate.get('matched_availability_metrics'):
                a = candidate['matched_availability_metrics']
                comparison['brier_gain_over_availability_percent'] = 100*(a['brier_score']-m['brier_score'])/a['brier_score']
            row['comparisons'].append(comparison)
    for row in rows.values():
        comp = row['comparisons']
        row['evaluated_periods'] = len(comp)
        row['brier_winning_periods'] = sum(x['brier_gain_relative_percent']>0 for x in comp)
        for field in ['brier_gain_relative_percent','log_loss_gain_relative_percent','capture_gain_pp',
                      'group_error_reduction_pp','brier_gain_over_availability_percent']:
            vals = [x[field] for x in comp if field in x]
            row[field] = float(np.mean(vals)) if vals else None
    return list(rows.values())


def inventory(config,out):
    if config.get('playbook_scope'):
        scope = base.read(base.ROOT/config['playbook_scope'])
        rows = scope['views']
        with (out/'inventario.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer = csv.DictWriter(f,fieldnames=['slide','vista','prioritaria','estado','representaciones','explicacion'])
            writer.writeheader()
            for row in rows:
                writer.writerow({k:('; '.join(row[k]) if isinstance(row[k],list) else row[k])
                                 for k in writer.fieldnames})
        return rows
    original = base.read(base.ROOT/'config/engineering_model_c_inventory_20261008.json')
    prepared = {
        3:'transfer_12m; ios_12m',4:'work_country; work_site',5:'within_team_pay_position; manager_pay_spread_band',
        6:'team_exit_intensity_12m; manager_team_size_band',7:'B: team_exits_12m',8:'job_family_detail; job_family_group',
        9:'region',11:'work_arrangement_group',13:'B: rehire',14:'prior_experience_band',
        18:'qv_availability (disponibilidad, no identifica inequívocamente no respuesta)',19:'qv_M16 (Q4); qv_M14 (Q12)',
        20:'qv_career (cambio de redacción)',21:'qv_mean33 (33 ítems comunes)',22:'qv_region_relative',
        26:'time_at_level_band; time_in_job_profile_band (fuente desde noviembre de 2025)',27:'B: tenure_playbook_band',
        28:'B: time_since_promotion_band',30:'B: level_grouped',31:'layers_band (capa registrada, no CEO validado)',
        32:'compensation_grade_detail; grade_family',33:'comp_ratio_band (razón almacenada)',34:'manager_location_relation',
        38:'manager_left_6m',39:'B: manager_changes_12m',40:'B: manager_changes_12m',
        42:'Representación parcial: transferencias, cambios de manager y promociones',44:'acquisition_recorded',45:'B: direct_reports_band'}
    excluded = {
        1:'Pendiente: cobertura de feed, enlace y conocimiento histórico de aplicaciones no confirmados; no imputar cero a ausencia de enlace.',
        2:'Pendiente: misma limitación de aplicaciones; no asumir ausencia de búsqueda de empleo.',
        10:'Excluida: atributo protegido fuera de la autorización de predicción.',
        12:'Constante: la población del experimento ya es Engineering.',
        15:'Pendiente: distancia residencial requiere integración histórica de domicilios/geografía fuera de las entradas autorizadas de este experimento.',
        16:'Pendiente: no hay indicador estructurado comparable en las fuentes QVoice enlazadas; no se procesa texto libre.',
        17:'Pendiente: no hay indicador estructurado comparable de comentario en las fuentes enlazadas.',
        23:'Pendiente: fuente externa con fecha de publicación no integrada.',
        24:'Pendiente: no se identificó una tabla Draup en el preflight; falta integración temporal.',
        25:'Pendiente: fuente LinkedIn no integrada y sin evidencia histórica de disponibilidad.',
        29:'Parcial: B conserva promociones/episodio; falta validar el evento exacto de entrada al grado actual.',
        35:'Pendiente: diferencia horaria o tiempo de viaje requiere definición y mapping temporal de sitios; la coincidencia de país no lo demuestra.',
        36:'Excluida: alto riesgo del manager no tiene definición histórica independiente del modelo y puede introducir circularidad.',
        37:'Parcial: se prueba la intensidad del equipo actual; no se equipara a toda la historia de personas que reportaron al empleado.',
        41:'Pendiente: metadata confirma ciclos y timestamps técnicos, sin fecha efectiva/publicación validada del índice.',
        43:'Excluida: identidades de líderes no son predictores autorizados; profundidad registrada se trata por separado.'}
    rows = []
    for item in original:
        number = item['order']
        rows.append({'order':number,'inventory_concept':item['variable'],
                     'disposition':prepared.get(number,excluded.get(number,'Pendiente de definición'))})
    with (out/'inventario.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return rows


def bar_chart(rows,config,path,title,expected):
    eligible = [r for r in rows if r['evaluated_periods']==expected and r['brier_gain_relative_percent'] is not None]
    eligible.sort(key=lambda r:r['brier_gain_relative_percent'])
    if not eligible:
        return
    labels = [config['feature_labels'][r['feature']].replace('QVoice: ','') for r in eligible]
    values = [r['brier_gain_relative_percent'] for r in eligible]
    fig,ax = plt.subplots(figsize=(11,max(5,len(eligible)*.34+1.4)))
    fig.patch.set_facecolor('#f7f9fc');ax.set_facecolor('#f7f9fc')
    y = np.arange(len(values))
    colors = ['#147d92' if v>0 else '#b7c1ce' for v in values]
    ax.barh(y,values,color=colors,height=.7)
    ax.axvline(0,color='#556476',lw=.8)
    ax.set_yticks(y,labels,fontsize=9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,pos:fmt(v)))
    ax.set_xlabel('Mejora relativa de Brier frente al mismo modelo base (%) · positivo mejora',fontsize=10)
    ax.set_title(title+'\n'+f'{expected} periodos con historia suficiente; cada variable se añade por separado',loc='left',fontsize=13,pad=16)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='y',length=0)
    ax.grid(axis='x',color='#dde3eb',alpha=.65);ax.set_axisbelow(True)
    fig.text(.015,.015,'Engineering · salidas voluntarias en los seis meses siguientes. '
             'Fuente: results.json y comparacion-variables.csv; corte '+config['knowledge_boundary']+'.',
             fontsize=8,color='#556476',ha='left')
    fig.tight_layout(rect=(0,.045,1,1))
    fig.savefig(path,dpi=170,facecolor=fig.get_facecolor())
    plt.close(fig)


def build(result,config,out):
    out = Path(out)
    summaries = candidate_summary(result)
    inc.write(out/'candidate-summary.json',summaries)
    flat = [{k:('; '.join(v) if k in ('failed_periods','insufficient_history_periods') else v)
             for k,v in r.items() if k!='comparisons'} for r in summaries]
    if flat:
        with (out/'comparacion-variables.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer = csv.DictWriter(f,fieldnames=list(flat[0]))
            writer.writeheader()
            writer.writerows({k:fmt(v) if isinstance(v,float) else v for k,v in row.items()} for row in flat)
    inventory(config,out)
    hr = [r for r in summaries if r['family']=='RH']
    qr = [r for r in summaries if r['family']=='QVoice' and r['anchor']=='B']
    def title(rows,periods,fallback):
        eligible=[r for r in rows if r['evaluated_periods']==periods and r['brier_gain_relative_percent'] is not None]
        if not eligible:
            return fallback
        best=max(eligible,key=lambda r:r['brier_gain_relative_percent'])
        if best['brier_gain_relative_percent']<=0:
            return 'Las incorporaciones individuales no reducen Brier en promedio'
        label=config['feature_labels'][best['feature']].replace('QVoice: ','')
        return textwrap.fill(label+' aporta la mayor reducción media de Brier',width=80)
    bar_chart(hr,config,out/'variables-rh.png',title(hr,5,'Qué añade cada variable a B'),5)
    bar_chart(qr,config,out/'variables-qvoice.png',title(qr,2,'Qué añade cada señal de QVoice a B'),2)
    lines = ['# B completo como base: qué aportan las incorporaciones','',
             'Modo `presentation`. Ejecución `'+str(result.get('run_id',''))+'`; datos conocidos hasta '+config['knowledge_boundary']+'.','',
             f'Se conservaron los **ocho predictores y las dos interacciones de B**. Se examinaron **{len(result["hr_candidates"])} incorporaciones de RH** '
             f'y **{len(result["qvoice_candidates"])} señales de QVoice**, una por una. Dentro de cada corte se evaluaron también todos los pares y tríos de una lista de seis elegida sólo con datos pasados.','',
             'Los grupos permanecen en antigüedad × salidas previas del equipo × nivel. La captura se mide al priorizar grupos que cubren el 30% de las personas; cada grupo elegible tiene al menos 300 personas por foto.','',
             '## Selección final experimental','']
    additions = result['final']['hr_additions']
    lines.append('Incorporaciones de RH: '+(', '.join(config['feature_labels'][f] for f in additions) if additions else '**ninguna superó la regla interna frente a B**')+'.')
    lines.append('')
    for anchor,choice in result['final']['qvoice'].items():
        text = ', '.join(config['feature_labels'][f] for f in choice['features']) or 'sin preguntas adicionales'
        lines.append(f'- Sobre {anchor}: {text}; ajuste `{choice["kind"]}`.')
    lines += ['',f'Corte final: {result["final"]["cutoff"]}. Los coeficientes finales no se usaron para simular resultados externos anteriores. No se sustituyó ningún modelo publicado.','',
              '## Resultado temporal de la regla de selección','',
              'Las cifras de cada alternativa corresponden al proceso que selecciona sólo con pasado. Las variables elegidas pueden cambiar entre periodos.','',
              '| Ventana | Alternativa | Salidas captadas (%) | Brier × 1000 | Error de los mismos grupos (pp) |',
              '|---|---|---:|---:|---:|']
    for scope,models in result['summary'].items():
        for name,metrics in models.items():
            lines.append(f'| {scope} · {len(metrics["periods"])} periodos | {name} | {fmt(metrics["capture_percent"])} | {fmt(1000*metrics["brier_score"])} | {fmt(metrics["common_group_snapshot_mae_pp"])} |')
    lines += ['', 'RH usa cinco ventanas de feb-2024 a feb-2026. QVoice usa ago-dic-2025 y ene-feb-2026. Comparar alternativas dentro de la misma ventana de esta tabla. Brier y error de grupos: menor es mejor.','',
              'Los controles `refresh` sólo actualizan el intercepto. Cada pregunta tiene además un control con sus mismos estados de disponibilidad, para distinguir contenido de encuesta de calibración y ausencia de respuesta.','',
              '## Variables individuales','',
              'Las tablas sólo promedian los periodos con historia suficiente en entrenamiento y comparan cada incorporación contra su base en esos mismos periodos. Los resultados de una y cinco ventanas no son equivalentes. Las tablas individuales son exploratorias; la selección final se hizo dentro de cada corte.','']
    if config.get('playbook_scope'):
        scope = base.read(base.ROOT/config['playbook_scope'])
        lines += ['La fuente de alcance es el **playbook V11 de 43 variables**, identificado por su hash en la configuración. Sus vistas se cruzan una por una con las representaciones y limitaciones de esta ejecución.','',
                  '## Selecciones por periodo','',
                  '| Periodo | Incorporaciones RH | QVoice sobre B | Grupos elegibles de B por foto |',
                  '|---|---|---|---:|']
        for row in result['periods']:
            rh = ', '.join(config['feature_labels'][f] for f in row['hr_selection']) or 'B completo'
            selected_q = row.get('qvoice_selections',{}).get('B')
            qs = ', '.join(config['feature_labels'][f] for f in selected_q['features']) if selected_q else 'Fuera de ventana QVoice'
            if selected_q and not qs:
                qs = 'Sin contenido adicional ('+selected_q['kind']+')'
            metrics = row['metrics']['B']
            lo,hi = metrics['minimum_eligible_groups'],metrics['maximum_eligible_groups']
            count = str(lo) if lo==hi else f'{lo}–{hi}'
            lines.append(f'| {row["period"]["id"]} | {rh} | {qs} | {count} |')
        lines += ['', 'Se mantienen las dimensiones de los grupos de B para medir el efecto de las variables. El número de grupos elegibles se recalcula por foto; no se fuerza a 22. Esta comparación no busca un óptimo de agrupaciones.','',
                  '| Ventana | Modelo | Captura por grupos (%) | Diagnóstico por predicción (%) | Diferencia (pp) |',
                  '|---|---|---:|---:|---:|']
        for window,models in result['summary'].items():
            for model in ['B','B_RH','B_Q','B_RH_Q']:
                if model in models:
                    m=models[model]
                    lines.append(f'| {window} | {model} | {fmt(m["capture_percent"])} | {fmt(m["individual_capacity_capture_percent"])} | {fmt(m["individual_minus_group_capture_pp"],True)} |')
        lines += ['', 'El diagnóstico usa la misma capacidad del 30% en cada foto y reparte los empates proporcionalmente. Sólo se conservan resultados agregados; no se publica una lista de personas. Una diferencia positiva indica mayor captura observada al ordenar las predicciones sin la restricción de los grupos actuales; no demuestra un óptimo ni una política operativa.','',
                  '## Preparaciones y límites del playbook','']
        lines += ['- '+item for item in scope['notes']]
        lines += ['', 'La falta de historia verificable se distingue de una variable que sí se probó y no mejoró el modelo. Véase el [inventario por vista del V11](inventario.csv).','']
    for name,rows,expected,image in [('RH',hr,5,'variables-rh.png'),('QVoice sobre B',qr,2,'variables-qvoice.png')]:
        lines += [f'### {name}','',f'![Incorporaciones individuales]({image})','',
                  '| Incorporación | Periodos | Mejora de Brier (%) | Cambio de captura (pp) | Periodos con mejor Brier |',
                  '|---|---:|---:|---:|---:|']
        rows.sort(key=lambda r:(-r['evaluated_periods'],-(r['brier_gain_relative_percent'] if r['brier_gain_relative_percent'] is not None else -1e6)))
        for r in rows:
            lines.append(f'| {config["feature_labels"][r["feature"]]} | {r["evaluated_periods"]}/{expected} | {fmt(r["brier_gain_relative_percent"],True)} | {fmt(r["capture_gain_pp"],True)} | {r["brier_winning_periods"]} |')
        lines.append('')
    lines += ['## Estabilidad y límites','',
              '| Comparación pareada | IC 95% del cambio de captura (pp) |',
              '|---|---:|']
    for interval in result['intervals']:
        if interval:
            lo,hi = interval['capture_delta_pp']
            lines.append(f'| {interval["left"]} frente a {interval["right"]} | {fmt(lo,True)} a {fmt(hi,True)} |')
    lines += ['', 'Intervalos con personas completas remuestreadas en RAM, conservando juntas sus observaciones y dando el mismo peso a cada periodo. Son condicionales a las selecciones ya realizadas; no convierten una búsqueda retrospectiva en confirmación prospectiva.','']
    lines += ['- '+s for s in result['limitations']]
    lines += ['', 'La posición salarial relativa sólo se calcula en grupos de cinco o más personas con el mismo manager, país, grado y moneda; el resto mantiene una categoría no comparable. La dispersión usa grupos comparables de dos o más. Sus importes se quedan dentro de SQL.','',
              '## Evidencia y reproducción','',
              '- [Inventario completo y motivo de cada exclusión](inventario.csv).',
              '- [Resultados por variable](comparacion-variables.csv) y [resultados completos](results.json).',
              '- [Consultas y evidencia de entradas](evidence-ledger.json).',
              '- [Configuración congelada](frozen-config.json), [validación](verification.json) y [manifest](manifest.json).',
              '- `selection/`: decisiones internas; `periods/`: evaluación externa; `models/`: artefactos experimentales reproducibles.','',
              'Las categorías infrecuentes de las incorporaciones RH se agrupan sólo a partir de entrenamiento. Los ocho predictores de B y sus dos interacciones siempre permanecen. No se modificaron scores de assessment ni se guardaron filas, llaves o predicciones individuales.','']
    (out/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
