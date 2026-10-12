"""Verificar lectura segura, plan SQL y esquema sin devolver filas de empleados."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from qvoice_model_data import ROOT, DEFAULT_CONFIG, load_config, sha256_file, utc_now, write_json
from qvoice_model_experiment import output_columns, write_model_sql
import critical_tech_discrete_hazard_model as hz


def verify(config: dict, destination: Path) -> dict:
    sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))
    import run_readonly_query as helper

    path = write_model_sql(config)
    # El valor es constante de prueba. No se devuelve ninguna llave ni respuesta.
    sql = hz.render_query(path.read_text(encoding="utf-8"), pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-31"))
    sql = helper.validate_readonly(sql.replace("__RUN_SALT__", "0" * 64))
    expected = output_columns(config)
    if set(expected) & helper.SENSITIVE_OUTPUT_COLUMNS:
        raise ValueError("El esquema propuesto contiene columnas restringidas.")
    forbidden_rejected = 0
    for forbidden in ("DELETE FROM source", "SELECT * FROM source", "SELECT 1; SELECT 2"):
        try:
            helper.validate_readonly(forbidden)
        except ValueError:
            forbidden_rejected += 1
    if forbidden_rejected != 3:
        raise ValueError("El helper no rechazó las consultas de prueba prohibidas.")
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXPLAIN " + sql)
                plan_line_count = len(cursor.fetchall())
                cursor.execute("SELECT " + ", ".join(expected) + " FROM (" + sql + ") contract_probe LIMIT 0")
                actual = [column[0] for column in cursor.description]
                if actual != expected or cursor.fetchone() is not None:
                    raise ValueError("El esquema no coincide o se obtuvo una fila de datos en la sonda vacía.")
        except helper.psycopg2.Error as error:
            raise RuntimeError(f"No se validó el plan SQL ({type(error).__name__}): {error.pgerror}") from None
    result = {"created_at": utc_now(), "reporting_mode": "presentation", "query": str(path.relative_to(ROOT)),
              "query_sha256": sha256_file(path), "sql_explain_passed": plan_line_count > 0, "plan_line_count": plan_line_count,
              "schema_passed": actual == expected, "columns": actual, "employee_rows_returned": 0,
              "forbidden_statements_rejected": forbidden_rejected, "helper": ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py",
              "scope": "EXPLAIN y SELECT con LIMIT 0; no ejecuta el entrenamiento ni acredita disponibilidad de QVoice."}
    write_json(destination, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = verify(load_config(arguments.config), arguments.output)
    print("Plan SQL y contrato de columnas verificados sin devolver filas de empleados.")
