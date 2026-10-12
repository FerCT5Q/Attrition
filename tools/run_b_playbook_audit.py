"""Ejecuta un contrato V11 por vez; conserva sólo evidencia agregada."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import engineering_model_c as base

ROOT = base.ROOT
OUT = ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1'


def execute(contract_path):
    path = Path(contract_path).resolve()
    contract = base.read(path)
    target = OUT/'input-evidence'/f"v11-{contract['id']}.json"
    if target.exists():
        raise RuntimeError('La evidencia ya existe; usar una revisión nueva.')
    rows,executions = [],[]
    for query_name in contract.get('queries',[contract['query']]):
        query = ROOT/query_name
        sql = base.db.validate_readonly(query.read_text(encoding='utf-8'))
        part_path = target.parent/(target.stem+'-parts')/(query.stem+'.json')
        if part_path.exists():
            saved = base.read(part_path)
            if saved['sql_sha256']!=base.sha(query):
                raise RuntimeError('Cambió una consulta con agregados ya conservados.')
            rows.extend(saved['rows'])
            executions.append({k:saved[k] for k in ['query','sql_sha256','executed_at','aggregate_rows']})
            print(f'Auditoría {contract["id"]}: se conserva la consulta ya completada {query.name}.',flush=True)
            continue
        try:
            with base.db.connect() as connection:
                connection.set_session(readonly=True, autocommit=True)
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [c[0] for c in cursor.description]
                    if set(columns) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                        raise RuntimeError('Salida restringida en auditoría.')
                    part = [dict(zip(columns,row)) for row in cursor.fetchmany(1001)]
            if len(part)>1000:
                raise RuntimeError('Consulta excede el límite de agregados.')
            rows.extend(part)
            executions.append({'query':query_name,'sql_sha256':base.sha(query),
                               'executed_at':datetime.now(timezone.utc).isoformat(),'aggregate_rows':len(part)})
            base.write(part_path,{**executions[-1],'rows':part,'employee_level_rows_persisted':False})
            if len(contract.get('queries',[]))>1:
                print(f'Auditoría {contract["id"]}: {len(executions)}/{len(contract["queries"])} consultas completadas.',flush=True)
        except base.db.psycopg2.Error as exc:
            if isinstance(exc,(base.db.psycopg2.errors.SyntaxError,base.db.psycopg2.errors.UndefinedColumn)):
                raise RuntimeError(f'SQL guardado inválido: {exc.diag.message_primary}; posición {exc.diag.statement_position}.') from None
            raise RuntimeError(f'Consulta read-only incompleta ({type(exc).__name__}).') from None
    if not rows or len(rows)>1000:
        raise RuntimeError('Resultado vacío o fuera del límite de agregados.')
    failures = []
    if 'expected_rows' in contract and len(rows)!=contract['expected_rows']:
        failures.append('número de filas')
    for column in contract.get('zero_fields',[]):
        if any(row[column] is None or row[column]!=0 for row in rows):
            failures.append(column)
    for column in contract.get('positive_fields',[]):
        if sum(float(row.get(column) or 0) for row in rows)<=0:
            failures.append(column)
    result = {'reporting_mode':'presentation','executed_at':datetime.now(timezone.utc).isoformat(),
              'query':contract['query'],'sql_sha256':base.sha(ROOT/contract['query']),'executions':executions,
              'contract_path':path.relative_to(ROOT).as_posix(),'contract_sha256':base.sha(path),
              'contract':contract,'rows':rows,'outcome':'pass' if not failures else 'fail',
              'failed_rules':failures,'employee_level_rows_persisted':False,'assessment_score_changed':False}
    base.write(target,result)
    text = f"# {contract['title']}\n\nModo `presentation`. {contract['history']}\n\n"
    text += f"Pregunta: {contract['claim']}\n\nMotivo: {contract['use']}\n\n"
    text += f"Tipo: `{contract['semantic_type']}`. Población: {contract['population']}. Grain: {contract['grain']}.\n\n"
    text += f"Conocimiento: {contract['known_at']}. Ventana: {contract['window']}.\n\n"
    text += f"Método y regla: {contract['acceptance_rule']} SQL: `{contract['query']}`.\n\n"
    text += f"Resultado: **{result['outcome']}**. Métricas completas en [{target.name}]({target.name}).\n\n"
    text += f"Conclusión: {contract['conclusion_if_pass'] if not failures else 'Se requiere resolver '+', '.join(failures)}.\n\n"
    text += f"Limitación: {contract['limitation']}\n\nAcción: {contract['action']}. Impacto en score: ninguno.\n\n"
    text += f"Ejecución: {result['executed_at']}. SHA256 SQL: `{result['sql_sha256']}`.\n"
    target.with_suffix('.md').write_text(text,encoding='utf-8')
    print(json.dumps({'concept':contract['id'],'outcome':result['outcome'],'rows':rows},ensure_ascii=False,default=str),flush=True)
    if failures:
        raise RuntimeError('Contrato pendiente; revisar antes de continuar.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    execute(parser.parse_args().contract)
