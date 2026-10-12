"""Informe de la comparación de agrupaciones a partir de evidencia agregada."""
from pathlib import Path
import json
import re
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

import engineering_c_group_selection as analysis

ROOT = analysis.ROOT
OUT = ROOT / 'output/analysis/engineering/20261008/c-group-selection-v1'
DISPLAY = {**analysis.historical.DISPLAY,
    'prior_experience_band': 'Experiencia previa', 'time_at_level_band': 'Tiempo en el nivel',
    'manager_left_6m': 'Salida del manager en seis meses', 'ios_12m': 'Movimientos IOS en 12 meses',
    'layers_band': 'Capa organizativa registrada', 'work_arrangement_group': 'Modalidad de trabajo',
    'region': 'Región', 'comp_ratio_band': 'Banda de comp ratio', 'grade_family': 'Familia de grado',
    'acquisition_recorded': 'Adquisición registrada', 'transfer_12m': 'Transferencia en 12 meses'}


def display(value):
    return re.sub('|'.join(re.escape(k) for k in sorted(DISPLAY, key=len, reverse=True)),
                  lambda match: DISPLAY[match.group(0)], value)


def fmt(value, suffix=''):
    if value is None:
        return '—'
    if 0 < value < .05:
        return '<0.1' + suffix
    s = f'{value:.1f}'.rstrip('0').rstrip('.')
    return ('0' if s == '-0' else s) + suffix


def main():
    result = analysis.base.read(OUT / 'results.json')
    # Con seis snapshots sin duplicados, ningún evento-persona aparece más de
    # seis veces: 180 eventos-exposición garantizan al menos 30 personas.
    privacy_bounds = []
    for path in sorted((OUT / 'development-candidates').glob('*.json')):
        candidates = analysis.base.read(path)
        minimum_lower_bound = min(c['observed_percent'] / 100 * c['mean_people_per_snapshot']
                                  for c in candidates)
        if minimum_lower_bound < 30:
            raise RuntimeError('Una candidata necesita reconciliar eventos distintos antes de publicar.')
        privacy_bounds.append({'file': str(path.relative_to(OUT)),
            'minimum_lower_bound_distinct_event_people': minimum_lower_bound,
            'outcome': 'pass'})
    analysis.write(OUT / 'development-publication-check.json', {
        'method': 'Eventos-exposición / seis fotos es cota inferior de personas distintas con evento; frame sin duplicados.',
        'minimum_distinct_event_people_required': 30, 'checks': privacy_bounds})
    summary = result['summary']['30']
    selected = summary['C_selected']
    reference = summary['B_cuts']
    diff = selected['comparison']['difference_vs_B_cuts_pp']
    primary_preferred = selected['meets_preference_rule']
    headline = ('C con selección propia supera a B con cortes bajo el criterio retrospectivo'
                if primary_preferred else
                'La búsqueda de cortes de C todavía no demuestra una ventaja consistente sobre B')
    if abs(diff) < .05:
        headline = 'C con cortes propios muestra una captura media similar a B y menor error por grupo'
    elif diff < 0:
        headline = 'B con sus cortes conserva más salidas que la selección principal de C'

    lines = ['# Comparación de agrupaciones de B y C', '', f'## {headline}', '',
        'Ejecución: 8-oct-2026. Modo: `presentation`. Población: Engineering, Employee, Regular, activo, sin RF360.', '',
        'Objetivo: priorizar grupos para explorar acciones de retención. Resultado objetivo: salida voluntaria en los seis meses siguientes a cada foto. '
        'La evidencia describe asociación y capacidad de priorización; no estima el efecto de una intervención.', '',
        '## Resultado principal: priorizar al 30% de la población', '',
        'Promedio con igual peso de cuatro periodos. Captura = salidas observadas en la población priorizada / salidas observadas totales. '
        'Cada periodo contiene seis snapshots: una persona y su salida pueden contribuir en varias ventanas; '
        'los eventos del cálculo son persona-snapshot con salida, no salidas únicas sumadas a través del tiempo.', '',
        '| Modelo y agrupación | Captura | Estimado R6 | Observado R6 | Error por grupo | Error grupo-mes | Grupos elegibles, media |',
        '|---|---:|---:|---:|---:|---:|---:|']
    order = ['B_cuts', 'C_Bcuts', 'C_selected', 'C_gini', 'B_tree8', 'B_tree16', 'C_tree8', 'C_tree16']
    for name in order:
        entry = summary[name]
        m = entry['metrics']
        lines.append(f'| {entry["label"]} | {fmt(m["capture_percent"], "%")} | {fmt(m["predicted_percent"], "%")} | '
                     f'{fmt(m["observed_percent"], "%")} | {fmt(m["group_mae_pp"], " pp")} | '
                     f'{fmt(m["group_snapshot_mae_pp"], " pp")} | {fmt(entry["structure"]["mean_eligible_groups"])} |')
    ci = selected['comparison']['ci95_pp']
    delta_text = 'diferencia de captura menor a 0.1 pp' if abs(diff) < .05 else f'{fmt(diff)} pp de captura'
    lines += ['', f'C con selección propia frente a B cortes: **{delta_text}**, '
              f'IC95 [{fmt(ci[0])}, {fmt(ci[1])}]. Gana en {selected["winning_periods"]} periodos, '
              f'pierde en {selected["losing_periods"]} y empata en {selected["tied_periods"]}. '
              f'Regla formal de preferencia retrospectiva: **{"cumple" if primary_preferred else "no cumple"}**.', '',
        'La regla exige mejora media de captura, al menos tres victorias temporales, IC95 positivo '
        'y un empeoramiento no mayor a 0.1 pp en error por grupo y grupo-mes. '
        'Se fijó antes del cálculo. El IC es condicional a modelos, cortes y asignaciones ya fijados; '
        'no incorpora el proceso completo de selección ni sustituye evidencia prospectiva. '
        'Son intervalos puntuales, sin corrección por comparaciones múltiples; los escenarios secundarios conservan carácter exploratorio.', '',
        'El error por grupo promedia el error absoluto de las tasas de cada grupo durante el periodo, ponderado por personas priorizadas. '
        'El error grupo-mes evalúa cada grupo en cada foto antes de promediar, evitando que meses con sobreestimación compensen meses con subestimación. '
        'R6 es probabilidad acumulada a seis meses. Todos los errores se expresan en puntos porcentuales. '
        'Comparar errores de agrupaciones distintas también cambia la granularidad: grupos grandes pueden suavizar errores. '
        'Por eso se incluye más adelante la comparación de B y C sobre exactamente la misma selección y los mismos cortes.', '',
        '![Comparación de captura](comparacion-captura.png)', '',
        '## Qué cambia al conservar los mismos cortes', '',
        'B cortes y C mismos cortes cruzan **antigüedad × salidas del equipo × nivel**. '
        'Los modelos estiman el riesgo y ordenan esos mismos segmentos en cada snapshot. '
        'Por tanto, pueden seleccionar personas distintas aun usando las mismas definiciones.', '']
    same_c = summary['C_Bcuts']
    lines += [f'C con los mismos cortes cambia la captura en {fmt(same_c["comparison"]["difference_vs_B_cuts_pp"])} pp frente a B. '
              f'Gana en {same_c["winning_periods"]} de cuatro periodos. '
              f'IC95 de diferencia [{fmt(same_c["comparison"]["ci95_pp"][0])}, {fmt(same_c["comparison"]["ci95_pp"][1])}] pp: '
              'la ventaja de captura no es concluyente al 30%. '
              f'El error grupo-mes pasa de {fmt(reference["metrics"]["group_snapshot_mae_pp"])} '
              f'a {fmt(same_c["metrics"]["group_snapshot_mae_pp"])} pp.', '',
              'También se conservó exactamente la población seleccionada por B y se cambió únicamente el estimador a C:', '',
              '| Estimador sobre la selección de B | Estimado R6 | Observado R6 | Error por grupo | Error grupo-mes |',
              '|---|---:|---:|---:|---:|']
    cross = [f['evaluation']['B_cuts']['same_selected_people_C_estimator'] for f in result['folds']]
    cross_mean = {k: np.mean([r[k] for r in cross]) for k in
                  ['predicted_percent', 'observed_percent', 'group_mae_pp', 'group_snapshot_mae_pp']}
    for name, metrics in [('B', reference['metrics']), ('C', cross_mean)]:
        lines.append(f'| {name} | {fmt(metrics["predicted_percent"], "%")} | {fmt(metrics["observed_percent"], "%")} | '
                     f'{fmt(metrics["group_mae_pp"], " pp")} | {fmt(metrics["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', '## Selección temporal de cortes para C', '',
        'Se restauraron cuatro modelos B y cuatro C. **Cero ajustes hazard**: sus coeficientes y calibración no cambiaron. '
        'Se reutilizaron los árboles de ocho hojas y se ajustaron árboles de hasta dieciséis hojas a las predicciones previas al periodo.', '',
        'Para cada periodo se probaron todos los cruces de dos y tres dimensiones disponibles entre las siete originales de B '
        'y las adicionales presentes en el C de ese corte temporal. No se exige que los cuatro C tengan los mismos términos. '
        'Se excluyen calendario, interacciones como dimensiones y dimensiones constantes en desarrollo.', '',
        '| Periodo evaluado: fotos | Desarrollo: fotos maduras | Último resultado conocido del desarrollo | Candidatos | Selección por prioridad | Selección por Gini |',
        '|---|---|---|---:|---|---|']
    for f in result['folds']:
        d = f['development']
        lines.append(f'| {f["first_snapshot"]} a {f["last_snapshot"]} | {d["first_snapshot"]} a {d["last_snapshot"]} | '
                     f'{d["latest_outcome"]} | {f["candidates_count"]} | {display(f["selection_priority"]["winner"]["name"])} | '
                     f'{display(f["selection_efficiency"]["winner"]["name"])} |')
    distinct_definitions = len({f['selection_priority']['winner']['name'] for f in result['folds']})
    lines += ['', f'La selección principal eligió **{distinct_definitions} definiciones distintas en cuatro orígenes**. '
              'El promedio evalúa la política de volver a seleccionar con datos anteriores a cada periodo. '
              'No demuestra que la última combinación, por sí sola, gane durante los cuatro periodos.']
    lines += ['', 'La selección usa las seis últimas fotos con seguimiento a seis meses terminado antes del origen externo. '
        'La evaluación utiliza las siguientes seis fotos. Las etiquetas de desarrollo participaron parcialmente en el ajuste del hazard: '
        'es desarrollo de agrupaciones, no validación independiente del modelo. Las salidas del periodo externo no escogen sus cortes.', '',
        'Selección por prioridad: mayor captura al 30%, tolerancia relativa de 2%; entre las candidatas cercanas, '
        'error grupo-mes a no más de 0.1 pp del mínimo; después menos dimensiones y menos grupos. '
        'Un árbol necesita mejorar captura más de 2% relativo sin empeorar ese error más de 0.1 pp. '
        'Selección Gini: diagnóstico que recupera el criterio histórico de conservar el ordenamiento completo, con parsimonia. '
        'No se cambia el criterio principal después de mirar estos resultados.', '',
        '## Comportamiento en cada periodo', '',
        '| Fotos | B cortes: captura | C mismos cortes: captura | C selección: captura | Diferencia C selección − B | B: error grupo-mes | C selección: error grupo-mes |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for f in result['folds']:
        ev = f['evaluation']
        b, c, s = [ev[k]['scenarios']['30']['metrics'] for k in ['B_cuts', 'C_Bcuts', 'C_selected']]
        lines.append(f'| {f["first_snapshot"]} a {f["last_snapshot"]} | {fmt(b["capture_percent"], "%")} | '
                     f'{fmt(c["capture_percent"], "%")} | {fmt(s["capture_percent"], "%")} | '
                     f'{fmt(s["capture_percent"]-b["capture_percent"], " pp")} | {fmt(b["group_snapshot_mae_pp"], " pp")} | '
                     f'{fmt(s["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', '## Sensibilidad a la capacidad', '',
        '| Capacidad | B cortes: captura | C mismos cortes: captura | C selección: captura | C Gini: captura | C selección cumple regla |',
        '|---|---:|---:|---:|---:|---|']
    for cap, entries in result['summary'].items():
        values = [fmt(entries[k]['metrics']['capture_percent'], '%') for k in ['B_cuts', 'C_Bcuts', 'C_selected', 'C_gini']]
        lines.append(f'| {cap}% | ' + ' | '.join(values) + f' | {"Sí" if entries["C_selected"]["meets_preference_rule"] else "No"} |')
    c40 = result['summary']['40']['C_Bcuts']
    ci40 = c40['comparison']['ci95_pp']
    lines += ['', '**Resultado favorable en el escenario secundario del 40%:** C con los mismos cortes de B '
              f'captura {fmt(c40["metrics"]["capture_percent"], "%")} frente a '
              f'{fmt(result["summary"]["40"]["B_cuts"]["metrics"]["capture_percent"], "%")}; '
              f'diferencia {fmt(c40["comparison"]["difference_vs_B_cuts_pp"])} pp, '
              f'IC95 [{fmt(ci40[0])}, {fmt(ci40[1])}]. Gana en {c40["winning_periods"]} periodos y '
              f'{"cumple" if c40["meets_preference_rule"] else "no cumple"} la regla de preferencia retrospectiva. '
              'Esta capacidad se declaró antes del cálculo; no sustituye al escenario principal del 30%.', '',
              '## Conservación del ordenamiento completo', '',
              'Eficiencia = Gini de concentración de salidas al ordenar grupos / Gini al ordenar personas por el mismo modelo. '
              'Se calcula por snapshot y después se promedia. El resto forma un bloque final para esta curva; '
              'permanece fuera de la prioridad. Una eficiencia menor en C no prueba peor captura que B: '
              'cada eficiencia usa el ranking individual de su propio modelo como denominador.', '',
              '| Agrupación | Eficiencia Gini | Resto | Peor error publicable, media por periodo |',
              '|---|---:|---:|---:|']
    for name in order:
        e = summary[name]
        lines.append(f'| {e["label"]} | {fmt(e["structure"]["efficiency_percent"], "%")} | '
                     f'{fmt(e["structure"]["rest_percent"], "%")} | '
                     f'{fmt(e["metrics"]["worst_publishable_group_error_pp"], " pp")} |')
    lines += ['', '## Grupos completos alrededor de la capacidad del 30%', '',
        'La comparación exacta al 30% asigna el mismo peso fraccional a las personas del grupo del límite, equivalente a '
        'selección aleatoria dentro del grupo. No utiliza un ranking individual para desempatar. '
        'Estas alternativas muestran decisiones sobre grupos completos, con capacidades distintas entre diseños:', '',
        '| Agrupación | Cobertura excluyendo límite | Captura excluyendo límite | Cobertura incluyendo límite | Captura incluyendo límite |',
        '|---|---:|---:|---:|---:|']
    for name in ['B_cuts', 'C_Bcuts', 'C_selected', 'C_gini']:
        a, b = [summary[name].get(mode, {}) for mode in ['whole_groups_excluding_boundary', 'whole_groups_including_boundary']]
        lines.append(f'| {summary[name]["label"]} | {fmt(a.get("coverage_percent"), "%")} | {fmt(a.get("capture_percent"), "%")} | '
                     f'{fmt(b.get("coverage_percent"), "%")} | {fmt(b.get("capture_percent"), "%")} |')
    ext = result['extension']
    lines += ['', '## Foto adicional madura de febrero de 2026', '',
        f'Foto {ext["snapshot"]}; seguimiento hasta {ext["followup_end"]}; {ext["people"]} personas. '
        f'Modelos y selección de {ext["model_origin"]}. No se añade como quinto periodo al promedio y no es un holdout virgen.', '',
        '| Agrupación | Grupos elegibles | Resto | Captura al 30% | Estimado | Observado | Error grupo-mes |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name in ['B_cuts', 'C_Bcuts', 'C_selected', 'C_gini', 'B_tree8', 'B_tree16', 'C_tree8', 'C_tree16']:
        e = ext['evaluation'][name]
        m, s = e['scenarios']['30']['metrics'], e['structure']
        lines.append(f'| {analysis.LABELS[name]} | {fmt(s["mean_eligible_groups"])} | {fmt(s["rest_percent"], "%")} | '
                     f'{fmt(m["capture_percent"], "%")} | {fmt(m["predicted_percent"], "%")} | {fmt(m["observed_percent"], "%")} | '
                     f'{fmt(m["group_snapshot_mae_pp"], " pp")} |')
    lines += ['', '### Grupos priorizados por la selección principal de C en esa foto', '',
        'Los nombres de nivel describen nivel profesional, no nivel de riesgo. Las bandas son las representaciones archivadas '
        'de C; comp ratio y capas organizativas conservan sus límites semánticos documentados.', '',
        '| Definición | Personas efectivas seleccionadas | Estimado R6 | Observado R6 | Error |',
        '|---|---:|---:|---:|---:|']
    groups = ext['evaluation']['C_selected']['scenarios']['30']['selected_groups']
    for g in sorted(groups, key=lambda x: -x.get('predicted_percent', 0)):
        if 'mean_selected_people_per_snapshot' not in g:
            continue
        lines.append(f'| {display(g["group"].replace("|", "/"))} | {fmt(g["mean_selected_people_per_snapshot"])} | '
                     f'{fmt(g["predicted_percent"], "%")} | {fmt(g.get("observed_percent"), "%")} | {fmt(g.get("error_pp"), " pp")} |')
    lines += ['', 'Observados suprimidos cuando no hay al menos 30 personas distintas con evento y 30 personas efectivas '
        'por foto seleccionada. Las personas efectivas pueden ser fraccionales por la política del límite. '
        'La elegibilidad del grupo completo exige al menos 300 personas en cada foto.', '',
        '## Lectura y límites', '',
        '- B árbol y B cortes tienen el mismo modelo hazard. Cambia la pérdida de información al resumir el riesgo en grupos; '
        'una representación no mejora automáticamente los coeficientes ni el pronóstico individual.',
        '- Los cruces de C conservan reglas de dos o tres dimensiones; los árboles usan hasta tres o cuatro condiciones por hoja. '
        'Más grupos no implican mayor utilidad. Importan captura, calibración, tamaño, persistencia y una intervención plausible.',
        '- Se prueban todos los cruces del espacio declarado, no todos los umbrales posibles ni todas las particiones posibles. '
        'La selección principal sigue el criterio de prioridad; Gini es una alternativa documentada.',
        '- La prioridad se ordena por riesgo medio predicho vigente en cada snapshot. La comparación previa de árboles ordenaba '
        'por el riesgo de entrenamiento congelado. No mezclar ambas tablas como si compartieran la política.',
        '- Se usa la receta de agrupación original de B sobre los B reconstruidos y el frame temporal corregido de C. '
        'Esto no reproduce las cifras históricas del deck. Los 22 grupos de julio de 2026 tampoco se imponen a otras fotos.',
        '- El análisis original de B escogió cortes usando el promedio de los mismos cuatro periodos publicados. Aquí C selecciona '
        'antes de cada periodo. B conserva una referencia ya favorecida por exploración histórica; la comparación es retrospectiva.',
        '- Sólo cuatro periodos y años explorados previamente. El bootstrap por persona conserva ventanas juntas, pero no demuestra '
        'estabilidad ante cambios económicos futuros ni incertidumbre del proceso de selección completo.',
        '- IOS usa fecha efectiva sin fecha de publicación confirmada; snapshots susceptibles a revisiones históricas. '
        'Capas y comp ratio son valores almacenados. No se reevaluaron scores ni se sustituyen sus contratos de entrada.',
        '- Otras salidas cuentan como no voluntarias; no se ajusta un modelo de riesgos competitivos. '
        'Los snapshots fiscales no siempre distan el mismo número de días.', '',
        '## Evidencia, conservación y tiempo', '',
        f'- Consulta guardada: `{result["query"]}`. Frontera de conocimiento: {result["knowledge_boundary"]}.',
        '- Evidencia: `results.json`, `folds/`, `development-candidates/`, `analysis-checks.json`, `preservation.json` y `manifest.json`.',
        '- Plan: `docs/plans/attrition-c-group-selection-20261008.md`. Configuración congelada: `frozen-config.json`.',
        '- Se reconciliaron población y métricas globales de los ocho modelos. Comprobaciones de capacidad por foto, '
        'captura directa frente a agregados, madurez temporal y conservación de artefactos.',
        f'- Cálculo: {fmt(result["elapsed_seconds"]/60)} minutos; carga: {fmt(result["load_seconds"]/60)} minutos. '
        'Cero reajustes hazard; ocho modelos restaurados. Informe construido sólo con agregados.',
        '- B, B+QVoice y C conservan sus artefactos. No se inició C+QVoice ni se promovió una especificación a producción.',
        '- No se guardaron filas, claves, riesgos individuales ni salarios exactos.', '']
    (OUT / 'informe.md').write_text('\n'.join(lines), encoding='utf-8')

    # Julia: comparación horizontal directa. Barras desde cero, referencias grises,
    # selección principal azul. Evitar recortar diferencias pequeñas; mostrar valores.
    chart_order = ['B_tree8', 'B_tree16', 'B_cuts', 'C_tree8', 'C_tree16', 'C_Bcuts', 'C_selected', 'C_gini']
    values = [summary[k]['metrics']['capture_percent'] for k in chart_order]
    labels = [summary[k]['label'] for k in chart_order]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(11.8, 6.7))
    colors = ['#2664b5' if k == 'C_selected' else '#698baf' if k == 'C_gini' else '#b2bac4' for k in chart_order]
    bars = ax.barh(labels, values, height=.65, color=colors)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.17)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, '%')))
    ax.set_xlabel('Porcentaje de salidas observadas capturadas al priorizar al 30%')
    for bar, val in zip(bars, values):
        ax.text(val + .6, bar.get_y() + bar.get_height()/2, fmt(val, '%'), va='center')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.grid(axis='x', color='#e4e7eb', linewidth=.7)
    ax.set_axisbelow(True)
    short = ('C con selección propia mejora la captura de B con cortes' if diff > 0 else
             'B con cortes captura más que la selección principal de C')
    if abs(diff) < .05:
        short = 'B y C con cortes propios muestran una captura media similar'
    fig.suptitle(short, x=.03, y=.98, ha='left', fontsize=17, weight='bold')
    fig.text(.03, .89, 'Engineering · salida voluntaria a seis meses · media de cuatro periodos\n'
             'Fotos de febrero de 2024 a enero de 2026; C elige cortes antes de cada periodo; B conserva los históricos.', fontsize=10)
    fig.text(.03, .02, 'Fuente: results.json y queries/profiles/engineering_model_c_person_month_20261008.sql · 8-oct-2026\n'
             'Población: Employee, Regular, activo, sin RF360. Prioridad fraccional en el grupo límite; evidencia retrospectiva.', fontsize=8.5)
    fig.subplots_adjust(left=.32, right=.96, top=.84, bottom=.16)
    fig.savefig(OUT / 'comparacion-captura.png', dpi=170, facecolor='white')
    fig.savefig(OUT / 'comparacion-captura.svg', facecolor='white')
    plt.close(fig)
    analysis.write(OUT / 'visual-review.json', {'method': 'morgan-vis', 'reporting_mode': 'presentation',
        'message': short, 'choice': 'Barras horizontales desde cero; etiquetas directas para diferencias pequeñas.',
        'alternatives': ['Puntos con eje recortado: exageran diferencias pequeñas.',
                         'Tabla sola: conserva detalle pero dificulta comparar ocho diseños.'],
        'limits': 'Evidencia retrospectiva; no causal; captura sobre persona-snapshot, capacidad igual.',
        'visible_number_maximum_decimals': 1})
    final = result['folds'][-1]
    analysis.write(OUT / 'selected-grouping.json', {
        'status': 'retrospective_experiment', 'model_hazard_unchanged': True,
        'model_reference': 'output/analysis/engineering/20261008/model-c-v2/folds/fold-4-C-model.json',
        'model_origin': final['origin'],
        'definition': final['evaluation']['C_selected']['definition'],
        'display_name': display(final['selection_priority']['winner']['name']),
        'minimum_group_people_each_snapshot': 300,
        'ranking': 'Riesgo medio predicho vigente por grupo en cada foto; resto fuera de prioridad.',
        'coarse_cut_implementation': 'source/tools/engineering_playbook_group_selection.py::coarse_keys',
        'additional_dimensions': 'Bandas almacenadas en el frame de C, sin cambiar sus umbrales.',
        'interpretation': 'Última selección evaluada; no es selección ganadora en los cuatro periodos ni promoción automática.',
        'qvoice_included': False})
    extra = analysis.base.read(OUT / 'additional-preservation-before.json')
    okay = all(analysis.base.sha(ROOT / p) == digest for p, digest in extra.items())
    if not okay:
        raise RuntimeError('Cambió un archivo adicional de B o B+QVoice.')
    analysis.write(OUT / 'additional-preservation-after.json', {'unchanged': True, 'checked_files': len(extra),
        'before': 'additional-preservation-before.json', 'files_before_after_sha256': extra})
    dest = OUT / 'source/tools' / Path(__file__).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), dest)
    manifest = analysis.base.read(OUT / 'manifest.json')
    manifest['status'] = 'completed_analysis_and_report'
    manifest['files'] = {str(p.relative_to(OUT)): analysis.base.sha(p) for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    analysis.write(OUT / 'manifest.json', manifest)
    print(headline)
    print('Informe y gráfico guardados; conservación de artefactos anteriores confirmada.')


if __name__ == '__main__':
    main()
