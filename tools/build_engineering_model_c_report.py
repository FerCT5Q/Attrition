"""Reporte español y figura agregada de C, sin cambiar modelos ni resultados."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/analysis/engineering/20261008/model-c-v2'
LABELS={
 'level_grouped':'Nivel', 'tenure_playbook_band':'Antigüedad en Qualcomm', 'calendar_month':'Mes del calendario',
 'manager_changes_12m':'Cambios de manager en 12 meses', 'team_exits_12m':'Salidas previas del equipo en 12 meses',
 'direct_reports_band':'Reportes directos', 'time_since_promotion_band':'Tiempo desde promoción',
 'rehire':'Recontratación (proxy)', 'level_x_tenure':'Nivel × antigüedad',
 'tenure_x_manager_changes':'Antigüedad × cambios de manager', 'prior_experience_band':'Experiencia previa',
 'time_at_level_band':'Tiempo en el nivel', 'manager_left_6m':'Salida del manager en 6 meses',
 'ios_12m':'Movimientos IOS en 12 meses', 'layers_band':'Capa organizativa almacenada',
 'work_arrangement_group':'Modalidad de trabajo', 'region':'Región', 'comp_ratio_band':'Banda de comp ratio almacenado',
 'grade_family':'Prefijo de compensation grade', 'acquisition_recorded':'Adquisición registrada',
 'transfer_12m':'Transferencia registrada en 12 meses'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def fmt(x):
    if x is None:
        return '—'
    if 0<abs(x)<.05:
        return ('−' if x<0 else '')+'<0.1'
    return f'{x:.1f}'.rstrip('0').rstrip('.')


def rule(item):
    clauses=[]
    for r in item['conditions']:
        field,value=r['condition'].split('=',1)
        value=value.replace('years','años').replace('year','año').replace('(unknown)','desconocido')
        clauses.append(f'{LABELS.get(field,field)} {"=" if r["present"] else "≠"} {value}')
    return '; '.join(clauses) or 'Población completa'


def make_plot(result):
    fs=result['folds'];x=np.arange(len(fs));b=[f['B'] for f in fs];c=[f['C'] for f in fs]
    labels=[f"{f['first_snapshot'][:7]}\na {f['last_snapshot'][:7]}\nn={int(f['B']['exposures']):,}" for f in fs]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(13,8.4),layout='constrained')
    colors={'B':'#626b78','C':'#1769ab','observado':'#181818'}
    ax=axes[0,0]
    for name,values in [('B',[r['predicted_percent'] for r in b]),('C',[r['predicted_percent'] for r in c]),('observado',[r['observed_percent'] for r in b])]:
        ax.plot(x,values,marker='o',color=colors[name],label=name)
    calibration_better=np.mean([r['calibration_error_pp'] for r in c])<np.mean([r['calibration_error_pp'] for r in b])
    calibration_difference=abs(np.mean([r['calibration_error_pp'] for r in c])-np.mean([r['calibration_error_pp'] for r in b]))
    calibration_title='El error global medio cambia poco' if calibration_difference<.05 else ('C reduce el error de estimación global' if calibration_better else 'B conserva menor error de estimación global')
    ax.set_title(calibration_title,loc='left',fontweight='bold');ax.set_ylabel('% de persona-snapshots');ax.legend(frameon=False,ncol=3)
    ax=axes[0,1]
    ax.bar(x-.18,[r['lift_at_10_percent'] for r in b],.36,color=colors['B'],label='B')
    ax.bar(x+.18,[r['lift_at_10_percent'] for r in c],.36,color=colors['C'],label='C')
    ranking_better=np.mean([r['lift_at_10_percent'] for r in c])>np.mean([r['lift_at_10_percent'] for r in b])
    wins=sum(cc['lift_at_10_percent']>bb['lift_at_10_percent'] for bb,cc in zip(b,c))
    ax.axhline(1,color='#aaa',lw=1);ax.set_title(f'C mejora el lift medio; gana en {wins} de {len(fs)} periodos' if ranking_better else 'B conserva mayor lift medio',loc='left',fontweight='bold');ax.set_ylabel('Lift: veces la tasa media');ax.legend(frameon=False)
    ax=axes[1,0];groups=[f['groups']['summary'] for f in fs]
    ax.bar(x-.18,[g['B_group_mae_pp'] for g in groups],.36,color=colors['B'],label='B')
    ax.bar(x+.18,[g['C_group_mae_pp'] for g in groups],.36,color=colors['C'],label='C')
    groups_better=np.mean([g['C_group_mae_pp'] for g in groups])<np.mean([g['B_group_mae_pp'] for g in groups])
    ax.set_title(('C' if groups_better else 'B')+' estima mejor dentro de los grupos de C',loc='left',fontweight='bold');ax.set_ylabel('Error absoluto medio ponderado, pp');ax.legend(frameon=False)
    ax=axes[1,1];gains=[100*(bb['log_loss']-cc['log_loss'])/bb['log_loss'] for bb,cc in zip(b,c)]
    ax.bar(x,gains,color=['#1769ab' if g>=0 else '#b95539' for g in gains]);ax.axhline(0,color='#222',lw=1)
    ax.set_title('Cambio de log-loss frente a B',loc='left',fontweight='bold');ax.set_ylabel('% de mejora de C; positivo es mejor')
    for xx,gain in zip(x,gains):
        ax.annotate(f'{fmt(gain)}%',(xx,gain),xytext=(0,4 if gain>=0 else -14),textcoords='offset points',ha='center')
    for ax in axes.flat:
        ax.set_xticks(x,labels);ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:fmt(v)));ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
    fig.suptitle('Modelo C sin QVoice frente a B · evaluación temporal retrospectiva',fontsize=16,fontweight='bold')
    fig.supxlabel('Fuente: engineering_model_c_person_month_20261008.sql · ejecución: 8-oct-2026\n'
                  'Engineering · activos regulares, sin RF360 · salida voluntaria en seis meses / persona-snapshots elegibles',fontsize=9)
    fig.savefig(OUT/'comparacion-b-c.png',dpi=160)
    fig.savefig(OUT/'comparacion-b-c.svg')
    plt.close(fig)


def main():
    r=read(OUT/'results.json');cfg=read(OUT/'frozen-config.json');d=r['decision'];b=d['B_mean'];c=d['C_mean']
    traces=[read(p) for p in (OUT/'selection').glob('*.json')]
    failed=sum(sum(t['failed'] for t in trace['trials']) for trace in traces)
    make_plot(r)
    lines=['# Modelo C sin QVoice frente a B','',f'**Resultado: {d["status"]}.**','',
           'Modo de entrega: `presentation`. Ejecución del 8 de octubre de 2026; datos con frontera de conocimiento del 7 de septiembre de 2026.',
           '', '## Resumen','',
           f'- El C experimental archivado contiene {len(r["final_features"])} términos y utiliza hazard mensual cloglog, sin calibración posterior. Es la última especificación evaluada, con corte de entrenamiento {r["final_training_cutoff"]}.',
           f'- La comparación requirió {r["hazard_fits"]} evaluaciones hazard solicitadas; hubo compresión exacta y reutilización de ajustes. No se conserva un conteo completo de ajustes nuevos frente a recuperados de memoria.',
           f'- La ejecución optimizada hasta su cierre consumió {fmt(r["elapsed_seconds"]/60)} minutos, incluida la selección adicional detenida. La comparación completa y la carga ocuparon aproximadamente {fmt(r["completed_evaluation_seconds"]/60)} minutos. Un intento previo se conserva en `model-c-v1/interrupted.json`.',
           '- B se conserva como referencia. C + QVoice no se ha iniciado.',
           '- Las métricas siguientes evalúan el proceso de selección y reajuste de C en cada fecha; las listas varían. Se omitió el reajuste adicional a septiembre de 2026 después de que C no superó la regla de promoción. No se publican pronósticos actuales.',
           '', '## Comparación global','',
           'Promedio simple de cuatro periodos externos de seis snapshots. PR-AUC se informa como average precision. Las pérdidas se escalan por 1000 para que sean legibles. Las cifras visibles se redondean; los cambios relativos se calculan sin redondear.',
           '', '| Métrica | B | C | Lectura |','|---|---:|---:|---|']
    specs=[('Log-loss × 1000','log_loss',1000,False),('Brier × 1000','brier_score',1000,False),('PR-AUC (%)','pr_auc',100,True),
           ('Lift del 10% superior','lift_at_10_percent',1,True),('Error global (pp)','calibration_error_pp',1,False),
           ('Error del 20% superior propio (pp)','top_quintile_calibration_error_pp',1,False)]
    for label,key,scale,higher in specs:
        gain=(c[key]-b[key])/b[key]*100*(1 if higher else -1) if b[key] else 0
        lines.append(f'| {label} | {fmt(b[key]*scale)} | {fmt(c[key]*scale)} | {fmt(abs(gain))}% {"mejora" if gain>0 else "deterioro" if gain<0 else "igual"} |')
    lines+=['','![Comparación temporal de B y C](comparacion-b-c.png)','',
            'Log-loss penaliza probabilidades equivocadas; Brier mide error cuadrático. Menor es mejor en ambos. PR-AUC y lift evalúan concentración de salidas; mayor es mejor. Error en pp compara riesgo medio predicho con frecuencia observada.',
            '', '## Lo que ocurre dentro de los grupos','',
            'Cada árbol se aprende antes del periodo evaluado. Las columnas de error B y C usan exactamente las mismas personas y reglas de C.',
            '', '| Snapshots de predicción | Error de B en grupos (pp) | Error de C en grupos (pp) | Error B en grupo alto (pp) | Error C en grupo alto (pp) | Cobertura del grupo alto | Salidas capturadas |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for f in r['folds']:
        g=f['groups']['summary']
        lines.append(f'| {f["first_snapshot"]} a {f["last_snapshot"]} | {fmt(g["B_group_mae_pp"])} | {fmt(g["C_group_mae_pp"])} | {fmt(g["high_B_error_pp"])} | {fmt(g["high_C_error_pp"])} | {fmt(g["high_coverage_percent"])}% | {fmt(g["high_capture_percent"])}% |')
    lines+=['','El grupo alto suma hojas completas desde el riesgo mayor hasta cubrir al menos 20% en entrenamiento; su tamaño futuro puede variar. No equivale siempre al quintil exacto. Las tasas agregadas cuentan persona-snapshots; una persona o salida puede contribuir a varias ventanas solapadas.',
            '', '### Capacidad de ordenar grupos, comparando los árboles propios','',
            '| Periodo | Lift10 de grupos B | Lift10 de grupos C |','|---|---:|---:|']
    for f in r['folds']:
        gr=f['groups']['ranking_of_frozen_groups']
        lines.append(f'| {f["first_snapshot"][:7]} a {f["last_snapshot"][:7]} | {fmt(gr["B"]["lift_at_10_percent"])} | {fmt(gr["C"]["lift_at_10_percent"])} |')
    lines+=['','Se ponderan los empates de las hojas para comparar a igual 10% de población. Es una métrica de ranking, no una instrucción para dividir un grupo operativo.',
            '', '### Grupos del último periodo evaluado','']
    last=r['folds'][-1];old_rules={int(x['node']):x for x in last['group_definition']['rules']}
    lines += [f'Reglas aprendidas en la foto {last["group_definition"]["training_snapshot"]}. Predicciones desde {last["first_snapshot"]} hasta {last["last_snapshot"]}; seguimiento de la última foto hasta {last["latest_outcome"]}. Son las reglas del último backtest y del modelo experimental archivado.',
              '', '| Grupo | Regla | Personas medias por foto | Observado R6 | B estimado | C estimado |',
              '|---|---|---:|---:|---:|---:|']
    for g in last['groups']['rows']:
        if g.get('suppressed'):
            continue
        lines.append(f'| G{g["node"]}{" · alto" if g["high"] else ""} | {rule(old_rules[g["node"]])} | {fmt(g["mean_people_per_snapshot"])} | {fmt(g["observed_percent"])}% | {fmt(g["B_predicted_percent"])}% | {fmt(g["C_predicted_percent"])}% |')
    lines+=['','Una tasa observada no publicable se muestra como —; se exigen al menos 30 personas por foto y 30 personas distintas con salida en las ventanas del grupo.',
            '', '## Cómo se seleccionó C','',
            '1. Se revisaron 21 términos candidatos: 19 variables/representaciones y dos interacciones. Todas las variables base de B podían salir.',
            '2. Un filtro L1 supervisado, ajustado sólo con el pasado, produjo conjuntos de variables. También compitieron B y el conjunto completo.',
            '3. Cada conjunto se reajustó con cloglog y tres intensidades L2. Dos validaciones internas con etiquetas R6 maduras eligieron la combinación.',
            '4. Se priorizó log-loss, con restricciones de Brier y ranking; entre resultados próximos se eligió la lista más corta.',
            '5. Se reajustó antes de cada fecha externa y se evaluaron los seis snapshots siguientes. Las reglas de grupos también se congelaron antes.',
            '', f'Se descartaron {failed} combinaciones de variables y L2 que no convergieron en al menos una validación interna. Sus registros permanecen en el recorrido; no se consideraron resultados válidos.',
            '', 'No se usó PCA ni se buscaron todas las combinaciones posibles. L1 selecciona utilizando la salida, mientras PCA busca variación entre predictores. Mantener variables originales facilita explicar los grupos.',
            '', '| Origen | Términos de C | L2 | Variables seleccionadas |','|---|---:|---:|---|']
    for f in r['folds']:
        lines.append(f'| {f["origin"]} | {len(f["C_features"])} | {fmt(f["C_l2"])} | '+', '.join(LABELS[x] for x in f['C_features'])+' |')
    lines+=['','### Variables del modelo experimental archivado','']+[f'- {LABELS[f]} (`{f}`).' for f in r['final_features']]
    lines+=['','## Artefacto conservado','',
            f'Se conserva la última especificación que se evaluó fuera de muestra: origen **{r["final_training_cutoff"]}**, con etiquetas mensuales conocidas hasta **{last["train_latest_label"]}**.',
            '', 'La comparación quedó completa. Se detuvo la selección adicional destinada al reajuste con datos hasta septiembre de 2026 al comprobar que C no superaba B bajo la regla prevista. Este cambio de cierre está registrado en `finalization.json`; no cambia ninguno de los cuatro resultados externos.']
    ga=read(OUT/'trained-model/groups.json');rules={x['node']:x for x in ga['rules']}
    for g in sorted(r['forecast_groups'],key=lambda x:-x['predicted_risk_6m_percent']):
        lines.append(f'| G{g["node"]} | {rule(rules[g["node"]])} | {g["people"]} | {fmt(g["predicted_risk_6m_percent"])}% | {"Sí" if g["high"] else "No"} |')
    lines+=['',f'El árbol resume los riesgos del modelo con R² de {fmt(100*ga["training_r2"])}% en su foto de entrenamiento. Ese R² mide fidelidad del resumen, no exactitud frente a salidas.',
            '', '## Regla de decisión e incertidumbre','',
            '| Comprobación previamente definida | Cumple |','|---|---|']
    check_labels={'loss':'Log-loss mejora al menos 0,5%','brier':'Brier no empeora','pr_auc':'PR-AUC mejora al menos 2%',
                  'lift10':'Lift10 mejora al menos 2%','temporal_pr':'PR-AUC gana en al menos 3 de 4 periodos',
                  'temporal_lift':'Lift10 gana en al menos 3 de 4 periodos','same_groups':'Error de grupos no empeora más de 0,1 pp',
                  'high_group':'Error del grupo alto no empeora más de 0,1 pp','loss_interval':'IC95 de diferencia de log-loss queda por debajo de cero'}
    for key,value in d['checks'].items():
        lines.append(f'| {check_labels[key]} | {"Sí" if value else "No"} |')
    interval=r['paired_loss_intervals']['log_loss'];lo,hi=[x*1000 for x in interval['ci95']]
    lines+=['',f'Diferencia pareada C − B en log-loss × 1000: {fmt(interval["difference_C_minus_B"]*1000)}; IC95 [{fmt(lo)}, {fmt(hi)}]. Negativo favorece C. Bootstrap por persona, {cfg["bootstrap_repetitions"]} réplicas; las ventanas de cada persona permanecen juntas.',
            '', 'Este intervalo reúne todos los persona-snapshots y pondera por su cantidad; la tabla principal da el mismo peso a cada periodo. El árbol usa la última foto del entrenamiento mensual, que tiene un intervalo de salida ya observado; puede ser anterior a la última foto disponible sin etiqueta.',
            '', '## Alcance y límites','']+[f'- {text}' for text in cfg['limitations']]
    lines+=['- B y C utilizan la misma población y el mismo frame corregido para exigir fecha de registro previa en salidas usadas como features; las cifras pueden diferir del B publicado anteriormente.',
            '- El bootstrap mantiene fijos los modelos y grupos entrenados; no reentrena la selección en cada réplica y no cubre toda la incertidumbre de selección o de cambios entre años.',
            '- Regiones, antigüedad y adquisición describen contexto; sus coeficientes no identifican causas. No se debe asumir que cambiar una variable reducirá attrition en esa magnitud.',
            '- Capas y comp ratio conservan significado de campo almacenado. Se probaron representaciones limitadas de varios conceptos y se documentaron las exclusiones; no se demuestra un óptimo entre las 43 variables.',
            '- Las reglas permiten orientar revisiones de carrera, movilidad y continuidad del equipo, con contraste de contexto antes de actuar. No se publicaron puntuaciones individuales.',
            '', '## Trazabilidad','',
            '- [Resultados y métricas de cálculo](results.json).',
            '- [Configuración congelada](frozen-config.json).',
            '- [Modelo C entrenado](trained-model/model-c.json).',
            '- [Reglas de grupos](trained-model/groups.json).',
            '- [Manifiesto de fuentes y privacidad](manifest.json).',
            '- Inventario completo: `config/engineering_model_c_inventory_20261008.json`.',
            '- Consulta guardada: `queries/profiles/engineering_model_c_person_month_20261008.sql`.',
            '- Evidencia de entradas: `input-evidence/`; recorrido de selección y cortes temporales: `selection/`.',
            '- Autorización: `config/attrition_model_in_memory_training_authorization_20261001.json`. Sin filas, llaves temporales, scores personales ni compensación exacta persistidos.', '']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    inventory=read(ROOT/'config/engineering_model_c_inventory_20261008.json')
    text=['# Inventario de variables para C','','| Orden | Concepto | Estado | Representación o razón |','|---:|---|---|---|']
    for row in inventory:
        text.append(f'| {row["order"]} | {row["variable"]} | {row["status"]} | {row["representation_or_reason"]} |')
    (OUT/'inventario.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    context=['# Modelo C: referencia del experimento sin QVoice','',f'Estado: **{d["status"]}**.',
             '', '## Artefactos','',f'- Carpeta: `{OUT.relative_to(ROOT).as_posix()}`.',
             '- Modelo: `trained-model/model-c.json`; encoder, coeficientes, variables, L2 y límite de conocimiento.',
             '- Reglas: `trained-model/groups.json`; sólo grupos, sin identificadores ni puntuaciones personales.',
             '- Informe: `informe.md`; métricas verificables: `results.json`; recorrido: `selection/`.',
             '', '## Selección y uso','',
             '- Filtrado L1 sobre el pasado, refit cloglog L2, validación temporal anidada y selección por pérdidas R6 con restricciones de ranking.',
             f'- Las métricas evalúan la política de selección en cuatro periodos. Se archiva la última especificación evaluada, con corte {r["final_training_cutoff"]}; no se terminó el reajuste adicional a septiembre de 2026 porque C no superó la regla de promoción.',
             '- Las filas repetidas de diseño se comprimen exactamente en memoria; penalización, likelihood y criterios permanecen iguales.',
             '- QVoice está excluido. No se inició C + QVoice.',
             '- B y B + QVoice se conservan en sus carpetas anteriores. El control de esta comparación reproduce la receta B sobre el mismo frame temporal corregido de C.',
             '', '## Términos del modelo final','']+[f'- `{x}`: {LABELS[x]}.' for x in r['final_features']]
    context += ['', '## Límites','',
                '- Experimento retrospectivo, sin validación prospectiva nueva ni garantía causal de las acciones.',
                '- Transferencia previa al 23 de octubre de 2023 se codifica como historia no confirmada. Comp ratio y capas son valores almacenados; no se demostró aquí su fórmula ni una raíz CEO.',
                '- Consulta: `queries/profiles/engineering_model_c_person_month_20261008.sql`; inventario: `config/engineering_model_c_inventory_20261008.json`.',
                '- No se asignaron nuevos scores de assessment; las comprobaciones de entrada se conservan como evidencia limitada al modelo.', '']
    (ROOT/'docs/context/model-c.md').write_text('\n'.join(context),encoding='utf-8')
    print('Informe, inventario y figura comparativa generados.')


if __name__=='__main__':
    main()
