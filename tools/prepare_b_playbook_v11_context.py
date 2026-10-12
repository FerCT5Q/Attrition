"""Correspondencia explícita V11/modelo y preflight de metadata, sin filas HR."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import engineering_model_c as base

ROOT = base.ROOT
OUT = ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1'
DECK = ROOT/'output/distribution/attrition-43-variable-distributions-v11.html'
MANIFEST = ROOT/'output/distribution/json/attrition-43-variable-distributions-v11-manifest.json'
QUERY = ROOT/'queries/audits/engineering_b_playbook_v11_metadata_20261011.sql'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')


# La correspondencia se razona por lámina; no se infiere por coincidencia de nombres.
MAPPING = {
 3:('parcial',['ios_12m'],'Desglosar los seis motivos del playbook, permitiendo solapamientos.'),
 4:('parcial',['region','work_country'],'Incorporar mercado laboral; no confundir región con mercado.'),
 5:('parcial',['work_arrangement_group'],'Contrastar la agrupación V11 de tres modalidades con la agrupación usada por C.'),
 6:('constante',[],'Engineering ya define la población; no discrimina dentro de ella.'),
 7:('B',['rehire'],'Conservar el indicador de B.'),
 8:('parcial',['acquisition_recorded'],'Probar la categoría de adquisición; sin registro no acredita contratación orgánica.'),
 9:('incluida',['prior_experience_band'],'Conservar las bandas de experiencia previa y su cobertura histórica.'),
 10:('preparación existente por incorporar',[],'Revisar la preparación geográfica y su vigencia histórica; derivar únicamente bandas en RAM.'),
 11:('preparación existente por incorporar',[],'Reconstruir temas de comentarios con taxonomía congelada y waves anteriores al año predicho.'),
 12:('incluida',['qv_M16','qv_M14'],'Intent to Stay: las preguntas se prueban por separado; aliases contados una sola vez.'),
 13:('incluida',['qv_career'],'Mantener la limitación de cambio de redacción en 2024.'),
 14:('incluida',['qv_mean33'],'Promedio de los 33 ítems comunes; no es el promedio de todas las preguntas de cada wave.'),
 15:('parcial',['time_at_level_band','time_in_job_profile_band'],'Revisar el tiempo en rol y el tiempo en nivel exactos; no equiparar etiquetas.'),
 16:('B',['tenure_playbook_band'],'Conservar las seis bandas de B.'),
 17:('B',['time_since_promotion_band'],'Conservar la historia de promoción de B.'),
 18:('parcial',['time_since_promotion_band','grade_family','compensation_grade_detail'],'La lámina cruza promociones de Annual Review y tasas por track; revisar fecha de conocimiento y entrada al grado, sin asumir equivalencia.'),
 19:('parcial',['layers_band'],'V11 tiene reconstrucción de jerarquía; el modelo usaba bandas de la capa almacenada.'),
 20:('B',['direct_reports_band'],'Conservar el tamaño directo de B; no confundirlo con todo el equipo del manager.'),
 21:('incluida',['comp_ratio_band'],'Razón almacenada por bandas; no afirmar validación de la fórmula de origen.'),
 22:('parcial',['team_exits_6m','team_exits_12m'],'Contrastar salidas bajo el manager histórico con la definición de compañeros de las features actuales.'),
 23:('incluida',['manager_left_6m'],'Salida previa del manager; fecha efectiva y conocida antes de t.'),
 24:('preparación existente por revisar',[],'Revisar aplicaciones registradas y enlace. Ausencia de enlace/feed no equivale a cero aplicaciones.'),
 25:('parcial',['work_country','work_site'],'Revisar las vistas de ubicación del playbook; no usar domicilios como categorías.'),
 26:('parcial',['work_site'],'Añadir ciudad laboral; algunos códigos de sitio representan un país entero.'),
 27:('parcial',['team_exits_3m','team_exits_6m','team_exit_recency_12m'],'El estudio por evento aporta una hipótesis; no se copia su outcome como predictor.'),
 28:('contexto', ['manager_team_size_band','team_exit_intensity_12m'],'La restricción a equipos de seis o más es una sensibilidad del estudio, no una variable individual adicional.'),
 29:('incluida',['job_family_detail','job_family_group'],'Probar detalle y grupo por separado con categorías raras agrupadas sólo en entrenamiento.'),
 30:('excluida',[],'Atributo protegido fuera de la autorización de predicción.'),
 31:('preparación existente por incorporar',[],'Reconstruir flags de temas y presencia de comentario; conservar falta de enlace y no comentario por separado.'),
 32:('limitación temporal por comprobar',[],'El Heartbeat relativo requiere sus preguntas de escala; no sustituirlo por respuestas binarias ni adelantar wave 2026.'),
 33:('B',['level_grouped'],'Conservar el nivel de B.'),
 34:('incluida',['grade_family','compensation_grade_detail'],'Se prueban familia y grado; documentar diferencia entre prefijo R/T y todos los tracks válidos.'),
 35:('contexto',['layers_band','compensation_grade_detail'],'El corte de 0–2 capas requiere la jerarquía reconstruida; es un cruce, no una nueva fuente.'),
 36:('incluida',['compensation_grade_detail'],'Código completo, sin importes.'),
 37:('incluida',['within_team_pay_position','manager_pay_spread_band'],'El cálculo activo usa pares comparables y recálculo independiente, sin importes fuera de SQL.'),
 38:('preparación existente por incorporar',[],'Reutilizar mapping de oficinas y zonas horarias, con fecha, DST y desconocidos explícitos.'),
 39:('parcial',['manager_location_relation'],'Contrastar categorías de sitio exactas de V11 con la representación ampliada sitio/ciudad/país.'),
 40:('preparación existente por incorporar',[],'El ratio observado/esperado tiene definición independiente: recalcular historia conocida, estratos y suavizado.'),
 41:('preparación existente por incorporar',[],'Flag de 18 intervalos con observabilidad y benchmark; no es la intensidad de salidas de 12 meses.'),
 42:('B',['manager_changes_12m'],'La existencia de un evento está representada por el conteo de B.'),
 43:('parcial',['manager_changes_12m','manager_changes_3m','manager_changes_6m'],'Revisar las definiciones de evento del playbook; conservar términos de B.'),
 44:('limitación temporal documentada',[],'La fecha efectiva/publicación del Talent index no está confirmada; revalidar metadata antes de decidir.'),
}


def main():
    if (OUT/'playbook-correspondence.json').exists():
        raise RuntimeError('El preflight ya existe; no sobrescribir.')
    deck_manifest = base.read(MANIFEST)
    if base.sha(DECK)!=deck_manifest['output']['deck_sha256']:
        raise RuntimeError('El playbook V11 cambió respecto de su manifest.')
    rows=[]
    for stage in deck_manifest['ordered_stages']:
        number=stage['slide_number']
        if number<3:
            continue
        state,features,note=MAPPING[number]
        rows.append({**stage,'priority':stage['group'].startswith('Prioritized'),
                     'current_representation':features,'current_status':state,'review_action':note})
    assert len(rows)==42 and {r['slide_number'] for r in rows}==set(MAPPING)
    OUT.mkdir(parents=True,exist_ok=True)
    prior=ROOT/'output/analysis/engineering/20261011/b-incremental-v2/input-evidence'
    shutil.copytree(prior,OUT/'input-evidence')
    write(OUT/'playbook-correspondence.json',{'reporting_mode':'presentation',
        'source':DECK.relative_to(ROOT).as_posix(),'source_sha256':base.sha(DECK),
        'manifest':MANIFEST.relative_to(ROOT).as_posix(),'manifest_sha256':base.sha(MANIFEST),
        'reviewed_at':datetime.now(timezone.utc).isoformat(),'rows':rows,
        'note':'El nombre 43 del playbook no implica una correspondencia 1:1 entre láminas y features; se conserva cada vista y su prioridad.'})
    lines=['# Correspondencia del playbook V11 con la ronda B + X','',
        'Modo `presentation`. Referencia señalada expresamente por el usuario. Esta tabla identifica brechas de implementación; no asigna scores de assessment.','',
        '| Slide | Vista del playbook | Prioritaria | Estado en la ronda interrumpida | Acción |',
        '|---:|---|---|---|---|']
    for row in rows:
        lines.append(f'| {row["slide_number"]} | {row["title"]} | {"Sí" if row["priority"] else "No"} | {row["current_status"]} | {row["review_action"]} |')
    (OUT/'correspondencia-playbook.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sql=QUERY.read_text(encoding='utf-8')
    with base.db.connect() as connection:
        connection.set_session(readonly=True,autocommit=True)
        with connection.cursor() as cursor:
            cursor.execute(base.db.validate_readonly(sql))
            columns=[c[0] for c in cursor.description]
            metadata=[dict(zip(columns,row)) for row in cursor.fetchall()]
    if len(metadata)>=500:
        raise RuntimeError('Metadata truncada.')
    write(OUT/'input-evidence/playbook-metadata.json',{
        'reporting_mode':'presentation','executed_at':datetime.now(timezone.utc).isoformat(),
        'query':QUERY.relative_to(ROOT).as_posix(),'sql_sha256':base.sha(QUERY),
        'semantic_type':'metadata','rows':metadata,'employee_rows_read':False,
        'assessment_score_changed':False,'outcome':'pass'})
    print(json.dumps({'v11_sha256_verified':True,'slides_mapped':len(rows),
        'priority_slides':sum(r['priority'] for r in rows),'metadata_fields':len(metadata),
        'output':OUT.relative_to(ROOT).as_posix()},ensure_ascii=False))


if __name__=='__main__':
    main()
