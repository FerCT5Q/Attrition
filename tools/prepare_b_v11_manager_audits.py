"""Congela auditorías separadas para contexto del manager a 6 y 18 intervalos."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011.sql'


def main():
    prefix=SOURCE.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0]
    prefix=prefix.replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07')
    common="""
, integrity AS (
 SELECT SUM(CASE WHEN n<>1 THEN 1 ELSE 0 END) AS duplicate_exposure_keys,
        SUM(CASE WHEN variants<>1 THEN 1 ELSE 0 END) AS contradictory_exposure_keys FROM workforce
), attribution_check AS (
 SELECT COUNT(*)-COUNT(DISTINCT employee_id::VARCHAR||'|'||term_date::VARCHAR) AS duplicate_attributions FROM attributions
)
SELECT EXTRACT(year FROM e.snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT e.employee_id) AS employee_count,
 MAX(i.duplicate_exposure_keys) AS duplicate_exposure_keys,
 MAX(i.contradictory_exposure_keys) AS contradictory_exposure_keys,
 MAX(a.duplicate_attributions) AS duplicate_attributions,
 SUM(CASE WHEN e.latest_known_date>e.snapshot_date THEN 1 ELSE 0 END) AS future_event_violations,
"""
    parts={
      'manager6':"""
 SUM(CASE WHEN e.manager_observed_expected6_band<>'(historia no confirmada)' THEN 1 ELSE 0 END) AS observable_rows,
 SUM(CASE WHEN e.manager_team_exits6_v11='2+' THEN 1 ELSE 0 END) AS two_plus_exit_rows,
 SUM(CASE WHEN e.oe6 IS NOT NULL AND (e.exposure6<=0 OR e.intervals6<1 OR e.intervals6>6 OR e.global_intervals6<>6 OR e.prior_rate<=0) THEN 1 ELSE 0 END) AS history_violations,
 SUM(CASE WHEN e.exits6<0 OR e.exits6>e.exposure6 OR e.expected6<0 OR e.expected6>e.exposure6 OR e.oe6<0 THEN 1 ELSE 0 END) AS bound_violations,
 SUM(CASE WHEN ABS(e.oe6-(1+(e.exits6-e.expected6)/(e.expected6+60*e.prior_rate)))>0.00000001 THEN 1 ELSE 0 END) AS independent_formula_mismatches
""",
      'manager18':"""
 SUM(CASE WHEN e.manager_above_average18<>'(historia no confirmada)' THEN 1 ELSE 0 END) AS observable_rows,
 SUM(CASE WHEN e.manager_above_average18='above benchmark' THEN 1 ELSE 0 END) AS above_benchmark_rows,
 SUM(CASE WHEN e.eligible18=1 AND (e.intervals18<>18 OR e.first18<>e.seq-18 OR e.last18<>e.seq-1 OR e.exposure18/18.0<4 OR e.exits18<2 OR e.exposure18<=0) THEN 1 ELSE 0 END) AS history_violations,
 SUM(CASE WHEN e.manager_above_average18='above benchmark' AND (e.eligible18<>1 OR e.rate18<1.3*e.benchmark) THEN 1
 WHEN e.manager_above_average18='not above benchmark' AND (e.eligible18<>1 OR e.rate18>=1.3*e.benchmark) THEN 1 ELSE 0 END) AS threshold_violations,
 SUM(CASE WHEN ABS(e.benchmark-e.independent_benchmark)>0.00000001 THEN 1 ELSE 0 END) AS independent_formula_mismatches
"""}
    for name,part in parts.items():
        query=ROOT/f'queries/audits/engineering_b_v11_{name}_20261011.sql'
        path=ROOT/f'config/b_playbook_v11_contracts/{name}.json'
        if query.exists() or path.exists():
            raise RuntimeError('La auditoría ya existe.')
        query.write_text(prefix+common+part+'FROM encoded e CROSS JOIN integrity i CROSS JOIN attribution_check a\nGROUP BY 1 HAVING COUNT(DISTINCT e.employee_id)>=30 ORDER BY 1;\n',encoding='utf-8')
        contract={'schema_version':4,'id':name,
          'title':'Contexto del manager a seis intervalos' if name=='manager6' else 'Rotación del equipo sobre benchmark a dieciocho intervalos',
          'claim':'Los eventos se asignan al equipo del inicio del intervalo y sólo se cuentan una vez conocidos en t.',
          'use':'Contrastar las definiciones históricas del V11 manteniendo todos los términos de B.',
          'semantic_type':'derived_feature','population':'Employee, Regular, activo y sin RF360 para exposición y benchmark; Engineering para la asignación final',
          'grain':'persona-foto; historia agregada del manager actual',
          'known_at':'Exposición en inicio del intervalo; primera observación del evento <= t, sin conflicto de tipo conocido en t',
          'window':'2020-07-26 a 2026-09-07, con 21 meses anteriores de contexto',
          'history':'Se reutiliza la definición V11, agregando la puerta explícita de conocimiento del evento para cada fecha. Historia insuficiente sigue desconocida.',
          'query':query.relative_to(ROOT).as_posix(),'source_query':SOURCE.relative_to(ROOT).as_posix(),
          'zero_fields':['duplicate_exposure_keys','contradictory_exposure_keys','duplicate_attributions','future_event_violations','history_violations','independent_formula_mismatches',
                         'bound_violations' if name=='manager6' else 'threshold_violations'],
          'positive_fields':['person_snapshots','observable_rows'],'expected_rows':7,
          'acceptance_rule':('Seis intervalos globales, estratos con al menos 30 exposiciones o fallback global, prior de 60 exposiciones y reconciliación O/E por identidad algebraica independiente.' if name=='manager6' else
              'Dieciocho intervalos contiguos, equipo medio >=4, al menos dos salidas; tasa >=1.3 veces benchmark ponderado, reconciliado con suma de tasas por pesos.')+' Cero duplicados, contradicciones, eventos futuros y diferencias de fórmula.',
          'conclusion_if_pass':'La representación respeta el contrato temporal y puede probarse como B + X',
          'limitation':'Describe exposición histórica, no causalidad ni evaluación del manager. Se excluyen eventos sin exposición inicial única y tipos conflictivos; no se publican identidades.',
          'action':'Probar cada representación por separado y mantener estados desconocidos'}
        path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Dos auditorías preparadas; ejecutar seis intervalos y terminar su revisión antes de dieciocho.')


if __name__=='__main__':
    main()
