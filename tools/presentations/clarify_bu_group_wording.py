"""Aclara los dos usos de BU en una copia de la revisión de nueve slides."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'output/presentations/20261013-0735_revision-julia-9-slides'
OUT=ROOT/'output/presentations/20261013-0809_aclaracion-bu-grupos'
TEMPLATE=Path('C:/Users/fcarranz/.codex/skills/html-slide-generator/templates/fullscreen/base-fullscreen.html')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source=BASE/'presentacion-eng.html'; html=source.read_text(encoding='utf-8')
    changes={
      'Smaller BU groups':'BU subdivision: tested, not adopted',
      '100-person splits fail in the CQ/FQ review; retain base groups.':
        'Minimum-100 scenarios did not pass both periods. Base groups retained.',
      'Same people, dates and group definitions · lower log-loss means closer probabilities':
        'Same tenure × team exits × level groups; BU only adjusts risk · lower log-loss is better'
    }
    for before,after in changes.items():
        assert html.count(before)==1,before
        html=html.replace(before,after)
    old=BeautifulSoup(source.read_text(encoding='utf-8'),'html.parser')
    new=BeautifulSoup(html,'html.parser')
    assert len(new.select('.slide-stage'))==len(new.select('.nav-pill'))==9
    unchanged=[]
    for i in [1,2,4,5,6,7,9]:
        assert str(old.select_one(f'#slide-{i}'))==str(new.select_one(f'#slide-{i}'))
        unchanged.append(i)
    assert [x.get_text() for x in old.select('#slide-8 tbody td')]==[x.get_text() for x in new.select('#slide-8 tbody td')]
    assert [str(x) for x in old.select('script,style')]==[str(x) for x in new.select('script,style')]
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'presentacion-eng.html'; shutil.copy2(TEMPLATE,target)
    target.write_text(html,encoding='utf-8')
    shutil.copy2(TEMPLATE,OUT/'template-origin.html')
    shutil.copytree(BASE/'historical-evidence',OUT/'historical-evidence',dirs_exist_ok=True)
    evidence=json.loads((BASE/'evidence.json').read_text(encoding='utf-8'))
    evidence.update(revision_base=str(source.relative_to(ROOT)),revision_base_sha256=sha(source),
                    deck_sha256=sha(target),changes=changes,unchanged_slides=unchanged,
                    estimator_numbers_unchanged=True,group_definitions_unchanged=True,
                    replaces_deliverable=str(source.relative_to(ROOT)))
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'guion.md').write_text(
      '# Aclaración puntual: BU como predictor y como subdivisión\n\n'
      'Modo `presentation`. Se conserva el guion de nueve slides y todo su diseño. '
      'Se cambia únicamente la redacción en slides 3 y 8 para responder a la duda del usuario.\n\n'
      'En 3, se identifica la subdivisión BU como prueba no adoptada. En 8, se explicita '
      'que los modelos se comparan sobre grupos comunes de antigüedad × salidas del equipo × nivel; '
      'BU es predictor en las variantes que lo incorporan. No se cambia ninguna cifra.\n\n'
      'La revisión previa probó 27 escenarios de subdivisión: nueve con mínimo 100, '
      'ninguno admisible en ambos periodos. Sólo las sensibilidades de mínimo 150/200 '
      'con FQ + BU y capacidad 10% pasaron. Eso no respalda una subdivisión general. '
      'Fuente: J01, `subdivision`. La frase anterior “Smaller BU groups” era ambigua.\n',encoding='utf-8')
    print(target)


if __name__=='__main__': main()
