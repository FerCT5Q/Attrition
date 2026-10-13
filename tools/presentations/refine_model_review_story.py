"""Revisión colectiva: punto de partida, pruebas, mejoras y pendientes; nueve slides."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'output/presentations/20261013-0813_observaciones-originales-slide3'
OUT=ROOT/'output/presentations/20261013-0817_revision-modelo-inicial'
TEMPLATE=Path('C:/Users/fcarranz/.codex/skills/html-slide-generator/templates/fullscreen/base-fullscreen.html')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source=BASE/'presentacion-eng.html'; html=source.read_text(encoding='utf-8')
    old=BeautifulSoup(html,'html.parser')
    changes=[]
    def replace(selector,new_inner):
        nonlocal html
        node=old.select_one(selector); assert node is not None,selector
        before=str(node); assert html.count(before)==1,selector
        revised=BeautifulSoup(before,'html.parser').find()
        revised.clear(); revised.append(BeautifulSoup(new_inner,'html.parser'))
        html=html.replace(before,str(revised))
        changes.append({'selector':selector,'after':new_inner})

    replace('title','Engineering attrition — model improvement review')
    replace('#slide-3 .slide-title-text','We started with clear groups and five areas to improve')
    replace('#slide-3 .commit-card .side-head','Questions raised in the initial review')
    items=[
      ('Test an alternative model','Could random survival forest estimate risk better?'),
      ('Add relevant signals','Could QVoice and time at level improve the HR model?'),
      ('Require a measurable improvement','Compare capture and estimation error on the same people and periods.'),
      ('Reduce overestimation','Bring estimates closer to observed exits in the highest-risk group.'),
      ('Check fairness across groups','Assess differences in representation, coverage and error across segments.')]
    replace('#slide-3 .commits',''.join('<li><div class="cm-head">'+h+'</div><div class="cm-status">'+p+'</div></li>' for h,p in items))
    replace('#slide-3 .src','Group diagram: Engineering, 26 Jul 2026 · Initial review: limitations and questions guiding the tests on the following slides · S04, S02')
    # Da cierre al contraste de algoritmo sin presentar el resultado antes de la prueba.
    replace('#slide-8 .s8-note','Earlier RSF + QVoice tests did not improve CQ’s capture/error balance. Here, CQ retains its August HR fit in January; candidates use the January cutoff. CQ remains selected pending review.')
    replace('#slide-8 .src','Engineering · active regular employees, excl. RF360 · Aug–Dec 2025 and Jan–Feb 2026 · 6-month exits, overlapping snapshots · equal period weights · J03, S12 · Retrospective comparisons')
    replace('#slide-9 .next-after','Before a pilot: verify IOS/QVoice availability, assess segment differences and test a later cohort. Group intervals are not individual predictions. Actions are hypotheses; their effect is unmeasured. · J01, J02')
    new=BeautifulSoup(html,'html.parser')
    assert len(new.select('.slide-stage'))==len(new.select('.nav-pill'))==9
    assert 'julia' not in new.title.get_text().lower()
    assert 'julia' not in ' '.join(x.get_text() for x in new.select('.slide-stage')).lower()
    for n in [1,2,4,5,6,7]:
        assert str(old.select_one(f'#slide-{n}'))==str(new.select_one(f'#slide-{n}'))
    assert str(old.select_one('#slide-3 .split-card'))==str(new.select_one('#slide-3 .split-card'))
    for selector in ['#slide-8 table','#slide-9 .j-next-grid']:
        assert str(old.select_one(selector))==str(new.select_one(selector))
    assert [str(x) for x in old.select('script,style')]==[str(x) for x in new.select('script,style')]
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'presentacion-eng.html'; shutil.copy2(TEMPLATE,target); target.write_text(html,encoding='utf-8')
    shutil.copy2(TEMPLATE,OUT/'template-origin.html')
    shutil.copytree(BASE/'historical-evidence',OUT/'historical-evidence',dirs_exist_ok=True)
    evidence=json.loads((BASE/'evidence.json').read_text(encoding='utf-8'))
    for key in ['updated_statuses','original_followup_headers']:
        evidence.pop(key,None)
    evidence.update(revision_base=str(source.relative_to(ROOT)),revision_base_sha256=sha(source),
        deck_sha256=sha(target),changes=changes,unchanged_slides=[1,2,4,5,6,7],
        review_origin='Observaciones consolidadas de varias personas; sin atribución individual.',
        narrative='Modelo inicial y preguntas → pruebas y mejoras medidas → pendientes antes de uso RH.',
        left_group_diagram_unchanged=True,estimator_numbers_unchanged=True,replaces_deliverable=str(source.relative_to(ROOT)))
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'guion.md').write_text(
      '# Revisión conjunta del modelo: de los problemas a las mejoras\n\n'
      'Modo `presentation`. Los comentarios consolidan aportaciones de varias personas; '
      'no se atribuyen a una autora ni a un autor. Se conserva la presentación de nueve slides.\n\n'
      '| Slides | Función narrativa |\n|---|---|\n'
      '| 1–2 | Resumen ejecutivo y recorrido. |\n'
      '| 3 | Modelo inicial: grupos comprensibles y cinco temas por resolver. No adelanta estados finales. |\n'
      '| 4 | Primeras pruebas de encuesta y límites de esas alternativas. |\n'
      '| 5–7 | Mejoras medidas de B a C y CQ, funcionamiento y límites de cobertura/calibración. |\n'
      '| 8 | Pruebas posteriores; comparación BU/ciudad y cierre del contraste RSF. |\n'
      '| 9 | Capacidad y ficha RH; validación y preguntas aún pendientes. |\n\n'
      'Los cinco temas siguen siendo algoritmo alternativo, nuevas señales, mejora verificable, '
      'sobreestimación y equidad. Las lagunas de validación no se convierten en fallos demostrados: '
      'revisar equidad no significa que ya se haya probado un sesgo injustificado. Tampoco se afirma '
      'que todo quedó resuelto. Las cifras, grupos, intervalos, diseño y animaciones se conservan.\n\n'
      'Fuente del cierre RSF: S12; el balance de captura/error frente a CQ no mejoró. '
      'Las brechas de calibración y segmentos permanecen en J01/J02. No se hicieron nuevas consultas '
      'ni cambios de modelo.\n',encoding='utf-8')
    print(target)


if __name__=='__main__': main()
