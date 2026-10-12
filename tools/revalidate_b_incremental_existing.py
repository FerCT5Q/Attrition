"""Revalidación secuencial de entradas heredadas, sin cambiar scores."""
from datetime import datetime, timezone
import json
from pathlib import Path

import engineering_model_c as base
from prepare_engineering_b_incremental import ROOT, OUT, aggregate, write, sha


def main():
    config = base.read(ROOT / 'config/engineering_b_incremental_20261011.json')
    for name in ['metadata','region','comp_ratio_band','grade_family','acquisition_recorded','transfer_12m','transfer_history']:
        base.audit(config,name)
    history = {
        'manager_recency': ('Cambios de manager observados a tres y seis meses; fechas efectivas y conocidas no posteriores a cada foto.',
                            ['monotonicity_violations','negative_count_violations']),
        'team_recency': ('Salidas voluntarias del equipo a tres y seis meses y fecha de última salida; mismo manager previo al evento.',
                         ['monotonicity_violations','last_event_consistency_violations','band_consistency_violations']),
        'manager_span': ('Tamaño reconstruido del equipo del manager actual en la misma foto; no es el campo de reportes del empleado.',
                         ['negative_span_violations']),
        'team_intensity': ('Salidas del equipo a doce meses por cien personas-mes de exposición bajo ese manager; sólo fechas pasadas.',
                           ['nonpositive_denominator_violations','numerator_exposure_violations'])
    }
    for name,(claim,zeros) in history.items():
        original = ROOT / f'queries/audits/engineering_model_d_{name}_20261010.sql'
        query = ROOT / f'queries/audits/engineering_b_incremental_{name}_20261011.sql'
        if query.exists():
            raise RuntimeError('No sobrescribir la evidencia histórica.')
        template = original.read_text(encoding='utf-8')
        if template.count("DATE '2025-01-01'") != 1:
            raise RuntimeError('Cambió la plantilla histórica.')
        query.write_text(template.replace("DATE '2025-01-01'", "DATE '2020-07-26'"),encoding='utf-8')
        result = aggregate(query,OUT / f'input-evidence/history-{name}-raw.json',claim,
                           'Cero en '+', '.join(zeros)+'; grain persona-snapshot, Engineering activo sin RF360.')
        okay = len(result['rows'])==1 and all(result['rows'][0][field]==0 for field in zeros)
        if name=='manager_span':
            okay = okay and result['rows'][0]['reconstructed_rows']==result['rows'][0]['manager_known_rows']
        result.update(outcome='pass' if okay else 'fail',semantic_type='derived_feature',
                      known_at='snapshot t',population='Employee, Regular, Engineering activo, sin RF360',
                      date_window=['2020-07-26','2026-09-07'],grain='persona-snapshot',
                      original_query=str(original.relative_to(ROOT)),original_sql_sha256=sha(original))
        write(OUT/f'input-evidence/history-{name}.json',result)
        narrative = f'# Historia: {name}\n\nSe amplía la revisión de la entrada de D a 2020–2026.\n\n'
        narrative += f'Pregunta: ¿la reconstrucción conserva el contrato? {claim}\n\nMotivo: probar su aporte individual sobre B.\n\n'
        narrative += f'Método y regla: `{query.relative_to(ROOT)}`; cero en {", ".join(zeros)}.\n\n'
        narrative += f'Observado: `{result["rows"][0]}`.\n\nConclusión: **{result["outcome"]}**.\n\n'
        narrative += 'Impacto en score: ninguno. Acción: '+('admitir como candidata experimental.' if okay else 'resolver la brecha antes de ajustar.')+'\n\n'
        narrative += f'Ejecución: {result["executed_at"]}. Población Engineering, Employee, Regular, activo, sin RF360; grain persona-snapshot.\n'
        (OUT/f'input-evidence/history-{name}.md').write_text(narrative,encoding='utf-8')
        print(json.dumps({'concept':name,'outcome':result['outcome'],'rows':result['rows']},default=str),flush=True)
        if not okay:
            raise RuntimeError('La reconstrucción histórica requiere revisión.')


if __name__=='__main__':
    main()
