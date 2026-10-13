"""Revisión de la copia de evolución elegida para este encargo; sólo agregados."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from html import escape
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/analysis/engineering/20261012/julia-rh-review-v1'
BASE=ROOT/'output/presentations/20261012-0833_evolucion-b-cq-error-vs-c/presentacion-eng.html'
OUT=ROOT/'output/presentations/20261012-2350_revision-julia-rh'
TEMPLATE=Path('C:/Users/fcarranz/.codex/skills/html-slide-generator/templates/fullscreen/base-fullscreen.html')
LABEL={'CQ':'CQ','FQ':'FQ','FQ_BU_L3':'FQ + BU L3'}
PERIOD={'aug_dec_2025':'Aug–Dec 2025','jan_feb_2026':'Jan–Feb 2026'}

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def f(v):
    if v is None:return 'Withheld'
    if abs(v)<.05 and v!=0:return '&lt;0.1' if v>0 else 'just below 0'
    return f'{v:,.1f}'.rstrip('0').rstrip('.').replace('-', '−') if v!=int(v) else f'{int(v):,}'
def ci(x,scale=1):return '['+', '.join(f(v*scale) for v in x)+']'
def table(headers,rows):
    return '<table class="review-table"><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def stage(number,title,subtitle,body,source='J01 · Engineering · active regular employees, excl. RF360 · Aug–Dec 2025 and Jan–Feb 2026 · 6-month follow-up · equal period weights'):
    return f'<div class="slide-stage review-stage data-context" id="slide-{number}"><div class="slide-heading"><div><h2 class="slide-title-text">{title}</h2><p class="slide-subtitle">{subtitle}</p></div></div><div class="review-body">{body}</div><div class="src">{source}</div></div>'
def box(head,body):return f'<article class="card review-note"><h3>{head}</h3><p>{body}</p></article>'

def build():
    d=read(RUN/'results.json');s=d['summary'];supp=read(RUN/'cohort-diagnostics-supplement.json')
    assert read(RUN/'verification.json')['archived_CQ_reproduced']
    OUT.mkdir(parents=True,exist_ok=True)
    shutil.copy2(TEMPLATE,OUT/'template-origin.html')
    # La plantilla se copia primero; esta revisión conserva CSS, JS y contenido
    # útil de la copia existente en lugar de regenerar desde una revisión vieja.
    target=OUT/'presentacion-eng.html';shutil.copy2(TEMPLATE,target)
    html=BASE.read_text(encoding='utf-8')
    html=html.replace('<title>Engineering attrition: from the core HR model to HR + employee feedback (CQ)</title>','<title>Engineering attrition — Julia review: estimation and HR readiness</title>')
    if 'deliverable-classification' not in html:
        html=html.replace('<head>','<head>\n<meta name="deliverable-classification" content="presentation">')
    html=html.replace('</head>','<link rel="icon" href="data:,">\n</head>')
    html=html.replace('Further tests did not justify replacing CQ','Earlier tests did not justify replacing CQ')
    html=html.replace('>Entry</','>Levels 7–8</').replace('>Mid</','>Levels 5–6</').replace('>Senior</','>Levels 1–3</')
    html=html.replace('6-month follow-up ·','6-month follow-up, overlapping snapshots ·')
    html=html.replace('<span class="mark m-open">○ Open</span> — not found in the studies reviewed','<span class="mark m-part">◐ Descriptive checks completed</span> — region, level, tenure and survey coverage; interpretation still needed')
    html=html.replace('From our starting model to today\'s choice','From the selected model to a fuller HR review')
    html=html.replace('<div class="ag-head">Further checks</div><div class="ag-slides">Slide 8</div><div class="ag-body">Survey mixes, additional signals (D) and an alternative method</div>','<div class="ag-head">Model and group checks</div><div class="ag-slides">Slides 8–11</div><div class="ag-body">Earlier tests, city, BU L3 and capacity</div>')
    html=html.replace('<div class="ag-slides">Slide 9</div><div class="ag-body">Confirm, review, pilot</div>','<div class="ag-slides">Slides 12–16</div><div class="ag-body">Survey coverage, calibration, stability and HR review</div>')
    html=html.replace('A pilot has not started.</div>','A pilot has not started. New candidates and HR diagnostics follow in slides 9–16.</div>')
    slides=[]
    differences=d['paired_differences']
    compare=table(['Model','Log-loss × 1,000 ↓','Brier × 1,000 ↓','Exits captured at 30% ↑','Group gap ↓'],[
        [LABEL[n],f(s[n]['30']['log_loss']*1000),f(s[n]['30']['brier']*1000),f(s[n]['30']['capture_percent'])+'%',f(s[n]['30']['group_snapshot_mae_pp'])+' pp'] for n in LABEL])
    delta=differences['FQ_minus_CQ']['30']['log_loss'];bu=differences['FQ_BU_L3_minus_FQ']['30']['log_loss']
    slides.append(stage(9,'FQ and FQ + BU L3 improve estimates; capture at 30% stays similar',
        'FQ = C + work city + QVoice · FQ + BU L3 adds the historical business-unit mapping · common group definitions',
        '<article class="card review-main">'+compare+'</article><div class="review-two">'+
        box('FQ vs CQ',f(delta['difference']*1000)+' log-loss × 1,000<br>95% CI '+ci(delta['ci95'],1000))+
        box('BU L3 added to FQ',f(bu['difference']*1000)+' log-loss × 1,000<br>95% CI '+ci(bu['ci95'],1000))+'</div><p class="review-caption">Lower losses mean closer probabilities. CQ retains its August HR base for January; FQ refits it. This comparison includes both city and a newer HR fit. BU vs FQ shares the same training origins. CQ remains selected.</p>'))
    caprows=[]
    for cap in ['10','20','30']:
        people=np.mean([np.mean([r['effective_people_selected'] for r in p['models']['CQ']['capacities'][cap]['monthly']]) for p in d['periods']])
        caprows.append([cap+'%',f(people),*[f(s[n][cap]['capture_percent'])+'%' for n in LABEL]])
    slides.append(stage(10,'Capacity changes how many exits the groups contain','Exact weighted capacity at each snapshot · same tenure × team exits × level groups, each with at least 300 people',
       '<article class="card review-main">'+table(['Capacity','Equivalent people / snapshot','CQ capture','FQ capture','FQ + BU L3 capture'],caprows)+'</article>'+
       box('A practical decision for HR','Agree how many people and groups can receive attention. The report includes both whole-group alternatives at the boundary: include or exclude the full tied block.')+
       '<p class="review-caption">Weighted capacity spreads the boundary fraction uniformly across the group. It does not identify individuals. Capture counts exit-bearing exposures in overlapping six-month windows.</p>'))
    subrows=[]
    for cap,minim in [(10,100),(10,150),(10,200),(30,100)]:
        r=next(r for r in d['subdivision'] if r['model']=='FQ_BU_L3' and r['capacity']==cap and r['minimum']==minim)
        subrows.append([str(cap)+'%',str(minim),f(r['median_people']),f(r['capture_percent'])+'%',f(r['error_pp'])+' pp','Pass' if r['passes_both_periods'] else 'Fail'])
    slides.append(stage(11,'The 100-person BU split does not pass the safeguards','FQ + BU L3 shown · no main 100-person scenario passes in both periods for any of the three models',
       '<article class="card review-main">'+table(['Capacity','Minimum child size','Median group size','Capture','Group gap','Both periods'],subrows)+'</article>'+
       box('Only the 10% sensitivities pass','Minimum sizes of 150 and 200 pass for FQ + BU L3. Keep them as limited scenarios to validate; this does not support a general switch to smaller groups.')+
       '<p class="review-caption">Every scenario preserves capacity and true REST. Pass also requires a smaller median group, capture loss ≤2% relative and gap increase ≤0.1 pp. Decisions use unrounded values; nonprioritized parents remain intact.</p>'))
    latest=d['periods'][1];qm=latest['models']['FQ_BU_L3'];qrows=qm['diagnostics']['qvoice']
    qtable=[]
    for st in ['completa','parcial','ausente']:
        row=next(r for r in qrows if r['cell']==st)
        qtable.append([{'completa':'Complete','parcial':'Partial','ausente':'Absent'}[st],f(row['person_month_observations']/latest['observations']*100)+'%',f(row['predicted_risk_percent'])+'%',f(row.get('observed_percent'))+'%'])
    slides.append(stage(12,'Missing feedback still changes the estimate','FQ + BU L3 · Jan–Feb 2026 · coverage denominator: all '+f(latest['observations'])+' person-month observations',
       '<article class="card review-main">'+table(['Usable QVoice information','Share of observations','Estimated risk','Observed rate'],qtable)+'</article>'+
       '<div class="review-two">'+box('Absence is an explicit model state','No linked response, another employment episode and unavailable items are distinguished. An absent survey does not automatically return the HR-only risk.')+
       box('Availability is not participation','Complete means all fields required by this model are valid. Partial means some are valid. The wave year is known; the actual publication date is not accredited.')+'</div>',
       'J01, J02 · Engineering · Jan–Feb 2026 snapshots · 6-month exits · models compared with their HR base on the same cohorts in the report'))
    calrows=[]
    for n in LABEL:
        c=latest['models'][n]['calibration'];assert c['status']=='scalar_tested' and not c['recommended']
        calrows.append([LABEL[n],f(c['bias_pp'])+' pp',ci(c['bias_ci95_pp']),f(c['posterior_bias_pp'])+' pp','Do not apply'])
    slides.append(stage(13,'The historical scalar makes the latest underestimation worse','Jan–Feb 2026 · estimated minus observed rate · negative values mean underestimation',
       '<article class="card review-main">'+table(['Model','Bias before','95% CI before','Bias after scalar','Decision'],calrows)+'</article>'+
       box('Keep the original risk and show the remaining gaps','The scalar was fitted using three earlier origins with mature outcomes. In the later period it worsens absolute bias and log-loss for all three models. August–December did not trigger the calibration test.')+
       '<p class="review-caption">Trigger: absolute bias ≥0.1 pp and its 95% CI excludes zero. Local month, group and common risk-band diagnostics remain in the report, with small cells withheld.</p>'))
    stab=d['monthly_stability']['FQ_BU_L3']['30'];cqstab=d['monthly_stability']['CQ']['30']
    months={'08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec','01':'Jan','02':'Feb'}
    rows=[]
    for a,b in zip(stab,cqstab):
        rows.append([months[a['from'][5:7]]+' → '+months[a['to'][5:7]],f(a['mean_absolute_risk_change_pp'])+' pp',f(a['rank_spearman']*100)+'%',f(a['weighted_priority_jaccard']*100)+'%',f(b['weighted_priority_jaccard']*100)+'%'])
    slides.append(stage(14,'January changes coincide with a new survey and model','People present in both snapshots · capacity 30% · FQ + BU L3, with CQ overlap as reference',
        '<article class="card review-main">'+table(['Transition','Mean absolute risk change','Rank correlation ×100','Priority overlap: FQ + BU','Priority overlap: CQ'],rows)+'</article>'+
        '<p class="review-caption">Weighted overlap = shared priority mass / union. December → January changes both the survey wave and fitted model. The report separates common people, new/departed people and composition; the change cannot be attributed to opinions alone.</p>'))
    observed={r['cell']:r for r in supp['cards_observed']['jan_feb_2026/CQ']}
    candidates=[r for r in latest['models']['CQ']['group_cards'] if r['cell'] in observed and r.get('selected_effective_person_months',0)>0 and r['cell'].startswith('2026-02')]
    card=max(candidates,key=lambda r:r['predicted_risk_percent']);card=dict(card,**{k:v for k,v in observed[card['cell']].items() if k!='cell'})
    definition=card['cell'].split(' | ')[1].replace('años','years').replace('año','year').replace('con salidas','with team exits').replace('sin salidas','no team exits').replace('alto','levels 1–3').replace('medio','levels 5–6').replace('entrada','levels 7–8')
    slides.append(stage(15,'A historical group card starts an HR conversation','Selected model CQ · '+escape(definition)+' · HR snapshot: 22 Feb 2026',
        '<div class="review-three">'+box('People in this snapshot',f(card['distinct_people'])+'<br>'+f(card['distinct_people_with_event'])+' people with an exit<br>'+f(card.get('unique_exit_events'))+' distinct dated exits')+
        box('Estimated mean risk',f(card['predicted_risk_percent'])+'%<br>Approximate 95% CI '+ci(card['estimated_mean_risk_ci95_delta_percent'])+'%')+
        box('Observed six-month rate',f(card['observed_percent'])+'%<br>Person-bootstrap 95% CI '+ci(card['observed_rate_ci95_cluster_percent'])+'%')+'</div>'+
        box('Validate continuity and development with HR','Proposed owner: HR partner and operational leadership. Check workload, vacancies and development access against aggregate listening. Agree actions within 30 days and review follow-through after 90 days.')+
        '<p class="review-caption">QVoice wave 2025; exact survey and availability dates unknown. These are two different intervals, not individual prediction intervals. Association does not establish the effect of an action. Other historical cards and window-level person counts are in the report.</p>',
        'J01, J02 · Engineering · historical cohort ≥30 people and ≥30 people with an event · six-month follow-up; dates, not current forecasts'))
    slides.append(stage(16,'Better estimation is supported; HR use still needs validation','CQ remains selected · FQ + BU L3 is the strongest candidate on average probability losses',
       '<div class="review-two">'+box('Predictive conclusion','FQ improves CQ; BU L3 adds a smaller improvement. Capture at 30% is similar. Keep the main grouping and do not apply the tested scalar.')+
       box('Before an operational pilot','Accredit the historical availability of IOS and QVoice, confirm owners and attention capacity, and evaluate a new cohort after model fitting.')+'</div>'+
       box('The review package is ready','44-variable inventory and model roles · comment-to-evidence matrix · 10/20/30% capacities · group cards, segment diagnostics and a reproducible technical annex.')+
       '<p class="review-caption">All conclusions are retrospective and conditional on the selected variables and rules. Proposed retention actions are hypotheses for HR to validate; their causal effect has not been measured.</p>'))
    start=html.index('<div class="slide-stage stage-3rows data-context" id="slide-9">')
    end=html.index('  <div class="nav-ctrl"',start)
    html=html[:start]+'\n'.join(slides)+'\n\n'+html[end:]
    nav=['Decision','Agenda','Starting point','First survey tests','B vs C','C vs CQ','How CQ works','Earlier tests','CQ / FQ / BU','Attention capacity','BU subdivision','QVoice coverage','Calibration','Monthly stability','Historical HR card','Next steps']
    buttons='\n'.join(f'<button class="nav-pill{" pill-active" if i==0 else ""}" data-slide="{i}">{i+1}. {name}</button>' for i,name in enumerate(nav))
    html=re.sub(r'      <button class="nav-pill pill-active" data-slide="0">.*?<button class="nav-pill" data-slide="8">9. Next steps</button>',buttons,html,flags=re.S)
    css='''
    /* Revisión de Julia: preserva los temas y el JS originales. */
    .review-stage { grid-template-rows: auto 1fr auto; padding: 34px 48px 28px; gap: 22px; }
    .review-stage .slide-title-text { font-size: 34px; line-height: 1.13; }
    .review-stage .slide-subtitle { font-size: 18px; line-height: 1.35; margin-top: 10px; }
    .review-body { display: flex; flex-direction: column; gap: 20px; min-height: 0; justify-content: center; }
    .review-main { padding: 10px 26px; }
    .review-table { border-collapse: collapse; width: 100%; font-size: 23px; line-height: 1.3; }
    .review-table th { font-size: 18px; color: var(--text-muted); text-align: right; padding: 15px 12px; border-bottom: 2px solid var(--border-subtle); }
    .review-table td { padding: 18px 12px; text-align: right; border-bottom: 1px solid var(--border-subtle); font-variant-numeric: tabular-nums; }
    .review-table tr:last-child td { border-bottom: 0; }
    .review-table th:first-child, .review-table td:first-child { text-align: left; }
    .review-table td:first-child { font-weight: 700; }
    .review-two { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
    .review-three { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 22px; }
    .review-note { padding: 24px 28px; }
    .review-note h3 { font-size: 24px; margin: 0 0 12px; color: var(--accent); }
    .review-note p { font-size: 22px; line-height: 1.42; margin: 0; }
    .review-caption { font-size: 18px; line-height: 1.4; color: var(--text-muted); margin: 0; }
    .review-stage .src { font-size: 13px; line-height: 1.35; }
    #slide-14 .review-table td { padding-top: 13px; padding-bottom: 13px; }
    .nav-panel { max-height: 740px; overflow-y: auto; }
    .nav-pill { padding-top: 8px; padding-bottom: 8px; }
    '''
    html=html.replace('</style>',css+'\n</style>',1)
    target.write_text(html,encoding='utf-8')
    sources={'J01':{'path':(RUN/'results.json').relative_to(ROOT).as_posix(),'sha256':sha(RUN/'results.json')},
             'J02':{'path':(RUN/'cohort-diagnostics-supplement.json').relative_to(ROOT).as_posix(),'sha256':sha(RUN/'cohort-diagnostics-supplement.json')}}
    evidence={'reporting_mode':'presentation','language_exception':'AGENTS.md: texto proyectado de decks de modelos en inglés; guion y evidencia en español',
              'base':BASE.relative_to(ROOT).as_posix(),'base_sha256':sha(BASE),'template_sha256':sha(TEMPLATE),'sources':sources,
              'choice':'Copia de evolución propuesta durante el encargo; no modifica el registro de adopción ni el modelo elegido.',
              'preserved':'Diapositivas 1–8 y controles originales, con actualización de agenda y frases de estado; cierre sustituido por revisión y siguientes pasos.',
              'employee_level_rows_persisted':False,'historical_card_cell':card['cell'],'deck_sha256':sha(target)}
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'guion.md').write_text('# Revisión para Julia y RH\n\nModo `presentation`. Parte de la copia de evolución B → C → CQ propuesta para este encargo. No implica adopción del candidato.\n\n'+
       '| Slide | Mensaje y visual | Fuente |\n|---|---|---|\n'+
       '\n'.join(f'| {i+9} | {re.search(r"<h2[^>]*>(.*?)</h2>",slide).group(1)}; tabla breve o ficha | J01'+(' y J02' if i in [3,6] else '')+' |' for i,slide in enumerate(slides))+
       '\n\nLas tablas permiten comparar cifras pequeñas sin exagerar diferencias con barras recortadas. Se preservan el diseño, los cuatro temas y la navegación. Los intervalos pareados se muestran junto al contraste correspondiente.\n\nLímites visibles: selección retrospectiva, historial IOS y publicación QVoice no acreditados; ninguna inferencia causal; celdas pequeñas suprimidas. Las fuentes S01–S14 de slides históricos se conservan en la carpeta de la base.\n',encoding='utf-8')
    # Preserva también el soporte narrativo de las fuentes históricas.
    for source in BASE.parent.iterdir():
        if source.suffix in ['.md','.json']:
            destination=OUT/'historical-evidence'/source.name;destination.parent.mkdir(exist_ok=True);shutil.copy2(source,destination)
    print(str(target))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,default=RUN);parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--base',type=Path,default=BASE)
    args=parser.parse_args();RUN=args.run.resolve();OUT=args.output.resolve();BASE=args.base.resolve()
    sys.stdout.reconfigure(encoding='utf-8');build()
