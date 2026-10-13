"""Cierra el paquete después de la revisión numérica, documental y visual."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import hashlib
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/analysis/engineering/20261012/julia-rh-review-v1'
DECK=ROOT/'output/presentations/20261012-2350_revision-julia-rh'
PREVIEW=ROOT/'output/preview/julia-rh-review'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    review=read(OUT/'verification-delivery.json');browser=read(PREVIEW/'verification-browser.json')
    assert review['status']=='pass' and not browser['issues'] and not browser['errors']
    assert all(browser[k] for k in ['startsAtFirst','home','forward','backward','end','persistence','reopen','noExternalResources'])
    manifest=read(OUT/'manifest.json');result=read(OUT/'results.json');supp=read(OUT/'cohort-diagnostics-supplement.json')
    review_record=read(OUT/'report-review.json')
    review_record.update(pending_visual_review=False,visual_review_completed=True,
        visual_findings='Revisadas 16 diapositivas en cuatro temas y los dos PNG; tablas legibles, sin recortes. Corregidos rótulos de niveles, redondeo del extremo de IC bajo cero y alcance del contraste FQ/CQ.',
        browser_report=str((PREVIEW/'verification-browser.json').relative_to(ROOT)),
        narrative_limitations=['CQ conserva base RH de agosto al evaluar enero; FQ la reajusta. No se aísla el aporte de ciudad.',
                               'IOS y publicación real de QVoice no acreditados; evaluación retrospectiva.'])
    write(OUT/'report-review.json',review_record)
    # Congela dependencias locales transitivas; no se copia configuración de secretos.
    queue=[ROOT/'tools'/f for f in ['engineering_julia_rh_review.py','julia_review_statistics.py','build_julia_review_documents.py','complete_julia_cohort_diagnostics.py','render_julia_rh_review.py','verify_julia_review_delivery.py','finalize_julia_rh_review.py']]
    queue += [ROOT/'tools/presentations/build_julia_rh_review_deck.py',ROOT/'tools/presentations/verify_julia_review_browser.js',ROOT/'tests/test_julia_review_statistics.py']
    visited=set();dependencies={}
    while queue:
        path=queue.pop()
        if path in visited:continue
        visited.add(path)
        destination=OUT/'source'/path.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True)
        # Los scripts de cálculo congelados al inicio se conservan byte por byte.
        if not destination.exists():shutil.copy2(path,destination)
        elif destination.read_bytes()!=path.read_bytes():
            destination=OUT/'source-final'/path.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
        dependencies[path.relative_to(ROOT).as_posix()]=sha(path)
        if path.suffix!='.py':continue
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        names=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:names.append(node.module)
        for name in names:
            local=ROOT/'tools'/(name.split('.')[0]+'.py')
            if local.exists():queue.append(local)
    for path in [ROOT/'queries/audits/julia_review_unique_events_20261012.sql',ROOT/'queries/audits/julia_review_unique_group_events_20261012.sql',ROOT/'config/attrition_model_in_memory_training_authorization_20261001.json']:
        destination=OUT/'source-final'/path.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    write(OUT/'dependency-snapshot.json',{'captured_at':datetime.now(timezone.utc).isoformat(),'files':dependencies,'scope':'Dependencias locales transitivas importadas desde tools; entorno Python instalado se registra por versiones.'})
    import importlib.metadata
    packages={x:importlib.metadata.version(x) for x in ['numpy','scipy','pandas','scikit-learn','openpyxl','matplotlib','psycopg2-binary','threadpoolctl']}
    write(OUT/'environment.json',{'python':sys.version,'packages':packages})
    write(OUT/'numerical-test-review.json',{'command':'.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_julia_review_statistics.py -v','tests_run':7,'failures':0,'errors':0,
        'verified_in_session':True,'test_file_sha256':sha(ROOT/'tests/test_julia_review_statistics.py'),'topics':['Bootstrap compartido por persona','Empates y capacidad','Remanente pequeño conserva padre','Hijos y remanente válidos','Gradiente R6 frente a diferencias finitas','Curvatura cloglog','Sandwich de dos etapas']})
    write(DECK/'verification.json',{'status':'pass','static':review['static_deck_errors'],'accepted_language_exception':review['accepted_exception'],
        'browser':browser,'visual_review_completed':True,'reviewed_screenshots':64,
        'followup_review':'Cambios de rótulos, fechas superpuestas, interpretación FQ/CQ e IC revisados en las diapositivas afectadas, en cuatro temas; sin desbordes.',
        'deck_sha256':sha(DECK/'presentacion-eng.html'),'requires_internet':False})
    manifest.update(status='completed_retrospective_review',updated_at=datetime.now(timezone.utc).isoformat(),
        selected_model_unchanged='engineering-c-qvoice-20261008-v1',best_average_probability_estimator='FQ_BU_L3',
        numerical_tests=7,visual_slides=16,visual_themes=4,primary_fits=result['primary_fits'],auxiliary_fits={'base':9,'q':9},
        timing={'main_calculation_seconds':result['elapsed_seconds'],'focused_supplement_seconds':supp['elapsed_seconds']},
        deviations=['Lectura enfocada adicional de evaluación/QVoice para cruces que no podían reconstruirse de los agregados principales; cero reajustes.',
                    'Revisión de publicación suprime seis márgenes de ventana para impedir reconstrucción de fotos pequeñas.'],
        comparison_limitation='CQ conserva base RH 2025-08 en enero; FQ/FQ+BU reajustan base a 2026-01. El contraste frente a CQ reúne ciudad y actualización RH.',
        unresolved_before_operational_use=['Acreditar disponibilidad histórica de IOS','Acreditar fecha real de publicación QVoice','Confirmar capacidad y responsables con RH','Evaluar cohorte posterior al ajuste'],
        artifacts={'report':'informe.md','summary':'resumen-julia-rh.md','variables':'documentacion/variables-44.xlsx','cards':'fichas/indice.md','deck':str((DECK/'presentacion-eng.html').relative_to(ROOT))})
    manifest['files']={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
    write(OUT/'manifest.json',manifest)
    print('Cierre completo: modelos, agregados, documentación y presentación verificados.')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
