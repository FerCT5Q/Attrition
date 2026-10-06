"""Empaqueta el preflight agregado del hazard mensual de Critical Tech."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERY = ROOT / "queries" / "audits" / "critical_tech_hazard_preflight_20260907.sql"
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20260907"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SAFE_COLUMNS = {
    "seg",
    "employee_snapshot_intervals",
    "distinct_employees",
    "complete_snapshot_months",
    "first_snapshot",
    "last_next_snapshot",
    "positive_hazard_intervals",
    "hazard_rate_percent",
    "diagnostic_outcome",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", type=Path, default=DEFAULT_QUERY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    query = (ROOT / args.query).resolve() if not args.query.is_absolute() else args.query.resolve()
    output = (ROOT / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(query), "--max-rows", "100"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    unexpected = set(payload.get("columns", [])) - SAFE_COLUMNS
    if unexpected or payload.get("truncated"):
        raise ValueError(f"Resultado no publicable: columnas={sorted(unexpected)}, truncado={payload.get('truncated')}")

    result_path = output / "hazard-preflight-results.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = list(payload.get("rows", []))
    pass_rows = [r for r in rows if r.get("diagnostic_outcome") == "pass"]
    pooled_rows = [r for r in rows if r.get("diagnostic_outcome") != "pass"]
    lines = [
        "# Preflight del hazard mensual de Critical Tech",
        "",
        f"El diagnóstico agregado encontró **{len(pass_rows)} segmentos** con al menos 30 eventos positivos y 24 intervalos completos. **{len(pooled_rows)} segmentos** permanecen poolenados o suprimidos por volumen.",
        "",
        "La salida es una comprobación de observabilidad y volumen para el modelo "
        "de supervivencia discreta; no es todavía el ajuste pooled ni una relación causal.",
        "",
        "| Segmento | Exposiciones | Empleados | Meses | Eventos | Hazard agregado | Estado |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in pass_rows:
        lines.append(
            f"| {row.get('seg')} | {row.get('employee_snapshot_intervals')} | "
            f"{row.get('distinct_employees')} | {row.get('complete_snapshot_months')} | "
            f"{row.get('positive_hazard_intervals')} | {row.get('hazard_rate_percent')}% | "
            f"{row.get('diagnostic_outcome')} |"
        )
    lines.extend(
        [
            "",
            "## Regla aplicada",
            "",
            "- Target: Voluntary deduplicado entre el snapshot y el siguiente snapshot real.",
            "- Fecha de conocimiento: 2026-09-07.",
            "- Diagnóstico independiente: ≥30 eventos positivos y ≥24 intervalos completos.",
            "- Segmentos pequeños: participan en un modelo pooled, pero no se publican por separado.",
            "",
            "Fuente: `queries/audits/critical_tech_hazard_preflight_20260907.sql`.",
        ]
    )
    (output / "hazard-preflight-report.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "artifact": "critical-tech-hazard-preflight",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": "2026-09-07",
        "query": str(query.relative_to(ROOT)),
        "query_sha256": sha256(query),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": sha256(result_path),
        "pass_segment_count": len(pass_rows),
        "pooled_or_suppressed_segment_count": len(pooled_rows),
        "employee_level_rows_persisted": False,
    }
    (output / "hazard-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
