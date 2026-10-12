"""Tabla y reporte de selección para la combinación QVoice fija con promedio 28."""
from pathlib import Path
import json
import csv
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'output/analysis/engineering/20261009/c-qvoice-mean28-v1'
NAMES = {'C': 'C', 'CQ': 'C + Q evaluado', 'overlap': 'C + Q fijo + promedio 33',
    'disjoint': 'C + Q fijo + promedio 28', 'items_only': 'C + Q fijo sin promedio',
    'mean28_availability': 'C + disponibilidad de Q fijo', 'C_availability': 'C + disponibilidad de Q evaluado',
    'selected': 'Selección interna entre alternativas'}
ORDER = ['C', 'CQ', 'overlap', 'disjoint', 'items_only']


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fmt(value):
    if value is None:
        return '—'
    formatted = f'{value:.1f}'.removesuffix('.0')
    return '0' if formatted == '-0' else formatted


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main(out):
    data = read(out/'results.json')
    stats = data['summary']
    decisions = read(out/'selection-decision.json') if (out/'selection-decision.json').exists() else None
    base_error = stats['C']['scenarios']['30']['group_snapshot_mae_pp']
    table = ['| Modelo | Captura al 30% ↑ | Error grupo-mes ↓ | Cambio de error vs C ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |',
             '|---|---:|---:|---:|---:|---:|']
    rows = []
    for name in ORDER:
        s, g = stats[name]['scenarios']['30'], stats[name]['global']
        error_change = 100*(s['group_snapshot_mae_pp']/base_error-1)
        table.append(f'| {NAMES[name]} | {fmt(s["capture_percent"])}% | {fmt(s["group_snapshot_mae_pp"])} pp | '
                     f'{fmt(error_change)}% | '
                     f'{fmt(g["log_loss"]*1000)} | {fmt(g["pr_auc"]*100)}% |')
        rows.append({'modelo': NAMES[name], 'captura_30_porcentaje': s['capture_percent'],
            'error_grupo_mes_pp': s['group_snapshot_mae_pp'], 'error_grupo_pp': s['group_mae_pp'],
            'log_loss_por_1000': g['log_loss']*1000, 'brier_por_1000': g['brier_score']*1000,
            'pr_auc_porcentaje': g['pr_auc']*100, 'cambio_error_vs_C_porcentaje': error_change})
    with (out/'tabla-comparativa.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out/'tabla-comparativa.md').write_text('# Selección de modelo: tabla actualizada\n\n'+
        'Engineering; fotos ago–dic 2025 y ene–feb 2026, seguimiento de seis meses. '
        'Igual peso por periodo. Evaluación retrospectiva.\n\n'+'\n'.join(table)+'\n', encoding='utf-8')
    lines = ['# C + Q con promedio de 28: evaluación de la combinación concreta', '',
        f'Fecha de cálculo: {data["date"][:10]}. Modo `presentation`. Etapa: **selección de modelo**.', '',
        '## Qué se evaluó', '',
        'Se entrenó en cada origen la misma combinación: **Career Goals + Wellbeing '
        '(Q8/Q10/Q11) + Confidence (Q13/Q17) + promedio de 28 preguntas**. Los coeficientes '
        'y L2 se aprendieron sólo con datos anteriores a cada periodo externo.', '',
        'Esto difiere de la prueba anterior, cuyos subconjuntos cambiaron entre periodos. '
        'La definición fija corresponde al candidato elegido en septiembre, después de '
        'explorar el histórico; por ello esta evaluación es retrospectiva y condicionada a '
        'esa elección. No es una validación prospectiva independiente de toda la selección.', '',
        '## Tabla actualizada', '', '![Comparación](comparacion.png)', '']+table
    lines += ['', 'Captura: proporción de salidas observadas dentro del 30% priorizado. Error grupo-mes: '
        'distancia absoluta entre tasa prevista y observada por grupo/foto, ponderada por población '
        'priorizada. Log-loss y Brier evalúan probabilidades; PR-AUC evalúa discriminación. '
        'El cambio relativo de error permite distinguir diferencias que desaparecen al '
        'redondear los puntos porcentuales. Un cambio negativo representa menor error.', '',
        '“Q evaluado” conserva los modelos históricos elegidos anteriormente. “Q fijo” usa '
        'las seis mismas preguntas en ambas ventanas. Comparar media 28 frente a 33 o sin '
        'media aísla el cambio de representación; frente a Q evaluado también cambia el conjunto '
        'de preguntas. Todos usan los mismos coeficientes base C y la misma agrupación.', '',
        '## Resultado por periodo', '',
        '| Fotos | Variante | Personas distintas | Captura al 30% | Error grupo-mes |',
        '|---|---|---:|---:|---:|']
    for period in data['periods']:
        label = 'Ago–dic 2025' if period['id'] == 'aug_dec_2025' else 'Ene–feb 2026'
        for name in ORDER:
            s = period['evaluation'][name]['scenarios']['30']['metrics']
            lines.append(f'| {label} | {NAMES[name]} | {period["people"]} | {fmt(s["capture_percent"])}% | '
                         f'{fmt(s["group_snapshot_mae_pp"])} pp |')
    lines += ['', '### Probabilidades sobre la misma prioridad elegida por C', '',
        'Se mantiene exactamente la población priorizada por C y sólo cambia el estimador. '
        'Esto ayuda a separar la precisión de probabilidades del cambio de grupos seleccionados.', '',
        '| Modelo | Riesgo observado | Riesgo estimado | Sesgo estimado − observado | Error grupo-mes |',
        '|---|---:|---:|---:|---:|']
    for name in ORDER:
        rows_c = [p['evaluation'][name]['on_C_selection'] for p in data['periods']]
        means = {k: np.mean([r[k] for r in rows_c]) for k in ['observed_percent', 'predicted_percent', 'group_snapshot_mae_pp']}
        lines.append(f'| {NAMES[name]} | {fmt(means["observed_percent"])}% | {fmt(means["predicted_percent"])}% | '
            f'{fmt(means["predicted_percent"]-means["observed_percent"])} pp | {fmt(means["group_snapshot_mae_pp"])} pp |')
    lines += ['', '## Incertidumbre de la captura', '',
        '| Comparación | Cambio medio al 30% | IC95 |', '|---|---:|---|']
    for interval in data['intervals']:
        if interval['metric'] != 'capture30' or interval['left'] != 'disjoint':
            continue
        lines.append(f'| Media 28 − {NAMES[interval["right"]]} | {fmt(interval["difference"])} pp | '
            f'[{fmt(interval["ci95"][0])}, {fmt(interval["ci95"][1])}] pp |')
    lines += ['', '### Incertidumbre de las probabilidades', '',
        '| Media 28 frente a | Cambio log-loss × 10000 ↓ | IC95 | Cambio Brier × 100000 ↓ | IC95 |',
        '|---|---:|---|---:|---|']
    for name in ['C', 'CQ', 'overlap', 'items_only']:
        pair = {r['metric']: r for r in data['intervals'] if r['left'] == 'disjoint' and r['right'] == name}
        cells = []
        for metric in ['log_loss', 'brier_score']:
            r = pair[metric]
            scale = 10000 if metric == 'log_loss' else 100000
            cells += [fmt(scale*r['difference']), f'[{fmt(scale*r["ci95"][0])}, {fmt(scale*r["ci95"][1])}]']
        lines.append('| '+NAMES[name]+' | '+' | '.join(cells)+' |')
    lines += ['', '500 remuestreos pareados de personas, igual peso por periodo. Intervalos '
        'condicionales a parámetros, configuración y prioridades, sin corrección por múltiples '
        'comparaciones. Las ventanas y personas se comparten; los dos periodos no son '
        'experimentos independientes. Los extremos pueden variar respecto de bootstraps anteriores. '
        'Un intervalo de captura [0, 0] refleja aportaciones iguales de las salidas observadas '
        'dentro de esta prioridad fija; no demuestra equivalencia universal.', '',
        '## Selección de modelo', '']
    if decisions:
        lines += [decisions['conclusion'], '', *['- '+s for s in decisions['reasons']], '']
    else:
        lines += ['La recomendación se registra tras revisar las métricas y sus límites.', '']
    lines += ['La regla estricta anterior se conserva como diagnóstico, separada de la '
        'decisión práctica de selección. No se suman métricas correlacionadas como si fueran '
        'votos independientes. Ningún resultado implica un piloto o despliegue.', '',
        '| Media 28 frente a | Victorias en captura | Empates | Derrotas |', '|---|---:|---:|---:|']
    for name in ['C', 'CQ']:
        c = data['comparison_mean28'][name]
        lines.append(f'| {NAMES[name]} | {c["wins"]} | {c["ties"]} | {c["losses"]} |')
    lines += ['', '## Población, grupos y derivación', '',
        '- Población: Engineering, Employee, Regular, activo, sin RF360 por snapshot.',
        '- Outcome: salida voluntaria en los seis meses siguientes a cada foto. Fotos de '
        'agosto–diciembre de 2025 y enero–febrero de 2026; seguimiento hasta agosto de 2026.',
        '- Grupos: antigüedad × salidas previas del equipo × nivel. Mínimo 300 personas por '
        'foto; tasas concretas sólo con 30 personas y 30 eventos distintos. El grupo del '
        'límite del 30% recibe peso uniforme fraccional.',
        '- Promedio 28: suma de indicadores favorables restantes / 28, en las seis bandas '
        'del playbook. Excluye Q8, Q10, Q11, Q13 y Q17 del promedio original de 33. Career '
        'no está entre los 33. Se exige validez de los 33 originales para conservar elegibilidad.',
        '- Mapping por texto, no por posición supuesta. Se conserva la política de encuesta '
        '2024 para 2025 y 2025 para 2026, con continuidad del episodio laboral.',
        '- Controles: media de 33, mismas preguntas sin media y disponibilidad de las '
        'preguntas de la variante media 28. L2 en {0.1, 1, 10}; mismos intervalos internos.', '',
        '### Sensibilidades de capacidad', '',
        '| Variante | Captura al 20% | Captura al 30% | Captura al 40% |', '|---|---:|---:|---:|']
    for name in ORDER:
        s = stats[name]['scenarios']
        lines.append('| '+NAMES[name]+' | '+' | '.join(fmt(s[cap]['capture_percent'])+'%' for cap in ['20', '30', '40'])+' |')
    lines += ['', '### Sensibilidad de agrupación: añadir adquisición registrada', '',
        '| Variante | Captura al 30% | Error grupo-mes |', '|---|---:|---:|']
    for name in ORDER:
        s = data['four_cuts_summary'][name]['scenarios']['30']
        lines.append(f'| {NAMES[name]} | {fmt(s["capture_percent"])}% | {fmt(s["group_snapshot_mae_pp"])} pp |')
    lines += ['', 'Las particiones son iguales entre modelos dentro de cada tabla. No se mezclan '
        'errores de particiones con distinta granularidad. La adquisición registrada describe '
        'el dato almacenado; “sin registro” no prueba ausencia de adquisición.', '',
        '## Colinealidad en las mismas preguntas fijas', '',
        '| Corte de ajuste | Variante | VIF máximo, casos completos | Número de condición | Rango / columnas, matriz completa |',
        '|---|---|---:|---:|---|']
    for period in data['periods']:
        for name in ['overlap', 'disjoint', 'items_only']:
            diagnostic = read(out/'folds'/period['id']/name/'collinearity.json')
            complete, full = diagnostic['complete_person_wave'], diagnostic['all_rows']
            lines.append(f'| {period["origin"]} | {NAMES[name]} | {fmt(complete["vif_max"])} | '
                f'{fmt(complete["condition_number"])} | {full["rank"]} / {full["columns"]} |')
    lines += ['', 'Los casos completos usan personas-encuesta distintas. VIF y condición describen '
        'las columnas QVoice, no toda la matriz conjunta con C ni efectos causales. Retirar '
        'preguntas del promedio elimina ese solapamiento aritmético, pero las preguntas aún '
        'pueden estar correlacionadas. Los estados compartidos de ausencia generan redundancias '
        'exactas en la matriz completa; L2 permite el ajuste, sin volver identificables sus '
        'efectos separados al quitar la penalización.', '',
        '## Artefacto final y límites', '',
        'El archivo `trained-model/model-mean28.json` es una copia exacta del modelo final '
        'del 7-sep-2026. Su estructura ahora tiene esta evaluación retrospectiva, con '
        'coeficientes históricos separados. Los coeficientes finales de septiembre todavía '
        'no tienen evaluación posterior a su ajuste. C base conserva origen 1-ago-2025.', '',
        'La selección de seis preguntas fue posterior a la exploración del histórico. '
        'El resultado permite comparar candidatos en esta etapa; no demuestra generalización '
        'a periodos aún no observados ni el efecto causal de acciones de retención. La '
        'disponibilidad real de encuestas y la redacción de Career mantienen sus límites previos.', '',
        '## Reproducción y comprobaciones', '',
        '- Plan: `docs/plans/attrition-c-qvoice-mean28-20261009.md`.',
        '- Consulta: `'+data['source_query']+'`, ejecutada el '+data['date'][:10]+' con corte 7-sep-2026.',
        '- Resultados: `results.json`, `tabla-comparativa.csv`, `folds/*/evaluation.json`.',
        '- Reproducción de C/CQ: `folds/*/reconciliation.json`. Derivación: `folds/*/*-derivation.json`.',
        '- Preservación: `preservation.json`; verificación y hashes: `verification.json` y `manifest.json`.',
        f'- {data["fit_count"]} ajustes de correcciones, cero reajustes C y cero reajustes del final '
        f'de septiembre. Proceso completado en {fmt(data["elapsed_seconds"]/60)} minutos.',
        '- Autorización: `'+data['authorization']+'`. Filas, respuestas y llaves sólo en RAM; '
        'se guardan parámetros y agregados. No se modifican modelos previos ni scores.', '']
    (out/'informe.md').write_text('\n'.join(lines), encoding='utf-8')
    fig, (ax, error_ax) = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True,
                                     gridspec_kw={'width_ratios': [1.2, 1]})
    y = np.arange(len(ORDER))
    values = [stats[name]['scenarios']['30']['capture_percent'] for name in ORDER]
    colors = ['#858d95', '#007b9f', '#858d95', '#bc6920', '#858d95']
    ax.barh(y, values, height=.6, color=colors)
    ax.set_yticks(y, [NAMES[n] for n in ORDER])
    ax.invert_yaxis()
    ax.set_xlim(0, max(values)*1.15)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt(v)))
    ax.set_xlabel('Salidas capturadas al priorizar 30% (%)')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    for pos, value in zip(y, values):
        ax.text(value+.3, pos, fmt(value)+'%', va='center')
    error_changes = [100*(stats[n]['scenarios']['30']['group_snapshot_mae_pp']/base_error-1) for n in ORDER]
    error_ax.axvline(0, color='#c1c6ca', linewidth=1)
    error_ax.scatter(error_changes, y, c=colors, s=70)
    error_ax.set_xlim(-4, 6)
    error_ax.set_xticks([-4, -2, 0, 2, 4, 6])
    error_ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt(v)))
    error_ax.set_xlabel('Cambio de error grupo-mes vs C (%)\nMenor es mejor')
    error_ax.spines[['top', 'right', 'left']].set_visible(False)
    error_ax.tick_params(axis='y', left=False, labelleft=False)
    for pos, value in zip(y, error_changes):
        error_ax.text(value+.25, pos, fmt(value)+'%', va='center')
    title = decisions['chart_title'] if decisions else 'Comparamos la misma combinación QVoice con promedio de 28'
    fig.suptitle(title, x=.02, ha='left', fontsize=13)
    fig.text(.02, .89, 'Engineering · ago–dic 2025 y ene–feb 2026 · seguimiento de seis meses · evaluación retrospectiva', fontsize=9)
    fig.text(.02, .025, 'Fuente: results.json · '+data['date'][:10]+' · Población, consulta y límites en informe.md. Igual peso por periodo.', fontsize=8)
    fig.tight_layout(rect=(.01, .06, .99, .88))
    fig.savefig(out/'comparacion.png', dpi=170, bbox_inches='tight')
    plt.close(fig)
    write(out/'visual-review.json', {'mode': 'presentation', 'audience': 'Responsable de selección de modelo',
        'chart': 'Barras de captura desde cero y panel de puntos para cambio relativo del error; misma población y horizonte.',
        'alternative_rejected': 'Eje doble para error y captura: mezcla unidades y dificulta lectura.',
        'figures_source': 'results.json', 'maximum_decimals': 1,
        'limitations': ['Configuración elegida tras explorar el histórico', 'No es piloto ni validación prospectiva']})
    print('Tabla comparativa, informe y gráfico actualizados.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT)
    main(parser.parse_args().output)
