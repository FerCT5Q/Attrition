"""Informe de agregados de C/QVoice; no consulta datos individuales."""
from pathlib import Path
import json
import hashlib
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'output/analysis/engineering/20261009/c-qvoice-overlap-v1'
NAMES = {'C': 'C', 'CQ': 'C + Q archivado', 'overlap': 'Preguntas + promedio completo',
         'disjoint': 'Preguntas + promedio sin duplicación', 'items_only': 'Sólo preguntas',
         'selected': 'Selección interna ampliada', 'C_availability': 'Sólo disponibilidad QVoice'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fmt(x):
    if x is None:
        return 'No identificable'
    return f'{x:.1f}'.removesuffix('.0')


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main(out):
    result = read(out/'results.json')
    stats, decisions = result['summary'], result['decisions']
    names = ['C', 'CQ', 'overlap', 'disjoint', 'items_only', 'selected']
    verdict = decisions['CQ']
    conclusion = ('C + Q cumple la regla retrospectiva declarada.' if verdict['passes_comparable_checks'] else
        'C + Q mejora algunas métricas, pero no cumple la regla conjunta para sustituir a C.')
    lines = ['# C + QVoice: comparación con C y revisión del promedio', '',
        'Fecha de cálculo: '+result['date'][:10]+'. Modo: `presentation`.', '',
        '## Resultado de la revisión', '', '**'+conclusion+'**', '',
        'Esta ejecución cierra la comprobación con la evidencia disponible. No agrega periodos '
        'independientes ni acredita el desempeño futuro del modelo final de septiembre.', '',
        'Los C + Q históricos seleccionaron preguntas individuales y no incluyeron el promedio de 33. '
        'Por tanto, sus resultados frente a C no se explican por duplicar preguntas dentro de ese promedio. '
        'El solapamiento sí existe en los artefactos finales de C + Q y B + Q.', '',
        '### Conclusiones concretas', '',
        '- C + Q cumple siete de las ocho condiciones originales: mejora el promedio, pero '
        'gana en captura en un periodo y empata en el otro. Se conserva C como referencia.',
        '- Retirar las preguntas individuales del promedio conserva exactamente la captura '
        'de la versión con promedio completo al 20%, 30% y 40%. Las diferencias de log-loss '
        'y Brier entre ambas son pequeñas y sus intervalos incluyen cero.',
        '- En las respuestas completas del corte final, el VIF máximo de C + Q baja de 4.1 '
        'a 3.5 al quitar la duplicación; ambos están debajo del umbral descriptivo de 10. '
        'La matriz completa sí es singular por indicadores de ausencia compartidos. '
        'Eso limita la interpretación separada de coeficientes, aunque L2 permite el ajuste.',
        '- La selección interna mantiene CQ en ambos periodos históricos. En septiembre '
        'elige una media de 28 ítems, con una mejora interna menor a 0.1% relativo. Se '
        'archiva como experimento; no acredita una mejora externa del modelo final.', '',
        '## Población, fechas y lectura', '',
        'Engineering, Employee, Regular, activo y sin RF360 en cada snapshot. Salida voluntaria '
        'durante los seis meses siguientes. Fotos de agosto–diciembre de 2025 y enero–febrero de 2026, '
        'con seguimiento hasta agosto de 2026. Los periodos tienen igual peso; las personas y las '
        'ventanas se repiten. La unidad de evaluación es persona-snapshot.', '',
        'Priorizar 30% es el escenario principal. Se usa una fracción uniforme del grupo que cruza '
        'el límite; no supone que una fracción de empleado sea una acción operativa. Grupos de '
        'antigüedad × salidas previas del equipo × nivel, con al menos 300 personas por foto. '
        'Las tasas de grupos concretos sólo se publican con al menos 30 personas y 30 eventos distintos.', '',
        '## Captura y precisión en la misma población', '', '![Comparación](comparacion.png)', '',
        '| Modelo | Captura al 30% ↑ | Error grupo-mes ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |',
        '|---|---:|---:|---:|---:|']
    for name in names:
        row = stats[name]
        lines.append(f'| {NAMES[name]} | {fmt(row["scenarios"]["30"]["capture_percent"])}% | '
            f'{fmt(row["scenarios"]["30"]["group_snapshot_mae_pp"])} pp | '
            f'{fmt(row["global"]["log_loss"]*1000)} | {fmt(row["global"]["pr_auc"]*100)}% |')
    lines += ['', 'Captura = salidas observadas dentro de la prioridad / todas las salidas observadas. '
        'Error grupo-mes = diferencia absoluta entre tasa prevista y observada por grupo/foto, '
        'ponderada por la población priorizada. Log-loss mide la calidad de las probabilidades; '
        'PR-AUC mide discriminación. Menos error no garantiza más captura.', '',
        'Las tres nuevas representaciones conservan los términos del mejor candidato con promedio '
        'de la búsqueda interna de cada origen. Ese candidato puede diferir del C + Q archivado. '
        'La comparación entre representaciones mantiene sus otras preguntas; la selección ampliada '
        'elige por Brier interno, incluyendo la opción de conservar el C + Q original.', '',
        '### Comparación por periodo', '',
        '| Fotos | Personas distintas | Registros persona-foto | Variante | Captura al 30% | Error grupo-mes |',
        '|---|---:|---:|---|---:|---:|']
    for period in result['periods']:
        label = 'Ago–dic 2025' if period['id'] == 'aug_dec_2025' else 'Ene–feb 2026'
        for name in names:
            m = period['evaluation'][name]['scenarios']['30']['metrics']
            lines.append(f'| {label} | {period["people"]} | {period["exposures"]} | {NAMES[name]} | '
                f'{fmt(m["capture_percent"])}% | {fmt(m["group_snapshot_mae_pp"])} pp |')
    lines += ['', '### Incertidumbre de las diferencias', '',
        '| Comparación | Cambio captura al 30% | IC95 |', '|---|---:|---|']
    for row in result['intervals']:
        if row['metric'] != 'capture30' or row['left'] == 'overlap' and row['right'] == 'C':
            continue
        lines.append(f'| {NAMES[row["left"]]} − {NAMES[row["right"]]} | {fmt(row["difference"])} pp | '
                     f'[{fmt(row["ci95"][0])}, {fmt(row["ci95"][1])}] pp |')
    lines += ['', 'Bootstrap pareado de personas con 500 réplicas. Los intervalos son condicionales '
        'a modelos y selecciones; no corrigen comparaciones múltiples. Un intervalo favorable en '
        'el promedio no demuestra superioridad en cada periodo. Se recalcularon con semilla '
        '20261009 y llaves efímeras nuevas; sus extremos pueden variar respecto del bootstrap '
        'anterior de 500 réplicas. Las estimaciones puntuales y las métricas archivadas se reprodujeron.', '',
        '## Decisión sobre C + Q archivado', '',
        f'Gana en captura en {verdict["winning_periods"]} de {len(result["periods"])} periodos. '
        f'Cambio medio: {fmt(verdict["capture_difference_pp"])} pp.', '',
        '| Condición original | Resultado |', '|---|---|']
    criteria = {'capture_wins_both_periods': 'Mejor captura en ambos periodos',
        'capture_ci_lower_positive': 'Intervalo de mejora media positivo',
        'group_error': 'Error por grupo dentro de tolerancia +0.1 pp',
        'group_snapshot_error': 'Error grupo-mes dentro de tolerancia +0.1 pp',
        'log_loss': 'Log-loss dentro de tolerancia +0.5% relativo',
        'brier': 'Brier dentro de tolerancia +0.5% relativo',
        'incremental_capture_vs_availability': 'Más captura que disponibilidad de encuesta',
        'incremental_loss_vs_availability': 'Pérdida no mayor que disponibilidad de encuesta'}
    for k, passed in verdict['checks'].items():
        lines.append(f'| {criteria[k]} | {"Cumple" if passed else "No cumple"} |')
    lines += ['', 'Las nuevas representaciones son pruebas de sensibilidad. Sus reglas comparables '
        'se guardan en `verdict.json`; no se promueven automáticamente y no tienen un control de '
        'disponibilidad propio recalculado. El control original se conserva para C + Q.', '',
        '## Qué comprobamos del promedio', '',
        '**Pregunta:** ¿Las preguntas que ya tienen coeficiente propio añaden redundancia al promedio?', '',
        '**Motivo:** distinguir problemas de identificabilidad de una mejora o deterioro predictivo.', '',
        '**Método:** mapping de textos, recálculo de bandas, correlaciones y rango de la matriz '
        'indicadora. Se exige la misma disponibilidad de los 33 ítems para las dos medias. '
        'Se retienen los estados de no respuesta. La media usa indicadores favorables, no valores Likert.', '',
        '**Regla:** cero discrepancias de mapping, bandas y elegibilidad. |r| ≥ 0.8, VIF ≥ 10 y '
        'número de condición ≥ 30 son indicadores descriptivos de revisión, no reglas de promoción.', '',
        '| Origen | Ítems excluidos | Ítems restantes | Discrepancias |', '|---|---|---:|---:|']
    for p in sorted(out.rglob('qv_remaining_*-derivation.json')):
        item = read(p)
        lines.append(f'| {p.parent.name} | {", ".join(item["excluded_items"])} | {item["denominator"]} | {item["mismatch_count"]} |')
    lines += ['', '### Variables de los modelos finales: diagnóstico sobre muestra común', '',
        'Se usan las variables seleccionadas por los artefactos finales sobre la muestra mensual '
        'de C con etiquetas conocidas hasta 7-sep-2026. Para B + Q es un diagnóstico de sus '
        'variables en esa muestra común; su ajuste original sólo usó etiquetas hasta 28-jun-2026. '
        'Las columnas indicadoras y referencias se reconstruyen para cada muestra diagnóstica.', '',
        '| Modelo / muestra | Columnas variables | Rango | Condición | VIF máximo |', '|---|---:|---:|---|---|']
    for label, filename in [('C + Q', 'archived-CQ-collinearity.json'), ('B + Q', 'archived-BQ-collinearity.json')]:
        diag = read(out/'trained-model'/filename)
        for key, sample in [('all_rows', 'todas las filas'), ('complete_person_wave', 'respuestas completas persona-wave')]:
            d = diag[key]
            condition = fmt(d['condition_number']) if d['condition_status'] == 'finite' else 'Singular'
            lines.append(f'| {label}, {sample} | {d["columns"]} | {d["rank"]} | {condition} | {fmt(d["vif_max"])} |')
    lines += ['', 'Una matriz singular impide identificar por separado todos los coeficientes sin '
        'penalización. L2 permite ajustar predicciones, pero no convierte esos coeficientes en '
        'efectos independientes. Los diagnósticos de casos completos separan la asociación entre '
        'respuestas de los indicadores de ausencia compartidos. Las correlaciones y VIF completos '
        'están en los JSON; no son importancia causal.', '',
        '### Representaciones finales: matriz de casos completos', '',
        '| Representación | Columnas | Rango | Condición | VIF máximo |', '|---|---:|---:|---|---|']
    for name in ['overlap', 'disjoint', 'items_only']:
        d = read(out/'trained-model'/name/'collinearity.json')['complete_person_wave']
        condition = fmt(d['condition_number']) if d['condition_status'] == 'finite' else 'Singular'
        lines.append(f'| {NAMES[name]} | {d["columns"]} | {d["rank"]} | {condition} | {fmt(d["vif_max"])} |')
    lines += ['', '**Impacto en scores:** ninguno. Es una validación del modelo y de la derivación '
        'experimental; no actualiza el assessment de las fuentes.', '',
        '## Sensibilidad a cuatro cortes', '',
        'Se añade adquisición registrada a los tres cortes comunes, con igual partición para C '
        'y todas las variantes. Son resultados separados; no se combinan sus errores con los de '
        'tres cortes ni se cambia la comparación principal.', '',
        '| Variante | Captura al 30% | Error grupo-mes |', '|---|---:|---:|']
    for name in names:
        m = result['four_cuts_summary'][name]['scenarios']['30']
        lines.append(f'| {NAMES[name]} | {fmt(m["capture_percent"])}% | {fmt(m["group_snapshot_mae_pp"])} pp |')
    lines += ['', '## Decisión y límites de aplicación', '',
        'Mantener C como referencia si C + Q no satisface la regla conjunta. Conservar las '
        'representaciones probadas como evidencia; una mejora interna no equivale a mejora externa.', '',
        f'La selección interna del corte 7-sep-2026 elige **{NAMES[result["final_selected_representation"]]}**. '
        'Sus parámetros están en `trained-model/selected-model.json`. No tiene evaluación posterior '
        'al ajuste. C conserva su base de agosto de 2025; no se realizó un refit del hazard.', '',
        'Para reconsiderar la sustitución, aplicar el modelo congelado a fotos posteriores a su '
        'ajuste, observar seis meses completos y repetir captura y precisión por grupo con '
        'población y capacidad comparables. Esta ejecución no genera esos resultados futuros.', '',
        '- El experimento de representaciones condiciona el subconjunto a la búsqueda original; '
        'no agota todas las combinaciones nuevas.',
        '- El promedio sin duplicación puede seguir correlacionado con las preguntas por '
        'actitudes compartidas. Quitar componentes comunes no asegura independencia.',
        '- La media de errores puede ocultar grupos altos mal estimados. Las tablas de grupos '
        'publicables y el mayor error están en `folds/*/evaluation.json`.',
        '- La política anual y los límites de redacción de Career se heredan de CQ. La fecha '
        'asignada por política no demuestra la fecha real de publicación de una encuesta.',
        '- Esta revisión no prueba causalidad ni cuántas salidas evitaría una intervención.', '',
        '## Reproducción, preservación y fuentes', '',
        f'- SQL: `{result["source_query"]}`; fecha: {result["date"][:10]}; corte 7-sep-2026.',
        '- Plan: `docs/plans/attrition-c-qvoice-overlap-20261009.md`.',
        '- Fuentes y parámetros anteriores: hashes en `preservation-before.json`; resultado en `preservation.json`.',
        '- Reconciliaciones de población y métricas: `analysis-checks.json`, `folds/*/reconciliation.json`.',
        '- Resultados: `results.json`, `verdict.json`, diagnósticos y derivaciones por origen.',
        f'- {result["representation_fit_count"]} ajustes de correcciones; {result["base_refits"]} reajustes C. '
        f'Tiempo del proceso completado: {fmt(result["elapsed_seconds"]/60)} minutos; no incluye reintentos anteriores.',
        '- Autorización RAM: `'+result['authorization']+'`. No se guardan filas, respuestas, llaves '
        'ni predicciones individuales. Se preservan los modelos anteriores.', '']
    (out/'informe.md').write_text('\n'.join(lines), encoding='utf-8')
    selected_names = ['C', 'CQ', 'overlap', 'disjoint', 'items_only']
    y = np.arange(len(selected_names))
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.4), gridspec_kw={'width_ratios': [1.2, 1]})
    colors = ['#7f8790', '#0078a0', '#7f8790', '#7f8790', '#7f8790']
    for ax, field, title in zip(axes, ['capture_percent', 'group_snapshot_mae_pp'],
                               ['Salidas capturadas al priorizar 30% (%)', 'Error por grupo y mes (pp)']):
        values = [stats[n]['scenarios']['30'][field] for n in selected_names]
        ax.barh(y, values, color=colors, height=.6)
        ax.set_yticks(y, [NAMES[n] for n in selected_names] if ax is axes[0] else ['']*len(y))
        ax.invert_yaxis()
        ax.set_xlim(0, max(values)*1.2)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt(v)))
        ax.set_title(title, loc='left', fontsize=11)
        for pos, value in zip(y, values):
            ax.text(value+max(values)*.025, pos, fmt(value), va='center', fontsize=10)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
    fig.suptitle('La revisión del promedio no desplaza al C + Q archivado', x=.03, ha='left', fontsize=14)
    fig.text(.03, .88, 'Engineering · fotos ago–dic 2025 y ene–feb 2026 · seguimiento de seis meses · igual peso por periodo', fontsize=9)
    fig.text(.03, .025, 'Fuente: results.json · '+result['date'][:10]+' · Consulta y población en informe.md. Evidencia retrospectiva; C permanece congelado.', fontsize=8)
    fig.tight_layout(rect=(.015, .06, .99, .86))
    fig.savefig(out/'comparacion.png', dpi=170, bbox_inches='tight')
    plt.close(fig)
    write(out/'visual-review.json', {'audience': 'Responsable del modelo de attrition',
        'decision': 'Mantener C o continuar la extensión QVoice según captura y precisión.',
        'chart': 'Barras horizontales con base cero; dos paneles con escalas propias declaradas.',
        'alternative': 'Descartado un eje doble: dificulta comparar porcentajes y puntos porcentuales.',
        'numbers_source': 'results.json', 'language': 'es', 'maximum_decimals': 1,
        'limitations': ['Periodos retrospectivos', 'Selección del subconjunto condicionada', 'Modelo final sin validación posterior']})
    print('Informe y gráfico agregados generados.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT)
    main(parser.parse_args().output)
