"""Informe de agrupaciones C con cuatro variables, usando agregados guardados."""
from pathlib import Path
import csv
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

import engineering_c_fourway_groups as study

ROOT=study.ROOT
OUT=ROOT/'output/analysis/engineering/20261008/c-fourway-groups-v1'


def fmt(x,suffix='',signed=False):
    if x is None:
        return '—'
    if 0<abs(x)<.05:
        return ('<0.1' if x>0 else '>-0.1')+suffix
    label=f'{x:.1f}'.rstrip('0').rstrip('.')
    return ('+' if signed and x>0 else '')+label+suffix


def definition(spec):
    return ' × '.join(study.DISPLAY.get(x,x) for x in spec['dimensions'])


def plot(r,title):
    variants=['C_plus1','C_four','C_near40']
    labels=['Cortes actuales + una variable','Cuatro variables seleccionadas','Búsqueda de 30–50 grupos']
    fig,ax=plt.subplots(figsize=(12,5.8))
    lows,highs=[],[]
    for i,name in enumerate(variants):
        value=r['summary']['30'][name]['comparison']
        point=value['difference_pp']
        low,high=value['ci95_pp']
        lows.append(low); highs.append(high)
        color='#246bb4' if name=='C_plus1' else '#788695'
        ax.errorbar(point,i,xerr=[[max(0,point-low)],[max(0,high-point)]],fmt='o',capsize=6,color=color,markersize=8,lw=2)
        ax.text(1.02,i,fmt(point,' pp',True)+'  ['+fmt(low)+', '+fmt(high)+']',transform=ax.get_yaxis_transform(),va='center',fontsize=11)
    ax.axvline(0,color='#454f5b',ls='--',lw=1)
    margin=max(.2,(max(highs)-min(lows))*.15)
    ax.set_xlim(min(0,min(lows))-margin,max(0,max(highs))+margin)
    ax.set_ylim(2.6,-.6)
    ax.set_yticks(range(3),labels,fontsize=11)
    ax.xaxis.set_major_locator(MaxNLocator(6))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:fmt(x)))
    ax.set_xlabel('Cambio de captura al priorizar al 30% · puntos porcentuales',labelpad=14)
    ax.tick_params(axis='both',length=0,pad=8)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.grid(axis='x',color='#edf0f3')
    ax.set_axisbelow(True)
    fig.suptitle(title,x=.025,y=.98,ha='left',fontsize=15,weight='bold')
    baseline=r['summary']['30']['C_current']['metrics']['capture_percent']
    fig.text(.025,.855,'C conserva sus coeficientes. Referencia: cortes actuales, '+fmt(baseline,'%')+' de captura.\n'
             'Media de cuatro periodos de 2024–2026; IC95 pareado por persona. Engineering, Employee, Regular, activo, sin RF360.',fontsize=10)
    fig.text(.025,.035,'Fuente: results.json · engineering_model_c_person_month_20261008.sql · ejecución 8-oct-2026.\n'
             'Salida voluntaria a seis meses. Intervalos condicionales, sin corrección por comparaciones múltiples.\n'
             'En la alternativa principal, el límite inferior del IC95 es positivo y menor a 0.1 pp, muy próximo a cero.',fontsize=8)
    fig.subplots_adjust(left=.30,right=.73,top=.71,bottom=.22)
    fig.savefig(OUT/'cambio-captura.png',dpi=170,facecolor='white')
    fig.savefig(OUT/'cambio-captura.svg',facecolor='white')
    plt.close(fig)


def main():
    r=study.base.read(OUT/'results.json')
    cfg=study.base.read(OUT/'frozen-config.json')
    summary=r['summary']['30']
    primary=summary['C_plus1']
    gains=[x for x in ['C_plus1','C_four','C_near40'] if summary[x]['meets_rule']]
    if primary['meets_rule']:
        title='Añadir una variable mejora ligeramente la captura de C al priorizar al 30%'
    elif gains:
        title='Una agrupación alternativa mejora la prioridad; añadir una variable no basta'
    else:
        title='Los cruces de cuatro variables aún no justifican sustituir los cortes de C'
    lines=['# C: más detalle en los grupos', '', '## '+title, '',
        'Modo `presentation`. Ejecución: 8-oct-2026. Población: Engineering, Employee, Regular, activo, sin RF360.', '',
        'Objetivo: explorar si una cuarta variable permite identificar mejor grupos prioritarios, incluyendo '
        'alternativas de aproximadamente 40 grupos. **El modelo C, sus coeficientes y sus predicciones individuales '
        'se conservan.** Se modifica la agrupación y el orden de prioridad de sus medias de riesgo.', '',
        '## Resultado al priorizar al 30%', '',
        'Promedio con igual peso de cuatro periodos de seis fotos: febrero–julio de 2024, agosto de 2024–enero de 2025, '
        'febrero–julio de 2025 y agosto de 2025–enero de 2026. Cada foto se sigue durante seis meses. '
        'Son periodos retrospectivos ya explorados, con personas y ventanas parcialmente compartidas.', '',
        '| Agrupación | Grupos elegibles, promedio | Captura | Cambio frente a C actual | IC95 del cambio | Periodos con mejora | Cumple regla |',
        '|---|---:|---:|---:|---|---:|---|']
    for name in study.NAMES:
        s=summary[name]
        c=s.get('comparison')
        lines.append(f'| {study.NAMES[name]} | {fmt(s["structure"]["mean_eligible_groups"])} | {fmt(s["metrics"]["capture_percent"],"%")} | '
            f'{fmt(c["difference_pp"]," pp",True) if c else "Referencia"} | '
            f'{"["+fmt(c["ci95_pp"][0])+", "+fmt(c["ci95_pp"][1])+"] pp" if c else "—"} | '
            f'{str(s["winning_periods"])+" de 4" if c else "—"} | {("Sí" if s["meets_rule"] else "No") if c else "Referencia"} |')
    lines+=['', '**Regla declarada:** intervalo de mejora media de captura por encima de cero, '
        'mejora en al menos tres de cuatro periodos y error por grupo y grupo-mes que no empeore más de 0.1 pp '
        'frente a la prioridad actual evaluada en esa misma partición candidata. El escenario principal es '
        'añadir una variable a los cortes actuales; las otras familias y capacidades son diagnósticas.', '',
        'La mejora de la alternativa principal es pequeña. Su límite inferior del IC95 es positivo pero '
        'muy próximo a cero; el cumplimiento de la regla es marginal con las 500 réplicas declaradas. '
        'Ese resultado merece una lectura prudente y no establece superioridad universal.', '',
        'Captura = salidas observadas concentradas en la población priorizada / salidas observadas totales. '
        'La capacidad es idéntica por snapshot, usando pesos uniformes en el grupo del límite. '
        'Las diferencias se calculan antes del redondeo.', '',
        '![Cambio de captura e incertidumbre](cambio-captura.png)', '',
        '## Qué sucede con la precisión al dividir grupos', '',
        'Una partición más detallada puede revelar errores que se compensaban dentro de grupos grandes. '
        'La columna «control comparable» evalúa la prioridad de C actual sobre los mismos subgrupos usados por '
        'la alternativa. De ese modo, ambas prioridades se comparan con idéntica granularidad.', '',
        '| Agrupación | Error propio por grupo | Control comparable | Error propio grupo-mes | Control comparable grupo-mes | Estimado R6 en prioridad | Observado R6 en prioridad |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,s in summary.items():
        m,c=s['metrics'],s['control_on_same_partition']
        lines.append(f'| {study.NAMES[name]} | {fmt(m["group_mae_pp"]," pp")} | {fmt(c["group_mae_pp"]," pp")} | '
            f'{fmt(m["group_snapshot_mae_pp"]," pp")} | {fmt(c["group_snapshot_mae_pp"]," pp")} | '
            f'{fmt(m["predicted_percent"],"%")} | {fmt(m["observed_percent"],"%")} |')
    lines+=['', 'Error por grupo: diferencia absoluta entre estimado y observado por grupo, ponderada por personas. '
        'Error grupo-mes: se calcula antes de promediar meses, evitando que errores de distinto signo se cancelen. '
        'Son puntos porcentuales. Log-loss, Brier y ranking individual de C no cambian: esta búsqueda no reajusta el hazard.', '',
        '| Agrupación | Mayor error publicable, promedio | Cobertura publicable de la prioridad | Población en resto | Definiciones elegidas entre cuatro periodos |',
        '|---|---:|---:|---:|---:|']
    for name,s in summary.items():
        m=s['metrics']
        lines.append(f'| {study.NAMES[name]} | {fmt(m.get("worst_publishable_group_error_pp")," pp")} | '
            f'{fmt(m["publishable_group_exposure_percent"],"%")} | {fmt(s["structure"]["rest_percent"],"%")} | {s["distinct_definitions"]} |')
    lines+=['', 'El mayor error sólo incluye grupos cuyo observado es publicable. La cobertura puede diferir '
        'entre agrupaciones. Resto contiene grupos con menos de 300 personas por foto, fuera de la prioridad.', '',
        '## Variables seleccionadas y consistencia temporal', '',
        '| Origen del C y selección | Alternativa | Cruce seleccionado | Grupos en desarrollo, promedio | Fallback de desarrollo |',
        '|---|---|---|---:|---|']
    for fold in r['folds']:
        for name in ['C_plus1','C_four','C_near40']:
            s=fold['selections'][name]
            lines.append(f'| {fold["origin"]} | {study.NAMES[name]} | {definition(s["definition"])} | '
                f'{fmt(s.get("winner_metrics",{}).get("mean_eligible_groups"))} | {"Sí" if s["fallback"] else "No"} |')
    lines+=['', 'Si las selecciones cambian, las métricas evalúan la política de volver a seleccionar con el pasado; '
        'no prueban una sola combinación en los cuatro periodos. El archivo final conserva la selección '
        'del último origen evaluado, 1-ago-2025. No se reajusta hasta septiembre de 2026.', '',
        '| Fotos evaluadas | Cruces explorados | C actual: captura | + una variable | Cuatro variables | Búsqueda 30–50 grupos |',
        '|---|---:|---:|---:|---:|---:|']
    for fold in r['folds']:
        values=[fold['evaluation'][name]['scenarios']['30']['metrics']['capture_percent'] for name in study.NAMES]
        lines.append(f'| {fold["first_snapshot"]} a {fold["last_snapshot"]} | {fold["candidate_count"]} | '+' | '.join(fmt(v,'%') for v in values)+' |')
    lines+=['', '## Sensibilidad a la capacidad', '',
        '| Capacidad | Alternativa | Captura | Cambio frente a C actual | IC95 | Cumple regla |',
        '|---|---|---:|---:|---|---|']
    for cap in ['20','30','40']:
        for name in ['C_plus1','C_four','C_near40']:
            s=r['summary'][cap][name]; c=s['comparison']
            lines.append(f'| {cap}% | {study.NAMES[name]} | {fmt(s["metrics"]["capture_percent"],"%")} | '
                f'{fmt(c["difference_pp"]," pp",True)} | [{fmt(c["ci95_pp"][0])}, {fmt(c["ci95_pp"][1])}] pp | '
                f'{"Sí" if s["meets_rule"] else "No"} |')
    lines+=['', '### La granularidad útil depende de cuánta población se atiende', '',
        '**Al concentrar acciones en el 20%, las agrupaciones más detalladas sí muestran una señal favorable.** '
        'La política de seleccionar cuatro variables captura 33.2% de las salidas frente a 31.7% con los cortes '
        'actuales: +1.5 pp, IC95 [0.6, 2.3], y mejora en tres de cuatro periodos. '
        'La búsqueda de 30–50 grupos mejora 0.9 pp, IC95 [0.2, 1.8]. '
        'Ambas cumplen la regla para esa capacidad secundaria declarada.', '',
        'Para el 30%, la señal favorable corresponde a conservar los tres cortes y añadir una variable, '
        'con una ganancia mucho menor. Para el 40%, ninguna alternativa supera la regla. '
        'El número de grupos y el porcentaje de población atendida son decisiones distintas.', '']
    ext=r['extension']
    lines+=['', '## Foto madura adicional: febrero de 2026', '',
        f'Foto {ext["snapshot"]}, seguimiento hasta {ext["followup_end"]}, {ext["people"]} personas. '
        'Se aplican las selecciones de agosto de 2025; esta foto no se añade al promedio histórico ni se usa '
        'para escoger el cruce final.', '',
        '| Agrupación | Grupos elegibles | Resto | Captura al 30% | Estimado R6 | Observado R6 | Error grupo-mes |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,entry in ext['evaluation'].items():
        s,m=entry['structure'],entry['scenarios']['30']['metrics']
        lines.append(f'| {study.NAMES[name]} | {fmt(s["mean_eligible_groups"])} | {fmt(s["rest_percent"],"%")} | '
            f'{fmt(m["capture_percent"],"%")} | {fmt(m["predicted_percent"],"%")} | {fmt(m["observed_percent"],"%")} | {fmt(m["group_snapshot_mae_pp"]," pp")} |')
    lines+=['', '### Cortes finales y grupos completos', '',
        '| Alternativa | Definición aplicada | Cobertura sin grupo límite | Captura sin grupo límite | Cobertura con grupo límite | Captura con grupo límite |',
        '|---|---|---:|---:|---:|---:|']
    csvrows=[]
    for name,entry in ext['evaluation'].items():
        scenario=entry['scenarios']['30']
        low,high=scenario['whole_groups_excluding_boundary'],scenario['whole_groups_including_boundary']
        lines.append(f'| {study.NAMES[name]} | {definition(entry["definition"])} | {fmt(low.get("coverage_percent"),"%")} | '
            f'{fmt(low.get("capture_percent"),"%")} | {fmt(high.get("coverage_percent"),"%")} | {fmt(high.get("capture_percent"),"%")} |')
        for row in scenario['selected_groups']:
            csvrows.append({'variante':name,**row})
    keys=list(dict.fromkeys(k for row in csvrows for k in row))
    with (OUT/'grupos-prioritarios-febrero.csv').open('w',encoding='utf-8-sig',newline='') as h:
        writer=csv.DictWriter(h,fieldnames=keys); writer.writeheader(); writer.writerows(csvrows)
    lines+=['', 'Los grupos concretos de cada alternativa se guardan en `grupos-prioritarios-febrero.csv` '
        'y en `results.json`. Las tasas suprimidas permanecen vacías. Los tamaños del CSV son personas '
        'efectivas seleccionadas; pueden ser fraccionales por el peso del grupo del límite.', '',
        '## Recomendación para continuar', '',
        '- **Con capacidad cercana al 30%:** la alternativa para seguir revisando es '
        'antigüedad × salidas del equipo × nivel × adquisición registrada, con 23 grupos elegibles en '
        'febrero de 2026. Es la última selección de la política «añadir una variable»; no fue la '
        'combinación seleccionada en los cuatro periodos y su ganancia media es marginal.',
        '- **Con capacidad limitada al 20%:** la política de seleccionar cuatro variables merece consideración '
        'por su mayor captura en ese escenario. Su último cruce es nivel × última promoción × tiempo en '
        'el nivel × adquisición registrada, con 30 grupos en febrero de 2026. La cifra media de mejora '
        'evalúa las cuatro selecciones históricas, no sólo este último cruce.',
        '- Las alternativas orientadas a unos 40 grupos generaron 36 en la última foto y no mejoraron la '
        'captura al 30%. La granularidad debe elegirse por capacidad, evidencia y precisión, sin fijar '
        '40 como objetivo numérico.',
        '- La mayor fragmentación deja más población en grupos de menos de 300 personas. En febrero, '
        'resto pasa de 5.3% con los cortes actuales a 9.4% con la variable adicional y 16.2% con la '
        'búsqueda de 30–50 grupos. Es parte del coste de ese detalle.',
        '- «Adquisición registrada» describe el registro disponible. «Sin registro» no demuestra ausencia '
        'de adquisición ni identifica una causa de attrition. Las acciones requieren diagnóstico adicional.', '',
        '## Búsqueda, evidencia y límites', '',
        f'- Se exploraron {sum(f["candidate_count"] for f in r["folds"])} cruces entre los cuatro periodos '
        '(una misma definición puede aparecer en varios). Se usan todos los cruces de cuatro conceptos del '
        'espacio disponible en cada C; no todos los umbrales posibles.',
        '- Los tres conceptos actuales conservan sus cortes. Las variables adicionales usan las bandas originales '
        'del C de cada origen, con faltantes explícitos. Se excluyen calendario, interacciones y repeticiones de concepto. '
        'La búsqueda anterior empleaba cruces de dos/tres dimensiones y versiones más gruesas de algunas variables.',
        '- En desarrollo: máximo 50 grupos por foto, al menos 80% de población en grupos elegibles y mínimo '
        '300 personas por grupo y foto. La familia de aproximadamente 40 exige media de 30–50. '
        'Estos límites de desarrollo no garantizan el mismo número de grupos en fechas futuras.',
        '- Selección: seis fotos con seguimiento R6 terminado antes del origen; mayor captura al 30%, '
        'tolerancia 2% relativo; menor exceso de error grupo-mes frente al control comparable, tolerancia 0.1 pp; '
        'después menos grupos, mayor captura y nombre estable.',
        '- Fallback: cortes actuales si no hay candidato admisible en desarrollo o la población elegible externa '
        'no alcanza para atender 40%. Se registra sin reselección basada en las salidas externas.',
        '- Los IC95 usan 500 remuestreos pareados por persona y conservan sus ventanas. Son condicionales '
        'a modelos, selección y asignación fijados; no corrigen comparaciones múltiples ni garantizan estabilidad futura.',
        '- Las etiquetas de desarrollo participaron parcialmente en el ajuste del hazard C. Las salidas externas '
        'no eligen sus cortes. La evidencia es retrospectiva y conserva las limitaciones de las fuentes de C.',
        '- Los cortes de referencia proceden de una exploración histórica de B sobre periodos ya inspeccionados. '
        'Esa historia puede favorecer la referencia; este experimento no demuestra que se hayan agotado todas '
        'las agrupaciones posibles, incluyendo divisiones adaptativas de cada grupo.',
        f'- Fuente SQL: `{r["query"]}`, ejecutada el 8-oct-2026; conocimiento hasta {r["knowledge_boundary"]}. '
        'Se reprodujeron población, métricas C y los cortes actuales contra sus archivos originales.',
        f'- Tiempo: {fmt(r["elapsed_seconds"]/60)} minutos, incluidos {fmt(r["load_seconds"]/60)} de carga. '
        'Cero reajustes hazard. Cruces calculados con índices enteros y acumulaciones en memoria.',
        '- Plan: `docs/plans/engineering-c-fourway-groups-20261008.md`; configuración: `frozen-config.json`; '
        'selecciones y modelos de agrupación: `selected-groupings.json`; evidencia: `folds/`, '
        '`development-candidates/`, `analysis-checks.json`, `preservation.json` y `manifest.json`.',
        '- B, C, B + QVoice y C + QVoice conservan sus archivos. No se publican ni guardan filas, llaves o riesgos individuales. '
        'Los grupos expresan asociaciones predictivas; no efectos causales de acciones de retención.', '']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    plot(r,title)
    dest=OUT/'source/tools'/Path(__file__).name
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(__file__,dest)
    study.write(OUT/'visual-design.json',{'skill':'morgan-vis','audience':'Propietario del modelo; escoger agrupación para priorizar acciones',
        'message':title,'design':'Puntos e IC95 de diferencia de captura, cero como referencia; primaria azul y secundarias grises.',
        'alternatives':['Barras de captura absoluta: ocultan diferencias pequeñas sin mostrar incertidumbre.','Línea temporal: sólo cuatro periodos con selecciones distintas.'],
        'limitations':'Comparaciones retrospectivas múltiples; efectos condicionales a las selecciones; grupos no miden causalidad.'})
    m=study.base.read(OUT/'manifest.json'); m['status']='completed_analysis_and_report'
    m['files']={str(p.relative_to(OUT)):study.base.sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
    study.write(OUT/'manifest.json',m)
    print(title)


if __name__=='__main__': main()
