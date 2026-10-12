"""Revisión de grupos C desde agregados archivados; sin consultas ni reajustes."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/engineering_c_priority_review_20261008.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def fmt(x, suffix='', signed=False):
    if x is None:
        return '—'
    if 0 < abs(x) < .05:
        return ('<0.1' if x > 0 else '>-0.1')+suffix
    value = f'{x:.1f}'.rstrip('0').rstrip('.')
    if signed and x > 0:
        value = '+'+value
    return value+suffix


def short(label):
    return label.replace('Antigüedad: ', '').replace('Salidas en su equipo: ', '').replace('Nivel: ', '')


def figure(rows, baseline, out):
    fig, ax = plt.subplots(figsize=(14, 8.5))
    for i, row in enumerate(rows):
        predicted, observed = row['predicted_percent'], row['observed_percent']
        if observed is not None:
            ax.plot([observed, predicted], [i, i], color='#c7cdd4', lw=2, zorder=1)
            ax.scatter([observed], [i], color='#246bb4', s=62, zorder=3)
        ax.scatter([predicted], [i], marker='D', color='#7c8590', s=42, zorder=2)
        ax.text(1.04, i, fmt(predicted, '%'), transform=ax.get_yaxis_transform(), va='center', fontsize=10)
        ax.text(1.22, i, fmt(observed, '%'), transform=ax.get_yaxis_transform(), va='center', fontsize=10,
                color='#246bb4' if observed is not None else '#555555')
    ax.axvline(baseline, color='#929aa4', ls=':', lw=1.2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r['id']+' · '+short(r['group'])+'\n'+fmt(r['full_group_people'])+' personas' for r in rows], fontsize=10)
    ax.set_ylim(len(rows)-.5, -.5)
    ax.set_xlim(0, 10)
    ax.set_xlabel('Salida voluntaria en los seis meses siguientes', fontsize=10, labelpad=12)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: fmt(x, '%')))
    ax.tick_params(axis='both', length=0, pad=8)
    ax.grid(axis='x', color='#edf0f3')
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(1.04, 1.03, 'C estima', transform=ax.transAxes, fontsize=10, weight='bold')
    ax.text(1.22, 1.03, 'Observado', transform=ax.transAxes, fontsize=10, weight='bold')
    fig.suptitle('El mayor riesgo estimado también presenta el mayor error publicable',
                 x=.025, y=.975, ha='left', fontsize=16, weight='bold')
    fig.text(.025, .90, 'Nueve grupos en la prioridad del 30% · Foto: 22-feb-2026 · Seguimiento hasta 22-ago-2026\n'
             'Engineering · Employee, Regular, activo, sin RF360 · Modelo C con cortes de antigüedad, salidas del equipo y nivel', fontsize=10)
    fig.legend(handles=[Line2D([], [], marker='D', linestyle='', color='#7c8590', label='Estimado por C'),
                        Line2D([], [], marker='o', linestyle='', color='#246bb4', label='Observado'),
                        Line2D([], [], linestyle=':', color='#929aa4', label='Referencia total: '+fmt(baseline, '%'))],
               loc='upper left', bbox_to_anchor=(.025, .89), frameon=False, ncol=3, fontsize=10)
    fig.text(.025, .065, 'Tamaños del grupo completo. G9 participa parcialmente al 30%; los otros ocho grupos entran completos.\n'
             'G2: observado suprimido. Tasas publicadas sólo con al menos 30 eventos distintos; nivel no describe edad ni riesgo.', fontsize=9)
    fig.text(.025, .025, 'Fuente: c-group-selection-v1/results.json · Consulta engineering_model_c_person_month_20261008.sql, ejecutada 8-oct-2026.\n'
             'C archivado al 1-ago-2025; evidencia retrospectiva. Esta figura no representa grupos asignados a la fecha actual.', fontsize=8)
    fig.subplots_adjust(left=.40, right=.79, top=.78, bottom=.17)
    fig.savefig(out/'riesgo-estimado-observado.png', dpi=170, facecolor='white')
    fig.savefig(out/'riesgo-estimado-observado.svg', facecolor='white')
    plt.close(fig)


def main():
    config = read(CONFIG)
    out = ROOT/config['output']
    if (out/'completed.json').exists():
        raise RuntimeError('Revisión finalizada: usar una carpeta nueva para otro análisis.')
    protected = [ROOT/'output/analysis/engineering/20261008'/name for name in
                 ['model-c-v2', 'c-group-selection-v1', 'model-c-plus-qvoice-v1',
                  'qvoice-model-b-calibrated-v1', 'qvoice-horizon-calibration-v1']]
    before = {str(p.relative_to(ROOT)): sha(p) for folder in protected for p in folder.rglob('*') if p.is_file()}
    source = read(ROOT/config['source'])
    extension = source['extension']
    model = extension['evaluation'][config['variant']]
    scenarios = model['scenarios']
    current = scenarios['30']
    full = {row['group']: row for row in scenarios['40']['selected_groups']}
    checks = {'snapshot': extension['snapshot'] == config['snapshot'],
              'followup_end': extension['followup_end'] == config['followup_end'],
              'mature': extension['followup_end'] <= source['knowledge_boundary'],
              'dimensions': model['definition']['dimensions'] == ['antiguedad', 'salidas_equipo', 'nivel'],
              'no_qvoice': read(ROOT/config['model'])['qvoice_included'] is False}
    baseline = current['metrics']['observed_percent']/current['metrics']['lift']
    checks['baseline_reconciled'] = all(math.isclose(v['metrics']['observed_percent']/v['metrics']['lift'], baseline, abs_tol=1e-10) for v in scenarios.values())
    rows = []
    history = []
    for i, row in enumerate(sorted(current['selected_groups'], key=lambda x:-x['predicted_percent']), 1):
        complete = full[row['group']]
        n = complete['mean_selected_people_per_snapshot']
        selected = row['mean_selected_people_per_snapshot']
        checks[f'G{i}_whole_group_size'] = math.isclose(n, round(n), abs_tol=1e-8) and n >= config['minimum_group_people'] and 0 < selected <= n+1e-8
        observed = row.get('observed_percent')
        checks[f'G{i}_same_group_rate'] = math.isclose(row['predicted_percent'], complete['predicted_percent'], abs_tol=1e-8)
        if row['observed_publishable']:
            checks[f'G{i}_observed_count'] = (complete['distinct_people_with_event'] >= config['minimum_public_events'] and
                math.isclose(n*observed/100, complete['distinct_people_with_event'], abs_tol=1e-8) and
                math.isclose(observed, complete['observed_percent'], abs_tol=1e-8))
        else:
            checks[f'G{i}_suppression'] = observed is None and 'distinct_people_with_event' not in row
        past = []
        for fold in source['folds']:
            found = next((g for g in fold['evaluation'][config['variant']]['scenarios']['30']['selected_groups'] if g['group'] == row['group']), None)
            value = {'id': f'G{i}', 'fold': fold['fold'], 'first_snapshot': fold['first_snapshot'],
                     'last_snapshot': fold['last_snapshot'], 'selected_snapshots': found.get('selected_snapshots', 0) if found else 0,
                     'predicted_percent': found.get('predicted_percent') if found else None,
                     'observed_percent': found.get('observed_percent') if found else None,
                     'error_pp': found.get('error_pp') if found else None}
            checks[f'G{i}_fold{fold["fold"]}_presence'] = 0 <= value['selected_snapshots'] <= 6
            if found and not found['observed_publishable']:
                checks[f'G{i}_fold{fold["fold"]}_suppression'] = value['observed_percent'] is None
            history.append(value)
            past.append(value)
        rows.append({'id':f'G{i}', 'group':row['group'], 'full_group_people':round(n),
                     'selected_people':selected, 'selected_fraction':selected/n,
                     'predicted_percent':row['predicted_percent'], 'observed_percent':observed,
                     'bias_pp':row['predicted_percent']-observed if observed is not None else None,
                     'error_pp':row.get('error_pp'),
                     'distinct_events_full_group':complete.get('distinct_people_with_event') if row['observed_publishable'] else None,
                     'observed_vs_population_ratio':observed/baseline if observed is not None else None,
                     'selected_snapshots_24':sum(p['selected_snapshots'] for p in past), 'history':past})
    n_selected = sum(r['selected_people'] for r in rows)
    predicted = sum(r['selected_people']*r['predicted_percent'] for r in rows)/n_selected
    checks['selected_size'] = math.isclose(n_selected, current['metrics']['mean_people_per_snapshot'], abs_tol=1e-8)
    checks['capacity'] = math.isclose(n_selected/extension['people'], .3, abs_tol=1e-10)
    checks['predicted_reconciled'] = math.isclose(predicted, current['metrics']['predicted_percent'], abs_tol=1e-10)
    checks['eight_whole_groups'] = sum(math.isclose(r['selected_fraction'], 1., abs_tol=1e-9) for r in rows) == 8
    checks['all_nine_size'] = sum(r['full_group_people'] for r in rows) == round(current['whole_groups_including_boundary']['mean_people_per_snapshot'])
    checks['core_eight_size'] = sum(r['full_group_people'] for r in rows if math.isclose(r['selected_fraction'], 1., abs_tol=1e-9)) == round(current['whole_groups_excluding_boundary']['mean_people_per_snapshot'])
    if not all(checks.values()):
        raise RuntimeError('Reconciliación incompleta: '+str([k for k,v in checks.items() if not v]))
    out.mkdir(parents=True, exist_ok=True)
    record = {'run_id':config['run_id'], 'reporting_mode':'presentation', 'source':config['source'],
              'source_query':source['query'], 'source_execution_date':'2026-10-08',
              'snapshot':extension['snapshot'], 'followup_end':extension['followup_end'],
              'model_origin':extension['model_origin'], 'population':extension['people'],
              'population_observed_percent':baseline, 'priority':current['metrics'],
              'groups':rows, 'scenarios':{k:{'metrics':v['metrics'], 'whole_groups_excluding_boundary':v['whole_groups_excluding_boundary'],
                                         'whole_groups_including_boundary':v['whole_groups_including_boundary']} for k,v in scenarios.items()},
              'historical_summary':source['summary']['30'][config['variant']],
              'hazard_refits':0, 'employee_level_rows_persisted':False, 'individual_scores_published':False}
    write(out/'results.json', record)
    fields = [k for k in rows[0] if k != 'history']
    with (out/'grupos-prioritarios.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in rows)
    with (out/'presencia-historica.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)
    report(record, source, out)
    figure(rows, baseline, out)
    source_files = [CONFIG, Path(__file__), ROOT/config['source'], ROOT/config['model'],
                    ROOT/source['query'], ROOT/'docs/plans/engineering-c-priority-review-20261008.md']
    for path in source_files:
        target = out/'source'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    write(out/'frozen-sources.json', {str(p.relative_to(ROOT)):sha(p) for p in source_files})
    write(out/'visual-design.json', {'skill':'morgan-vis','audience':'Propietario del modelo; diseñar una revisión de grupos y posibles acciones',
          'message':'El mayor riesgo estimado presenta el mayor error publicable dentro de los grupos priorizados',
          'design':'Puntos pareados: estimado gris, observado azul; tamaños completos, columna numérica y referencia de la población.',
          'alternatives':['Barras dobles: repetición visual y espacio excesivo para nueve grupos.','Sólo errores: oculta el nivel de riesgo y su referencia poblacional.'],
          'limits':['Se mantiene el orden predicho; las acciones son hipótesis.','Observado de G2 suprimido.','Fotos históricas con personas y ventanas compartidas; no prueba causal.'],
          'visible_decimal_maximum':1})
    checks['prior_artifacts_preserved'] = all(sha(ROOT/p) == digest for p,digest in before.items())
    if not checks['prior_artifacts_preserved']:
        raise RuntimeError('Cambió un artefacto anterior.')
    write(out/'preservation.json', {'unchanged':True,'files':before})
    write(out/'analysis-checks.json', {'outcome':'pass','checks':checks,'count':len(checks),
                                     'method':'Reconciliación de agregados archivados; sin datos individuales, consultas ni pruebas de software.'})
    write(out/'manifest.json', {'run_id':config['run_id'], 'reporting_mode':'presentation', 'status':'awaiting_visual_review',
          'created_at':datetime.now(timezone.utc).isoformat(), 'employee_level_rows_persisted':False,
          'files':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json'}})
    print(json.dumps({'groups':len(rows),'population':extension['people'],'checks':len(checks),'output':config['output']}))


def report(r, source, out):
    groups = r['groups']
    m = r['priority']
    base = r['population_observed_percent']
    core = r['scenarios']['30']['whole_groups_excluding_boundary']
    whole = r['scenarios']['30']['whole_groups_including_boundary']
    text = ['# Grupos prioritarios de C: riesgo, precisión y posibles acciones', '',
        'Modo `presentation`. Revisión 8-oct-2026, basada exclusivamente en agregados archivados.', '',
        '## Lectura principal', '',
        '**Los grupos aportan una señal útil para priorizar, pero requieren distinguir riesgo, tamaño y precisión.** '
        'El grupo con mayor riesgo estimado tiene la mayor sobreestimación publicable. '
        'El grupo más grande de la prioridad presenta una estimación bastante más cercana al observado.', '',
        '- Se conserva C con **antigüedad × salidas del equipo × nivel**, sin QVoice y con coeficientes de 1-ago-2025.',
        '- Foto: **22-feb-2026**, seguida hasta **22-ago-2026**. Población: **35313** personas de Engineering, '
        'Employee, Regular, activo, sin RF360. Es una revisión retrospectiva; la pertenencia actual a grupos debe actualizarse para un uso posterior.',
        '- Hay **20 grupos elegibles**, con mínimo 300 personas por foto; al priorizar 30% entran **ocho grupos completos y parte de un noveno**. '
        'Los nueve grupos priorizados no son los ocho del árbol histórico.',
        f'- La prioridad captura **{fmt(m["capture_percent"], "%")}** de las salidas al cubrir 30% de personas. '
        f'Observado **{fmt(m["observed_percent"], "%")}** frente a **{fmt(base, "%")}** en la población total; '
        f'estimado **{fmt(m["predicted_percent"], "%")}** y error medio por grupo **{fmt(m["group_mae_pp"], " pp")}**.', '',
        '## Nueve grupos de la prioridad del 30%', '',
        'Ordenados por el riesgo que C predijo, antes de utilizar el observado. G1–G9 son etiquetas de esta revisión. '
        '«Entrada» y «medio» describen nivel profesional; no describen edad ni nivel de riesgo. '
        '«Sin salidas» se refiere al historial registrado del equipo en los 12 meses anteriores.', '',
        '| Grupo | Definición: antigüedad · salidas previas del equipo · nivel | Personas del grupo | Personas priorizadas equivalentes | Estimado R6 | Observado R6 | Error con signo |',
        '|---|---|---:|---:|---:|---:|---:|']
    for row in groups:
        text.append(f'| {row["id"]} | {short(row["group"])} | {fmt(row["full_group_people"])} | {fmt(row["selected_people"])} | '
                    f'{fmt(row["predicted_percent"], "%")} | {fmt(row["observed_percent"], "%")} | {fmt(row["bias_pp"], " pp", True)} |')
    text += ['', 'Error con signo = estimado menos observado: positivo indica sobreestimación y negativo subestimación. '
        'El observado de G2 permanece suprimido; no se reconstruye a partir de totales. Su historia de selección '
        'apoya revisarlo, pero el observado de esta foto no se publica.', '',
        'G9 tiene 2580 personas y participa con peso uniforme equivalente a 353.9 personas al 30%. '
        'Ese peso permite comparar capacidades; no identifica a 353.9 personas reales ni asigna acciones individuales. '
        'La tasa de G9 describe su grupo completo y coincide bajo ponderación uniforme.', '',
        '![Riesgo estimado y observado por grupo](riesgo-estimado-observado.png)', '',
        '## Qué grupos revisaría primero y por qué', '',
        'Esta lectura orienta el diagnóstico sin cambiar el orden de riesgo del modelo:', '',
        '1. **G5: 3–5 años, entrada, sin salidas previas del equipo.** Es el mayor grupo: 3986 personas, '
        f'{fmt(100*3986/m["mean_people_per_snapshot"], "%")} de la prioridad equivalente. Su tasa observada es 4.7%, '
        'frente a 3.5% en el total. C estima 5.2%: sobreestima 0.5 pp. Aparece en las 24 fotos históricas. '
        'Es una base amplia para explorar necesidades de desarrollo; la causa del riesgo no está identificada.',
        '2. **G1: 3–5 años, entrada, con salidas previas del equipo.** Tiene 1424 personas y 5.5% observado. '
        'La señal de prioridad persiste en las 24 fotos, pero C estima 8.1%: sobreestima 2.6 pp. '
        'Conviene estudiar continuidad del trabajo y desarrollo profesional, evitando usar 8.1% como volumen esperado sin reconocer ese error.',
        '3. **G4: 3–5 años, nivel medio, con salidas previas.** Observado 6%, estimado 5.4%, '
        '521 personas y 31 salidas distintas. Tiene la tasa observada más alta entre los grupos publicables de esta foto, '
        'aunque menos eventos que los grupos grandes. Entra en las 12 fotos de los dos periodos históricos más recientes.',
        '4. **G6: 2–3 años, entrada, sin salidas previas.** Observado 5.7%, estimado 4.8% y 1008 personas. '
        'La subestimación de 0.8 pp en esta foto merece seguimiento. Históricamente aparece en las 24 fotos, '
        'pero el signo del error cambió: C lo sobreestimaba en los cuatro periodos agregados.', '',
        'G3 también requiere atención a la precisión: estima 6.4% frente a 4.9% observado. '
        'G2 tiene prioridad persistente y observado suprimido en esta foto. G7 y G8 complementan el núcleo seleccionado. '
        'G9 es principalmente una decisión de capacidad por su tamaño y posición en el límite.', '',
        '## Persistencia histórica de la prioridad', '',
        'Número de fotos donde cada grupo estuvo seleccionado, de seis por periodo. Incluye selección parcial en el límite. '
        'Un cero indica que no entró en esa prioridad; no permite concluir que su riesgo fuese bajo ni que el grupo fuese inelegible. '
        'La persistencia corresponde al grupo definido por sus cortes; las personas y los modelos cambian entre fotos.', '',
        '| Grupo | Feb–jul 2024 | Ago 2024–ene 2025 | Feb–jul 2025 | Ago 2025–ene 2026 | Total de 24 fotos |',
        '|---|---:|---:|---:|---:|---:|']
    for row in groups:
        text.append('| '+row['id']+' | '+' | '.join(str(v['selected_snapshots']) for v in row['history'])+' | '+str(row['selected_snapshots_24'])+' |')
    text += ['', '**Prioridad persistente no garantiza calibración estable.** G1 era subestimado en los tres primeros '
        'periodos y sobreestimado en el cuarto; en febrero de 2026 vuelve a estar sobreestimado. '
        'Un ajuste global de tasa podría mejorar unos grupos y empeorar otros. G5 muestra errores agregados '
        'menores a 0.8 pp en los cuatro periodos, pero eso no demuestra precisión en cada mes.', '',
        'Las 24 fotos pertenecen a cuatro periodos retrospectivos y comparten personas y ventanas de seguimiento. '
        'El conteo de presencia no equivale a 24 pruebas independientes ni es un intervalo de confianza.', '',
        '## Cómo traducir las señales en hipótesis de acción', '',
        'Son propuestas para diagnóstico y eventual piloto. Los cortes no demuestran estancamiento, sobrecarga, '
        'problemas del manager ni causas personales de salida.', '',
        '| Grupos | Señal observada | Hipótesis por comprobar | Primer paso propuesto | Seguimiento del eventual piloto |',
        '|---|---|---|---|---|',
        '| G5 y G6 | Riesgo observado elevado en nivel de entrada con 2–5 años, aun sin salidas previas registradas en el equipo | Las oportunidades de desarrollo y movilidad podrían ser relevantes | Revisar rutas de carrera y acceso a movilidad; recoger necesidades de desarrollo de forma agregada | Cobertura de conversaciones y planes; después comparar salida a seis meses con grupos comparables |',
        '| G1 y G3 | Prioridad persistente con salidas previas del equipo; estimaciones recientes por encima de lo observado | La continuidad del trabajo, la distribución de carga o las oportunidades podrían influir | Revisar carga, prioridades, respaldo de conocimiento y cobertura de vacantes a nivel de equipo | Cumplimiento de ajustes acordados; seguimiento de carga y salida a seis meses |',
        '| G4 y G8 | Nivel medio con salidas previas; C subestima el observado de esta foto | Cambios de responsabilidades o expectativas de desarrollo podrían ser relevantes | Revisar claridad del rol, continuidad y oportunidades; contrastar la hipótesis con evidencia agregada | Evolución de necesidades identificadas y salida a seis meses |',
        '| G7 | 1–2 años, entrada y salidas previas del equipo; observado por encima de la predicción | Continuidad del acompañamiento y expectativas del puesto podrían contribuir | Revisar acompañamiento, expectativas y transición después del primer año | Cobertura del acompañamiento y resultado a seis meses |',
        '| G2 | Prioridad histórica en 24 fotos; observado actual suprimido | Falta evidencia publicable de esta foto para caracterizar la precisión | Mantener el diagnóstico dentro del núcleo elegido y revisar evidencia agregada de mayor horizonte | Preservar supresión; no inferir ni publicar su tasa actual desde totales |',
        '| G9 | Estimación cercana al observado y posición en el límite de capacidad | Su inclusión completa depende de presupuesto y capacidad, además de riesgo | Evaluar cobertura adicional como escenario separado | Coste y alcance marginales; comparar con el núcleo completo |', '',
        'Para atribuir una reducción de salidas a una acción haría falta un diseño de evaluación del piloto. '
        'La captura del modelo no estima cuántas salidas se evitarían.', '',
        '## Decisión práctica de capacidad', '',
        '| Escenario archivado de febrero de 2026 | Personas equivalentes | Cobertura | Captura de salidas | Observado R6 | Estimado R6 |',
        '|---|---:|---:|---:|---:|---:|']
    for label, v in [('Ocho grupos completos', core), ('Capacidad exacta del 30%', m), ('Nueve grupos completos', whole),
                     ('Capacidad exacta del 40%', r['scenarios']['40']['metrics'])]:
        text.append(f'| {label} | {fmt(v["mean_people_per_snapshot"])} | {fmt(v["coverage_percent"], "%")} | '
                    f'{fmt(v["capture_percent"], "%")} | {fmt(v["observed_percent"], "%")} | {fmt(v["predicted_percent"], "%")} |')
    text += ['', '**Para diseñar una primera fase cercana al 30%, usaría los ocho grupos completos como referencia:** '
        'representan 29% de la población y capturan 41.6% de las salidas de esta foto. '
        'Incluir G9 completo eleva la cobertura a 36.3% y la captura a 49.9%; requiere capacidad adicional. '
        'La elección operativa dependerá de presupuesto y de actualizar la pertenencia a los grupos.', '',
        'Este recorte a grupos completos conserva la receta de C. No genera otro modelo ni cambia sus coeficientes.', '',
        '## Qué hace útil a un grupo', '',
        '- **Riesgo:** tasa observada y estimada, con una referencia explícita y la misma ventana.',
        '- **Alcance:** tamaño del grupo y capacidad necesaria; riesgo alto y volumen grande aportan información distinta.',
        '- **Precisión:** error con signo y absoluto; revisar cada grupo y fecha, además del promedio.',
        '- **Persistencia:** presencia en prioridad y estabilidad de la estimación; el cambio de personas importa.',
        '- **Interpretación y acción:** regla comprensible e hipótesis que se pueda contrastar y atender.',
        '- **Evidencia suficiente:** respetar tamaños y supresiones; un grupo grande no garantiza una estimación acertada.', '',
        '## Método, fuentes y límites', '',
        '- Resultado objetivo: salida voluntaria en los seis meses siguientes / personas activas en la foto. '
        'La predicción R6 acumula hazards mensuales. Los grupos se ordenan por riesgo medio predicho.',
        '- Tamaños completos de G1–G9 recuperados del escenario archivado del 40%, donde esos nueve grupos entran completos. '
        'Se reconciliaron tasas, eventos publicables, pesos de selección, suma de tamaños y predicciones.',
        '- Referencia poblacional = observado de prioridad / lift, conciliada entre las capacidades 20%, 30% y 40%. '
        'No se reconstruyen tasas o eventos de grupos suprimidos.',
        '- Historia: cuatro periodos de seis fotos, de 18-feb-2024 a 25-ene-2026. La foto adicional de febrero '
        'se presenta separada; no se añade como quinto periodo al promedio histórico.',
        f'- Fuente: `{r["source"]}`, `extension.evaluation.C_Bcuts` y `folds[].evaluation.C_Bcuts`.',
        f'- Consulta original: `{r["source_query"]}`, ejecutada el 8-oct-2026, conocimiento hasta 7-sep-2026. '
        'Esta revisión no ejecuta consultas ni reentrenamientos.',
        '- Se conservan los límites de C: fuentes históricas revisables, variables proxy y otras salidas tratadas '
        'como no voluntarias. Las hipótesis de acción requieren evidencia adicional.',
        '- Archivos: `results.json`, `grupos-prioritarios.csv`, `presencia-historica.csv`, `analysis-checks.json`, '
        '`preservation.json` y `manifest.json`. Los modelos anteriores permanecen intactos.', '']
    (out/'informe.md').write_text('\n'.join(text), encoding='utf-8')


if __name__ == '__main__':
    main()
