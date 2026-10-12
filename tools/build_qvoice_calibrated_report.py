"""Informe y figuras en español desde los resultados agregados del modelo nuevo."""
from pathlib import Path
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from qvoice_model_data import write_json, sha256_file, utc_now

NAMES={'control':'B de referencia','base_calibrated':'B con calibración comparable','availability':'B + disponibilidad calibrado','uncalibrated':'B + QVoice sin calibrar','response':'B + QVoice calibrado'}
PERIODS={'aug_dec_2025':'Agosto–diciembre de 2025','jan_feb_2026':'Enero–febrero de 2026'}
BLOCK_NAMES={'q4':'Q4: permanencia futura','q12':'Q12: rara vez piensa buscar otro empleo',
             'career':'Career: metas de carrera','mean33':'Promedio de 33 preguntas',
             'engagement':'Engagement (Q1, Q2, Q3)','connection':'Connection (Q5, Q7)',
             'wellbeing':'Wellbeing (Q8, Q10, Q11)','confidence':'Confidence (Q13, Q17)'}


def selected_name(selected):
    if selected['kind']=='pca':
        return f'PCA con {selected["components"]} componentes'
    return ' + '.join(BLOCK_NAMES[b] for b in selected['blocks'])

def fmt(value):
    if abs(value)<0.05 and value!=0:
        return '<0.1' if value>0 else '>−0.1'
    return f'{value:,.1f}'.rstrip('0').rstrip('.')

def build(root, figure_only=False):
    results=json.loads((root/'comparison-results.json').read_text(encoding='utf-8'))
    periods=results['periods']
    ranking=results['decision']['checks']['ranking_vs_control']
    brier=results['decision']['checks']['brier_score_vs_control']
    if results['decision']['status']=='prometedora' and all(results['matched_calibration_checks'].values()):
        headline='QVoice mejora la comparación retrospectiva con B'
    elif ranking and brier:
        headline='QVoice mejora el ranking; la calibración limita el resultado'
    elif ranking:
        headline='QVoice mejora el ranking, pero no cumple el criterio conjunto'
    else:
        headline='B + QVoice no supera de forma consistente a B'
    charts=root/'charts'
    charts.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(15,4.8))
    metrics=[('pr_auc',100,'Cambio de PR-AUC (pp)\nMayor es mejor'),('brier_score',10000,'Cambio de Brier × 10,000\nMenor es mejor'),('calibration_error_pp',100,'Cambio de error de calibración (pb)\nMenor es mejor')]
    for ax,(metric,scale,label) in zip(axes,metrics):
        for i,p in enumerate(periods):
            delta=scale*(p['response'][metric]-p['control'][metric])
            interval=p['uncertainty']['paired_differences']['response__minus__control'][metric]
            lo,hi=scale*interval['lower'],scale*interval['upper']
            ax.plot([lo,hi],[i,i],color='#316395',lw=2)
            ax.scatter([delta],[i],s=45,color='#173a63',zorder=4)
        ax.axvline(0,color='#999',linestyle='--',lw=1)
        ax.set_yticks([0,1],['Ago–dic 2025','Ene–feb 2026'])
        ax.set_ylim(1.7,-.7)
        ax.set_xlabel(label)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:fmt(x)))
        ax.spines[['top','right','left']].set_visible(False)
        ax.tick_params(axis='y',length=0)
    fig.suptitle(headline,fontsize=15,x=.03,ha='left')
    counts='; '.join(f'{"Ago–dic 2025" if p["period"]=="aug_dec_2025" else "Ene–feb 2026"}: {p["people"]:,} personas / {int(p["control"]["exposures"]):,} observaciones persona-snapshot' for p in periods)
    fig.text(.03,.02,'Engineering regular sin RF360 · Salida voluntaria en seis meses · Diferencia: B + QVoice calibrado menos B de referencia\n'+counts+'\nIntervalos bootstrap de 95% por persona, condicionados al modelo · Evaluación retrospectiva\nFuente: comparison-results.json · Corte 7-sep-2026 · Ejecución 8-oct-2026 · presentation',fontsize=8.5)
    fig.subplots_adjust(left=.08,right=.99,bottom=.32,top=.8,wspace=.45)
    fig.savefig(charts/'comparacion-con-b.png',dpi=180)
    plt.close(fig)
    if figure_only:
        print(charts/'comparacion-con-b.png')
        return
    model=json.loads((root/'trained-model/model.json').read_text(encoding='utf-8'))
    stages=[(PERIODS[p['period']],root/'folds'/p['period']) for p in periods]
    stages.append(('Artefacto al 7-sep-2026',root/'trained-model'))
    searches=[(name,json.loads((directory/'selection.json').read_text(encoding='utf-8'))) for name,directory in stages]
    lines=['# Modelo B + QVoice calibrado', '',
           'Clasificación: `presentation`. Modelo experimental desarrollado el 8 de octubre de 2026. Corte de conocimiento: 7 de septiembre de 2026.', '',
           f'El artefacto entrenado seleccionó **{model["selected"]["id"]}**. El procedimiento retrospectivo obtuvo **{results["decision"]["status"]}** según el criterio conjunto de ranking, Brier y calibración.', '',
           f'**{headline}.** La selección final es: {selected_name(model["selected"])}.', '',
           '![Comparación agregada frente a B](charts/comparacion-con-b.png)', '',
           '## Modelo entregado', '',
           '- [Parámetros y transformaciones del modelo entrenado](trained-model/model.json)',
           '- [Búsqueda completa del modelo entrenado](trained-model/selection.json)',
           '- [Resultados de la comparación temporal](comparison-results.json)',
           '- [Plan y reglas fijadas antes de ejecutar](../../../../../docs/plans/attrition-b-plus-qvoice-calibrated-20261008.md)', '',
           'El modelo añade una corrección QVoice al predictor de B y después calibra intercepto y pendiente con meses reservados. La fórmula mensual es `h = 1 − exp(−exp(a + b(eta_B + X_QVoice beta)))`; el riesgo a seis meses es `1 − producto(1 − h_m)`. El calendario avanza y las demás covariables se mantienen en el valor conocido del snapshot.', '',
           'B conserva su receta de diez features. En esta extensión sus coeficientes se estiman primero y sirven como offset fijo al ajustar QVoice. El experimento anterior reajustaba conjuntamente B y QVoice; las magnitudes de ambas ejecuciones no se consideran intercambiables.', '',
           '## Resultados en los periodos reservados', '',
           'PR-AUC se presenta multiplicada por 100; lift compara la tasa del 10% de mayor riesgo con la tasa de toda la cohorte. Brier se multiplica por 10,000. La calibración es el error absoluto entre probabilidad media y tasa observada, en puntos base (100 pb = 1 pp).', '']
    for p in periods:
        lines += [f'### {PERIODS[p["period"]]}', '',
                  f'{p["people"]:,} personas distintas; {p["snapshot_count"]} snapshots; {int(p["control"]["exposures"]):,} exposiciones persona-snapshot. La etiqueta mide al menos una salida voluntaria en los seis meses siguientes. La cohorte coincide en los cinco modelos.', '',
                  f'Combinación elegida usando sólo meses anteriores: **{p["selected"]["id"]}**. Cobertura con todos sus componentes disponibles: {fmt(p["response_complete_coverage_percent"])}%.', '',
                  '| Modelo | PR-AUC × 100 | Lift@10% | Brier × 10,000 | Error general (pb) | Error quintil superior (pb) |',
                  '|---|---:|---:|---:|---:|---:|']
        for name in NAMES:
            m=p[name]
            lines.append(f'| {NAMES[name]} | {fmt(m["pr_auc"]*100)} | {fmt(m["lift_at_10_percent"])} | {fmt(m["brier_score"]*10000)} | {fmt(m["calibration_error_pp"]*100)} | {fmt(m["top_quintile_calibration_error_pp"]*100)} |')
        lines += ['']
    labels={'ranking':'PR-AUC y lift en ambos periodos','brier_score':'Brier medio','calibration_error_pp':'Error general medio','top_quintile_calibration_error_pp':'Error del quintil superior medio'}
    lines += ['## Resultado del criterio conjunto', '',
              'El estado del experimento aplica ocho comprobaciones frente a B de referencia y el control de disponibilidad. Se añaden cuatro frente a B con calibración comparable. Para Brier y errores de calibración, «medio» significa la media aritmética de los dos periodos, con igual peso para cada periodo. Para ranking se exige mejorar tanto PR-AUC como lift en cada uno.', '',
              '| Comprobación | Resultado |','|---|---|']
    for key,passed in results['decision'].get('checks',{}).items():
        metric,ref=key.rsplit('_vs_',1)
        lines.append(f'| {labels[metric]} frente a {NAMES[ref]} | {"Cumple" if passed else "No cumple"} |')
    for key,passed in results['matched_calibration_checks'].items():
        lines.append(f'| {labels[key]} frente a B con calibración comparable | {"Cumple" if passed else "No cumple"} |')
    if ranking and brier and not results['decision']['checks']['calibration_error_pp_vs_control']:
        lines += ['',
                  '**Interpretación:** hay aporte predictivo de QVoice en ranking y Brier, pero el modelo calibrado no cumple la regla conjunta porque empeora la calibración general frente a B. El estado «sin mejora demostrada» se refiere a cumplir todo el criterio; no elimina las mejoras parciales observadas.', '']
    if all(results['matched_calibration_checks'].values()):
        lines += ['Frente a B ajustado y calibrado con los mismos tramos, QVoice cumple las cuatro comprobaciones agregadas. Esto respalda un aporte adicional de las respuestas bajo este procedimiento; las magnitudes y la incertidumbre siguen siendo las de una evaluación retrospectiva.', '']
    if all(p['response']['calibration_error_pp']>p['uncalibrated']['calibration_error_pp'] for p in periods):
        lines += ['La calibración con meses reservados aumentó el error general respecto a B + QVoice sin calibrar en ambos periodos. Por tanto, haber ejecutado la calibración no significa haber mejorado todas las medidas de calibración futura.', '']
    lines += ['### Tasa media predicha y observada', '',
              'Cada tasa usa como denominador las exposiciones persona-snapshot del periodo y como evento una salida voluntaria en los seis meses siguientes. Una persona puede aparecer en varios snapshots.', '',
              '| Periodo | Observada | B de referencia | B con calibración comparable | B + QVoice sin calibrar | B + QVoice calibrado |',
              '|---|---:|---:|---:|---:|---:|']
    for p in periods:
        rates=[p['control']['observed_percent']]+[p[name]['predicted_percent'] for name in ('control','base_calibrated','uncalibrated','response')]
        lines.append(f'| {PERIODS[p["period"]]} | '+ ' | '.join(f'{fmt(v)}%' for v in rates)+' |')
    lines += ['', 'El control B con calibración comparable usa los mismos tramos que el candidato; el control de disponibilidad conserva los estados de ausencia sin utilizar el contenido de las respuestas. La calibración se estima antes del periodo evaluado y puede deteriorarse cuando cambia la tasa posterior.', '',
              '## Qué se exploró', '',
              'Se evaluaron las 255 combinaciones no vacías de ocho bloques: Q4, Q12, Career, promedio 33, Engagement, Connection histórico, Wellbeing histórico y Confidence. Cada combinación probó tres penalizaciones. También se probaron PCA con 1, 2, 3, 5 y 10 componentes, cada uno con tres penalizaciones. Son 780 ajustes por corte; 2,340 entre los dos cortes retrospectivos y el corte del artefacto final.', '',
              'Esta búsqueda es exhaustiva entre los ocho bloques definidos. No explora todas las interacciones ni los subconjuntos de los 33 ítems individuales. Las correlaciones y la varianza explicada por PCA están en los archivos de selección; describen redundancia y variación, sin medir causalidad ni garantizar capacidad predictiva. PCA resume cómo varían juntas las respuestas; su construcción no usa la etiqueta de attrition. Su utilidad predictiva se compara después con la misma regla de Brier mensual.', '',
              '| Corte | Candidato seleccionado | Tipo | L2 |', '|---|---|---|---:|']
    for p in periods:
        s=p['selected']
        lines.append(f'| {PERIODS[p["period"]]} | {s["id"]} | {s["kind"]} | {fmt(s["l2"])} |')
    s=model['selected']
    lines.append(f'| Artefacto al 7-sep-2026 | {s["id"]} | {s["kind"]} | {fmt(s["l2"])} |')
    lines += ['', '### Combinaciones frente a PCA', '',
              'Los valores siguientes son Brier **mensuales del tramo de selección**, multiplicados por 10,000. Sirven para escoger la representación y no son una estimación independiente de desempeño. Las diferencias pequeñas pueden desaparecer al redondear; los JSON conservan la precisión completa.', '',
              '| Corte | Ajustes que convergieron / intentados | Mejor combinación | Brier × 10,000 | Mejor PCA | Brier × 10,000 |',
              '|---|---:|---|---:|---|---:|']
    for name,search in searches:
        eligible=[r for r in search['trials'] if r['converged'] and r['monthly_brier'] is not None]
        best={kind:min((r for r in eligible if r['kind']==kind),key=lambda r:(r['monthly_brier'],r['parameters'],r['l2'],r['id'])) for kind in ('blocks','pca')}
        lines.append(f'| {name} | {len(eligible)} / {len(search["trials"])} | {best["blocks"]["id"]} | {fmt(best["blocks"]["monthly_brier"]*10000)} | {best["pca"]["id"]} | {fmt(best["pca"]["monthly_brier"]*10000)} |')
    lines += ['', '### Cómo interpretar las señales seleccionadas', '',
              f'El artefacto final conserva **{selected_name(model["selected"])}**. Se eligió por el resultado conjunto al añadirlo a B. Una variable incluida no demuestra que tenga la mayor correlación individual con attrition ni que cause salidas.', '',
              'Las selecciones históricas y la selección final pueden diferir porque cambian los meses de ajuste y selección. Debe evaluarse esa estabilidad antes de atribuir importancia definitiva a un tema.', '']
    winners=[search['selected'] for _,search in searches]
    if all(winner['kind']=='blocks' for winner in winners):
        common=set.intersection(*(set(winner['blocks']) for winner in winners))
        stable=', '.join(BLOCK_NAMES[b] for b in BLOCK_NAMES if b in common) or 'ninguno'
        lines += [f'Bloques presentes en las tres selecciones: **{stable}**. Es una señal descriptiva de estabilidad; los cortes comparten historia y no son tres experimentos independientes.', '']
    lines += [
              '### Fechas de selección y calibración', '',
              '| Modelo | Etiquetas para selección: ajuste hasta | Snapshots de selección | Coeficientes finales: etiquetas hasta | Snapshots de calibración |',
              '|---|---|---|---|---|']
    for (name,directory),(_,search) in zip(stages,searches):
        stage_model=json.loads((directory/'model.json').read_text(encoding='utf-8'))
        lines.append(f'| {name} | {search["maximum_training_label_end"]} | {", ".join(search["selection_dates"])} | {stage_model["maximum_fit_label_end"]} | {", ".join(stage_model["calibration_snapshots"])} |')
    lines += ['', '## Fechas del artefacto entrenado', '',
              f'- Fin máximo de etiquetas usadas para ajustar coeficientes: {model["maximum_fit_label_end"]}.',
              f'- Snapshots reservados para calibración: {", ".join(model["calibration_snapshots"])}.',
              f'- Fin máximo de etiquetas usadas para calibrar: {model["maximum_calibration_label_end"]}.', '',
              'Los folds evalúan el procedimiento que selecciona y calibra; el artefacto final tiene la selección y los coeficientes estimados al corte disponible. Se mantiene como versión experimental hasta obtener evidencia posterior suficiente.', '',
              '## Límites de interpretación', '',
              '- Los periodos retrospectivos ya fueron inspeccionados en el desarrollo anterior. No equivalen a un holdout externo nuevo.',
              '- El primer corte dispone de poca historia QVoice bajo la política anual y sólo dos meses para selección y dos para calibración; la selección puede ser inestable.',
              '- Se utiliza QVoice 2024 en 2025 y QVoice 2025 en 2026. QVoice 2026 corresponde a 2027 y queda fuera del modelo actual.',
              '- Q6 y Q9 no tienen historia en ambos periodos; Heartbeat no se reconstruye con sus 53 ordinales en 2024/2025. Los comentarios se excluyen por texto libre.',
              '- Career conserva una diferencia de redacción en 2024. Su equivalencia entre waves sigue siendo exploratoria, incluso cuando el predictor se selecciona.',
              '- Los intervalos bootstrap conservan juntas las observaciones de cada persona. Son condicionales al modelo ajustado y no repiten la selección de 780 candidatos.',
              '- La cobertura completa cuenta todas las respuestas requeridas. Los faltantes permanecen en la cohorte con estados explícitos; PCA los imputa con medias de entrenamiento y conserva indicadores de ausencia.', '',
              'No se guardaron filas de empleados, llaves, respuestas ni scores individuales. Los parámetros del modelo y los resultados publicados son agregados.', '',
              '## Comprobaciones y procedencia', '',
              '- [Pruebas numéricas, temporales, de serialización y contratos](validation/test-results.json).',
              '- [Validación del SQL y del contrato de columnas](validation/model-sql-check.json).',
              '- [Reconciliación de la búsqueda, parámetros, fechas y comparación](validation/artifact-checks.json).',
              '- [Manifest y huellas de los artefactos](manifest.json).', '',
              'Las definiciones y evaluaciones de los siete conceptos están enlazadas en `variables/<concepto>/assessment-reference.json`. La consulta guardada es `queries/profiles/engineering_qvoice_person_month_20261008_full.sql`; se ejecutó el 8 de octubre de 2026 para la población y el corte declarados. El manifiesto y `inputs/` conservan las fuentes, la política anual, la configuración y el código de esta ejecución.', '']
    (root/'informe-modelo-b-qvoice-calibrado.md').write_text('\n'.join(lines),encoding='utf-8')
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    manifest['report']='informe-modelo-b-qvoice-calibrado.md'
    for p in [root/manifest['report'],charts/'comparacion-con-b.png']:
        manifest['artifact_sha256'][str(p.relative_to(root)).replace('\\','/')]=sha256_file(p)
    manifest['report_finalized_at']=utc_now()
    manifest['code_sha256']['tools/build_qvoice_calibrated_report.py']=sha256_file(Path(__file__))
    write_json(root/'manifest.json',manifest)
    print(root/manifest['report'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-root',type=Path,required=True)
    parser.add_argument('--figure-only',action='store_true')
    args=parser.parse_args()
    build(args.run_root,args.figure_only)
