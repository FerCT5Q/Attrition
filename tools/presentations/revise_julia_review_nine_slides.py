"""Revisión de nueve slides sobre la base existente: Julia y C+BU explícito."""
from __future__ import annotations
import hashlib
import json
from html import escape
from pathlib import Path
import re
import shutil
import numpy as np
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'output/presentations/20261012-0833_evolucion-b-cq-error-vs-c/presentacion-eng.html'
RUN=ROOT/'output/analysis/engineering/20261012/julia-rh-review-v1'
BU=ROOT/'output/analysis/engineering/20261013/c-bu-isolation-v1'
OUT=ROOT/'output/presentations/20261013-0735_revision-julia-9-slides'
TEMPLATE=Path('C:/Users/fcarranz/.codex/skills/html-slide-generator/templates/fullscreen/base-fullscreen.html')


def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def f(v):
    if v is None: return 'Withheld'
    if 0<abs(v)<.05: return '&lt;0.1' if v>0 else 'just below 0'
    return f'{round(float(v),1):,.1f}'.rstrip('0').rstrip('.').replace('-','−')
def ci(values): return '['+', '.join(f(x) for x in values)+']'
def table(headers, rows, cls='j-table'):
    return '<table class="'+cls+'"><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def inner(soup, selector, value):
    node=soup.select_one(selector); assert node is not None,selector
    node.clear(); node.append(BeautifulSoup(value,'html.parser'))


def build():
    d=read(RUN/'results.json'); supplement=read(RUN/'cohort-diagnostics-supplement.json'); b=read(BU/'results.json')
    assert read(BU/'manifest.json')['status']=='completed_retrospective_comparison'
    assert all(max(x['archival_metric_abs_difference'].values())<1e-8 for x in read(BU/'verification.json')['checks'])
    assert len(d['periods'])==2
    html=BASE.read_text(encoding='utf-8')
    ids=list(re.finditer(r'<div class="slide-stage[^>]*id="slide-(\d+)">',html))
    assert [int(x[1]) for x in ids]==list(range(1,10))
    end=html.index('  <div class="nav-ctrl"',ids[-1].start())
    starts=[x.start() for x in ids]+[end]
    originals=[html[starts[i]:starts[i+1]] for i in range(9)]
    slides=[BeautifulSoup(x,'html.parser') for x in originals]
    # Portada y recorrido: conserva el mensaje elegido y el orden de nueve slides.
    inner(slides[0],'.cover-decision','<b>Selected:</b> HR + employee feedback (CQ). New BU and city results are on slide 8; HR readiness is on slide 9. A pilot has not started.')
    inner(slides[1],'.slide-title-text','From our starting model to the latest evidence')
    cards=slides[1].select('.ag-item')
    inner(cards[2],'.ag-body','BU L3 with and without feedback; work city')
    inner(cards[3],'.ag-body','Capacity, group review and validation before a pilot')
    inner(slides[1],'.flow-branches .flow-branch:last-child','↳ BU L3 · city · further checks')
    # Misma explicación de grupos; las tres etiquetas son códigos de nivel.
    for node in slides[2].select('.chip-g'):
        if node.text in ['Entry','Mid','Senior']:
            node.string={'Entry':'Levels 7–8','Mid':'Levels 5–6','Senior':'Levels 1–3'}[node.text]
    inner(slides[2],'.slide-title-text','Keep understandable groups; use the review to guide HR questions')
    inner(slides[2],'.commit-card .side-head','Julia’s review: findings and limits')
    items=[
      ('Variable → candidate action','44-variable guide: possible actions, owners and cautions.'),
      ('Differences across segments','Region, level, tenure and QVoice checked; differences need context.'),
      ('Monthly stability','January changes with the survey wave and model; track both.'),
      ('Smaller BU groups','100-person splits fail in the CQ/FQ review; retain base groups.'),
      ('Before operational use','Confirm data availability dates and test a later cohort.')]
    inner(slides[2],'.commits',''.join('<li><div class="cm-head">'+a+'</div><div class="cm-status">'+z+'</div></li>' for a,z in items))
    inner(slides[2],'.src','Group diagram: Engineering, 26 Jul 2026 · Review: Aug–Dec 2025 and Jan–Feb 2026 · Differences do not by themselves establish unfair bias · S04, J01, J02')
    # Slides 4 y 5 conservan íntegramente la comparación histórica existente.
    cal=d['periods'][1]['models']['CQ']['calibration']
    assert not cal['recommended']
    inner(slides[5],'.kpi-note','<b>Calibration still needs work.</b> In Jan–Feb 2026, CQ underestimated the overall rate by '+f(-cal['bias_pp'])+' pp. The tested scalar increased that gap to '+f(-cal['posterior_bias_pp'])+' pp; keep the original risk.')
    inner(slides[5],'.src','Engineering · Aug–Dec 2025 and Jan–Feb 2026 · 6-month exits, overlapping snapshots · equal period weights · Historical comparison: S11, S12 · Calibration review: J01')
    # Explicación de CQ conservada, con evidencia concreta del dato ausente.
    qrows={x['cell']:x for x in d['periods'][1]['models']['CQ']['diagnostics']['qvoice']}
    qtable=table(['Usable QVoice','Share','Estimated','Observed'],[
        [en,f(qrows[st]['population_share_percent'])+'%',f(qrows[st]['predicted_risk_percent'])+'%',f(qrows[st]['observed_percent'])+'%']
        for st,en in [('completa','Complete'),('parcial','Partial'),('ausente','Absent')]])
    oldnotes=slides[6].select_one('.s7-notes')
    oldnotes.replace_with(BeautifulSoup('<div class="j-qgrid"><article class="card j-compact"><h3>CQ · Jan–Feb 2026</h3>'+qtable+
      '<p class="j-small">Denominator: '+f(d['periods'][1]['observations'])+' person-month observations. Complete = all required fields valid; partial = some; absent = none.</p></article>'+
      '<article class="card j-compact"><h3>Missing feedback is a model state</h3><p>No linked response, a different employment episode and unavailable items are distinguished. Absence does not automatically return the HR-only estimate.</p><p class="j-small">Wave: 2025. Survey date, publication date and data age are unknown. This is availability, not the participation rate among invitees.</p></article></div>','html.parser'))
    inner(slides[6],'.src','Top: final September CQ structure; historical models used separate saved selections · Bottom: historical CQ, 6-month outcomes · Group-level use only · S01, J01, J02')
    # Sustituye los datos de Further tests, sin insertar ninguna diapositiva.
    display=[('CQ','C + QVoice (CQ) · selected'),('C_BU','C + BU L3 · no QVoice'),
             ('C_BU_Q','C + BU L3 + QVoice'),('FQ','C + city + QVoice'),('FQ_BU_L3','C + city + BU L3 + QVoice')]
    rows=[]
    for n,label in display:
        m=b['summary'][n]['30']; rows.append([label,f(m['log_loss']*1000),f(m['capture_percent'])+'%',f(m['group_snapshot_mae_pp'])+' pp'])
    inner(slides[7],'.slide-title-text','C + BU alone does not beat CQ; city and feedback add value')
    inner(slides[7],'.slide-subtitle','Same people, dates and group definitions · lower log-loss means closer probabilities')
    # El periodo cabe en el subtítulo; el chip previo comprimiría el nuevo título.
    slides[7].select_one('.period-strip').decompose()
    inner(slides[7],'.s8n > .card',table(['Model','Log-loss × 1,000 ↓','Exits captured at 30% ↑','Group gap ↓'],rows))
    delta=b['differences']['C_BU_minus_C_refit']['30']['log_loss']
    inner(slides[7],'.note-box','<b>BU added to C with the same training dates:</b> '+f(delta['difference']*1000)+' log-loss × 1,000; 95% CI '+ci([1000*x for x in delta['ci95']])+'. The report separates BU’s contribution from updating the HR fit.')
    inner(slides[7],'.s8-note','CQ retains its August HR fit in January; candidates use the January cutoff. These are retrospective comparisons of complete estimators. CQ remains selected pending review.')
    inner(slides[7],'.src','Engineering · active regular employees, excl. RF360 · Aug–Dec 2025 and Jan–Feb 2026 · 6-month exits, overlapping snapshots · equal period weights · J03 · Brier and earlier tests in supporting evidence')
    # Capacidad y una ficha de ejemplo ocupan el espacio de próximos pasos.
    inner(slides[8],'.slide-title-text','Next: agree capacity, validate a group’s needs and test a later cohort')
    caprows=[]
    for cap in ['10','20','30']:
        monthly=[row for p in d['periods'] for row in p['models']['CQ']['capacities'][cap]['monthly']]
        groups=[row['priority_groups'] for row in monthly]
        people=np.mean([np.mean([row['effective_people_selected'] for row in p['models']['CQ']['capacities'][cap]['monthly']]) for p in d['periods']])
        grange=str(min(groups)) if min(groups)==max(groups) else str(min(groups))+'–'+str(max(groups))
        caprows.append([cap+'%',f(people),grange,f(d['summary']['CQ'][cap]['capture_percent'])+'%'])
    observed={row['cell']:row for row in supplement['cards_observed']['jan_feb_2026/CQ']}
    candidates=[row for row in d['periods'][1]['models']['CQ']['group_cards'] if row['cell'] in observed and row.get('selected_effective_person_months',0)>0 and row['cell'].startswith('2026-02')]
    card=max(candidates,key=lambda row:row['predicted_risk_percent']); card=dict(card,**observed[card['cell']])
    assert card['distinct_people']>=30 and card['distinct_people_with_event']>=30
    definition=card['cell'].split(' | ')[1].replace('años','years').replace('año','year').replace('con salidas','with team exits').replace('entrada','levels 7–8').replace('medio','levels 5–6').replace('alto','levels 1–3')
    body=('<div class="j-next-grid"><article class="card j-compact"><h3>Choose attention capacity · CQ</h3><p class="j-small">Aug–Dec 2025 and Jan–Feb 2026 · 6-month exits</p>'+table(['Capacity','People¹','Groups²','Exits captured'],caprows)+
        '<p class="j-small">¹ Equivalent people per snapshot, averaged with equal period weights. ² Range of touched groups; includes the boundary group.</p><p class="j-small">The report compares including or excluding the entire boundary group. Weighted capacity selects no named individuals.</p></article>')
    body+=('<article class="card j-compact"><h3>Historical group card · CQ</h3><p class="j-definition">'+escape(definition)+'<br>HR snapshot: 22 Feb 2026</p><div class="j-card-metrics">'+
       '<div><b>'+f(card['distinct_people'])+'</b><span>people in this snapshot</span></div><div><b>'+f(card['unique_exit_events'])+'</b><span>unique exits within 6 months</span></div>'+
       '<div><b>'+f(card['predicted_risk_percent'])+'%</b><span>estimated mean risk<br>Approx. 95% CI '+ci(card['estimated_mean_risk_ci95_delta_percent'])+'%</span></div>'+
       '<div><b>'+f(card['observed_percent'])+'%</b><span>observed rate<br>Bootstrap 95% CI '+ci(card['observed_rate_ci95_cluster_percent'])+'%</span></div></div>'+
       '<p class="j-small">Complete QVoice: '+f(card['qvoice_complete_percent'])+'% of '+f(card['qvoice_coverage_denominator'])+' people. Wave 2025; survey/publication dates and data age unknown.</p></article></div>')
    body+='<div class="note-box j-action"><b>HR partner + operational leaders:</b> investigate vacancies, workload and development access. Agree one candidate action within 30 days; review completion after 90 days. Use groups to guide conversations; no individual labeling or sanctions.</div>'
    body+='<div class="j-links"><a href="../../analysis/engineering/20261013/c-bu-isolation-v1/documentacion/variables-44-ampliada.xlsx">44-variable action guide</a> · <a href="../../analysis/engineering/20261012/julia-rh-review-v1/fichas/indice.md">Group cards</a> · <a href="../../analysis/engineering/20261012/julia-rh-review-v1/diagnosticos-completos.md">Calibration, stability and segments</a></div>'
    inner(slides[8],'.s9n',body)
    inner(slides[8],'.next-after','Before a pilot: verify historical IOS/QVoice availability and test a later cohort. Intervals describe group estimates and historical rates, not individual predictions. Actions are hypotheses; their effect is unmeasured. · J01, J02')
    # Sólo las diapositivas modificadas se serializan. Se conservan 4 y 5 byte por byte.
    parts=[str(s) if i not in [3,4] else originals[i] for i,s in enumerate(slides)]
    html=html[:starts[0]]+'\n'.join(parts)+html[end:]
    html=html.replace('<title>Engineering attrition: from the core HR model to HR + employee feedback (CQ)</title>',
                      '<title>Engineering attrition — Julia review — 9 slides</title>')
    html=html.replace('<head>','<head>\n<meta name="deliverable-classification" content="presentation">\n<link rel="icon" href="data:,">',1)
    html=html.replace('>8. Further tests<','>8. BU and city tests<')
    css='''
    /* Revisión autorizada: nueve diapositivas sobre la base existente. */
    #slide-3 .cm-head { font-size: 18px; }
    #slide-3 .cm-status { font-size: 16px; line-height: 1.35; }
    #slide-3 .chip-g { padding: 6px; }
    #slide-6 .kpi-note { font-size: 18px; line-height: 1.4; }
    #slide-7 .s7n { gap: 18px; }
    #slide-7 .st-card { padding: 12px 24px 18px; }
    #slide-7 .st-num { font-size: 25px; }
    #slide-7 .st-head { font-size: 23px; }
    #slide-7 .st-body { font-size: 19px; }
    .j-qgrid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 22px; }
    .j-compact { padding: 19px 24px; gap: 10px; justify-content: flex-start; }
    .j-compact h3 { color: var(--accent); font-size: 22px; margin: 0 0 4px; }
    .j-compact p { font-size: 19px; line-height: 1.4; margin: 0; }
    .j-compact .j-small, .j-small { font-size: 15px; line-height: 1.35; color: var(--text-muted); }
    .j-table { border-collapse: collapse; width: 100%; font-size: 22px; font-variant-numeric: tabular-nums; }
    .j-table th { text-align: right; color: var(--text-muted); font-size: 16px; padding: 12px 10px; border-bottom: 2px solid var(--border-subtle); }
    .j-table td { text-align: right; padding: 14px 10px; border-bottom: 1px solid var(--border-subtle); }
    .j-table th:first-child, .j-table td:first-child { text-align: left; }
    .j-table td:first-child { font-weight: 650; }
    .j-table tr:last-child td { border-bottom: 0; }
    #slide-7 .j-table { font-size: 19px; }
    #slide-7 .j-table th, #slide-7 .j-table td { padding: 7px 8px; }
    #slide-8 .j-table td { padding: 18px 16px; }
    #slide-8 .j-table tbody tr:last-child { color: var(--accent); background: var(--accent-soft); }
    #slide-8 .note-box { font-size: 20px; }
    #slide-8 .s8-note { font-size: 17px; line-height: 1.4; }
    #slide-9 .slide-title-text { font-size: 34px; }
    #slide-9 .s9n { gap: 18px; }
    .j-next-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
    #slide-9 .j-table { font-size: 21px; }
    #slide-9 .j-table th, #slide-9 .j-table td { padding: 10px 7px; }
    .j-card-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 18px; }
    .j-card-metrics b { display: block; color: var(--accent); font-size: 29px; line-height: 1.1; }
    .j-card-metrics span { font-size: 16px; line-height: 1.25; display: block; margin-top: 3px; }
    #slide-9 .j-definition { font-size: 18px; line-height: 1.3; font-family: inherit; }
    .j-action { font-size: 19px; line-height: 1.4; }
    .j-links { font-size: 16px; }
    .j-links a { color: var(--accent); text-decoration: underline; }
    #slide-9 .next-after { font-size: 15px; line-height: 1.4; }
    '''
    html=html.replace('</style>',css+'\n</style>',1)
    parsed=BeautifulSoup(html,'html.parser')
    assert len(parsed.select('.slide-stage'))==len(parsed.select('.nav-pill'))==9
    assert [x['id'] for x in parsed.select('.slide-stage')]==['slide-'+str(i) for i in range(1,10)]
    assert [x['data-slide'] for x in parsed.select('.nav-pill')]==list(map(str,range(9)))
    assert len(parsed.select('[data-theme]'))==4
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'presentacion-eng.html'
    shutil.copy2(TEMPLATE,OUT/'template-origin.html'); shutil.copy2(TEMPLATE,target)
    target.write_text(html,encoding='utf-8')
    sources={'J01':RUN/'results.json','J02':RUN/'cohort-diagnostics-supplement.json','J03':BU/'results.json'}
    evidence={'reporting_mode':'presentation','employee_level_rows_persisted':False,
       'base':str(BASE.relative_to(ROOT)),'base_sha256':sha(BASE),'template_sha256':sha(TEMPLATE),'deck_sha256':sha(target),
       'slide_count':9,'base_slide_count':9,'historical_slides_4_5_preserved':True,
       'sources':{k:{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for k,p in sources.items()},
       'language_exception':'AGENTS.md exige inglés en el deck; apoyo analítico en español.',
       'model_selection_changed':False,'replaces_deliverable':'output/presentations/20261012-2350_revision-julia-rh/presentacion-eng.html',
       'historical_card_cell':card['cell'],'slide8_model_order':[x[0] for x in display],
       'slide8_values':rows,'slide9_capacity_values':caprows}
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for p in BASE.parent.iterdir():
        if p.suffix in ['.json','.md']:
            dest=OUT/'historical-evidence'/p.name; dest.parent.mkdir(exist_ok=True); shutil.copy2(p,dest)
    storyboard=[('Decisión','CQ elegido; se conserva captura histórica y se señala la prueba nueva.'),
      ('Agenda','Mismo recorrido y nueve espacios; pruebas BU/ciudad en 8, preparación RH en 9.'),
      ('Grupos','Mismo diagrama; se corrigen etiquetas de nivel y se resume revisión Julia.'),
      ('Primeras pruebas QVoice','Sin cambios.'),('B frente a C','Sin cambios.'),
      ('C frente a CQ','Misma gráfica; la nota muestra subestimación global y escalar no recomendado.'),
      ('Cómo funciona CQ','Mismo flujo; añade cobertura completa/parcial/ausente y resultado observado.'),
      ('Pruebas adicionales','Sustituye tabla anterior por C+BU con/sin QVoice, CQ y ciudad.'),
      ('Próximos pasos','Capacidad 10/20/30, ficha histórica y acción candidata con dueño/plazo.')]
    (OUT/'guion.md').write_text('# Revisión de Julia en las nueve diapositivas originales\n\n'
      'Modo `presentation`. Audiencia: Julia y líderes RH. Decisión: distinguir estimación predictiva '
      'de preparación para una conversación o piloto. Corrección autorizada por el usuario; conserva '
      'el número de slides, el inglés, diseño base y orden. La copia de 16 deja de ser la entrega recomendada.\n\n'
      '| Slide | Tema | Cambio |\n|---|---|---|\n'+'\n'.join(f'| {i+1} | {a} | {z} |' for i,(a,z) in enumerate(storyboard))+
      '\n\nLas tablas comparan diferencias pequeñas sin exagerarlas con ejes truncados. Se conservan '
      'gráficos y animaciones originales. La tabla de cinco modelos en 8 separa explícitamente presencia '
      'de QVoice. La ficha de 9 es un ejemplo histórico, no un pronóstico actual; su sobreestimación '
      'local permanece visible. Intervalo del riesgo: aproximación por coeficientes; tasa observada: '
      'bootstrap por persona. No son intercambiables ni individuales.\n\n'
      'El respaldo de 44 variables contiene las cuatro clasificaciones solicitadas y variable→acción. '
      'Fichas completas distinguen fotos, personas distintas y exposiciones; diagnóstico conserva bandas, '
      'curvas, segmentos y cambios mensuales. La versión corta enlaza ese respaldo y no añade anexos. '
      'Disponibilidad histórica IOS/QVoice por acreditar, acciones sin efecto causal medido y CQ elegido '
      'quedan explícitos.\n',encoding='utf-8')
    print(target)


if __name__=='__main__': build()
