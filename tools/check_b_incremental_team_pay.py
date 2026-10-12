"""Reconciliación focalizada de una discrepancia de entradas, sólo agregados."""
from prepare_engineering_b_incremental import ROOT, OUT, aggregate, write
import sys

if '--independent' in sys.argv:
    result = aggregate(ROOT / 'queries/audits/engineering_b_incremental_team_pay_independent_20261011.sql',
                       OUT / 'input-evidence/team-pay-independent.json',
                       'Reconstruir grupos comparables directamente desde filas fuente, sin reutilizar los CTE del modelo.',
                       'Reconciliar conteos positivos y posición; detener dispersión mientras no coincidan.')
    print(result['rows'], flush=True)
    raise SystemExit(0)

prefix = (ROOT / 'queries/profiles/engineering_b_incremental_pending_person_month_20261011.sql').read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0].rstrip()
prefix = prefix.replace('__PERIOD_START__','2026-01-01').replace('__PERIOD_END__','2026-09-07')
mode = 'distinct' if '--distinct' in sys.argv else 'followup'
if mode == 'distinct':
    prefix = prefix.replace('COUNT(*) AS peer_n', 'COUNT(DISTINCT employee_id) AS peer_n')
    prefix = prefix.replace('COUNT(*) AS comparable_groups', 'COUNT(min_pay) AS comparable_groups')
query = ROOT / f'queries/audits/engineering_b_incremental_team_pay_{mode}_20261011.sql'
ending = """
SELECT (SELECT COUNT(*) FROM population) AS population_rows,
       (SELECT COUNT(*) FROM complete_pay) AS complete_pay_rows,
       (SELECT COUNT(*) FROM peer_stats WHERE peer_n>=2) AS peer_groups_ge2,
       (SELECT COUNT(*) FROM peer_stats WHERE peer_n>=5) AS peer_groups_ge5,
       (SELECT COUNT(*) FROM manager_spread) AS manager_spread_rows,
       (SELECT COUNT(*) FROM manager_spread WHERE comparable_groups>0) AS positive_spread_rows,
       (SELECT COUNT(*) FROM population p JOIN manager_spread s
          ON s.snapshot_date=p.snapshot_date AND s.manager_id=p.manager_id) AS exact_spread_matches,
       (SELECT COUNT(*) FROM population p JOIN peer_stats s
          ON s.snapshot_date=p.snapshot_date AND s.manager_id=p.manager_id WHERE s.peer_n>=2) AS direct_peer_matches
"""
if query.exists():
    raise RuntimeError('No sobrescribir la comprobación focalizada.')
query.write_text('/* Regla: existencia de grupos >=5 implica grupos >=2 y coincidencias de manager en la población elegible. */\n'+prefix+'\n'+ending+';\n',encoding='utf-8')
result = aggregate(query, OUT / f'input-evidence/team-pay-{mode}.json',
                   'Investigar cero coincidencias de dispersión pese a existir posiciones relativas comparables.',
                   'Grupos >=5 implican grupos >=2; reconciliar conteos antes de habilitar dispersión.')
print(result['rows'],flush=True)
