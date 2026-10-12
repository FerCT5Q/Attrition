"""Revisión reproducible del informe agregado, sin consultar ni reajustar modelos."""
from pathlib import Path
import json
import shutil

from qvoice_horizon_calibration import render_report
from qvoice_model_data import ROOT, sha256_file, write_json, utc_now


def build(root):
    result = json.loads((root/'comparison-results.json').read_text(encoding='utf-8'))
    destination = root/'informe.md'
    render_report(result, destination)
    report = destination.read_text(encoding='utf-8')
    # Evitar que una diferencia pequeña positiva se presente como cero exacto.
    for row in result['periods']:
        for metrics in row['metrics'].values():
            if 0 < metrics['top_quintile_calibration_error_pp'] < .05:
                report = report.replace('| 0 |', '| <0.1 |')
    labels = {'aug_dec_2025': 'Ago–dic 2025', 'jan_feb_2026': 'Ene–feb 2026', 'final': 'Artefacto final'}
    lines = []
    for c in result['calibration_details']:
        status = 'sin ajuste por historia insuficiente' if c['status'] != 'fitted' else 'ajuste estimado'
        change = 100*(c['multiplier']-1)
        text = f'{change:+.1f}%'.replace('+0.0%', '0%')
        lines.append(f'- **{labels[c["target"]]}**, corte {c["cutoff"]}: {status}; '
                     f'{len(c["origins"])} orígenes; cambio del hazard acumulado: {text}. '
                     f'Orígenes: {", ".join(c["origins"]) or "ninguno admisible"}.')
    begin = report.index('- **aug_dec_2025**')
    end = report.index('\n\nCada ajuste auxiliar', begin)
    report = report[:begin]+'\n'.join(lines)+report[end:]
    p = next(r for r in result['periods'] if r['period'] == 'jan_feb_2026')
    change = 100*(p['calibration']['multiplier']-1)
    relative = 100*(p['metrics']['scalar']['log_loss']/p['metrics']['uncalibrated']['log_loss']-1)
    ci = next(r['ci95'] for r in p['paired_loss_intervals'] if r['left'] == 'scalar' and r['metric'] == 'log_loss')
    explanation = (f'## Por qué el ajuste empeoró este periodo\n\n'
        f'Las predicciones históricas de abril–junio de 2025 llevaron a reducir el hazard '
        f'acumulado en {abs(change):.1f}%. En enero–febrero de 2026, el modelo sin corrección '
        f'ya subestimaba el riesgo medio. Aplicar esa reducción lo alejó más del resultado real. '
        f'La corrección sí mejoró el objetivo en la historia usada para aprenderla, pero ese '
        f'ajuste no se trasladó bien a este periodo posterior. No se demuestra que el cambio '
        f'de wave sea la causa.\n\n'
        f'Frente a no corregir, el log-loss subió {relative:.1f}%. La diferencia absoluta '
        f'fue positiva también en el bootstrap por persona: IC del 95% de '
        f'{ci[0]*1000:.1f} a {ci[1]*1000:.1f} unidades de log-loss × 1000. '
        f'Este intervalo está condicionado a los modelos y a los meses observados.\n\n'
        '## Ganancia de QVoice frente a B\n\n')
    for row in result['periods']:
        m, b = row['metrics']['uncalibrated'], row['metrics']['control']
        explanation += (f'- {labels[row["period"]]}: log-loss menor en '
            f'{100*(1-m["log_loss"]/b["log_loss"]):.1f}% y Brier menor en '
            f'{100*(1-m["brier_score"]/b["brier_score"]):.1f}%.\n')
    explanation += ('\nLa reducción de pérdida es modesta; la mejora relativa de PR-AUC es mayor. '
        'B conserva menor error de calibración general en ambos periodos, por lo que '
        'B + QVoice sin corrección sigue siendo un candidato y no un reemplazo aprobado.\n\n')
    report = report.replace('## Rendimiento\n', explanation+'## Rendimiento\n')
    destination.write_text(report, encoding='utf-8')
    review = {'created_at': utc_now(), 'reporting_mode': 'presentation',
        'audience_and_decision': 'Usuario del proyecto; decidir si conservar el ajuste de calibración y reducir tiempo de ejecución.',
        'main_message': result['recommendation'],
        'visual_choice': 'Tabla breve de las cuatro variantes para comparación exacta; no se añade gráfico redundante.',
        'checks': ['Misma población y denominadores en cada periodo.',
                   'Riesgo explícito a seis meses, no tasa mensual.',
                   'Diferencias positivas menores de 0.05 pp visibles como <0.1 pp.',
                   'Conservar límites por historia, selección previa y ventanas solapadas.',
                   'Separar menos ajustes de aceleración medida en la misma tarea.'],
        'script_sha256': sha256_file(Path(__file__)), 'report_sha256': sha256_file(destination)}
    write_json(root/'report-review.json', review)
    shutil.copy2(Path(__file__), root/'inputs'/Path(__file__).name)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    manifest['report_review'] = 'report-review.json'
    manifest['artifacts_sha256'] = {str(p.relative_to(root)).replace('\\', '/'): sha256_file(p)
                                  for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    write_json(root/'manifest.json', manifest)
    print(f'Informe revisado: {destination.relative_to(ROOT)}')


if __name__ == '__main__':
    build(ROOT/'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1')
