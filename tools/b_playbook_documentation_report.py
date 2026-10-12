"""Copia legible del informe congelado, con ejes compatibles con un decimal."""
from __future__ import annotations

import re
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator


def axis_label(value, position=None):
    rounded=round(float(value),1)
    return str(int(rounded)) if rounded.is_integer() else f'{rounded:.1f}'


def render(folder,out,config,results,candidates):
    """Lee sólo métricas agregadas; no cambia datos, selección ni artefactos previos."""
    checks=[]
    for family,periods,filename in [('RH',5,'variables-rh.png'),('QVoice',2,'variables-qvoice.png')]:
        rows=[r for r in candidates if r['family']==family and r['anchor']=='B'
              and r['evaluated_periods']==periods and r['brier_gain_relative_percent'] is not None]
        rows.sort(key=lambda r:r['brier_gain_relative_percent'])
        if not rows:
            raise RuntimeError('Faltan métricas comparables para el gráfico '+family)
        labels=[config['feature_labels'][r['feature']].replace('QVoice: ','') for r in rows]
        values=[r['brier_gain_relative_percent'] for r in rows]
        fig,ax=plt.subplots(figsize=(11,max(5,len(rows)*.34+1.6)))
        fig.patch.set_facecolor('#f7f9fc')
        ax.set_facecolor('#f7f9fc')
        ax.barh(range(len(rows)),values,color=['#147d92' if v>0 else '#b7c1ce' for v in values],height=.7)
        ax.axvline(0,color='#556476',lw=.8)
        ax.set_yticks(range(len(rows)),labels,fontsize=9)
        ax.xaxis.set_major_locator(MultipleLocator(.1))
        ax.xaxis.set_major_formatter(FuncFormatter(axis_label))
        ax.set_xlabel('Mejora relativa de Brier frente a B (%) · positivo mejora',fontsize=10)
        best=labels[-1]
        title=(best[0].upper()+best[1:]+' aporta la mayor reducción media de Brier'
               if values[-1]>0 else 'Las incorporaciones individuales no reducen Brier en promedio')
        ax.set_title(textwrap.fill(title,width=85)+'\n'+
                     f'{periods} periodos con historia suficiente; cada variable se añade por separado',
                     loc='left',fontsize=13,pad=16)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis='y',length=0)
        ax.grid(axis='x',color='#dde3eb',alpha=.65)
        ax.set_axisbelow(True)
        window='feb-2024 a feb-2026' if family=='RH' else 'ago-dic-2025 y ene-feb-2026'
        fig.text(.015,.027,'Engineering · empleados regulares activos, sin RF360 · '+window+
                 ' · salidas voluntarias en los seis meses siguientes.',fontsize=8,color='#556476')
        fig.text(.015,.012,'Fuente: ../candidate-summary.json y ../results.json · ejecución 12-oct-2026 · corte '+
                 config['knowledge_boundary']+'.',fontsize=8,color='#556476')
        fig.tight_layout(rect=(0,.055,1,1))
        fig.canvas.draw()
        left,right=ax.get_xlim()
        ticks=[x for x in ax.get_xticks() if left<=x<=right]
        displayed=[axis_label(x) for x in ticks]
        if len(displayed)!=len(set(displayed)):
            raise RuntimeError('El gráfico conserva etiquetas repetidas en el eje.')
        fig.savefig(folder/filename,dpi=170,facecolor=fig.get_facecolor())
        plt.close(fig)
        checks.append({'file':filename,'variables':len(rows),'tick_labels':displayed,
                       'ticks_are_unique':True,'source_values_unchanged':True})
    original=(out/'informe.md').read_text(encoding='utf-8')
    # Los gráficos revisados viven en el suplemento; las demás referencias
    # siguen apuntando a los resultados originales, un nivel arriba.
    report=re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)',
                  lambda match:'['+match[1]+'](../'+match[2]+')',original)
    first,body=report.split('\n',1)
    report=(first+'\n\n[Copia original y trazabilidad](../informe.md) · '
            '[Diccionario y decisiones por variable](diccionario.md)\n'+body)
    (folder/'informe.md').write_text(report,encoding='utf-8')
    return checks
