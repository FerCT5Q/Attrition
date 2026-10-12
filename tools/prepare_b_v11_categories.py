"""Materializa contratos y SQL de categorías V11; no ejecuta consultas."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'queries/profiles/engineering_b_v11_categories_person_month_20261011.sql'
CONCEPTS={
 'city':('Ciudad laboral','work_city','city_variants',"country IS NOT NULL AND city IS NOT NULL",'direct_field',
    'Distinguir ciudades dentro de países o códigos de oficina amplios.',
    'La ciudad registrada es laboral; no representa domicilio ni movilidad real.'),
 'labor-market':('Mercado laboral registrado','labor_market_detail','market_variants',"market IS NOT NULL",'direct_field',
    'Contrastar diferencias entre mercados laborales más allá de la región.',
    'Se modela la etiqueta registrada; no se acredita una delimitación económica externa.'),
 'arrangement':('Modalidad de trabajo del V11','work_arrangement_v11','arrangement_variants',"arrangement IS NOT NULL",'grouped_mapping',
    'Probar la agrupación de tres modalidades que se revisó en el playbook.',
    'La etiqueta de la foto no demuestra asistencia física ni resuelve las discrepancias de fechas de vigencia. No se extraen motivos sensibles.'),
 'acquisition':('Adquisición registrada, con detalle','acquisition_detail','acquisition_variants',"acquisition IS NOT NULL",'direct_field',
    'Contrastar adquisiciones concretas sin perder B ni usar valores posteriores a la foto.',
    'Sin registro no equivale a contratación orgánica. No se consolidan aliases sin evidencia.')
}


def main():
    prefix=SOURCE.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0]
    prefix=prefix.replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07')
    for name,(title,feature,variants,present,semantic,use,limitation) in CONCEPTS.items():
        query=ROOT/f'queries/audits/engineering_b_v11_{name}_20261011.sql'
        target=ROOT/f'config/b_playbook_v11_contracts/{name}.json'
        if query.exists() or target.exists():
            raise RuntimeError('No sobrescribir un contrato previo.')
        extra=''
        zero=['duplicate_keys','contradictory_cells','missing_encoding_violations']
        null_value='sin registro' if name=='acquisition' else '(unknown)'
        if name=='arrangement':
            extra=",\n SUM(CASE WHEN arrangement='ONSITE' AND work_arrangement_v11<>'Onsite' THEN 1\n" \
                  " WHEN arrangement='SHORT-TERM REMOTE WORK' AND work_arrangement_v11<>'Short-Term Remote Work' THEN 1\n" \
                  " WHEN arrangement NOT IN ('ONSITE','SHORT-TERM REMOTE WORK') AND work_arrangement_v11<>'Other offsite arrangements' THEN 1 ELSE 0 END) AS mapping_violations"
            zero.append('mapping_violations')
        sql=prefix+f"""
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 COUNT(DISTINCT snapshot_date) AS snapshots,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN {variants}<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN {present} THEN 1 ELSE 0 END) AS populated_rows,
 MIN(CASE WHEN {present} THEN snapshot_date END) AS first_observed_snapshot,
 COUNT(DISTINCT CASE WHEN {present} THEN {feature} END) AS categories,
 SUM(CASE WHEN NOT({present}) AND {feature}<>'{null_value}' THEN 1 ELSE 0 END) AS missing_encoding_violations{extra}
FROM encoded GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1;
"""
        query.write_text(sql,encoding='utf-8')
        contract={'schema_version':4,'id':name,'title':title,'feature':feature,
          'claim':'La representación conserva el valor de la foto sin conflictos, duplicación ni imputación con datos futuros.',
          'use':use,'semantic_type':semantic,'population':'Employee, Regular, activo, Engineering, sin RF360',
          'grain':'persona-foto mensual','known_at':'valor registrado en la misma foto; no rellenar con una foto posterior',
          'window':'2020-07-26 a 2026-09-07','history':'Se conserva la historia mensual disponible y sus estados sin dato; la primera fecha observada se recalcula en esta consulta.',
          'query':query.relative_to(ROOT).as_posix(),'source_query':SOURCE.relative_to(ROOT).as_posix(),
          'zero_fields':zero,'positive_fields':['person_snapshots'],'expected_rows':7,
          'acceptance_rule':'Siete años agregados, al menos 30 personas por fila, cero llaves duplicadas o contradictorias y cero violaciones del mapping/nulos. La cobertura no se fuerza.',
          'conclusion_if_pass':'Representación disponible para la prueba incremental; su utilidad predictiva aún no se conoce',
          'limitation':limitation,'action':'Agrupar categorías raras sólo con el entrenamiento y probar como B + X'}
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Cuatro contratos preparados; ejecutar y revisar uno por uno.')


if __name__=='__main__':
    main()
