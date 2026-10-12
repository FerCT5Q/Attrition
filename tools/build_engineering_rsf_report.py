"""Informe agregado del bosque de supervivencia y sus comparadores archivados."""
from pathlib import Path
import csv
import json
import shutil
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/analysis/engineering/20261008/random-survival-forest-v1'
sys.path.insert(0,str(ROOT/'tools'))
import engineering_model_c as base

NAMES = {'B':'B · cortes actuales','C':'C · cortes actuales','RSF_raw':'RSF sin calibrar',
 'RSF':'RSF calibrado','RSF_tree':'RSF · árbol explicativo','C_tree':'C · árbol archivado',
 'C_plus1':'C · cortes + una variable','C_four':'C · cuatro variables','C_near40':'C · cerca de 40 grupos',
 'CQ':'C + QVoice sin calibrar','CQ_scalar':'C + QVoice con escalar R6','BQ':'B + QVoice sin calibrar',
 'BQ_scalar':'B + QVoice con escalar R6','BQ_monthly_calibrated':'B + QVoice con calibración mensual',
 'C_refresh':'C · intercepto actualizado','C_availability':'C · disponibilidad QVoice',
 'C_scalar':'C · escalar R6','C_refresh_scalar':'C · intercepto y escalar',
 'C_availability_scalar':'C · disponibilidad y escalar'}


def fmt(v,suffix='',signed=False):
    if v is None:
        return '—'
    if 0 < abs(v) < .05:
        return ('+' if signed and v>0 else '-' if v<0 else '')+'<0.1'+suffix
    rounded = round(float(v),1)
    s = f'{rounded:.1f}'.removesuffix('.0')
    return ('+' if signed and rounded>0 else '')+s+suffix


def read(path):
    return base.read(path)


def rule(history,config,name='RSF'):
    summary = history['summary']
    ref = summary['C']
    value = summary[name]
    interval = next(x for x in history['intervals'] if x['model']==name and x['metric']=='capture30')
    differences = [p['evaluation'][name]['scenarios']['30']['metrics']['capture_percent']-p['evaluation']['C']['scenarios']['30']['metrics']['capture_percent'] for p in history['periods']]
    checks = {'capture_ci_positive':interval['ci95'][0]>0,'winning_periods':sum(d>1e-9 for d in differences)>=3}
    for key in ['group_mae_pp','group_snapshot_mae_pp']:
        checks[key] = value['scenarios']['30'][key] <= ref['scenarios']['30'][key]+config['preference']['maximum_group_error_increase_pp']
    for key in ['log_loss','brier_score']:
        checks[key] = value['global'][key] <= ref['global'][key]*(1+config['preference']['maximum_relative_loss_increase'])
    return {'model':name,'reference':'C','meets_rule':all(checks.values()),'checks':checks,
            'winning_period_count':sum(d>1e-9 for d in differences),'capture_difference_pp':interval['difference'],
            'capture_difference_ci95_pp':interval['ci95']}


def figures(history,verdict):
    names = ['B','C','RSF_raw','RSF','RSF_tree']
    data = history['summary']
    title = f'El bosque cambia {fmt(verdict["capture_difference_pp"]," pp",True)} la captura media frente a C'
    fig,ax = plt.subplots(figsize=(12,6))
    vals = [data[n]['scenarios']['30']['capture_percent'] for n in names]
    colors = ['#7d8996','#7d8996','#7d8996','#246bb4','#7d8996']
    ax.barh(range(len(names)),vals,color=colors,height=.55)
    ax.set_yticks(range(len(names)),[NAMES[n] for n in names])
    ax.invert_yaxis()
    ax.set_xlim(0,max(vals)*1.18)
    ax.set_xlabel('Porcentaje de salidas observado dentro de la población priorizada')
    for i,v in enumerate(vals):
        ax.text(v+.4,i,fmt(v,'%'),va='center')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis='x',alpha=.15)
    ax.set_axisbelow(True)
    fig.suptitle(title,fontsize=15,fontweight='bold',x=.025,ha='left')
    fig.text(.025,.9,'Captura a seis meses · capacidad del 30% · diferencias calculadas antes de redondear',fontsize=11)
    fig.text(.025,.025,'Engineering, Employee, Regular, activo, sin RF360. Fotos: febrero 2024–enero 2026.\n'
             'Fuente: historical-results.json; engineering_rsf_person_month_20261008.sql; experimento 8–9 oct 2026.',fontsize=9)
    fig.tight_layout(rect=(0,.12,1,.88))
    fig.savefig(OUT/'captura-comparada.png',dpi=160)
    fig.savefig(OUT/'captura-comparada.svg')
    plt.close(fig)
    fig,ax = plt.subplots(figsize=(11,5.5))
    for n,color in [('C','#7d8996'),('RSF_raw','#adb6bf'),('RSF','#246bb4')]:
        values = [p['evaluation'][n]['scenarios']['30']['metrics']['group_snapshot_mae_pp'] for p in history['periods']]
        ax.plot(range(4),values,'o-',color=color,label=NAMES[n])
    ax.set_xticks(range(4),['Feb–jul 2024','Ago 2024–ene 2025','Feb–jul 2025','Ago 2025–ene 2026'])
    ax.set_ylabel('Error por grupo y foto · puntos porcentuales')
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x,pos:fmt(x)))
    ax.legend(frameon=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='y',alpha=.15)
    fig.suptitle('La calibración del bosque eleva el error en los primeros periodos',x=.03,ha='left',fontsize=15,fontweight='bold')
    fig.text(.03,.89,'Prioridad del 30% · cortes comunes de antigüedad, salidas del equipo y nivel',fontsize=10)
    fig.text(.03,.02,'Engineering, Employee, Regular, activo, sin RF360; salida voluntaria a seis meses.\n'
             'Fuente: historical-results.json; consulta RSF archivada; experimento 8–9 oct 2026.',fontsize=9)
    fig.tight_layout(rect=(0,.11,1,.88))
    fig.savefig(OUT/'error-grupos-periodos.png',dpi=160)
    fig.savefig(OUT/'error-grupos-periodos.svg')
    plt.close(fig)


def main():
    result = read(OUT/'results.json')
    history = read(OUT/'historical-results.json')
    qvoice = read(OUT/'qvoice-results.json')
    config = read(OUT/'frozen-config.json')
    verdict = rule(history,config)
    raw_verdict = rule(history,config,'RSF_raw')
    final_model = read(OUT/'trained-model/model.json')
    final_groups = read(OUT/'trained-model/groups.json')
    base.write(OUT/'verdict.json',verdict)
    base.write(OUT/'verdict-uncalibrated.json',raw_verdict)
    figures(history,verdict)
    lines = ['# Random Survival Forest frente a B, C y sus variantes','',
      'Experimento iniciado el 8-oct-2026 y completado el 9-oct-2026. Modo `presentation`. '
      'Población: Engineering, Employee, Regular, activo, sin RF360.','',
      '## Conclusión','',
      ('El bosque calibrado cumple la regla retrospectiva de preferencia frente a C.' if verdict['meets_rule'] else
       'El bosque calibrado no cumple todos los requisitos declarados para sustituir a C.'),
      f'La captura al priorizar al 30% cambia {fmt(verdict["capture_difference_pp"]," pp",True)}, '
      f'IC95 [{fmt(verdict["capture_difference_ci95_pp"][0])}, {fmt(verdict["capture_difference_ci95_pp"][1])}] pp; '
      f'mejora en {verdict["winning_period_count"]} de cuatro periodos.','',
      'La regla exige mejora de captura con IC95 positivo y tres victorias, sin aumentar los errores '
      'por grupo/grupo-mes más de 0.1 pp ni log-loss/Brier más de 0.5% relativo. '
      'La comparación principal usa los mismos cortes de grupos.','',
      f'La versión sin calibrar es más competitiva: cambia la captura '
      f'{fmt(raw_verdict["capture_difference_pp"]," pp",True)} y gana en '
      f'{raw_verdict["winning_period_count"]} de cuatro periodos. '
      + ('Cumple la regla conjunta.' if raw_verdict['meets_rule'] else
         'Tampoco cumple la regla conjunta: los detalles de cada condición están en verdict-uncalibrated.json.'),'',
      ('Recomendación: revisar la adopción del candidato con una evaluación futura independiente.' if verdict['meets_rule'] else
       'Recomendación: mantener C como referencia y conservar RSF sin calibrar como candidato experimental. '
       'Su ligera ganancia de captura no viene acompañada de una mejora estable entre periodos; '
       'la calibración ensayada empeora el promedio histórico. La variante de C que añade un corte '
       'ofrece una captura semejante con menor error de los grupos.'),'',
      '![Captura comparada](captura-comparada.png)','',
      '## Cuatro periodos históricos','',
      'Febrero–julio 2024, agosto 2024–enero 2025, febrero–julio 2025 y agosto 2025–enero 2026. '
      'Cada foto tiene seguimiento de seis meses. Las medias dan igual peso a cada periodo; '
      'las personas y ventanas pueden repetirse. Las diferencias se calculan antes de redondear.','',
      '| Variante | Grupos, media | Captura 20% | Captura 30% | Captura 40% | Error grupo-mes al 30% |',
      '|---|---:|---:|---:|---:|---:|']
    for name,s in history['summary'].items():
        lines.append(f'| {NAMES[name]} | {fmt(s["groups_mean"])} | '+
                     ' | '.join(fmt(s['scenarios'][cap]['capture_percent'],'%') for cap in ['20','30','40'])+
                     f' | {fmt(s["scenarios"]["30"]["group_snapshot_mae_pp"]," pp")} |')
    lines += ['', 'Captura = salidas observadas dentro de la prioridad / todas las salidas observadas. '
      'La capacidad se iguala en cada foto, con peso uniforme en el grupo del límite. '
      'Los grupos de menos de 300 personas van a resto. El número de grupos de la tabla es la media '
      'de grupos elegibles por foto, no el número de grupos que se atendería. Las cifras de personas, '
      'errores y grupos completos están en los JSON. Error grupo-mes es el promedio absoluto de '
      'la diferencia entre riesgo estimado y observado de cada grupo en cada foto, ponderado '
      'por su población priorizada. Se expresa en puntos porcentuales.','',
      '### Precisión global y discriminación','',
      '| Modelo | Log-loss × 1000 ↓ | Brier × 1000 ↓ | PR-AUC ↑ | R6 estimado | R6 observado |',
      '|---|---:|---:|---:|---:|---:|']
    for name in ['B','C','RSF_raw','RSF']:
        g = history['summary'][name]['global']
        lines.append(f'| {NAMES[name]} | {fmt(g["log_loss"]*1000)} | {fmt(g["brier_score"]*1000)} | '
                     f'{fmt(g["pr_auc"]*100,"%")} | {fmt(g["predicted_percent"],"%")} | {fmt(g["observed_percent"],"%")} |')
    lines += ['', 'Log-loss penaliza probabilidades equivocadas, sobre todo errores con mucha confianza. '
      'Brier mide el error cuadrático de las probabilidades. Ambos se muestran multiplicados por 1000 '
      'para facilitar la lectura. PR-AUC resume la separación de salidas en un evento poco frecuente. '
      'La precisión por grupo se evalúa aparte: una tasa global correcta puede ocultar errores que se compensan.','',
      '![Error por periodo](error-grupos-periodos.png)','',
      '### Precisión sobre la misma población priorizada por C','',
      'Se mantienen los grupos y la selección del 30% de C para comparar únicamente las probabilidades.','',
      '| Modelo | R6 estimado | R6 observado | Error por grupo | Error grupo-mes |',
      '|---|---:|---:|---:|---:|']
    for name in ['B','C','RSF_raw','RSF']:
        rows = [p['evaluation'][name]['on_C_priority'] for p in history['periods']]
        vals = {k:np.mean([r[k] for r in rows]) for k in ['predicted_percent','observed_percent','group_mae_pp','group_snapshot_mae_pp']}
        lines.append(f'| {NAMES[name]} | {fmt(vals["predicted_percent"],"%")} | {fmt(vals["observed_percent"],"%")} | '
                     f'{fmt(vals["group_mae_pp"]," pp")} | {fmt(vals["group_snapshot_mae_pp"]," pp")} |')
    prior_trees = read(ROOT/'output/analysis/engineering/20261008/bc-priority-comparison-v1/results.json')
    lines += ['', '### Referencia anterior: prioridades de los árboles B/C','',
      'La comparación archivada de árboles ordenaba las hojas por su riesgo de entrenamiento. '
      'Se conserva aquí como referencia histórica. Las tablas anteriores ordenan los grupos por '
      'la media de predicciones de cada foto; por eso no se mezclan sus reglas de prioridad.','',
      '| Árbol y orden archivados | Captura al 30% | Error grupo-mes |',
      '|---|---:|---:|']
    for name in ['B','C']:
        values = [f['scenarios']['30'][name]['metrics'] for f in prior_trees['folds']]
        lines.append(f'| {name} | {fmt(np.mean([r["capture_percent"] for r in values]),"%")} | '
                     f'{fmt(np.mean([r["group_snapshot_mae_pp"] for r in values])," pp")} |')
    base.write(OUT/'archived-tree-context.json',{'source':'output/analysis/engineering/20261008/bc-priority-comparison-v1/results.json',
        'source_sha256':base.sha(ROOT/'output/analysis/engineering/20261008/bc-priority-comparison-v1/results.json'),
        'priority':'Orden de las hojas fijado en entrenamiento; referencia contextual con los mismos periodos.',
        'folds':[{k:f[k] for k in ['fold','origin','first_snapshot','last_snapshot','scenarios']} for f in prior_trees['folds']]})
    lines += ['',
      '## Comparación en los periodos disponibles de QVoice','',
      'Agosto–diciembre de 2025 y enero–febrero de 2026; mismo conjunto de personas/fotos para todos '
      'los modelos de cada periodo. Se restauraron los parámetros históricos de las variantes. '
      'Este bloque tiene menos historia y no se mezcla con el promedio de los cuatro periodos. '
      'En enero–febrero de 2026 el bosque tiene ajuste de enero, mientras B y C conservan su '
      'último ajuste archivado de agosto de 2025; las correcciones QVoice conservan sus propios '
      'cortes de actualización. Es una comparación de las versiones disponibles, no una '
      'aislación perfecta del efecto de la familia del modelo.','',
      'B + QVoice se reproduce con su SQL original para el historial de salidas del equipo: '
      'usa fecha efectiva y frontera global. C/RSF añade que cada salida ya estuviera registrada '
      'en la foto. Se alinearon personas, fechas y episodios. Una etiqueta R6 entre 238451 '
      'observaciones difiere por el límite global de registro de BQ, confirmado mediante recálculo '
      'agregado. Todos los modelos se evalúan con la misma etiqueta y cortes de C; la reproducción '
      'de las métricas archivadas de BQ utiliza su etiqueta original. Por tanto BQ conserva la '
      'limitación temporal de su versión archivada y C hereda esa diferencia de observación. '
      'La conciliación predictiva exige reproducir todas sus métricas, incluido ranking; '
      'la diferencia inicial no se atribuye a empates numéricos. Véanse bq-input-reconciliation.json '
      'y bq-label-contract-audit.json.','',
      '| Variante | Captura al 30% | Error grupo-mes | Log-loss × 1000 | Brier × 1000 |',
      '|---|---:|---:|---:|---:|']
    for name,s in qvoice['summary'].items():
        lines.append(f'| {NAMES[name]} | {fmt(s["scenarios"]["30"]["capture_percent"],"%")} | '
                     f'{fmt(s["scenarios"]["30"]["group_snapshot_mae_pp"]," pp")} | '
                     f'{fmt(s["global"]["log_loss"]*1000)} | {fmt(s["global"]["brier_score"]*1000)} |')
    recent_rsf = qvoice['summary']['RSF']['scenarios']['30']
    recent_cq = qvoice['summary']['CQ']['scenarios']['30']
    recent_bq = qvoice['summary']['BQ']['scenarios']['30']
    lines += ['', 'En estos periodos recientes, el bosque calibrado estima mejor las tasas de los '
      f'grupos: error {fmt(recent_rsf["group_snapshot_mae_pp"]," pp")}, frente a '
      f'{fmt(recent_cq["group_snapshot_mae_pp"]," pp")} de C + QVoice sin calibración posterior y '
      f'{fmt(recent_bq["group_snapshot_mae_pp"]," pp")} de B + QVoice sin calibración posterior. '
      f'Su captura es {fmt(recent_rsf["capture_percent"],"%")}, frente a '
      f'{fmt(recent_cq["capture_percent"],"%")}/{fmt(recent_bq["capture_percent"],"%")}, respectivamente. '
      'Es un punto favorable para la precisión reciente de RSF; su ventaja depende del periodo '
      'y de la métrica. Las diferencias puntuales entre variantes QVoice y RSF no se presentan '
      'como una prueba directa de superioridad estadística.']
    lines += ['', 'Las variantes de grupos C comparten sus predicciones individuales; cambian la agrupación '
      'y la prioridad. El escalar conserva el orden individual, aunque promediar probabilidades transformadas '
      'puede cambiar el orden de grupos. Las variantes QVoice conservan sus fechas originales de ajuste '
      'y sus limitaciones de calibración. El bosque de este experimento no incorpora QVoice.','',
      '## Foto adicional con modelos del mismo origen','',
      'Foto del 22-feb-2026, seguida hasta el 22-ago-2026. Aquí B, C y RSF conservan '
      'el origen de agosto de 2025; permite revisar esta fecha con igual antigüedad de los modelos. '
      'No se añade al promedio de los cuatro periodos.','',
      '| Modelo | Captura al 30% | R6 estimado en prioridad | R6 observado | Error grupo-mes |',
      '|---|---:|---:|---:|---:|']
    extension = read(OUT/'extension.json')
    for name,entry in extension['evaluation'].items():
        m = entry['scenarios']['30']['metrics']
        lines.append(f'| {NAMES[name]} | {fmt(m["capture_percent"],"%")} | '
                     f'{fmt(m["predicted_percent"],"%")} | {fmt(m["observed_percent"],"%")} | '
                     f'{fmt(m["group_snapshot_mae_pp"]," pp")} |')
    lines += ['',
      '## Qué se entrenó y cómo se calibró','',
      '- Biblioteca: scikit-survival '+str(result['library_version'])+'. Bosque con divisiones log-rank y '
      'curvas de supervivencia; horizonte discretizado en seis meses calendario desde cada foto.',
      '- Cada foto es un nuevo origen con covariables conocidas. R6 = 1-S(6); los meses sin seguimiento '
      'completo se censuran en el último mes completo al origen. La etiqueta madura coincide con y_6m de C.',
      '- Ocho configuraciones por origen: señales base B o todos los conceptos candidatos de C, hojas '
      'mínimas 150/400 y selección de variables sqrt/0.5. One-hot aprendida sólo en entrenamiento.',
      '- 80 árboles al seleccionar; 200 al ajustar. Bootstrap de hasta 40000 filas por árbol, '
      'profundidad máxima 12 y cuatro hilos. Las filas de una persona pueden aparecer en distintas fotos; '
      'los intervalos de incertidumbre remuestrean personas completas.',
      '- Optimización: se omiten las filas de peso cero de cada muestra bootstrap, conservando '
      'los índices seleccionados, sus multiplicidades, el eje temporal y las semillas. El primer '
      'árbol de cada ajuste optimizado se contrasta con la ejecución completa de la biblioteca; '
      'se exige igualdad de divisiones y curvas dentro de tolerancia numérica. El primer bosque '
      'histórico se conserva tal como se ajustó con la implementación completa.',
      '- Tres fotos maduras para elegir la configuración y tres posteriores para calibrar. '
      'Todas anteriores al periodo externo. El bosque auxiliar se ajusta antes de las seis fotos.',
      '- Calibración escalar: R ajustado = 1-(1-R crudo)^exp(a). Se transfiere al bosque reajustado '
      'al origen; por eso se publican ambas versiones y se comprueba el resultado fuera del ajuste.',
      '- Árbol explicativo: hasta 16 hojas y profundidad 4, ajustado a predicciones del bosque '
      'en la última foto de entrenamiento. Sus reglas agrupan; el riesgo lo sigue estimando el bosque.',
      '- El modelo final en trained-model/ usa el corte 7-sep-2026. Sus parámetros se distinguen '
      'de los cinco modelos históricos; no se presentan como si ya hubieran sido evaluados a futuro.','',
      '### Modelo final archivado','',
      f'Configuración: `{final_model["specification"]["id"]}`; {final_model["trees"]} árboles. '
      f'El árbol explicativo final tiene {len(final_groups["rules"])} hojas. Su número de grupos '
      'elegibles dependerá del tamaño de cada grupo en la foto donde se aplique.','',
      'Variables: '+', '.join('`'+f+'`' for f in final_model['specification']['features'])+'.','',
      '### Selecciones por origen','',
      '| Origen | Señales elegidas | Hoja mínima | Variables por división | Multiplicador calibración |',
      '|---|---|---:|---|---:|']
    for path in sorted((OUT/'folds').glob('*/selection.json'))+[OUT/'trained-model/selection.json']:
        info = read(path); w = info['winner']
        lines.append(f'| {info["origin"]} | {w["feature_set"]} | {w["min_samples_leaf"]} | '
                     f'{w["max_features"]} | {fmt(info["calibration"]["multiplier"])} |')
    lines += ['', '## Interpretación y límites','',
      '- Un bosque puede captar interacciones sin especificarlas previamente, pero sus cientos de árboles '
      'son más difíciles de explicar que una fórmula. Los cortes comunes y el árbol explicativo '
      'permiten revisar grupos y el coste de simplificar.',
      '- Sólo se estiman y contrastan curvas hasta seis meses. No se valida una extrapolación a 12 meses.',
      '- Se conserva el outcome de B/C: otras salidas no son el evento voluntario. No se añade '
      'un modelo de riesgos competitivos. Se heredan límites de registro tardío y observación.',
      '- Se evaluó una rejilla acotada de hiperparámetros y estas representaciones de variables. '
      'El resultado describe este experimento; no demuestra que se haya agotado toda la familia RSF.',
      '- Para agrupar el bosque se probaron los cortes comunes y un árbol explicativo de hasta '
      '16 hojas. No se hizo una búsqueda exhaustiva de cruces de cuatro variables específica para '
      'RSF; las variantes de cuatro cortes comparadas pertenecen al experimento archivado de C.',
      '- Los periodos fueron explorados anteriormente; la evidencia es retrospectiva. Los IC95 usan '
      '500 remuestreos por persona y son condicionales a modelos, selecciones y prioridades; '
      'no corrigen comparaciones múltiples.',
      '- Selección y calibración usan fotos diferentes, pero sus ventanas de seguimiento se '
      'superponen. El periodo externo comienza después de que terminaron ambas ventanas; '
      'la separación de fotos no implica independencia estadística entre selección y calibración.',
      '- Frecuencia de divisiones en serialization-check.json describe uso de variables; no es '
      'importancia causal. Los grupos sugieren dónde investigar, sin demostrar que una acción evite salidas.',
      f'- Tiempo del último proceso completado (ajuste final): {fmt(result["elapsed_seconds"]/60)} minutos, '
      f'incluidos {fmt(result["load_seconds"]/60)} de carga. Cero reajustes de B/C y sus variantes.',
      '- Hubo un intento de carga previo interrumpido por permisos de Windows antes de completar '
      'el primer candidato. Ese intento y la instalación de dependencias no están incluidos '
      'en el tiempo de la ejecución completada; se registra en setup-interruption.json.',
      '- Una segunda interrupción ocurrió al interpretar los identificadores numéricos del árbol '
      'archivado de C. El bosque ya entrenado se recuperó de sus parámetros y se corrigió la lectura '
      'de esas hojas; evaluation-interruption.json conserva el registro. El tiempo anterior a '
      'reanudar tampoco forma parte del último cronómetro de ejecución.',
      '- Las interrupciones del bloque B + QVoice y su corrección de contrato se documentan '
      'en resume-history.json; los cinco bosques históricos completos se reutilizaron. '
      'El cronómetro final tampoco incluye esas ejecuciones interrumpidas.',
      '- Una carga perdió la conexión a Redshift y terminó con OperationalError e InterfaceError '
      'tras el cambio al 9-oct-2026. La carga final usa una conexión por año y reintento acotado. '
      'No se confirmó la causa exacta de la desconexión.',
      '- Una segunda desconexión ocurrió al cargar 2026. La comprobación posterior SELECT 1 '
      'funcionó. Se separaron las fases de comparación y ajuste final, con keepalive y reintentos '
      'de conexión. comparison-completed.json registra el tiempo de la comparación completada; '
      'el cronómetro anterior sólo corresponde al último proceso y no al tiempo total de la tarea.',
      '', '## Fuentes y reproducción','',
      '- Configuración: frozen-config.json; plan: source/docs/plans/engineering-random-survival-forest-20261008.md.',
      '- Consulta: queries/profiles/engineering_rsf_person_month_20261008.sql; ejecuciones 8–9 oct 2026; '
      'conocimiento hasta 7-sep-2026. Derivada de la consulta C + QVoice conservando las covariables de C.',
      '- Evidencia: population.json, input-checks.json, historical-results.json, qvoice-results.json y extension.json.',
      '- Modelos: folds/<origen>/ y trained-model/. forest-parameters.npz contiene sólo parámetros '
      'de inferencia; no contiene filas, llaves, muestras bootstrap ni etiquetas individuales.',
      '- predict_export() en el script del experimento permite reconstruir R6 crudo; model.json contiene '
      'el escalar. Las predicciones se mantienen exclusivamente en memoria.',
      '- Preservación: preservation.json y manifest.json. Resultados agregados y tasas suprimidas '
      'según los mínimos de publicación; autorización RAM del 1-oct-2026.',
      '- summary-reconciliation.json documenta la actualización de los promedios tras recuperar '
      'un bosque: la diferencia de PR-AUC está por debajo del redondeo mostrado. '
      'revisions/before-summary-reconciliation/ conserva los agregados y el código anteriores; '
      'los parámetros de los modelos y los intervalos bootstrap se conservan.','']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    all_rows = []
    for period in history['periods']:
        for name,entry in period['evaluation'].items():
            for row in entry['scenarios']['30']['selected_groups']:
                all_rows.append({'origin':period['origin'],'model':name,**row})
    fields = list(dict.fromkeys(k for row in all_rows for k in row))
    with (OUT/'grupos-prioritarios.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader(); writer.writerows(all_rows)
    context = '# Modelo Random Survival Forest\n\nExperimento: 8–9 oct 2026. Modo `presentation`.\n\n'
    context += ('Cumple' if verdict['meets_rule'] else 'No cumple')+' la regla retrospectiva de preferencia frente a C al 30%.\n\n'
    context += '[Informe y comparación](../../output/analysis/engineering/20261008/random-survival-forest-v1/informe.md).\n\n'
    context += 'Se comparan B, C, variantes de grupos y QVoice en sus periodos correspondientes. '
    context += 'Los modelos anteriores permanecen archivados. El bosque final tiene corte 7-sep-2026; '
    context += 'el experimento conserva modelos históricos, calibradores, parámetros de inferencia sin filas y evidencia agregada.\n'
    (ROOT/'docs/context/model-random-survival-forest.md').write_text(context,encoding='utf-8')
    for source in [Path(__file__),ROOT/'docs/context/model-random-survival-forest.md']:
        target = OUT/'source'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
    manifest = read(OUT/'manifest.json')
    manifest['status'] = 'completed_analysis_and_report'
    manifest['files'] = {str(p.relative_to(OUT)):base.sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
    base.write(OUT/'manifest.json',manifest)
    print(json.dumps(verdict))


if __name__=='__main__':
    main()
