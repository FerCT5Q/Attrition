"""Restaura los cinco compromisos de la base en el panel derecho del slide 3."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'output/presentations/20261013-0809_aclaracion-bu-grupos'
ORIGINAL=ROOT/'output/presentations/20261012-0833_evolucion-b-cq-error-vs-c/presentacion-eng.html'
OUT=ROOT/'output/presentations/20261013-0813_observaciones-originales-slide3'
TEMPLATE=Path('C:/Users/fcarranz/.codex/skills/html-slide-generator/templates/fullscreen/base-fullscreen.html')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source=BASE/'presentacion-eng.html'; html=source.read_text(encoding='utf-8')
    current=BeautifulSoup(html,'html.parser')
    original=BeautifulSoup(ORIGINAL.read_text(encoding='utf-8'),'html.parser')
    panel=original.select_one('#slide-3 .commit-card')
    headers=[x.get_text() for x in panel.select('.cm-head')]
    states=[
        ('m-yes','✓ Done','Random survival forest was tested; CQ remains selected.'),
        ('m-yes','✓ Done','QVoice and time at level were evaluated — slides 5–7.'),
        ('m-part','◐ Under review','CQ remains selected; city and BU are candidates — slide 8.'),
        ('m-part','◐ Further work','Some groups remain overestimated; the scalar did not help.'),
        ('m-part','◐ Partial','Segment comparisons completed; fairness assessment remains open.')
    ]
    assert len(headers)==len(states)==5
    for node,(cls,label,text) in zip(panel.select('.cm-status'),states):
        node.clear(); node.append(BeautifulSoup(f'<span class="mark {cls}">{label}</span> — {text}','html.parser'))
    before=str(current.select_one('#slide-3 .commit-card'))
    assert html.count(before)==1
    html=html.replace(before,str(panel))
    old_source=current.select_one('#slide-3 .src').get_text()
    assert html.count(old_source)==1
    html=html.replace(old_source,'Group diagram: Engineering, 26 Jul 2026 · Original follow-ups, with evidence updated through 13 Oct 2026 · Segment differences alone do not establish unfair bias · S04, S12, S01, J01')
    revised=BeautifulSoup(html,'html.parser')
    assert headers==[x.get_text() for x in revised.select('#slide-3 .cm-head')]
    assert len(revised.select('.slide-stage'))==len(revised.select('.nav-pill'))==9
    for n in [1,2,4,5,6,7,8,9]:
        assert str(current.select_one(f'#slide-{n}'))==str(revised.select_one(f'#slide-{n}'))
    assert str(current.select_one('#slide-3 .split-card'))==str(revised.select_one('#slide-3 .split-card'))
    assert [str(x) for x in current.select('script,style')]==[str(x) for x in revised.select('script,style')]
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'presentacion-eng.html'; shutil.copy2(TEMPLATE,target); target.write_text(html,encoding='utf-8')
    shutil.copy2(TEMPLATE,OUT/'template-origin.html')
    shutil.copytree(BASE/'historical-evidence',OUT/'historical-evidence',dirs_exist_ok=True)
    evidence=json.loads((BASE/'evidence.json').read_text(encoding='utf-8'))
    evidence.update(revision_base=str(source.relative_to(ROOT)),revision_base_sha256=sha(source),
                    original_followups_source=str(ORIGINAL.relative_to(ROOT)),original_followups_sha256=sha(ORIGINAL),
                    original_followup_headers=headers,updated_statuses=states,
                    deck_sha256=sha(target),changes='Se restauran los cinco temas originales del panel derecho del slide 3; sólo se actualizan sus estados y la nota de fuente.',
                    unchanged_slides=[1,2,4,5,6,7,8,9],left_group_diagram_unchanged=True,
                    estimator_numbers_unchanged=True,replaces_deliverable=str(source.relative_to(ROOT)))
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'guion.md').write_text(
      '# Slide 3: observaciones originales y estado actualizado\n\n'
      'Modo `presentation`. Fuente de los cinco temas: panel “Since our last update” '
      'de la base de nueve slides del 12-oct a las 08:33. Se conserva cada encabezado '
      'exactamente y en su orden; no se presentan como transcripción literal de una '
      'conversación original.\n\n'
      'La revisión anterior sustituyó esa lista por una síntesis de análisis posteriores '
      'y añadió BU. Eso confundía compromisos anteriores con hallazgos nuevos. Se restaura '
      'el panel y se actualizan sólo los estados: RSF probado; QVoice y tiempo en nivel '
      'evaluados; candidatos nuevos por revisar; sobreestimaciones locales pendientes; '
      'comparaciones descriptivas por segmento realizadas sin dar por cerrada la evaluación de equidad.\n\n'
      'Evidencia: S12 (RSF/D), S01 (decisión vigente), J01 (calibración, grupos y segmentos). '
      'Se conserva el diagrama izquierdo, las cifras, las otras ocho slides, CSS y JavaScript.\n',encoding='utf-8')
    print(target)


if __name__=='__main__': main()
