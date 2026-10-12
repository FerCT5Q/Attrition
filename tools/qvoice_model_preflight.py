"""Inspección de metadata QVoice y HRDA antes de consultar agregados de empleados."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qvoice_model_data import ROOT, DEFAULT_CONFIG, inspect_sources, load_config, write_json, sha256_file, utc_now


def run(output: Path, config_path: Path = DEFAULT_CONFIG) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    config = load_config(config_path)
    metadata = inspect_sources(config)
    write_json(output / "source-metadata.json", metadata)
    sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))
    import run_readonly_query as helper
    query = ROOT / config.get("paths", {}).get(
        "portfolio_metadata_query", "queries/audits/qvoice_model_portfolio_metadata_20261006.sql"
    )
    sql = helper.validate_readonly(query.read_text(encoding="utf-8"))
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor() as cursor:
            cursor.execute(sql)
            names = [column[0] for column in cursor.description]
            rows = [dict(zip(names, values)) for values in cursor.fetchall()]
    write_json(output / "redshift-metadata.json", {"rows": rows, "query": str(query.relative_to(ROOT)), "sql_sha256": sha256_file(query), "executed_at": utc_now(), "metadata_only": True})
    print(f"Metadata de {len(metadata['waves'])} archivos y {len(rows)} columnas de HRDA guardada.", flush=True)
    for wave in metadata["waves"]:
        missing = [key for key, item in wave["mapping"].items() if key in {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12", "Q13", "Q17", "career"} and not item["binary_indices"]]
        print(f"{wave['year']}: componentes binarios ausentes {missing}; encabezados de fecha {wave['date_headers']}", flush=True)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve(), args.config.resolve())
