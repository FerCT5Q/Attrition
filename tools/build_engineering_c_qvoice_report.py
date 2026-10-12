"""Informe C + QVoice usando exclusivamente resultados agregados del experimento."""
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

import engineering_model_c_qvoice as study

ROOT = study.ROOT
OUT = ROOT/'output/analysis/engineering/20261008/model-c-plus-qvoice-v1'


def fmt(x, suffix=''):
    if x is None:
        return '—'
    if 0 < x < .05:
        return '<0.1'+suffix
    if -.05 < x < 0:
        return '>-0.1'+suffix
    text = f'{x:.1f}'.rstrip('0').rstrip('.')
    return ('0' if text == '-0' else text)+suffix


def selected_label(spec):
    labels = {'q4': 'Q4', 'q12': 'Q12', 'career': 'Career Goals',
              'mean33': 'Promedio de 33 preguntas', 'engagement': 'Engagement (Q1/Q2/Q3)',
              'connection': 'Connection (Q5/Q7)', 'wellbeing': 'Wellbeing (Q8/Q10/Q11)',
              'confidence': 'Confidence (Q13/Q17)'}
    if spec['kind'] == 'pca':
        return f'PCA: {spec["components"]} componentes de 33 preguntas'
    return ' + '.join(labels[b] for b in spec['blocks'])


def main():
    r = study.base.read(OUT/'results.json')
    s = r['summary']
    d = r['decisions']['CQ']['30']
    scalar = r['decisions']['CQ_scalar']['30']
    loss_delta = 100*(s['CQ']['global']['log_loss']/s['C']['global']['log_loss']-1)
    capture_delta = d['capture_difference_pp']
    if d['meets_rule']:
        title = 'C + QVoice mejora la priorización con los cortes acordados bajo el criterio retrospectivo'
    elif loss_delta < 0:
        title = 'QVoice mejora la pérdida predictiva de C, pero falta demostrar la mejora conjunta en grupos'
    else:
        title = 'C + QVoice todavía no demuestra una mejora conjunta frente a C'
    ci = d['capture_ci95_pp']
    lines = ['# C + QVoice frente a C', '', f'## {title}', '',
        'Fecha de ejecución: 8-oct-2026. Modo: `presentation`.', '',
        'Objetivo: identificar grupos donde enfocar acciones de retención, estimando su salida voluntaria a seis meses. '
        'Población: Engineering, Employee, Regular, activo, sin RF360. Se conserva la agrupación elegida: '
        '**antigüedad × salidas del equipo × nivel**. El modelo C base conserva sus coeficientes.', '',
        '## Veredicto bajo el criterio declarado', '',
        f'- C + QVoice sin calibración posterior: **{"cumple" if d["meets_rule"] else "no cumple"}** la regla principal al 30%.',
        f'- C + QVoice con escalar R6: **{"cumple" if scalar["meets_rule"] else "no cumple"}** esa regla.',
        f'- La versión sin calibración cambia la captura media en **{fmt(capture_delta)} pp**, '
        f'IC95 [{fmt(ci[0])}, {fmt(ci[1])}]; gana en {d["winning_periods"]} de dos periodos.',
        f'- Su log-loss R6 cambia {fmt(loss_delta)}% frente a C; un cambio negativo indica menor pérdida.', '',
        'La regla exige ganar captura en ambos periodos, IC95 medio positivo, errores por grupo y grupo-mes '
        'que no empeoren más de 0.1 pp, log-loss y Brier que no empeoren más de 0.5% relativo, '
        'y aporte frente al control de disponibilidad. Es una regla retrospectiva, no una promoción automática.', '']
    checks = {
        'capture_wins_both_periods': 'La captura mejora en ambos periodos',
        'capture_ci_lower_positive': 'El IC95 del cambio medio de captura queda por encima de cero',
        'group_error': 'El error por grupo queda dentro de la tolerancia',
        'group_snapshot_error': 'El error grupo-mes queda dentro de la tolerancia',
        'log_loss': 'El log-loss queda dentro de la tolerancia',
        'brier': 'El Brier queda dentro de la tolerancia',
        'incremental_capture_vs_availability': 'Las respuestas capturan más que el control de disponibilidad',
        'incremental_loss_vs_availability': 'Las respuestas tienen pérdida no mayor que el control de disponibilidad'}
    lines += ['| Comprobación al 30% | C + Q sin calibración | C + Q con escalar R6 |', '|---|---|---|']
    for key, label in checks.items():
        lines.append(f'| {label} | {"Cumple" if d["checks"][key] else "No cumple"} | '
                     f'{"Cumple" if scalar["checks"][key] else "No cumple"} |')
    if not d['meets_rule']:
        changes = [p['evaluation']['CQ']['scenarios']['30']['metrics']['capture_percent'] -
                   p['evaluation']['C']['scenarios']['30']['metrics']['capture_percent'] for p in r['periods']]
        ties = sum(abs(x) <= 1e-9 for x in changes)
        losses = sum(x < -1e-9 for x in changes)
        lines += ['', f'Al 30% hay {d["winning_periods"]} periodo con mejora, {ties} empate y {losses} derrotas. '
                  'La ganancia media tiene un intervalo positivo, pero la consistencia temporal exigida '
                  'por la regla sigue pendiente. **C + QVoice queda como extensión prometedora para '
                  'validación adicional; C se conserva como referencia.**', '']
    b30, q30 = s['C']['scenarios']['30'], s['CQ']['scenarios']['30']
    lines += [f'El error medio por grupo cambia {fmt(100*(q30["group_mae_pp"]/b30["group_mae_pp"]-1))}% relativo; '
              'la diferencia absoluta es pequeña y ambos redondean a 1 pp. '
              f'El promedio del mayor error publicable por periodo pasa de '
              f'{fmt(b30["worst_publishable_group_error_pp"])} a '
              f'{fmt(q30["worst_publishable_group_error_pp"])} pp. '
              'La mejora promedio no garantiza mejores estimaciones en cada grupo.', '',
              'La calibración adicional conserva la misma captura y apenas cambia las pérdidas: '
              'en esta comparación no aporta una ventaja práctica clara sobre C + Q sin calibración posterior.', '']
    lines += ['',
        '## Comparación al priorizar al 30%', '',
        'Promedio con igual peso de dos periodos: fotos de agosto–diciembre de 2025 (cinco fotos) '
        'y enero–febrero de 2026 (dos fotos). Cada foto se evalúa por sus siguientes seis meses; '
        'la última termina seguimiento en agosto de 2026. No comparar estas cifras directamente '
        'con el promedio de cuatro periodos de la selección original de C.', '',
        '| Modelo | Captura | Estimado en prioridad | Observado en prioridad | Error por grupo | Error grupo-mes |',
        '|---|---:|---:|---:|---:|---:|']
    order = ['C', 'CQ', 'CQ_scalar', 'C_scalar', 'C_refresh', 'C_availability', 'C_availability_scalar']
    for name in order:
        m = s[name]['scenarios']['30']
        lines.append(f'| {study.NAMES[name]} | {fmt(m["capture_percent"], "%")} | {fmt(m["predicted_percent"], "%")} | '
                     f'{fmt(m["observed_percent"], "%")} | {fmt(m["group_mae_pp"], " pp")} | {fmt(m["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', 'Captura = salidas observadas en la población priorizada / salidas observadas totales. '
        'Los conteos corresponden a persona-snapshot; una persona y su salida pueden contribuir a varias ventanas. '
        'Error por grupo = diferencia absoluta de la tasa estimada y observada por grupo, ponderada por personas. '
        'Error grupo-mes calcula ese error antes de promediar meses, evitando compensaciones temporales.', '',
        '![Captura al 30% por periodo](captura-por-periodo.png)', '',
        '## Estimaciones en toda la población', '',
        '| Modelo | Log-loss × 1000 ↓ | Brier × 1000 ↓ | PR-AUC ↑ | Lift del 10% ↑ | Estimado R6 | Observado R6 | Error agregado |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in order:
        m = s[name]['global']
        lines.append(f'| {study.NAMES[name]} | {fmt(m["log_loss"]*1000)} | {fmt(m["brier_score"]*1000)} | '
            f'{fmt(m["pr_auc"]*100, "%")} | {fmt(m["lift_at_10_percent"], "×")} | {fmt(m["predicted_percent"], "%")} | '
            f'{fmt(m["observed_percent"], "%")} | {fmt(m["calibration_error_pp"], " pp")} |')
    lines += ['', f'El Brier de C + Q cambia {fmt(100*(s["CQ"]["global"]["brier_score"]/s["C"]["global"]["brier_score"]-1))}% relativo. '
        f'El error de calibración agregado aumenta {fmt(s["CQ"]["global"]["calibration_error_pp"]-s["C"]["global"]["calibration_error_pp"], " pp")} '
        'en promedio, aunque ambos valores mostrados redondean a 0.1 pp.', '',
        'Log-loss y Brier evalúan la calidad de las probabilidades. Se muestran multiplicados por 1000 para '
        'mantener un decimal sin ocultar diferencias; esa escala no cambia las comparaciones. PR-AUC y lift describen '
        'el ranking individual usado sólo como diagnóstico interno: no se publica un listado de empleados. '
        'Una mejora individual puede quedar diluida al resumirse en los mismos grupos de tres variables.', '',
        '## Consistencia entre periodos y capacidades', '',
        '| Periodo de fotos | Personas distintas | Capacidad | C: captura | C + Q: captura | C + Q escalar: captura | C: error grupo-mes | C + Q: error grupo-mes |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for p in r['periods']:
        for cap in ['20', '30', '40']:
            b, q, cal = [p['evaluation'][n]['scenarios'][cap]['metrics'] for n in ['C', 'CQ', 'CQ_scalar']]
            lines.append(f'| {p["first_snapshot"]} a {p["last_snapshot"]} | {p["people"]} | {cap}% | '
                f'{fmt(b["capture_percent"], "%")} | {fmt(q["capture_percent"], "%")} | {fmt(cal["capture_percent"], "%")} | '
                f'{fmt(b["group_snapshot_mae_pp"], " pp")} | {fmt(q["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', '| Variante | Capacidad | Cambio medio de captura frente a C | IC95 | Periodos con mejora | Cumple regla |',
              '|---|---:|---:|---|---:|---|']
    for variant, scenarios in r['decisions'].items():
        for cap, value in scenarios.items():
            ci = value['capture_ci95_pp']
            lines.append(f'| {study.NAMES[variant]} | {cap}% | {fmt(value["capture_difference_pp"], " pp")} | '
                f'[{fmt(ci[0])}, {fmt(ci[1])}] pp | {value["winning_periods"]} de 2 | {"Sí" if value["meets_rule"] else "No"} |')
    lines += ['', 'Los intervalos se obtuvieron con 500 remuestreos pareados por persona, conservando sus ventanas juntas. '
        'Son intervalos puntuales, condicionales a la selección y modelos ajustados; no corrigen comparaciones múltiples. '
        'Dos periodos cortos, con personas repetidas y ventanas superpuestas, no establecen estabilidad de largo plazo.', '',
        '## Qué QVoice se seleccionó', '',
        'Se buscaron 255 subconjuntos de ocho bloques, además de cinco tamaños PCA como diagnóstico; '
        'tres penalizaciones por candidato: 780 ajustes por corte. La selección utiliza dos intervalos mensuales '
        'anteriores al periodo externo. Después se reajusta sólo la corrección elegida sobre C con todas las '
        'etiquetas mensuales maduras anteriores al origen.', '',
        '| Corte | C base disponible desde | Combinación seleccionada | Penalización L2 |',
        '|---|---|---|---:|']
    for p in r['periods']:
        lines.append(f'| {p["origin"]} | {p["C_origin"]} | {selected_label(p["selected"])} | {fmt(p["selected"]["l2"])} |')
    final = study.base.read(OUT/'trained-model/model.json')
    lines.append(f'| Final: {r["knowledge_boundary"]} | {final["base_model_origin"]} | {selected_label(r["final_selected"])} | {fmt(r["final_selected"]["l2"])} |')
    lines += ['', 'Bloques disponibles: Intent to Stay Q4 y Q12 por separado; Career Goals; promedio de 33 preguntas; '
        'Engagement Q1/Q2/Q3; Connection Q5/Q7; Wellbeing Q8/Q10/Q11; Confidence Q13/Q17. '
        'El promedio de 33 incluye preguntas ya presentes en otros bloques; no son fuentes independientes. '
        'Career conserva una diferencia de redacción de 2024 y se interpreta exploratoriamente.', '',
        'En el artefacto final, Intent to Stay Q4 y Q12 entran dentro del promedio de 33 preguntas '
        '(M16 y M14, respectivamente), sin coeficientes propios para esas dos preguntas. '
        'Mapping conservado en `qvoice-model-b-calibrated-v1/preflight/source-metadata.json`.', '',
        'La wave 2024 se usa sólo en snapshots de 2025 y la wave 2025 sólo en snapshots de 2026. '
        'Se exige continuidad del episodio laboral. Los duplicados de fuente se excluyen y se mantienen estados '
        'de ausencia de respuesta o pregunta. Q6/Q9, Heartbeat, comentarios y wave 2026 quedan excluidos.', '',
        'El modelo final contiene una corrección reajustada al corte de conocimiento; sus coeficientes no '
        'se atribuyen retrospectivamente a los periodos evaluados. El C base sigue congelado en agosto de 2025.', '',
        '### Respuestas utilizables en el frame de C', '',
        'Cobertura sobre todas las observaciones persona-snapshot cargadas del año correspondiente, '
        'después del enlace y del control de episodio. Estos porcentajes incluyen meses que sólo sirven '
        'para entrenamiento o proyección; no describen únicamente las dos ventanas evaluadas.', '',
        '| Wave | Año de los snapshots | Pregunta o resumen | Observaciones del año | Respuesta utilizable |',
        '|---|---:|---|---:|---:|']
    input_checks = study.base.read(OUT/'qvoice-input-checks.json')
    qlabels = {'qv_Q4': 'Intent to Stay Q4', 'qv_Q12': 'Intent to Stay Q12',
               'qv_career': 'Career Goals', 'qv_mean33': 'Promedio de 33 preguntas'}
    for row in input_checks['coverage_person_snapshot']:
        if row['feature'] in qlabels:
            lines.append(f'| {row["wave"]} | {int(row["wave"])+1} | {qlabels[row["feature"]]} | '
                         f'{row["exposures"]} | {fmt(row["valid_percent"], "%")} |')
    lines += ['',
        '## Cómo se calibró y qué se puede atribuir a las respuestas', '',
        'C + Q sin calibración posterior es el candidato principal declarado. La alternativa aplica '
        '`R6_calibrado = 1 - (1 - R6)^exp(a)`. El escalar usa etiquetas de seis meses maduras antes del corte '
        'y predicciones auxiliares entrenadas antes de sus propias fotos. Con menos de tres orígenes '
        'admisibles se utiliza identidad.', '',
        '| Periodo | C: estado del escalar | C: multiplicador | C + Q: estado del escalar | C + Q: multiplicador |',
        '|---|---|---:|---|---:|']
    for p in r['periods']:
        c, q = p['calibrators']['C'], p['calibrators']['CQ']
        status = lambda x: 'Ajustado' if x['status'] == 'fitted' else 'Identidad: historia insuficiente'
        lines.append(f'| {p["id"]} | {status(c)} | {fmt(c["multiplier"], "×")} | {status(q)} | {fmt(q["multiplier"], "×")} |')
    lines += ['', 'Las columnas y penalización elegidas al corte se reutilizan retrospectivamente en los auxiliares: '
        'no es una validación anidada completa del calibrador. Las salidas del periodo externo no se utilizan. '
        'El escalar conserva el ranking individual; el orden de medias de grupos puede cambiar y se evalúa nuevamente.', '',
        'Los controles separan tres efectos: C con intercepto actualizado aprende sólo la tasa; C con disponibilidad '
        'aprende si hay una respuesta utilizable y los estados de ausencia; C + Q añade el contenido de las respuestas. '
        'Se aplica también el escalar a los controles para comparar calibraciones equivalentes.', '',
        '### Comparaciones pareadas adicionales', '',
        '| Comparación | Métrica | Diferencia | IC95 |', '|---|---|---:|---|']
    for item in r['intervals']:
        if item['metric'] not in ['capture30', 'log_loss']:
            continue
        factor = 1000 if item['metric'] == 'log_loss' else 1
        unit = 'Log-loss × 1000' if item['metric'] == 'log_loss' else 'Captura al 30%, pp'
        ci = item['ci95']
        lines.append(f'| {study.NAMES[item["left"]]} menos {study.NAMES[item["right"]]} | {unit} | '
            f'{fmt(item["difference"]*factor)} | [{fmt(ci[0]*factor)}, {fmt(ci[1]*factor)}] |')
    lines += ['', '## Grupos y estimación sobre la misma población priorizada', '',
        'Las definiciones de grupos son iguales en todas las variantes. El número elegible cambia por foto '
        'con el mínimo de 300 personas. Sólo cambia el riesgo estimado medio y, potencialmente, el orden de prioridad. '
        'Esta evaluación no crea nuevos grupos por respuestas QVoice.', '',
        '| Periodo | Grupos elegibles, mínimo–máximo | Estimador sobre prioridad de C | Error por grupo | Error grupo-mes |',
        '|---|---|---|---:|---:|']
    for p in r['periods']:
        for name in ['C', 'CQ', 'CQ_scalar']:
            entry = p['evaluation'][name]
            m = entry['on_C_selection']
            lines.append(f'| {p["id"]} | {entry["groups_minimum"]}–{entry["groups_maximum"]} | {study.NAMES[name]} | '
                f'{fmt(m["group_mae_pp"], " pp")} | {fmt(m["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', '### Grupos priorizados y mayor error publicable al 30%', '',
        '| Periodo | Modelo | Grupos priorizados por foto, promedio | Mayor error de grupo publicable | Cobertura publicable dentro de prioridad |',
        '|---|---|---:|---:|---:|']
    for p in r['periods']:
        for name in ['C', 'CQ', 'CQ_scalar']:
            m = p['evaluation'][name]['scenarios']['30']['metrics']
            lines.append(f'| {p["id"]} | {study.NAMES[name]} | {fmt(m["mean_selected_groups_per_snapshot"])} | '
                         f'{fmt(m["worst_publishable_group_error_pp"], " pp")} | '
                         f'{fmt(m["publishable_group_exposure_percent"], "%")} |')
    lines += ['', 'El mayor error se calcula sobre los grupos cuyo observado cumple las reglas de publicación. '
              'La cobertura indica qué proporción de observaciones priorizadas representan esos grupos; '
              'no es el peor error entre todos los grupos pequeños o suprimidos.', '',
              '### Grupos priorizados por C + Q en enero–febrero de 2026', '',
              'Se usa la variante principal sin calibración posterior al 30%. Las tasas resumen sólo '
              'las fotos en que cada grupo fue priorizado y aplican el peso del grupo del límite. '
              'El promedio de personas se calcula sobre las dos fotos. Esta tabla describe el periodo '
              'retrospectivo; no es una lista vigente de intervención.', '',
              '| Grupo | Personas priorizadas por foto, promedio | Riesgo estimado R6 | Salida observada R6 | Error |',
              '|---|---:|---:|---:|---:|']
    for group in sorted(r['periods'][-1]['evaluation']['CQ']['scenarios']['30']['selected_groups'],
                        key=lambda row: row.get('predicted_percent', -1), reverse=True):
        lines.append(f'| {group["group"]} | {fmt(group.get("mean_selected_people_per_snapshot"))} | '
                     f'{fmt(group.get("predicted_percent"), "%")} | {fmt(group.get("observed_percent"), "%")} | '
                     f'{fmt(group.get("error_pp"), " pp")} |')
    lines += ['', '— indica una cifra suprimida por las reglas de publicación.', '']
    lines += ['', '### Alternativas con grupos completos alrededor del 30%', '',
        '| Periodo | Modelo | Cobertura sin grupo límite | Captura sin grupo límite | Cobertura con grupo límite | Captura con grupo límite |',
        '|---|---|---:|---:|---:|---:|']
    for p in r['periods']:
        for name in ['C', 'CQ', 'CQ_scalar']:
            v = p['evaluation'][name]['scenarios']['30']
            low, high = v['whole_groups_excluding_boundary'], v['whole_groups_including_boundary']
            lines.append(f'| {p["id"]} | {study.NAMES[name]} | {fmt(low.get("coverage_percent"), "%")} | '
                f'{fmt(low.get("capture_percent"), "%")} | {fmt(high.get("coverage_percent"), "%")} | '
                f'{fmt(high.get("capture_percent"), "%")} |')
    lines += ['', '## Alcance, conservación y fuentes', '',
        '- Los grupos identifican asociaciones predictivas. No estiman salidas evitables ni el efecto de una acción.',
        '- Persisten los límites del C original: revisiones históricas de snapshots, fecha efectiva de IOS, '
        'capas/comp ratio almacenados y tratamiento de otras salidas como no voluntarias.',
        '- La regla anual QVoice es una hipótesis de negocio aprobada; no acredita fechas reales de publicación.',
        '- C base se reproduce contra el último fold archivado; la población y etiquetas se reconciliaron. '
        'La consulta de C sólo se amplió con los indicadores existentes de continuidad de episodio.',
        f'- Consulta: `{r["query"]}`. Ejecución 8-oct-2026; conocimiento hasta {r["knowledge_boundary"]}.',
        '- Plan previo: `docs/plans/attrition-model-c-plus-qvoice-20261008.md`; configuración congelada: `frozen-config.json`.',
        '- Evidencia: `results.json`, `folds/`, `trained-model/`, `qvoice-input-checks.json`, `analysis-checks.json` y `preservation.json`.',
        f'- Tiempo: {fmt(r["elapsed_seconds"]/60)} minutos; carga y QVoice: {fmt(r["load_seconds"]/60)} minutos. '
        'Cero reajustes de C base. Matrices y offsets reutilizados en la búsqueda.',
        '- Los modelos anteriores conservan sus hashes. No se guardan filas, respuestas, llaves o riesgos individuales. '
        'Tasas de grupos sólo con al menos 30 personas por foto seleccionada y 30 personas distintas con evento.', '']
    (OUT/'informe.md').write_text('\n'.join(lines), encoding='utf-8')
    plot(r, title)
    target = OUT/'source/tools'/Path(__file__).name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, target)
    review = {'skill': 'morgan-vis', 'audience': 'Propietario del modelo; decidir si continuar C + QVoice.',
        'message': title, 'design': 'Barras por periodo desde cero, etiquetas directas, C gris y QVoice azul.',
        'alternatives': ['Media única: oculta variación entre los dos periodos.', 'Curva temporal: sólo dos bloques y duración desigual.'],
        'limitations': 'Evaluación retrospectiva, dos periodos, mismas cohortes y sin efecto causal.',
        'source': r['query'], 'maximum_visible_decimals': 1}
    study.write(OUT/'visual-design.json', review)
    m = study.base.read(OUT/'manifest.json')
    m['status'] = 'completed_analysis_and_report'
    m['files'] = {str(p.relative_to(OUT)): study.base.sha(p) for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    study.write(OUT/'manifest.json', m)
    print(title)


def plot(r, title):
    names = ['C', 'CQ', 'CQ_scalar']
    labels = ['C', 'C + Q sin calibración', 'C + Q con escalar R6']
    colors = ['#a7afb9', '#2868b5', '#74a5cd']
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), sharex=True)
    for ax, p in zip(axes, r['periods']):
        vals = [p['evaluation'][n]['scenarios']['30']['metrics']['capture_percent'] for n in names]
        bars = ax.barh(labels, vals, color=colors, height=.58)
        ax.invert_yaxis()
        ax.set_title(('Agosto–diciembre de 2025' if p['id'] == 'aug_dec_2025' else 'Enero–febrero de 2026')+
                     f'\n{p["people"]} personas distintas', loc='left', fontsize=12, pad=20)
        for bar, value in zip(bars, vals):
            ax.text(value+.5, bar.get_y()+bar.get_height()/2, fmt(value, '%'), va='center', fontsize=11)
        ax.set_xlim(0, max(55, max(vals)+8))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt(x, '%')))
        ax.set_xlabel('Captura de salidas al priorizar al 30%')
        ax.tick_params(axis='both', length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis='x', color='#e6e9ed', linewidth=.7)
        ax.set_axisbelow(True)
    if r['decisions']['CQ']['30']['meets_rule']:
        short = 'C + QVoice mejora la priorización bajo el criterio retrospectivo'
    else:
        short = 'C + QVoice mejora la captura en 2025 y empata al inicio de 2026'
    fig.suptitle(short, x=.02, y=.98, ha='left', fontsize=16, weight='bold')
    fig.text(.02, .875, 'Engineering · salida voluntaria en los seis meses siguientes a cada foto\n'
             'Mismos cortes: antigüedad × salidas del equipo × nivel. C base archivado; evaluación retrospectiva.', fontsize=10)
    fig.text(.02, .035, 'Fuente: results.json y queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql · 8-oct-2026\n'
             'Employee, Regular, activo, sin RF360. Peso uniforme en grupo límite; observaciones persona-snapshot.', fontsize=8)
    fig.subplots_adjust(left=.18, right=.96, top=.72, bottom=.2, wspace=.85)
    fig.savefig(OUT/'captura-por-periodo.png', dpi=170, facecolor='white')
    fig.savefig(OUT/'captura-por-periodo.svg', facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
