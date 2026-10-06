"""Build aggregate metrics for internal-analysis or presentation HTML reports.

This utility reads frozen assessment artifacts and writes an optional
``private-aggregate-metrics.json`` beside each sensitive report.  It never
copies employee identifiers, names, addresses, free text, or exact compensation
into the output. In `presentation` mode it also anonymizes protected-category
labels. In explicitly requested `internal_analysis` mode it may retain real
stored categorical labels when every displayed bucket meets n >= 30. The
renderer uses this file only for explanatory charts; it does not alter
assessment scores.

For Gender, ``--refresh-gender`` executes the already-reviewed, aggregate-only
Redshift audit via the project read-only helper.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_RUN = Path("output/assessments/attrition-43-monthly-fiscal-20260816")
METRICS_FILENAME = "private-aggregate-metrics.json"
MINIMUM_COHORT = 30


EVENT_TITLES = {
    "Applied to a job": "Eventos de solicitud observados en el feed",
    "More than 3 job applications": "Eventos de solicitud observados en el feed",
    "High risk manager": "Terminaciones observadas en la fuente",
    "High turnover under this person": "Terminaciones observadas en la fuente",
}

EVENT_NOTES = {
    "More than 3 job applications": (
        "La prevalencia corresponde al evento fuente observado; no prueba ni "
        "reemplaza el conteo móvil validado de más de tres solicitudes."
    ),
    "High risk manager": (
        "La prevalencia corresponde al evento fuente; no existe una etiqueta "
        "aprobada de manager de alto riesgo."
    ),
    "High turnover under this person": (
        "La prevalencia corresponde al evento fuente; no equivale a una "
        "clasificación derivada de alta rotación sin umbral aprobado."
    ),
}

SURVEY_TITLES = {
    "Non-respondents": "Cobertura de la fuente de respuestas por wave",
    "Intent to Stay items": "Respuestas observables de los items de Intent to Stay",
    "Career goals item": "Respuestas observables del item Career goals",
    "Average of all Qvoice items": "Respuestas estructuradas observables de QVoice",
    "Standardized / normalized within region": "Respuestas estructuradas observables de QVoice",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construye métricas agregadas privadas para los HTML v2 sensibles."
    )
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument(
        "--refresh-gender",
        action="store_true",
        help="Ejecuta el audit agregado actual de Gender mediante el helper read-only.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe archivos private-aggregate-metrics.json existentes.",
    )
    parser.add_argument(
        "--reporting-mode",
        choices=("presentation", "internal_analysis"),
        default="presentation",
        help=(
            "presentation anonimiza etiquetas protegidas; internal_analysis "
            "conserva etiquetas categóricas agregadas para uso interno explícito."
        ),
    )
    parser.add_argument(
        "--variables",
        nargs="+",
        help="Opcional: carpetas de variables sensibles a procesar en este paso secuencial.",
    )
    return parser.parse_args(argv)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_number(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def as_int(value: Any) -> int:
    return int(round(as_number(value)))


def percentage(numerator: float, denominator: float) -> float | None:
    return round(100.0 * numerator / denominator, 4) if denominator else None


def annual_coverage(coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in coverage_rows:
        year = str(row.get("fiscal_year") or "Sin FY")
        group = groups.setdefault(
            year,
            {
                "fiscal_year": year,
                "snapshots": 0,
                "eligible": 0.0,
                "observable": 0.0,
                "missing": 0.0,
                "event": 0.0,
                "has_event": False,
            },
        )
        group["snapshots"] += 1
        group["eligible"] += as_number(row.get("eligible_employees"))
        group["observable"] += as_number(row.get("observable_employees"))
        group["missing"] += as_number(row.get("missing_employees"))
        if row.get("event_employees") is not None:
            group["event"] += as_number(row.get("event_employees"))
            group["has_event"] = True

    result: list[dict[str, Any]] = []
    for group in groups.values():
        observable = group["observable"]
        result.append(
            {
                "fiscal_year": group["fiscal_year"],
                "snapshots": group["snapshots"],
                "eligible": as_int(group["eligible"]),
                "observable": as_int(observable),
                "missing": as_int(group["missing"]),
                "coverage_percent": percentage(observable, group["eligible"]),
                "event_count": as_int(group["event"]) if group["has_event"] else None,
                "event_percent": percentage(group["event"], observable) if group["has_event"] else None,
            }
        )
    return result


def aggregate_totals(annual_rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = sum(as_number(row.get("eligible")) for row in annual_rows)
    observable = sum(as_number(row.get("observable")) for row in annual_rows)
    missing = sum(as_number(row.get("missing")) for row in annual_rows)
    has_event = any(row.get("event_count") is not None for row in annual_rows)
    event = sum(as_number(row.get("event_count")) for row in annual_rows) if has_event else None
    return {
        "fiscal_periods": len(annual_rows),
        "eligible": as_int(eligible),
        "observable": as_int(observable),
        "missing": as_int(missing),
        "coverage_percent": percentage(observable, eligible),
        "event_count": as_int(event) if event is not None else None,
        "event_percent": percentage(event or 0, observable) if event is not None else None,
    }


def metric_cards(totals: dict[str, Any], status: str) -> list[dict[str, Any]]:
    if status == "unavailable":
        return [
            {"label": "Cifras verificables", "value": "No disponibles", "note": "No existe una fuente aprobada."}
        ]
    cards = [
        {"label": "Observaciones agregadas", "value": totals["eligible"], "note": "Grain definido por la fuente."},
        {"label": "Cobertura agregada", "value": totals["coverage_percent"], "format": "percent", "note": "Observable / elegible."},
        {"label": "Datos faltantes", "value": totals["missing"], "note": "Registros agregados sin valor observable."},
        {"label": "Periodos fiscales", "value": totals["fiscal_periods"], "note": "Periodos con evidencia congelada."},
    ]
    if totals.get("event_count") is not None:
        cards[2] = {
            "label": "Eventos fuente", "value": totals["event_count"], "note": "No equivale necesariamente a la feature derivada.",
        }
    return cards


def query_rows(evidence: dict[str, Any], suffix: str) -> list[dict[str, Any]]:
    for query_name, rows in evidence.items():
        if str(query_name).endswith(suffix) and isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def top_value_distribution(
    evidence: dict[str, Any], title: str, note: str, reporting_mode: str
) -> dict[str, Any] | None:
    rows = query_rows(evidence, "report_top_values.sql")
    if not rows:
        return None
    values = [
        {
            "label": str(row.get("value_label") or "Sin etiqueta"),
            "count": as_int(row.get("employee_count")),
            "row_count": as_int(row.get("row_count")),
        }
        for row in rows
        if as_int(row.get("employee_count")) >= MINIMUM_COHORT
    ]
    if not values:
        return None
    values.sort(key=lambda item: (-item["count"], -item["row_count"]))
    total = sum(item["count"] for item in values)
    categories = [
        {
            "label": (
                item["label"]
                if reporting_mode == "internal_analysis"
                else f"BANDA {index + 1}"
            ),
            "count": item["count"],
            "percent": percentage(item["count"], total),
        }
        for index, item in enumerate(values[:10])
    ]
    return {
        "kind": (
            "internal_labeled_distribution"
            if reporting_mode == "internal_analysis"
            else "anonymized_distribution"
        ),
        "title": title,
        "subtitle": note,
        "categories": categories,
        "minimum_cohort": MINIMUM_COHORT,
    }


def numeric_band_distribution(report: dict[str, Any]) -> dict[str, Any] | None:
    rows = report.get("numeric_bands") or []
    categories = []
    for row in rows:
        count = as_int(row.get("employee_count"))
        if count < MINIMUM_COHORT:
            continue
        categories.append({"label": str(row.get("band_label") or "Banda"), "count": count})
    if not categories:
        return None
    total = sum(item["count"] for item in categories)
    for item in categories:
        item["percent"] = percentage(item["count"], total)
    return {
        "kind": "numeric_bands",
        "title": "Bandas agregadas de la métrica",
        "subtitle": "La métrica continua se presenta en bandas, no como valores individuales.",
        "categories": categories,
        "minimum_cohort": MINIMUM_COHORT,
    }


def event_distribution(variable: str, annual_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not any(row.get("event_count") is not None for row in annual_rows):
        return None
    categories = []
    for row in annual_rows:
        if row.get("event_count") is None:
            continue
        categories.append(
            {
                "label": row["fiscal_year"],
                "count": row["event_count"],
                "percent": row["event_percent"],
            }
        )
    return {
        "kind": "annual_event_prevalence",
        "title": EVENT_TITLES.get(variable, "Eventos fuente observados"),
        "subtitle": EVENT_NOTES.get(
            variable,
            "La cifra describe el evento fuente observado y no recalcula el score.",
        ),
        "categories": categories,
        "minimum_cohort": MINIMUM_COHORT,
    }


def survey_distribution(variable: str, annual_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not annual_rows:
        return None
    categories = [
        {
            "label": row["fiscal_year"],
            "count": row["observable"],
            "percent": row["coverage_percent"],
        }
        for row in annual_rows
        if as_int(row.get("eligible")) >= MINIMUM_COHORT
    ]
    if not categories:
        return None
    return {
        "kind": "survey_coverage",
        "title": SURVEY_TITLES[variable],
        "subtitle": "La cobertura de respuesta no confirma la escala, la definición ni la comparabilidad entre waves.",
        "categories": categories,
        "minimum_cohort": MINIMUM_COHORT,
    }


def run_gender_distribution(
    project_root: Path, reporting_mode: str
) -> dict[str, Any]:
    helper = project_root / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
    sql_name = (
        "gender_yearly_distribution_internal.sql"
        if reporting_mode == "internal_analysis"
        else "gender_yearly_distribution_safe.sql"
    )
    sql_file = project_root / "queries" / "audits" / sql_name
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(helper),
            "--sql-file",
            str(sql_file),
            "--max-rows",
            "100",
            "--reporting-mode",
            reporting_mode,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Falló el audit de Gender.")
    result = json.loads(completed.stdout)
    rows = [row for row in (result.get("rows") or []) if isinstance(row, dict)]
    if not rows:
        raise RuntimeError("El audit de Gender no devolvió filas agregadas.")
    return {"rows": rows, "query_reference": f"queries/audits/{sql_name}"}


def gender_metrics(
    result: dict[str, Any], reporting_mode: str
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    rows = result["rows"]
    annual: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in rows:
        year = str(row.get("fiscal_year") or "Sin FY")
        item = annual.setdefault(
            year,
            {
                "fiscal_year": year,
                "snapshots": None,
                "eligible": as_int(
                    row.get("populated_employees")
                    if reporting_mode == "internal_analysis"
                    else row.get("eligible_employee_snapshots")
                ),
                "observable": as_int(
                    row.get("populated_employees")
                    if reporting_mode == "internal_analysis"
                    else row.get("populated_employee_snapshots")
                ),
                "missing": (
                    0
                    if reporting_mode == "internal_analysis"
                    else as_int(row.get("missing_employee_snapshots"))
                ),
                "coverage_percent": (
                    100.0
                    if reporting_mode == "internal_analysis"
                    else as_number(row.get("coverage_percent"))
                ),
                "event_count": None,
                "event_percent": None,
                "categories": [],
            },
        )
        item["categories"].append(
            {
                "label": str(
                    row.get("gender")
                    if reporting_mode == "internal_analysis"
                    else row.get("anonymized_category")
                ),
                "count": as_int(
                    row.get("employee_count")
                    if reporting_mode == "internal_analysis"
                    else row.get("category_employee_snapshots")
                ),
                "percent": as_number(
                    row.get("percent_of_populated_employees")
                    if reporting_mode == "internal_analysis"
                    else row.get("percent_of_populated_employee_snapshots")
                ),
            }
        )
    annual_rows = list(annual.values())
    totals = aggregate_totals(annual_rows)
    all_categories: OrderedDict[str, int] = OrderedDict()
    for row in annual_rows:
        for category in row["categories"]:
            all_categories[category["label"]] = all_categories.get(category["label"], 0) + category["count"]
    category_total = sum(all_categories.values())
    distribution = {
        "kind": (
            "internal_category_yearly"
            if reporting_mode == "internal_analysis"
            else "anonymized_category_yearly"
        ),
        "title": (
            "Distribución anual de valores registrados"
            if reporting_mode == "internal_analysis"
            else "Distribución anual de códigos registrados"
        ),
        "subtitle": (
            "Análisis interno agregado; blanks se contabilizan como datos faltantes."
            if reporting_mode == "internal_analysis"
            else "Los códigos se anonimizan; blanks se contabilizan como datos faltantes."
        ),
        "categories": [
            {"label": label, "count": count, "percent": percentage(count, category_total)}
            for label, count in all_categories.items()
        ],
        "annual_categories": annual_rows,
        "minimum_cohort": MINIMUM_COHORT,
    }
    cards = metric_cards(totals, "available")
    cards[0] = {
        "label": (
            "Valores registrados"
            if reporting_mode == "internal_analysis"
            else "Códigos observados"
        ),
        "value": len(all_categories),
        "note": (
            "Etiquetas protegidas agregadas para análisis interno."
            if reporting_mode == "internal_analysis"
            else "Códigos no vacíos; etiquetas protegidas anonimizadas."
        ),
    }
    cards[3] = {"label": "Años fiscales", "value": len(annual_rows), "note": "Ventana cerrada al 2026-08-17."}
    return annual_rows, totals, {"cards": cards, "distribution": distribution}


def build_metrics(
    variable_dir: Path,
    gender_result: dict[str, Any] | None,
    reporting_mode: str,
) -> dict[str, Any]:
    assessment = read_json(variable_dir / "assessment.json")
    report = read_json(variable_dir / "report_detail.json")
    coverage = read_json(variable_dir / "coverage.json")
    evidence = read_json(variable_dir / "evidence" / "query-results.json")
    variable = str(assessment.get("variable") or variable_dir.name)
    annual_rows = annual_coverage(coverage)
    status = "available" if annual_rows else "unavailable"
    totals = aggregate_totals(annual_rows)
    distribution: dict[str, Any] | None = None
    limitations: list[str] = []
    evidence_refs = ["coverage.json", "evidence/query-results.json", "report_detail.json"]
    cards = metric_cards(totals, status)

    if variable == "Gender" and gender_result is not None:
        annual_rows, totals, gender = gender_metrics(gender_result, reporting_mode)
        cards = gender["cards"]
        distribution = gender["distribution"]
        status = "available"
        evidence_refs.append(gender_result["query_reference"])
        limitations.append(
            "La distribución es agregada y no confirma una definición de negocio ni autoriza uso predictivo."
        )
    elif variable == "Commute distance":
        status = "unavailable"
        cards = metric_cards(totals, status)
        limitations.append(
            "No existe una fuente aprobada de distancia ni un proxy geográfico autorizado; no se generan cifras."
        )
    elif variable == "Comp ratio":
        distribution = numeric_band_distribution(report)
        limitations.append(
            "Las bandas describen el campo almacenado; no validan su fórmula, midpoint ni lineage."
        )
    elif variable == "Compensation grade":
        distribution = top_value_distribution(
            evidence,
            (
                "Distribución agregada de grados registrados"
                if reporting_mode == "internal_analysis"
                else "Distribución agregada de bandas de grado"
            ),
            (
                "Análisis interno agregado con valores de grado almacenados."
                if reporting_mode == "internal_analysis"
                else "Los valores de grado se reemplazan por bandas anónimas ordenadas por frecuencia."
            ),
            reporting_mode,
        )
        limitations.append(
            "El grado es información de compensación gobernada; no se muestran valores de pago ni resultados individuales."
        )
    elif variable == "Within team compensation range":
        distribution = top_value_distribution(
            evidence,
            "Estructura de grado disponible para la derivación",
            "Es evidencia de soporte; no representa una distribución validada de la feature derivada.",
            reporting_mode,
        )
        limitations.append(
            "Aún no existe un cálculo validado de posición dentro del equipo; las cifras corresponden sólo a evidencia de soporte."
        )
    elif variable in EVENT_TITLES:
        distribution = event_distribution(variable, annual_rows)
        limitations.append(EVENT_NOTES.get(variable, "La cifra no recalcula ni confirma la feature derivada."))
    elif variable in SURVEY_TITLES:
        distribution = survey_distribution(variable, annual_rows)
        limitations.append(
            "Las cifras son de observabilidad agregada de la fuente y no sustituyen la validación de la escala ni de la wave."
        )

    if distribution is None and status != "unavailable":
        distribution = {
            "kind": "annual_coverage",
            "title": "Cobertura anual agregada",
            "subtitle": "La fuente no aporta una distribución publicable adicional para esta variable.",
            "categories": [
                {
                    "label": row["fiscal_year"],
                    "count": row["observable"],
                    "percent": row["coverage_percent"],
                }
                for row in annual_rows
            ],
            "minimum_cohort": MINIMUM_COHORT,
        }

    return {
        "schema_version": 1,
        # This file is intentionally a restricted aggregate input to the
        # assessment renderer.  The rendered report still obeys
        # ``reporting_mode`` and its n>=30 suppression policy, but the frozen
        # metrics bundle itself must carry the audience expected by that
        # renderer so it is never mistaken for a general presentation export.
        "audience": "private_aggregate",
        "reporting_mode": reporting_mode,
        "variable": variable,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": status,
        "population": assessment.get("population_filter"),
        "grain": assessment.get("level_data"),
        "minimum_cohort": MINIMUM_COHORT,
        "score_recalculated": False,
        "metric_cards": cards,
        "annual_series": annual_rows,
        "distribution": distribution,
        "limitations": limitations,
        "evidence_references": evidence_refs,
    }


def sensitive_variable_dirs(run_dir: Path) -> list[Path]:
    root = run_dir / "vars"
    result = []
    for variable_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        assessment_path = variable_dir / "assessment.json"
        if not assessment_path.is_file():
            continue
        assessment = read_json(assessment_path)
        if assessment.get("blocker_key") == "sensitive_restricted":
            result.append(variable_dir)
    return result


def select_sensitive_variable_dirs(
    run_dir: Path, selectors: list[str] | None
) -> list[Path]:
    directories = sensitive_variable_dirs(run_dir)
    if not selectors:
        return directories
    selected: list[Path] = []
    for selector in selectors:
        needle = selector.casefold().strip()
        matches = [
            path
            for path in directories
            if needle in {
                path.name.casefold(),
                path.name.split("-", 1)[-1].casefold(),
            }
        ]
        if len(matches) != 1:
            raise ValueError(
                f"El selector sensible '{selector}' produjo {len(matches)} coincidencias."
            )
        if matches[0] not in selected:
            selected.append(matches[0])
    return selected


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    run_dir = args.run_dir.resolve()
    variable_dirs = select_sensitive_variable_dirs(run_dir, args.variables)
    if not variable_dirs:
        raise ValueError("No se encontraron variables con blocker sensitive_restricted.")

    refresh_gender = args.refresh_gender and any(
        read_json(variable_dir / "assessment.json").get("variable") == "Gender"
        for variable_dir in variable_dirs
    )
    gender_result = (
        run_gender_distribution(project_root, args.reporting_mode)
        if refresh_gender
        else None
    )
    for variable_dir in variable_dirs:
        output = variable_dir / METRICS_FILENAME
        if output.exists() and not args.force:
            raise FileExistsError(f"Ya existe {output}; use --force para regenerarlo.")
        metrics = build_metrics(variable_dir, gender_result, args.reporting_mode)
        write_json(output, metrics)
        print(f"PASS {metrics['variable']}: {output}")
    print(f"Generated private aggregate metrics: {len(variable_dirs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
