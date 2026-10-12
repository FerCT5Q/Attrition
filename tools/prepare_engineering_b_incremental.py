"""Preflight de B incremental. Sólo metadata y agregados pueden salir del proceso."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.codex/skills/attrition-redshift-db/scripts'))
import run_readonly_query as db

OUT = ROOT / 'output/analysis/engineering/20261011/b-incremental-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str,
                               allow_nan=False) + '\n', encoding='utf-8')


def aggregate(query, target, claim, acceptance):
    if target.exists():
        raise RuntimeError('La evidencia ya existe; no se sobrescribe.')
    sql = db.validate_readonly(query.read_text(encoding='utf-8'))
    try:
        with db.connect() as conn:
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                cur.execute(sql)
                columns = [c[0] for c in cur.description]
                if set(columns) & db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('Columnas de salida restringidas.')
                rows = [dict(zip(columns, r)) for r in cur.fetchmany(1001)]
    except db.psycopg2.Error as exc:
        # No incluir SQL expandido ni detalle que pueda contener valores fuente.
        if isinstance(exc, db.psycopg2.errors.SyntaxError):
            raise RuntimeError(f'SQL guardado con error sintáctico: {exc.diag.message_primary}; posición {exc.diag.statement_position}.') from None
        raise RuntimeError(f'Consulta read-only incompleta ({type(exc).__name__}).') from None
    if len(rows) > 1000:
        raise RuntimeError('Resultado agregado excede el contrato de filas.')
    result = {'reporting_mode': 'presentation', 'executed_at': datetime.now(timezone.utc).isoformat(),
              'query': query.relative_to(ROOT).as_posix(), 'sql_sha256': sha(query),
              'claim': claim, 'acceptance_rule': acceptance, 'rows': rows,
              'employee_level_rows_persisted': False, 'assessment_score_changed': False}
    write(target, result)
    print(json.dumps({'query': result['query'], 'aggregate_rows': len(rows),
                      'result': target.relative_to(ROOT).as_posix()}, ensure_ascii=False), flush=True)
    return result


def finish_concept(name, result, contract, settings):
    okay = len(result['rows']) == 7 and all(all(r[c] == 0 for c in contract['zero_fields']) for r in result['rows'])
    result.update(outcome='pass' if okay else 'fail', contract=contract,
                  population=settings['population'], grain=settings['grain'],
                  date_window=[settings['start'], settings['knowledge_boundary']],
                  method='Consulta agregada guardada y regla de aceptación previa; resultado revisable por año.')
    target = OUT / f'input-evidence/{name}.json'
    write(target, result)
    result_hash = sha(target)
    narrative = f"# {name}: entrada del experimento B incremental\n\n"
    narrative += f"Modo `presentation`. {contract['history']}\n\n"
    narrative += f"Pregunta: ¿se sostiene esta entrada? {contract['claim']}\n\nMotivo: {contract['use']}\n\n"
    narrative += f"Tipo semántico: `{contract['semantic_type']}`. Conocimiento: {contract['known_at']}.\n\n"
    narrative += f"Población: {settings['population']}. Periodo: {settings['start']} a {settings['knowledge_boundary']}.\n\n"
    narrative += f"Método: `{contract['query']}`. Regla: cero en {', '.join(contract['zero_fields'])}; siete años agregados.\n\n"
    narrative += f"Resultado: **{result['outcome']}**. Métricas anuales completas en `{name}.json`.\n\n"
    narrative += f"Conclusión y acción: {'habilitar la representación experimental' if okay else 'resolver la brecha antes de modelar'}.\n\n"
    narrative += f"Límite: {contract['limitation']}\n\nImpacto en score: ninguno.\n\n"
    narrative += f"Ejecución: {result['executed_at']}. SHA256 del resultado: `{result_hash}`.\n"
    (OUT / f'input-evidence/{name}.md').write_text(narrative, encoding='utf-8')
    print(json.dumps({'concept': name, 'outcome': result['outcome'], 'rows': result['rows']}, ensure_ascii=False, default=str), flush=True)
    if not okay:
        raise RuntimeError('El concepto requiere revisión antes de continuar.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', action='store_true')
    parser.add_argument('--metadata-followup', action='store_true')
    parser.add_argument('--job-family', action='store_true')
    parser.add_argument('--concept')
    parser.add_argument('--finish-job-family', action='store_true')
    args = parser.parse_args()
    if args.metadata:
        aggregate(ROOT / 'queries/audits/engineering_b_incremental_metadata_20261011.sql',
                  OUT / 'input-evidence/portfolio-metadata.json',
                  'Localizar columnas para candidatas; no demostrar definición ni cobertura.',
                  'Metadata de hrda sin filas ni agregados de empleados; revisar presencia y tipo antes de cada contrato.')
    elif args.metadata_followup:
        aggregate(ROOT / 'queries/audits/engineering_b_incremental_metadata_followup_20261011.sql',
                  OUT / 'input-evidence/metadata-followup.json',
                  'Identificar fechas efectivas y posibles llaves; no confirmar su semántica.',
                  'Sólo metadata de columnas; timestamps técnicos no acreditan conocimiento histórico.')
    elif args.job_family:
        result = aggregate(ROOT / 'queries/audits/engineering_b_incremental_job_family_20261011.sql',
                           OUT / 'input-evidence/job-family-raw.json',
                           'Familia y grupo de puesto registrados en la foto de Engineering.',
                           'Cero duplicados, contradicciones, mappings ambiguos o desalineación de nulls; reportar cambios temporales.')
        okay = len(result['rows']) == 7 and all(all(r[c] == 0 for c in
            ['duplicate_keys','contradictory_cells','ambiguous_mappings','null_misalignment']) for r in result['rows'])
        result['outcome'] = 'pass' if okay else 'fail'
        write(OUT / 'input-evidence/job-family.json', result)
        print(json.dumps({'outcome': result['outcome'], 'rows': result['rows']}, ensure_ascii=False), flush=True)
        if not okay:
            raise RuntimeError('Revisar familia de puesto antes de continuar.')
    elif args.concept or args.finish_job_family:
        settings = json.loads((ROOT / 'config/engineering_b_incremental_inputs_20261011.json').read_text(encoding='utf-8'))
        name = args.concept or 'job-family'
        contract = settings['contracts'][name]
        raw = OUT / f'input-evidence/{name}-raw.json'
        if args.finish_job_family:
            result = json.loads(raw.read_text(encoding='utf-8'))
        else:
            result = aggregate(ROOT / contract['query'], raw, contract['claim'],
                               'Cero en ' + ', '.join(contract['zero_fields']))
        finish_concept(name, result, contract, settings)
    else:
        parser.error('Se requiere --metadata.')


if __name__ == '__main__':
    main()
