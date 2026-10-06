#!/usr/bin/env python
"""Profile attrition variables with aggregate, read-only, traceable evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import statistics
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import yaml

import portfolio_workflow as workflow


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RULES = SKILL_ROOT / "references" / "scoring-rules.yaml"
DEFAULT_QUERY_HELPER = (
    Path(__file__).resolve().parents[2]
    / "attrition-redshift-db"
    / "scripts"
    / "run_readonly_query.py"
)
QUERY_HELPER = Path(
    os.environ.get("VARIABLE_ASSESSMENT_QUERY_HELPER", str(DEFAULT_QUERY_HELPER))
).resolve()
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
EXPECTED_AGGREGATE_COLUMNS = {
    "snapshot_date",
    "eligible_employees",
    "observable_employees",
}
QUALITATIVE_CRITERIA = ("source", "definition", "consistency", "join", "effort")
CRITERION_LABELS = {
    "source": "Source",
    "definition": "Definition",
    "coverage": "Coverage",
    "missingness": "Missingness",
    "consistency": "Consistency",
    "history": "History",
    "join": "Join",
    "effort": "Effort",
}
RATIONALE_FIELDS = ("why", "evidence", "recommended_action")
VERIFICATION_FIELDS = (
    "method",
    "evidence",
    "result",
    "as_of_date",
    "query_reference",
    "acceptance_rule",
    "outcome",
)
DERIVATION_STATUSES = {"direct", "proposed", "testable", "validated", "blocked", "rejected"}
DERIVATION_STATUS_MAX_SCORE = {
    "direct": 2,
    "validated": 2,
    "testable": 1,
    "proposed": 1,
    "blocked": 0,
    "rejected": 0,
}
DERIVATION_REQUIRED_FIELDS = (
    "fields_and_tables",
    "formula",
    "grain",
    "temporal_window",
    "deduplication",
    "nulls_and_edge_cases",
    "leakage_controls",
    "snapshot_join",
    "sensitivity",
    "validations_needed",
    "estimated_effort",
    "decision_reason",
)
COMPARISON_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte"}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML object in {path}")
    return data


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def require_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def quoted_identifier(value: str, label: str = "identifier") -> str:
    return f'"{require_identifier(value, label)}"'


def quoted_table(value: str) -> str:
    parts = value.split(".")
    if len(parts) not in (1, 2):
        raise ValueError(f"Table must be table or schema.table: {value!r}")
    return ".".join(quoted_identifier(part, "table identifier") for part in parts)


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite values are not valid SQL literals.")
        return repr(value)
    if not isinstance(value, str):
        raise ValueError(f"Unsupported SQL literal: {value!r}")
    return "'" + value.replace("'", "''") + "'"


def nonblank_expression(column: str) -> str:
    col = quoted_identifier(column, "column")
    return f"NULLIF(TRIM(CAST({col} AS VARCHAR)), '') IS NOT NULL"


def filter_expression(item: dict[str, Any]) -> str:
    column = quoted_identifier(item["column"], "filter column")
    operator = str(item.get("operator", "eq")).lower()
    value = item.get("value")
    if operator == "eq":
        return f"{column} = {sql_literal(value)}"
    if operator == "ne":
        return f"{column} <> {sql_literal(value)}"
    if operator in {"gt", "gte", "lt", "lte"}:
        symbol = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[operator]
        return f"{column} {symbol} {sql_literal(value)}"
    if operator in {"in", "not_in"}:
        values = item.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(f"Filter {operator} requires a non-empty values list.")
        keyword = "IN" if operator == "in" else "NOT IN"
        return f"{column} {keyword} ({', '.join(sql_literal(v) for v in values)})"
    if operator == "is_null":
        return f"{column} IS NULL"
    if operator == "not_null":
        return f"{column} IS NOT NULL"
    raise ValueError(f"Unsupported filter operator: {operator}")


def population_clause(
    variable: dict[str, Any], rules: dict[str, Any]
) -> tuple[str, str]:
    population = variable.get("population") or {"mode": "default"}
    mode = str(population.get("mode", "default")).lower()
    filters: list[dict[str, Any]] = []

    if mode == "default":
        defaults = dict(rules["population"]["default"])
        defaults.update(population.get("overrides") or {})
        column_names = population.get("columns") or {}
        for key, value in defaults.items():
            if value is None:
                continue
            filters.append(
                {
                    "column": column_names.get(key, key),
                    "operator": "eq",
                    "value": value,
                }
            )
        display = population.get("display") or rules["population"]["display"]
    elif mode == "all":
        display = population.get("display") or "All source rows"
    elif mode == "custom":
        display = population.get("display")
        if not display:
            raise ValueError("Custom population requires a human-readable display value.")
    else:
        raise ValueError(f"Unknown population mode: {mode}")

    extra = population.get("filters") or []
    if not isinstance(extra, list):
        raise ValueError("population.filters must be a list.")
    filters.extend(extra)
    where = " AND ".join(filter_expression(item) for item in filters) or "1 = 1"
    return where, str(display)


def event_condition_expression(condition: dict[str, Any]) -> str:
    column_name = condition["column"]
    column = quoted_identifier(column_name, "event column")
    operator = str(condition.get("operator", "not_null")).lower()
    if operator == "not_null":
        return nonblank_expression(column_name)
    if operator == "eq":
        return f"{column} = {sql_literal(condition.get('value'))}"
    if operator == "in":
        values = condition.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("An event 'in' condition requires values.")
        return f"{column} IN ({', '.join(sql_literal(v) for v in values)})"
    if operator == "positive":
        return f"{column} > 0"
    raise ValueError(f"Unsupported event operator: {operator}")


def build_standard_sql(
    variable: dict[str, Any], rules: dict[str, Any]
) -> tuple[str, str]:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = source.get("table")
    if not table:
        raise ValueError(f"{variable.get('variable')}: standard mode requires source.table")
    source_columns = source.get("columns") or []
    observable_columns = measurement.get("observable_columns") or source_columns
    if not observable_columns:
        raise ValueError(
            f"{variable.get('variable')}: standard mode requires observable columns"
        )

    observable_mode = str(measurement.get("observable_mode", "all")).lower()
    if observable_mode not in {"all", "any"}:
        raise ValueError("measurement.observable_mode must be 'all' or 'any'.")
    connector = " AND " if observable_mode == "all" else " OR "
    observable = "(" + connector.join(nonblank_expression(c) for c in observable_columns) + ")"

    event_conditions = measurement.get("event_conditions") or []
    event_expression = None
    if event_conditions:
        event_mode = str(measurement.get("event_mode", "any")).lower()
        if event_mode not in {"all", "any"}:
            raise ValueError("measurement.event_mode must be 'all' or 'any'.")
        event_connector = " AND " if event_mode == "all" else " OR "
        event_expression = "(" + event_connector.join(
            event_condition_expression(item) for item in event_conditions
        ) + ")"

    date_column = quoted_identifier(
        measurement.get("date_column", "fis_mo_end_dt"), "date column"
    )
    employee_column = quoted_identifier(
        measurement.get("employee_id_column", "employee_id"), "employee ID column"
    )
    fiscal_year_name = measurement.get("fiscal_year_column", "fiscal_year")
    fiscal_year = (
        f"CAST({quoted_identifier(fiscal_year_name, 'fiscal year column')} AS VARCHAR(32))"
        if fiscal_year_name
        else "CAST(NULL AS VARCHAR(32))"
    )
    where, population_display = population_clause(variable, rules)
    event_select = (
        f"COUNT(DISTINCT CASE WHEN {event_expression} THEN {employee_column} END)"
        if event_expression
        else "CAST(NULL AS BIGINT)"
    )
    minimum_cohort = int(rules["population"]["minimum_shared_cohort"])

    sql = f"""
SELECT
  CAST({date_column} AS DATE) AS snapshot_date,
  {fiscal_year} AS fiscal_year,
  COUNT(DISTINCT {employee_column}) AS eligible_employees,
  COUNT(DISTINCT CASE WHEN {observable} THEN {employee_column} END) AS observable_employees,
  {event_select} AS event_employees
FROM {quoted_table(str(table))}
WHERE {where}
  AND {date_column} IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT {employee_column}) >= {minimum_cohort}
ORDER BY 1
""".strip()
    return sql, population_display


def configure_query_helper(path: str | Path | None) -> Path:
    """Select the project query adapter without coupling the engine to one database skill."""
    global QUERY_HELPER
    if path:
        QUERY_HELPER = Path(path).resolve()
    return QUERY_HELPER


def load_query_helper():
    if not QUERY_HELPER.exists():
        raise FileNotFoundError(
            "Required read-only query helper is missing: " + str(QUERY_HELPER)
        )
    module_spec = importlib.util.spec_from_file_location(
        "variable_assessment_readonly_query", QUERY_HELPER
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Could not load read-only query helper at {QUERY_HELPER}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def run_aggregate_query(sql: str, max_rows: int = 1000) -> list[dict[str, Any]]:
    helper = load_query_helper()
    guarded_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(guarded_sql)
            if cursor.description is None:
                return []
            columns = [description.name for description in cursor.description]
            sensitive = sorted(
                {column.lower() for column in columns}
                & set(helper.SENSITIVE_OUTPUT_COLUMNS)
            )
            if sensitive:
                raise ValueError(
                    "Aggregate query exposes blocked columns: " + ", ".join(sensitive)
                )
            rows = [dict(row) for row in cursor.fetchmany(max_rows + 1)]
            if len(rows) > max_rows:
                raise ValueError(
                    f"Aggregate query returned more than {max_rows} rows; narrow the date grain."
                )
            return rows


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def integer(value: Any, label: str) -> int:
    if value is None or value == "":
        return 0
    result = int(value)
    if result < 0:
        raise ValueError(f"{label} cannot be negative.")
    return result


def coverage_score(percent: float | None, rules: dict[str, Any]) -> int:
    if percent is None:
        return 0
    config = rules["coverage"]
    if percent >= float(config["score_2_min_percent"]):
        return 2
    if percent >= float(config["score_1_min_percent"]):
        return 1
    return 0


def normalize_rows(
    raw_rows: Iterable[dict[str, Any]], rules: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    minimum = int(rules["population"]["minimum_shared_cohort"])
    threshold = float(rules["usable_history"]["coverage_threshold_percent"])
    event_suppression = int(rules["privacy"]["suppress_event_counts_below"])
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_dates: set[date] = set()

    for raw in raw_rows:
        lowered = {str(key).lower(): value for key, value in raw.items()}
        missing = EXPECTED_AGGREGATE_COLUMNS - set(lowered)
        if missing:
            raise ValueError(
                "Aggregate result is missing required column(s): " + ", ".join(sorted(missing))
            )
        snapshot_date = parse_date(lowered["snapshot_date"])
        if snapshot_date is None:
            continue
        if snapshot_date in seen_dates:
            raise ValueError(
                f"Aggregate result has duplicate snapshot_date {snapshot_date}; return one row per date."
            )
        seen_dates.add(snapshot_date)
        eligible = integer(lowered["eligible_employees"], "eligible_employees")
        observable = integer(lowered["observable_employees"], "observable_employees")
        if eligible < minimum:
            warnings.append(
                f"Suppressed {snapshot_date}: eligible cohort {eligible} is below {minimum}."
            )
            continue
        if observable > eligible:
            raise ValueError(
                f"observable_employees exceeds eligible_employees on {snapshot_date}."
            )

        event_value = lowered.get("event_employees")
        event = None if event_value in (None, "") else integer(event_value, "event_employees")
        if event is not None and event > observable:
            raise ValueError(
                f"event_employees exceeds observable_employees on {snapshot_date}."
            )

        coverage = (observable / eligible * 100.0) if eligible else None
        event_prevalence = (
            event / observable * 100.0
            if event is not None and observable
            else None
        )
        row_notes = str(lowered.get("notes") or "").strip()
        event_suppressed = event is not None and 0 < event < event_suppression
        if event_suppressed:
            suffix = f"Event metrics suppressed (n<{event_suppression})."
            row_notes = f"{row_notes} {suffix}".strip()
            event = None
            event_prevalence = None

        rows.append(
            {
                "snapshot_date": snapshot_date.isoformat(),
                "fiscal_year": lowered.get("fiscal_year"),
                "eligible_employees": eligible,
                "observable_employees": observable,
                "missing_employees": eligible - observable,
                "observable_coverage_percent": round(coverage, 4) if coverage is not None else None,
                "coverage_score": coverage_score(coverage, rules),
                "event_employees": event,
                "event_prevalence_percent": (
                    round(event_prevalence, 4) if event_prevalence is not None else None
                ),
                "stable_at_threshold": bool(coverage is not None and coverage >= threshold),
                "notes": row_notes,
            }
        )

    rows.sort(key=lambda item: item["snapshot_date"])
    return rows, warnings


def first_usable_date(rows: list[dict[str, Any]], rules: dict[str, Any]) -> date | None:
    threshold = float(rules["usable_history"]["coverage_threshold_percent"])
    count = int(rules["usable_history"]["consecutive_observations"])
    if count < 1:
        raise ValueError("usable_history.consecutive_observations must be positive.")
    for index in range(0, len(rows) - count + 1):
        window = rows[index : index + count]
        if all(
            item["observable_coverage_percent"] is not None
            and float(item["observable_coverage_percent"]) >= threshold
            for item in window
        ):
            return parse_date(rows[index]["snapshot_date"])
    return None


def classify_cadence(dates: list[date], rules: dict[str, Any]) -> str:
    if not dates:
        return "not_validated"
    if len(dates) == 1:
        return "single_wave"
    gaps = [(right - left).days for left, right in zip(dates, dates[1:])]
    config = rules["frequency"]
    required_ratio = float(config["minimum_matching_gap_ratio"])
    candidates = (
        ("monthly", config["monthly_gap_days"]),
        ("quarterly", config["quarterly_gap_days"]),
        ("annual", config["annual_gap_days"]),
    )
    matches = []
    for name, bounds in candidates:
        low, high = int(bounds[0]), int(bounds[1])
        ratio = sum(low <= gap <= high for gap in gaps) / len(gaps)
        matches.append((ratio, name))
    ratio, name = max(matches)
    if ratio >= required_ratio:
        return name
    median = statistics.median(gaps)
    return f"irregular (mediana del intervalo: {median:g} días)"


def observation_frequency(
    rows: list[dict[str, Any]], measurement: dict[str, Any], rules: dict[str, Any]
) -> str:
    override = measurement.get("frequency_override")
    if override:
        return str(override)
    kind = str(measurement.get("type", "snapshot")).lower()
    dates = [parse_date(item["snapshot_date"]) for item in rows]
    cadence = classify_cadence([item for item in dates if item], rules)
    if kind in {"external", "unavailable"} or cadence == "not_validated":
        return "No validada"
    if cadence == "single_wave":
        return "Una sola wave"

    cadence_title = {
        "monthly": "Mensual",
        "quarterly": "Trimestral",
        "annual": "Anual",
    }.get(cadence, cadence.capitalize())
    if kind == "snapshot":
        return f"Snapshot {cadence_title.lower()}"
    if kind == "event":
        return f"Orientada a eventos; captura {cadence_title.lower()}"
    if kind in {"rolling_derived", "derived"}:
        return f"Derivada {cadence_title.lower()}"
    if kind == "survey":
        return f"Encuesta {cadence_title.lower()}"
    return cadence_title


def weighted_recent_coverage(
    rows: list[dict[str, Any]], count: int
) -> float | None:
    window = rows[-count:] if count > 0 else rows
    eligible = sum(int(item["eligible_employees"]) for item in window)
    observable = sum(int(item["observable_employees"]) for item in window)
    return observable / eligible * 100.0 if eligible else None


def automatic_systematic_missingness(
    rows: list[dict[str, Any]], rules: dict[str, Any]
) -> bool:
    config = rules["missingness"]
    count = int(config["systematic_window_observations"])
    values = [
        float(item["observable_coverage_percent"])
        for item in rows[-count:]
        if item["observable_coverage_percent"] is not None
    ]
    if len(values) < 2:
        return False
    return max(values) - min(values) > float(config["systematic_range_percent_points"])


def elapsed_months(start: date | None, end: date | None) -> float:
    if not start or not end or end < start:
        return 0.0
    completed = (end.year - start.year) * 12 + end.month - start.month
    if end.day < start.day:
        completed -= 1
    return float(max(completed, 0))


def status_score(
    criterion: str, status: str | None, rules: dict[str, Any], variable_name: str
) -> int:
    if not status:
        raise ValueError(f"{variable_name}: missing evidence status for {criterion}")
    options = rules["criteria"][criterion]
    if status not in options:
        raise ValueError(
            f"{variable_name}: invalid {criterion} status {status!r}; "
            f"choose one of {', '.join(options)}"
        )
    return int(options[status]["score"])


def text_value(value: Any) -> str:
    return str(value or "").strip()


def project_sql_reference(
    query_reference: Any, variable_name: str, context: str
) -> str:
    query_text = text_value(query_reference).split("#", 1)[0].strip()
    query_path = Path(query_text)
    allowed_roots = [
        (PROJECT_ROOT / "queries" / "audits").resolve(),
        (PROJECT_ROOT / "queries" / "profiles").resolve(),
    ]
    resolved_query = (PROJECT_ROOT / query_path).resolve()
    if (
        not query_text
        or query_path.is_absolute()
        or query_path.suffix.lower() != ".sql"
        or not any(resolved_query.is_relative_to(root) for root in allowed_roots)
        or not resolved_query.is_file()
    ):
        raise ValueError(
            f"{variable_name}: {context} query_reference must point to an existing "
            "project-relative SQL file under queries/audits/ or queries/profiles/."
        )
    return query_text


def compare_numeric(observed: float, operator: str, threshold: float) -> bool:
    if operator == "eq":
        return observed == threshold
    if operator == "ne":
        return observed != threshold
    if operator == "gt":
        return observed > threshold
    if operator == "gte":
        return observed >= threshold
    if operator == "lt":
        return observed < threshold
    if operator == "lte":
        return observed <= threshold
    raise ValueError(f"Unsupported validation operator: {operator}")


def is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def direct_field_available(variable: dict[str, Any]) -> bool:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    profile = variable.get("profile") or {}
    source_columns = source.get("columns") or []
    if isinstance(source_columns, str):
        source_columns = [source_columns]
    direct_flag = source.get("direct_field", True)
    measurement_type = str(measurement.get("type", "snapshot")).lower()
    profile_mode = str(profile.get("mode", "standard")).lower()
    return (
        direct_flag is not False
        and str(source.get("status") or "") == "confirmed_accessible"
        and bool(source_columns)
        and measurement_type not in {"derived", "rolling_derived", "external", "unavailable"}
        and profile_mode not in {"external", "unavailable"}
    )


def derivation_field_value(option: dict[str, Any], field: str) -> Any:
    aliases = {
        "fields_and_tables": ("fields_tables", "fields", "inputs"),
        "nulls_and_edge_cases": ("null_handling", "edge_cases"),
        "snapshot_join": ("join_with_snapshot", "join"),
        "decision_reason": ("selection_reason", "reason"),
    }
    if field in option:
        return option[field]
    for alias in aliases.get(field, ()):  # tolerate earlier draft names
        if alias in option:
            return option[alias]
    return None


def compact_derivation_option(option: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": text_value(option.get("id") or option.get("name") or "derivation"),
        "name": text_value(option.get("name") or option.get("id") or "derivation"),
        "status": text_value(option.get("status")).lower(),
    }
    for field in DERIVATION_REQUIRED_FIELDS:
        result[field] = derivation_field_value(option, field)
    return result


def derivation_options(variable: dict[str, Any]) -> list[dict[str, Any]]:
    raw = variable.get("derivation_options") or variable.get("derivations") or []
    if isinstance(raw, dict):
        raw = raw.get("options") or []
    if not isinstance(raw, list):
        raise ValueError(f"{variable.get('variable')}: derivation_options must be a list.")
    return [item for item in raw if isinstance(item, dict)]


def validate_derivation_plan(variable: dict[str, Any]) -> dict[str, Any]:
    variable_name = str(variable.get("variable") or "Variable")
    options = derivation_options(variable)
    direct_available = direct_field_available(variable)
    required = not direct_available
    no_derivation_reason = text_value(
        variable.get("no_derivation_reason") or variable.get("no_source_reason")
    )

    if required and not options and not no_derivation_reason:
        raise ValueError(
            f"{variable_name}: no direct field is available; provide derivation_options "
            "or no_derivation_reason."
        )

    normalized: list[dict[str, Any]] = []
    for index, option in enumerate(options, start=1):
        status = text_value(option.get("status")).lower()
        if status not in DERIVATION_STATUSES:
            raise ValueError(
                f"{variable_name}: derivation option {index} has invalid status "
                f"{status!r}; choose one of {', '.join(sorted(DERIVATION_STATUSES))}."
            )
        missing = [
            field
            for field in DERIVATION_REQUIRED_FIELDS
            if text_value(derivation_field_value(option, field)) == ""
        ]
        if missing:
            raise ValueError(
                f"{variable_name}: derivation option {index} is missing "
                + ", ".join(missing)
                + "."
            )
        normalized.append(compact_derivation_option(option))

    selected_name = text_value(
        variable.get("selected_derivation") or variable.get("selected_derivation_name")
    )
    selected: dict[str, Any] | None = None
    if normalized:
        selected = next(
            (item for raw, item in zip(options, normalized) if bool(raw.get("selected"))),
            None,
        )
        if selected_name:
            selected = next(
                (
                    item
                    for item in normalized
                    if item["name"] == selected_name or text_value(item.get("id")) == selected_name
                ),
                selected,
            )
        if selected is None:
            selected = normalized[0]

    if selected is None and no_derivation_reason:
        selected = {
            "name": "No viable derivation",
            "status": "blocked",
            "decision_reason": no_derivation_reason,
        }

    max_score = 2
    if selected is not None:
        max_score = DERIVATION_STATUS_MAX_SCORE[str(selected["status"])]
    return {
        "required": required,
        "direct_field_available": direct_available,
        "options": normalized,
        "selected": selected,
        "definition_max_score": max_score,
        "no_derivation_reason": no_derivation_reason or None,
    }


def derivation_score_cap(summary: dict[str, Any]) -> dict[str, Any] | None:
    selected = summary.get("selected") or {}
    max_score = int(summary.get("definition_max_score", 2))
    if max_score >= 2:
        return None
    status = str(selected.get("status") or "blocked")
    reason = (
        "La ruta seleccionada no está validada, por lo que Definition no puede recibir score 2."
        if max_score == 1
        else "No existe una ruta confiable y validada para construir la definición solicitada."
    )
    evidence = text_value(selected.get("decision_reason") or summary.get("no_derivation_reason"))
    if not evidence:
        evidence = f"El estado de la derivación seleccionada es {status}."
    action = (
        "Validar la derivación seleccionada con SQL agregado guardado y métricas de reconciliación."
        if max_score == 1
        else "Identificar una fuente aprobada o excluir la variable del conjunto candidato."
    )
    return {
        "criterion": "definition",
        "max_score": max_score,
        "status_rule": f"El estado de derivación {status} limita Definition a {max_score}",
        "reason": reason,
        "evidence": evidence,
        "recommended_action": action,
        "scoring_method": "Puerta de validación de derivación",
    }


def evaluate_scoring_validation(
    validation: dict[str, Any], variable_name: str, rules: dict[str, Any]
) -> dict[str, Any]:
    criterion = text_value(validation.get("criterion")).lower()
    if criterion not in rules["criteria_order"]:
        raise ValueError(
            f"{variable_name}: scoring validation has invalid criterion {criterion!r}."
        )
    validation_id = text_value(validation.get("id") or validation.get("validation_id"))
    if not validation_id:
        raise ValueError(f"{variable_name}: scoring validation requires id.")
    acceptance_rule = text_value(validation.get("acceptance_rule"))
    if not acceptance_rule:
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} requires acceptance_rule."
        )
    sql_reference = project_sql_reference(
        validation.get("sql_reference") or validation.get("query_reference"),
        variable_name,
        f"scoring_validations.{validation_id}",
    )

    outcome = text_value(validation.get("outcome")).lower()
    observed = validation.get("observed")
    threshold = validation.get("threshold")
    operator = text_value(validation.get("operator")).lower()
    metric = text_value(validation.get("metric"))
    provenance = validation.get("_provenance") or {}
    if metric or operator or threshold is not None or observed is not None:
        if not metric or operator not in COMPARISON_OPERATORS or not is_numeric(threshold):
            raise ValueError(
                f"{variable_name}: scoring validation {validation_id} requires metric, "
                "numeric observed, operator, and numeric threshold."
            )
        if is_numeric(observed):
            outcome = "pass" if compare_numeric(float(observed), operator, float(threshold)) else "fail"
        elif provenance.get("executed"):
            raise ValueError(
                f"{variable_name}: scoring validation {validation_id} did not "
                f"produce numeric metric {metric!r}."
            )
        else:
            outcome = "pending"

    outcome_scores = rules.get("validation_outcomes") or {
        "pass": 2,
        "warning": 1,
        "pending": 1,
        "fail": 0,
        "blocked": 0,
    }
    if "max_score" in validation:
        max_score = int(validation["max_score"])
    elif outcome in outcome_scores:
        max_score = int(outcome_scores[outcome])
    else:
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} needs max_score "
            "or a known outcome."
        )
    if max_score not in {0, 1, 2}:
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} max_score must be 0, 1, or 2."
        )
    if max_score == 2 and outcome and outcome != "pass":
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} cannot allow score 2 "
            f"with outcome {outcome!r}."
        )
    has_frozen_provenance = bool(
        provenance.get("executed")
        and provenance.get("sql_sha256")
        and provenance.get("result_sha256")
    )
    if outcome != "pending" and not has_frozen_provenance:
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} metrics/outcome "
            "must come from executed SQL with frozen result provenance."
        )
    if outcome == "pending" and max_score > 1:
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} without executed "
            "evidence cannot allow a score above 1."
        )
    reason = text_value(validation.get("reason") or validation.get("why"))
    evidence = text_value(validation.get("evidence") or validation.get("supporting_evidence"))
    action = text_value(validation.get("recommended_action"))
    if max_score < 2 and (not reason or not evidence or not action):
        raise ValueError(
            f"{variable_name}: scoring validation {validation_id} max_score {max_score} "
            "requires reason, evidence, and recommended_action."
        )
    if not evidence:
        evidence = (
            f"La validación {validation_id} usó {sql_reference} con la regla: {acceptance_rule}."
        )
    return {
        "id": validation_id,
        "criterion": criterion,
        "max_score": max_score,
        "status_rule": text_value(validation.get("status_rule"))
        or f"La validación ejecutable {validation_id} limita {criterion} a {max_score}",
        "reason": reason or "La validación ejecutable cumplió su regla de aceptación.",
        "evidence": evidence,
        "recommended_action": action or "No se requiere acción mientras la validación continúe cumpliéndose.",
        "scoring_method": "Validación ejecutable",
        "sql_reference": sql_reference,
        "acceptance_rule": acceptance_rule,
        "metric": metric or None,
        "operator": operator or None,
        "threshold": threshold,
        "observed": observed,
        "outcome": outcome or ("pass" if max_score == 2 else "pending"),
    }


def executable_validation_results(
    variable: dict[str, Any], rules: dict[str, Any]
) -> list[dict[str, Any]]:
    validations = variable.get("scoring_validations") or variable.get("validations") or []
    if isinstance(validations, dict):
        validations = validations.get("items") or []
    if not isinstance(validations, list):
        raise ValueError(f"{variable.get('variable')}: scoring_validations must be a list.")
    variable_name = str(variable.get("variable") or "Variable")
    return [
        evaluate_scoring_validation(item, variable_name, rules)
        for item in validations
        if isinstance(item, dict)
    ]


def apply_score_caps(
    scores: dict[str, int], caps: list[dict[str, Any]]
) -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    details: dict[str, dict[str, Any]] = {}
    for cap in caps:
        criterion = str(cap["criterion"])
        max_score = int(cap["max_score"])
        if criterion not in scores:
            raise ValueError(f"Unknown score cap criterion: {criterion}")
        base_score = scores[criterion]
        if max_score < base_score:
            scores[criterion] = max_score
            current = details.get(criterion)
            if current is None or max_score < int(current["max_score"]):
                details[criterion] = {**cap, "base_score": base_score}
    return scores, details


def structured_rationale(
    variable: dict[str, Any], criterion: str, required: bool = False
) -> dict[str, str] | None:
    variable_name = str(variable.get("variable") or "Variable")
    rationale = variable.get("rationale") or {}
    if not isinstance(rationale, dict):
        raise ValueError(f"{variable_name}: rationale must be a criterion mapping.")
    item = rationale.get(criterion)
    if item is None:
        if required:
            raise ValueError(
                f"{variable_name}: score 0/1 for qualitative criterion "
                f"{criterion} requires structured rationale."
            )
        return None
    if not isinstance(item, dict):
        raise ValueError(
            f"{variable_name}: rationale.{criterion} must contain why, evidence, "
            "and recommended_action."
        )
    values = {
        "why": text_value(
            item.get("why") or item.get("reason") or item.get("why_below_2")
        ),
        "evidence": text_value(
            item.get("evidence") or item.get("supporting_evidence")
        ),
        "recommended_action": text_value(item.get("recommended_action")),
    }
    missing = [field for field in RATIONALE_FIELDS if not values[field]]
    if missing and required:
        raise ValueError(
            f"{variable_name}: rationale.{criterion} is missing "
            + ", ".join(missing)
            + "."
        )
    return values if not missing else None


def structured_verification(
    variable: dict[str, Any],
    criterion: str,
    rules: dict[str, Any],
    required: bool = False,
) -> dict[str, Any] | None:
    variable_name = str(variable.get("variable") or "Variable")
    verification = variable.get("verification") or {}
    if not isinstance(verification, dict):
        raise ValueError(f"{variable_name}: verification must be a criterion mapping.")

    config = rules.get("verification") or {}
    semantic_type = text_value(verification.get("semantic_type"))
    allowed_types = [str(value) for value in config.get("semantic_types", [])]
    if not semantic_type or semantic_type not in allowed_types:
        if required:
            raise ValueError(
                f"{variable_name}: qualitative score 2 requires verification.semantic_type "
                f"from {', '.join(allowed_types)}."
            )
        return None

    item = verification.get(criterion)
    if item is None:
        if required:
            raise ValueError(
                f"{variable_name}: score 2 for qualitative criterion {criterion} "
                "requires structured verification."
            )
        return None
    if not isinstance(item, dict):
        raise ValueError(
            f"{variable_name}: verification.{criterion} must be an object."
        )

    provenance = item.get("_provenance") or {}
    if (
        not provenance.get("executed")
        or not text_value(provenance.get("sql_sha256"))
        or not text_value(provenance.get("result_sha256"))
    ):
        raise ValueError(
            f"{variable_name}: verification.{criterion} metrics/outcome must come "
            "from executed SQL with frozen result provenance."
        )

    values: dict[str, Any] = {
        field: text_value(item.get(field)) for field in VERIFICATION_FIELDS
    }
    missing = [field for field in VERIFICATION_FIELDS if not values[field]]
    if missing:
        raise ValueError(
            f"{variable_name}: verification.{criterion} is missing "
            + ", ".join(missing)
            + "."
        )
    try:
        verified_date = date.fromisoformat(values["as_of_date"][:10])
    except ValueError as exc:
        raise ValueError(
            f"{variable_name}: verification.{criterion}.as_of_date must be ISO YYYY-MM-DD."
        ) from exc
    if verified_date > date.today():
        raise ValueError(
            f"{variable_name}: verification.{criterion}.as_of_date cannot be in the future."
        )
    values["as_of_date"] = verified_date.isoformat()

    required_outcome = text_value(config.get("required_outcome") or "pass").lower()
    if values["outcome"].lower() != required_outcome:
        raise ValueError(
            f"{variable_name}: score 2 for {criterion} requires verification outcome "
            f"{required_outcome!r}; got {values['outcome']!r}."
        )
    values["outcome"] = required_outcome

    persisted_query_for = set(config.get("persisted_query_required_for", []))
    if criterion in persisted_query_for:
        query_text = values["query_reference"].split("#", 1)[0].strip()
        query_path = Path(query_text)
        allowed_roots = [
            (PROJECT_ROOT / "queries" / "audits").resolve(),
            (PROJECT_ROOT / "queries" / "profiles").resolve(),
        ]
        resolved_query = (PROJECT_ROOT / query_path).resolve()
        if (
            query_path.is_absolute()
            or query_path.suffix.lower() != ".sql"
            or not any(resolved_query.is_relative_to(root) for root in allowed_roots)
            or not resolved_query.is_file()
        ):
            raise ValueError(
                f"{variable_name}: verification.{criterion}.query_reference must point "
                "to an existing project-relative SQL file under queries/audits/ or "
                "queries/profiles/."
            )

    methods_by_criterion = config.get("methods_by_criterion") or {}
    allowed_methods = [
        str(value) for value in methods_by_criterion.get(criterion, [])
    ]
    if values["method"] not in allowed_methods:
        raise ValueError(
            f"{variable_name}: verification.{criterion}.method "
            f"{values['method']!r} is invalid; choose one of "
            + ", ".join(allowed_methods)
            + "."
        )

    metrics = item.get("metrics")
    metrics_required = criterion in set(config.get("metrics_required_for", []))
    if metrics_required and (not isinstance(metrics, dict) or not metrics):
        raise ValueError(
            f"{variable_name}: verification.{criterion} requires non-empty "
            "aggregate metrics."
        )
    values["metrics"] = dict(metrics) if isinstance(metrics, dict) else {}
    values["semantic_type"] = semantic_type
    values["provenance"] = dict(provenance)

    if criterion == "definition":
        complex_types = set(config.get("complex_definition_semantic_types", []))
        if semantic_type in complex_types:
            allowed_complex = set(config.get("complex_definition_methods", []))
            if values["method"] not in allowed_complex:
                raise ValueError(
                    f"{variable_name}: {semantic_type} definition score 2 requires "
                    "independent recalculation or authoritative lineage plus "
                    "aggregate reconciliation."
                )
        else:
            allowed_direct = set(config.get("direct_definition_methods", []))
            if values["method"] not in allowed_direct:
                raise ValueError(
                    f"{variable_name}: {semantic_type} definition score 2 requires "
                    "an authoritative definition plus an aggregate data audit."
                )

    metric_requirements = config.get("metric_requirements") or {}
    criterion_requirements = metric_requirements.get(criterion) or {}
    alias_groups = criterion_requirements.get(
        semantic_type, criterion_requirements.get("default", [])
    )
    for alias_group in alias_groups:
        aliases = [str(alias) for alias in alias_group]
        valid = any(
            alias in values["metrics"]
            and isinstance(values["metrics"][alias], (int, float))
            and not isinstance(values["metrics"][alias], bool)
            and math.isfinite(float(values["metrics"][alias]))
            for alias in aliases
        )
        if not valid:
            raise ValueError(
                f"{variable_name}: verification.{criterion}.metrics requires one "
                f"numeric value from ({' | '.join(aliases)})."
            )
    return values


def qualitative_status(
    variable: dict[str, Any], criterion: str
) -> str:
    if criterion == "source":
        return text_value((variable.get("source") or {}).get("status"))
    return text_value((variable.get("evidence") or {}).get(criterion))


def percent_text(value: float | None) -> str:
    return "no disponible" if value is None else f"{value:.2f}%"


def window_text(rows: list[dict[str, Any]], count: int) -> str:
    window = rows[-count:] if count > 0 else rows
    if not window:
        return "sin observaciones validadas"
    first = window[0]["snapshot_date"]
    last = window[-1]["snapshot_date"]
    date_range = first if first == last else f"{first} a {last}"
    return f"{len(window)} observación(es), {date_range}"


def recent_coverage_range(
    rows: list[dict[str, Any]], count: int
) -> float | None:
    values = [
        float(item["observable_coverage_percent"])
        for item in rows[-count:]
        if item.get("observable_coverage_percent") is not None
    ]
    return max(values) - min(values) if len(values) >= 2 else None


def point_label(scores: dict[str, int], rules: dict[str, Any]) -> str:
    total = sum(scores.values())
    zeroes = sum(value == 0 for value in scores.values())
    labels = rules["point_labels"]
    high = labels["high"]
    if (
        int(high["minimum_total"]) <= total <= int(high["maximum_total"])
        and zeroes <= int(high["maximum_zero_scores"])
    ):
        return str(high["label"])
    fixable = labels["medium_fixable_zero"]
    if total >= int(fixable["minimum_total"]) and zeroes <= int(
        fixable["maximum_zero_scores"]
    ):
        return str(fixable["label"])
    medium = labels["medium"]
    if int(medium["minimum_total"]) <= total <= int(medium["maximum_total"]):
        return str(medium["label"])
    low = labels["low"]
    if int(low["minimum_total"]) <= total <= int(low["maximum_total"]):
        return str(low["label"])
    return str(labels["zero"]["label"])


def apply_score_overrides(
    scores: dict[str, int], variable: dict[str, Any]
) -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    details: dict[str, dict[str, Any]] = {}
    variable_name = str(variable.get("variable") or "Variable")
    for criterion, override in (variable.get("score_overrides") or {}).items():
        if criterion not in scores:
            raise ValueError(f"Unknown score override criterion: {criterion}")
        if not isinstance(override, dict):
            raise ValueError(
                f"Override for {criterion} must contain score and reason."
            )
        score = int(override.get("score", -1))
        reason = str(override.get("reason") or "").strip()
        if score not in {0, 1, 2} or not reason:
            raise ValueError(
                f"Override for {criterion} requires score 0/1/2 and a reason."
            )
        base_score = scores[criterion]
        if score > base_score:
            raise ValueError(
                f"{variable_name}: score override {criterion}={score} would increase "
                f"the base score {base_score}; overrides may only reduce scores."
            )
        supporting_evidence = text_value(
            override.get("evidence") or override.get("supporting_evidence")
        )
        recommended_action = text_value(override.get("recommended_action"))
        if score < 2 and (not supporting_evidence or not recommended_action):
            raise ValueError(
                f"{variable_name}: score override {criterion}={score} requires "
                "evidence and recommended_action."
            )
        scores[criterion] = score
        details[criterion] = {
            "score": score,
            "base_score": base_score,
            "reason": reason,
            "evidence": supporting_evidence,
            "recommended_action": recommended_action,
        }
    return scores, details


def derive_scores(
    variable: dict[str, Any], rows: list[dict[str, Any]], frequency: str,
    usable_since: date | None, rules: dict[str, Any]
) -> tuple[dict[str, int], dict[str, Any]]:
    name = str(variable["variable"])
    source = variable.get("source") or {}
    evidence = variable.get("evidence") or {}
    scores = {
        "source": status_score("source", source.get("status"), rules, name),
        "definition": status_score(
            "definition", evidence.get("definition"), rules, name
        ),
        "consistency": status_score(
            "consistency", evidence.get("consistency"), rules, name
        ),
        "join": status_score("join", evidence.get("join"), rules, name),
        "effort": status_score("effort", evidence.get("effort"), rules, name),
    }
    for criterion in QUALITATIVE_CRITERIA:
        if scores[criterion] < 2:
            structured_rationale(variable, criterion, required=True)

    coverage_window = int(rules["coverage"]["assessment_window_observations"])
    recent_coverage = weighted_recent_coverage(rows, coverage_window)
    scores["coverage"] = coverage_score(recent_coverage, rules)

    missing_window = int(rules["missingness"]["assessment_window_observations"])
    missing_coverage = weighted_recent_coverage(rows, missing_window)
    missing_percent = None if missing_coverage is None else 100.0 - missing_coverage
    declared_systematic = (variable.get("quality") or {}).get("systematic_missingness")
    systematic = (
        automatic_systematic_missingness(rows, rules)
        if declared_systematic is None
        else bool(declared_systematic)
    )
    systematic_source = "automatic" if declared_systematic is None else "configured"
    missing_config = rules["missingness"]
    if missing_percent is None or missing_percent > float(
        missing_config["score_1_max_percent"]
    ):
        scores["missingness"] = 0
    elif (
        missing_percent <= float(missing_config["score_2_max_percent"])
        and not systematic
    ):
        scores["missingness"] = 2
    else:
        scores["missingness"] = 1

    latest = parse_date(rows[-1]["snapshot_date"]) if rows else None
    months = elapsed_months(usable_since, latest)
    history_config = rules["history"]
    leakage = bool((variable.get("quality") or {}).get("leakage_risk", False))
    if (
        usable_since is None
        or (
            history_config.get("score_0_for_single_wave")
            and frequency in {"Single wave", "Una sola wave"}
        )
        or (history_config.get("score_0_for_leakage") and leakage)
    ):
        scores["history"] = 0
    elif months >= float(history_config["score_2_min_months"]):
        scores["history"] = 2
    elif months >= float(history_config["score_1_min_months"]):
        scores["history"] = 1
    else:
        scores["history"] = 0

    ordered = {criterion: int(scores[criterion]) for criterion in rules["criteria_order"]}
    derivation_summary = validate_derivation_plan(variable)
    executable_validations = executable_validation_results(variable, rules)
    computed_verification_caps = variable.get("_computed_verification_caps") or []
    if not isinstance(computed_verification_caps, list):
        raise ValueError(f"{name}: _computed_verification_caps must be a list.")
    dependency_caps = variable.get("dependency_caps") or []
    if not isinstance(dependency_caps, list):
        raise ValueError(f"{name}: dependency_caps must be a list.")
    caps = list(executable_validations) + list(computed_verification_caps) + list(dependency_caps)
    derivation_cap = derivation_score_cap(derivation_summary)
    if derivation_cap is not None:
        caps.append(derivation_cap)
    ordered, score_cap_details = apply_score_caps(ordered, caps)
    ordered, override_details = apply_score_overrides(ordered, variable)
    score_2_verification: dict[str, dict[str, Any]] = {}
    for criterion in QUALITATIVE_CRITERIA:
        if ordered[criterion] == 2:
            verified = structured_verification(
                variable, criterion, rules, required=True
            )
            assert verified is not None
            score_2_verification[criterion] = verified
    systematic_window = int(missing_config["systematic_window_observations"])
    diagnostics = {
        "recent_coverage_percent": (
            round(recent_coverage, 4) if recent_coverage is not None else None
        ),
        "recent_missingness_percent": (
            round(missing_percent, 4) if missing_percent is not None else None
        ),
        "systematic_missingness": systematic,
        "systematic_missingness_source": systematic_source,
        "systematic_coverage_range_percent_points": recent_coverage_range(
            rows, systematic_window
        ),
        "history_months": round(months, 2),
        "leakage_risk": leakage,
        "score_override_reasons": {
            criterion: detail["reason"]
            for criterion, detail in override_details.items()
        },
        "score_override_details": override_details,
        "score_cap_details": score_cap_details,
        "executable_validations": executable_validations,
        "computed_verification_caps": computed_verification_caps,
        "dependency_caps": dependency_caps,
        "derivation": derivation_summary,
        "score_2_verification": score_2_verification,
    }
    return ordered, diagnostics


def rationale_entry(
    variable: dict[str, Any],
    criterion: str,
    score: int,
    status_rule: str,
    why: str,
    evidence: str,
    recommended_action: str,
    scoring_method: str,
) -> dict[str, Any]:
    source = variable.get("source") or {}
    return {
        "category": variable.get("category"),
        "variable": variable.get("variable"),
        "criterion": CRITERION_LABELS[criterion],
        "criterion_key": criterion,
        "score": int(score),
        "status_rule": status_rule,
        "why_below_2": why,
        "supporting_evidence": evidence,
        "recommended_action": recommended_action,
        "scoring_method": scoring_method,
        "source_table": source.get("table")
        or source.get("detail")
        or "No validada",
        "source_columns": source_columns_text(source) or "Por definir",
    }


def _build_score_rationales_legacy(
    variable: dict[str, Any],
    rows: list[dict[str, Any]],
    frequency: str,
    scores: dict[str, int],
    diagnostics: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    rationales: list[dict[str, Any]] = []
    overrides = diagnostics.get("score_override_details") or {}
    score_caps = diagnostics.get("score_cap_details") or {}
    coverage_config = rules["coverage"]
    missing_config = rules["missingness"]
    history_config = rules["history"]

    for criterion in rules["criteria_order"]:
        score = int(scores[criterion])
        if score == 2:
            continue

        override = overrides.get(criterion)
        if override:
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    (
                        "Configured override "
                        f"(base score {int(override['base_score'])})"
                    ),
                    str(override["reason"]),
                    str(override["evidence"]),
                    str(override["recommended_action"]),
                    "Configured override",
                )
            )
            continue

        cap = score_caps.get(criterion)
        if cap:
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    str(cap.get("status_rule") or f"Score capped at {score}"),
                    str(cap.get("reason") or "A validation capped this criterion below 2."),
                    str(cap.get("evidence") or "See validation details in profile JSON."),
                    str(cap.get("recommended_action") or "Resolve and rerun the validation."),
                    str(cap.get("scoring_method") or "Executable validation"),
                )
            )
            continue

        if criterion in QUALITATIVE_CRITERIA:
            status = qualitative_status(variable, criterion)
            configured = structured_rationale(variable, criterion, required=True)
            assert configured is not None
            meaning = str(rules["criteria"][criterion][status]["meaning"])
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    f"{status}: {meaning}",
                    configured["why"],
                    configured["evidence"],
                    configured["recommended_action"],
                    "Configured qualitative status",
                )
            )
            continue

        if criterion == "coverage":
            recent = diagnostics.get("recent_coverage_percent")
            count = int(coverage_config["assessment_window_observations"])
            score_two = float(coverage_config["score_2_min_percent"])
            score_one = float(coverage_config["score_1_min_percent"])
            if recent is None:
                why = "No validated recent coverage evidence is available."
                status_rule = (
                    f"No validated observations; score 1 requires >= {score_one:g}%."
                )
            elif score == 1:
                why = (
                    f"Recent observable coverage is below the {score_two:g}% "
                    "threshold for score 2."
                )
                status_rule = (
                    f"{score_one:g}% <= weighted coverage < {score_two:g}%"
                )
            else:
                why = (
                    f"Recent observable coverage is below the {score_one:g}% "
                    "minimum for score 1."
                )
                status_rule = (
                    f"Weighted coverage < {score_one:g}% or unavailable"
                )
            evidence = (
                f"Denominator-weighted coverage was {percent_text(recent)} across "
                f"the latest {window_text(rows, count)}. Thresholds: score 2 at "
                f">= {score_two:g}%; score 1 at >= {score_one:g}%."
            )
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    status_rule,
                    why,
                    evidence,
                    (
                        "Resolve eligibility or source-observability gaps and reprofile; "
                        f"target >= {score_two:g}% weighted coverage."
                    ),
                    "Calculated threshold",
                )
            )
            continue

        if criterion == "missingness":
            missing = diagnostics.get("recent_missingness_percent")
            count = int(missing_config["assessment_window_observations"])
            score_two = float(missing_config["score_2_max_percent"])
            score_one = float(missing_config["score_1_max_percent"])
            systematic = bool(diagnostics.get("systematic_missingness"))
            range_value = diagnostics.get(
                "systematic_coverage_range_percent_points"
            )
            systematic_note = ""
            if systematic:
                source = diagnostics.get("systematic_missingness_source")
                range_text = (
                    "not measurable"
                    if range_value is None
                    else f"{float(range_value):.2f} percentage points"
                )
                systematic_note = (
                    f" A {source} systematic-missingness flag applies; the recent "
                    f"coverage range was {range_text}."
                )
            if missing is None:
                why = "Missingness cannot be quantified without validated observations."
                status_rule = "Missingness unavailable -> score 0"
            elif score == 0:
                why = (
                    f"Recent missingness exceeds the {score_one:g}% maximum for "
                    "score 1."
                )
                status_rule = f"Weighted missingness > {score_one:g}%"
            elif systematic:
                why = "A systematic missingness pattern prevents a score of 2."
                status_rule = "Systematic pattern caps score at 1"
            else:
                why = (
                    f"Recent missingness exceeds the {score_two:g}% maximum for "
                    "score 2."
                )
                status_rule = (
                    f"{score_two:g}% < weighted missingness <= {score_one:g}%"
                )
            evidence = (
                f"Denominator-weighted missingness was {percent_text(missing)} "
                f"across the latest {window_text(rows, count)}. Thresholds: score 2 "
                f"at <= {score_two:g}%; score 1 at <= {score_one:g}%."
                + systematic_note
            )
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    status_rule,
                    why,
                    evidence,
                    (
                        "Investigate gaps by time and eligible segment, document the "
                        f"cause, and target <= {score_two:g}% non-systematic missingness."
                    ),
                    "Calculated threshold",
                )
            )
            continue

        if criterion == "history":
            usable_since = first_usable_date(rows, rules)
            latest = parse_date(rows[-1]["snapshot_date"]) if rows else None
            months = float(diagnostics.get("history_months") or 0)
            score_two = float(history_config["score_2_min_months"])
            score_one = float(history_config["score_1_min_months"])
            leakage = bool(diagnostics.get("leakage_risk"))
            if leakage:
                why = "Target leakage makes the observed history unusable."
                status_rule = "Leakage risk forces history score 0"
                action = (
                    "Remove target-derived or future-known fields and rebuild a "
                    "time-safe historical feature."
                )
            elif frequency == "Single wave":
                why = "Only one observation wave is available."
                status_rule = "Single wave forces history score 0"
                action = (
                    "Add comparable dated waves or backfill snapshots before using "
                    "the variable longitudinally."
                )
            elif usable_since is None:
                threshold = rules["usable_history"]["coverage_threshold_percent"]
                consecutive = rules["usable_history"]["consecutive_observations"]
                why = "No stable run of observations qualifies as usable history."
                status_rule = "No usable-since date -> score 0"
                action = (
                    f"Establish at least {consecutive} consecutive observations at "
                    f">= {threshold}% coverage."
                )
            elif score == 1:
                why = (
                    f"Usable history is shorter than the {score_two:g}-month "
                    "threshold for score 2."
                )
                status_rule = (
                    f"{score_one:g} <= usable months < {score_two:g}"
                )
                action = (
                    f"Backfill or continue collection until at least {score_two:g} "
                    "completed months are available."
                )
            else:
                why = (
                    f"Usable history is shorter than the {score_one:g}-month "
                    "minimum for score 1."
                )
                status_rule = f"Usable months < {score_one:g}"
                action = (
                    f"Backfill or continue collection until at least {score_one:g} "
                    "completed months are available."
                )
            evidence = (
                f"Usable since: {usable_since.isoformat() if usable_since else 'not established'}; "
                f"latest observation: {latest.isoformat() if latest else 'not available'}; "
                f"completed usable history: {months:g} months. Thresholds: score 2 "
                f"at >= {score_two:g} months; score 1 at >= {score_one:g} months."
            )
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    status_rule,
                    why,
                    evidence,
                    action,
                    "Calculated threshold",
                )
            )
            continue

        raise ValueError(f"Unsupported rationale criterion: {criterion}")

    return rationales


def build_score_rationales(
    variable: dict[str, Any],
    rows: list[dict[str, Any]],
    frequency: str,
    scores: dict[str, int],
    diagnostics: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build public Spanish rationale for every criterion below score 2."""
    rationales: list[dict[str, Any]] = []
    overrides = diagnostics.get("score_override_details") or {}
    score_caps = diagnostics.get("score_cap_details") or {}

    for criterion in rules["criteria_order"]:
        score = int(scores[criterion])
        if score == 2:
            continue

        override = overrides.get(criterion)
        if override:
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    f"Override configurado (score base {int(override['base_score'])})",
                    str(override["reason"]),
                    str(override["evidence"]),
                    str(override["recommended_action"]),
                    "Override configurado",
                )
            )
            continue

        cap = score_caps.get(criterion)
        if cap:
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    str(cap.get("status_rule") or f"El criterio queda limitado a {score}"),
                    str(cap.get("reason") or "Una validación limitó este criterio por debajo de 2."),
                    str(cap.get("evidence") or "Consultar el detalle de la validación en el profile JSON."),
                    str(cap.get("recommended_action") or "Resolver la condición y repetir la validación."),
                    str(cap.get("scoring_method") or "Validación ejecutable"),
                )
            )
            continue

        if criterion in QUALITATIVE_CRITERIA:
            status = qualitative_status(variable, criterion)
            configured = structured_rationale(variable, criterion, required=True)
            assert configured is not None
            meaning = str(rules["criteria"][criterion][status]["meaning"])
            rationales.append(
                rationale_entry(
                    variable,
                    criterion,
                    score,
                    f"{status}: {meaning}",
                    configured["why"],
                    configured["evidence"],
                    configured["recommended_action"],
                    "Estado cualitativo configurado",
                )
            )
            continue

        if criterion == "coverage":
            config = rules["coverage"]
            recent = diagnostics.get("recent_coverage_percent")
            count = int(config["assessment_window_observations"])
            score_two = float(config["score_2_min_percent"])
            score_one = float(config["score_1_min_percent"])
            if recent is None:
                why = "No existe evidencia validada de coverage reciente."
                status_rule = f"Sin observaciones validadas; score 1 requiere >= {score_one:g}%."
            elif score == 1:
                why = f"El coverage observable reciente está por debajo del umbral de {score_two:g}% para score 2."
                status_rule = f"{score_one:g}% <= coverage ponderado < {score_two:g}%"
            else:
                why = f"El coverage observable reciente está por debajo del mínimo de {score_one:g}% para score 1."
                status_rule = f"Coverage ponderado < {score_one:g}% o no disponible"
            evidence_text = (
                f"Coverage ponderado por denominador: {percent_text(recent)} durante "
                f"{window_text(rows, count)}. Umbrales: score 2 con >= {score_two:g}%; "
                f"score 1 con >= {score_one:g}%."
            )
            rationales.append(
                rationale_entry(
                    variable, criterion, score, status_rule, why, evidence_text,
                    f"Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= {score_two:g}%.",
                    "Threshold calculado",
                )
            )
            continue

        if criterion == "missingness":
            config = rules["missingness"]
            missing = diagnostics.get("recent_missingness_percent")
            count = int(config["assessment_window_observations"])
            score_two = float(config["score_2_max_percent"])
            score_one = float(config["score_1_max_percent"])
            systematic = bool(diagnostics.get("systematic_missingness"))
            range_value = diagnostics.get("systematic_coverage_range_percent_points")
            if missing is None:
                why = "Missingness no puede cuantificarse sin observaciones validadas."
                status_rule = "Missingness no disponible -> score 0"
            elif score == 0:
                why = f"Missingness reciente supera el máximo de {score_one:g}% para score 1."
                status_rule = f"Missingness ponderado > {score_one:g}%"
            elif systematic:
                why = "Un patrón sistemático de missingness impide asignar score 2."
                status_rule = "Un patrón sistemático limita el score a 1"
            else:
                why = f"Missingness reciente supera el máximo de {score_two:g}% para score 2."
                status_rule = f"{score_two:g}% < missingness ponderado <= {score_one:g}%"
            systematic_note = ""
            if systematic:
                range_text = (
                    "no medible" if range_value is None
                    else f"{float(range_value):.2f} puntos porcentuales"
                )
                systematic_note = f" Se detectó un patrón sistemático; rango reciente de coverage: {range_text}."
            evidence_text = (
                f"Missingness ponderado por denominador: {percent_text(missing)} durante "
                f"{window_text(rows, count)}. Umbrales: score 2 con <= {score_two:g}%; "
                f"score 1 con <= {score_one:g}%." + systematic_note
            )
            rationales.append(
                rationale_entry(
                    variable, criterion, score, status_rule, why, evidence_text,
                    f"Investigar brechas por fecha y segmento elegible; objetivo <= {score_two:g}% sin patrón sistemático.",
                    "Threshold calculado",
                )
            )
            continue

        if criterion == "history":
            config = rules["history"]
            usable_since = first_usable_date(rows, rules)
            latest = parse_date(rows[-1]["snapshot_date"]) if rows else None
            months = float(diagnostics.get("history_months") or 0)
            score_two = float(config["score_2_min_months"])
            score_one = float(config["score_1_min_months"])
            leakage = bool(diagnostics.get("leakage_risk"))
            if leakage:
                why = "El leakage del outcome vuelve inutilizable la historia observada."
                status_rule = "El riesgo de leakage fuerza History a 0"
                action = "Eliminar campos futuros o derivados del target y reconstruir una feature segura en el tiempo."
            elif frequency in {"Single wave", "Una sola wave"}:
                why = "Sólo existe una wave de observación."
                status_rule = "Una sola wave fuerza History a 0"
                action = "Agregar waves comparables o reconstruir snapshots históricos antes del uso longitudinal."
            elif usable_since is None:
                threshold = rules["usable_history"]["coverage_threshold_percent"]
                consecutive = rules["usable_history"]["consecutive_observations"]
                why = "No existe una racha estable que califique como historia utilizable."
                status_rule = "Sin fecha usable-since -> score 0"
                action = f"Lograr al menos {consecutive} observaciones consecutivas con >= {threshold}% de coverage."
            elif score == 1:
                why = f"La historia utilizable es menor al umbral de {score_two:g} meses para score 2."
                status_rule = f"{score_one:g} <= meses utilizables < {score_two:g}"
                action = f"Continuar la colección o backfill hasta completar al menos {score_two:g} meses."
            else:
                why = f"La historia utilizable es menor al mínimo de {score_one:g} meses para score 1."
                status_rule = f"Meses utilizables < {score_one:g}"
                action = f"Continuar la colección o backfill hasta completar al menos {score_one:g} meses."
            evidence_text = (
                f"Usable since: {usable_since.isoformat() if usable_since else 'no establecida'}; "
                f"última observación: {latest.isoformat() if latest else 'no disponible'}; "
                f"historia utilizable completada: {months:g} meses. Umbrales: score 2 con "
                f">= {score_two:g} meses; score 1 con >= {score_one:g} meses."
            )
            rationales.append(
                rationale_entry(
                    variable, criterion, score, status_rule, why, evidence_text,
                    action, "Threshold calculado",
                )
            )
            continue

        raise ValueError(f"Unsupported rationale criterion: {criterion}")

    return rationales


def history_description(
    rows: list[dict[str, Any]], usable_since: date | None, rules: dict[str, Any]
) -> tuple[str, date | None, date | None]:
    first_observed = next(
        (
            parse_date(item["snapshot_date"])
            for item in rows
            if int(item["observable_employees"]) > 0
        ),
        None,
    )
    latest = parse_date(rows[-1]["snapshot_date"]) if rows else None
    if not rows:
        return "No existen observaciones históricas validadas.", first_observed, latest
    if usable_since:
        return (
            f"Utilizable desde {usable_since.isoformat()}; primera observación "
            f"{first_observed.isoformat() if first_observed else 'no observada'}; "
            f"última {latest.isoformat() if latest else 'desconocida'}.",
            first_observed,
            latest,
        )
    threshold = rules["usable_history"]["coverage_threshold_percent"]
    count = rules["usable_history"]["consecutive_observations"]
    return (
        f"Primera observación {first_observed.isoformat() if first_observed else 'no observada'}, "
        f"pero ninguna racha de {count} observaciones consecutivas alcanzó >= {threshold}% de coverage.",
        first_observed,
        latest,
    )


def source_columns_text(source: dict[str, Any]) -> str:
    columns = source.get("columns") or []
    if isinstance(columns, str):
        return columns
    return ", ".join(str(item) for item in columns)


def offline_rows(data: Any, variable_name: str) -> list[dict[str, Any]]:
    if data is None:
        raise ValueError("No offline aggregate data was loaded.")
    if isinstance(data, dict) and "variables" in data:
        data = data["variables"]
    if isinstance(data, dict) and "rows" in data:
        return list(data["rows"])
    if isinstance(data, dict):
        rows = data.get(variable_name)
        if rows is None:
            rows = data.get(slugify(variable_name))
        if rows is None:
            raise ValueError(f"Offline aggregate data has no entry for {variable_name!r}.")
        if isinstance(rows, dict):
            rows = rows.get("coverage") or rows.get("rows") or []
        return list(rows)
    if isinstance(data, list):
        return list(data)
    raise ValueError("Unsupported offline aggregate JSON structure.")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "variable"


def resolve_custom_sql(variable: dict[str, Any], spec_path: Path) -> str:
    profile = variable.get("profile") or {}
    sql_file = profile.get("aggregate_sql_file")
    if not sql_file:
        raise ValueError(
            f"{variable.get('variable')}: aggregate_sql mode requires aggregate_sql_file"
        )
    path = Path(sql_file)
    if not path.is_absolute():
        path = spec_path.parent / path
    return path.read_text(encoding="utf-8")


def _offline_evidence_rows(
    offline_data: Any, variable_name: str, reference: str
) -> list[dict[str, Any]] | None:
    if not isinstance(offline_data, dict):
        return None
    root = offline_data.get("variables") or offline_data
    payload = root.get(variable_name) or root.get(slugify(variable_name))
    if not isinstance(payload, dict):
        return None
    queries = payload.get("queries") or {}
    for key in (reference, Path(reference).as_posix(), Path(reference).name, Path(reference).stem):
        rows = queries.get(key) if isinstance(queries, dict) else None
        if rows is not None:
            return [dict(row) for row in rows if isinstance(row, dict)]
    return None


def freeze_declared_evidence(
    variable: dict[str, Any], rules: dict[str, Any], offline_data: Any
) -> dict[str, Any]:
    if "_computed_verification_caps" in variable:
        return variable
    variable_name = str(variable.get("variable") or "Variable")
    records: dict[str, dict[str, Any]] = {}
    items: list[tuple[str, str, dict[str, Any]]] = []
    for criterion, item in (variable.get("verification") or {}).items():
        if criterion == "semantic_type" or not isinstance(item, dict):
            continue
        reference = project_sql_reference(
            item.get("query_reference"), variable_name, f"verification.{criterion}"
        )
        items.append((reference, f"verification:{criterion}", item))
    validations = variable.get("scoring_validations") or variable.get("validations") or []
    if isinstance(validations, dict):
        validations = validations.get("items") or []
    for item in validations if isinstance(validations, list) else []:
        if not isinstance(item, dict):
            continue
        reference = project_sql_reference(
            item.get("sql_reference") or item.get("query_reference"),
            variable_name,
            f"scoring_validations.{item.get('id')}",
        )
        items.append((reference, f"scoring_validation:{item.get('id')}", item))
    for reference, purpose, item in items:
        if reference in records:
            continue
        sql_path = (PROJECT_ROOT / reference).resolve()
        sql = sql_path.read_text(encoding="utf-8-sig")
        offline_rows = _offline_evidence_rows(offline_data, variable_name, reference)
        if offline_data is not None:
            if offline_rows is None:
                continue
            rows = offline_rows
            source = "offline_frozen_result"
        else:
            rows = run_aggregate_query(sql, max_rows=1000)
            source = "executed_redshift_sql"
        records[reference] = workflow.make_query_record(
            reference, sql, rows, purpose, variable, item, source
        )
    frozen, _ = workflow.freeze_variable_evidence(
        variable,
        records,
        rules,
        "offline_frozen_result" if offline_data is not None else "executed_redshift_sql",
    )
    return frozen


def profile_one(
    variable: dict[str, Any], rules: dict[str, Any], spec_path: Path,
    offline_data: Any = None, print_sql: bool = False
) -> dict[str, Any] | None:
    if not print_sql:
        variable = freeze_declared_evidence(variable, rules, offline_data)
    name = str(variable.get("variable") or "").strip()
    if not name:
        raise ValueError("Each variable requires a non-empty variable name.")
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    profile = variable.get("profile") or {}
    mode = str(profile.get("mode", "standard")).lower()

    population_display = str(
        (variable.get("population") or {}).get("display")
        or rules["population"]["display"]
    )
    sql = None
    if mode == "standard":
        sql, population_display = build_standard_sql(variable, rules)
    elif mode == "aggregate_sql":
        sql = resolve_custom_sql(variable, spec_path)
        population_display = str(
            (variable.get("population") or {}).get("display")
            or "Defined by aggregate SQL"
        )
    elif mode not in {"unavailable", "external"}:
        raise ValueError(f"{name}: unknown profile mode {mode!r}")

    if print_sql:
        if sql:
            print(f"-- {name}\n{sql}\n")
        else:
            print(f"-- {name}: no database query ({mode})\n")
        return None

    if mode in {"unavailable", "external"}:
        raw_rows: list[dict[str, Any]] = []
    elif offline_data is not None:
        raw_rows = offline_rows(offline_data, name)
    else:
        raw_rows = run_aggregate_query(sql or "")

    rows, warnings = normalize_rows(raw_rows, rules)
    usable_since = first_usable_date(rows, rules)
    frequency = observation_frequency(rows, measurement, rules)
    history_text, first_observed, latest = history_description(rows, usable_since, rules)
    scores, diagnostics = derive_scores(
        variable, rows, frequency, usable_since, rules
    )
    score_rationales = build_score_rationales(
        variable, rows, frequency, scores, diagnostics, rules
    )
    total = sum(scores.values())
    points = point_label(scores, rules)
    blocker_key = str(variable.get("blocker", "none"))
    blocker_options = rules["blockers"]
    if blocker_key not in blocker_options:
        raise ValueError(
            f"{name}: invalid blocker {blocker_key!r}; choose one of "
            + ", ".join(blocker_options)
        )
    blocker = blocker_options[blocker_key]
    result = str(blocker["label"]) if blocker["overrides_points"] else points

    measurement_key = str(measurement.get("type", "snapshot"))
    measurement_label = rules["measurement_labels"].get(
        measurement_key, measurement_key.replace("_", " ").title()
    )
    first_observed_text = first_observed.isoformat() if first_observed else None
    usable_text = usable_since.isoformat() if usable_since else None
    first_event = next(
        (
            item["snapshot_date"]
            for item in rows
            if item["event_employees"] is not None and item["event_employees"] > 0
        ),
        None,
    )
    for row in rows:
        row["first_observed_date"] = first_observed_text
        row["usable_since_date"] = usable_text

    return {
        "category": variable.get("category"),
        "variable": name,
        "notes": variable.get("notes"),
        "source_type": source.get("type", "Database"),
        "source_table": source.get("table") or source.get("detail") or "No validada",
        "source_columns": source_columns_text(source) or "Por definir",
        "level_data": variable.get("level_data") or "Por definir",
        "history_available": variable.get("history_override") or history_text,
        "observation_frequency": frequency,
        "blocker_key": blocker_key,
        "blocker_label": blocker["label"],
        "definition_text": variable.get("definition"),
        "measurement_type": measurement_label,
        "population_filter": population_display,
        "numerator_definition": variable.get("numerator_definition")
        or "Empleados con todos los campos fuente requeridos poblados.",
        "scores": scores,
        "total": total,
        "point_result": points,
        "result": result,
        "first_observed_date": first_observed_text,
        "usable_since_date": usable_text,
        "latest_observation_date": latest.isoformat() if latest else None,
        "first_event_date": first_event,
        "diagnostics": diagnostics,
        "derivation": diagnostics.get("derivation") or {},
        "executable_validations": diagnostics.get("executable_validations") or [],
        "warnings": warnings,
        "coverage": rows,
        "score_rationales": score_rationales,
        "score_verification": diagnostics.get("score_2_verification") or {},
    }


def validate_spec(
    spec: dict[str, Any], rules: dict[str, Any]
) -> list[dict[str, Any]]:
    required_version = int(rules["verification"]["required_spec_version"])
    version = int(spec.get("version") or 0)
    if version < required_version:
        raise ValueError(
            f"Assessment spec version {required_version} or newer is required. "
            f"Version {version or 'missing'} is legacy and lacks mandatory "
            "score-2 verification evidence."
        )
    variables = spec.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError("The spec must contain a non-empty variables list.")
    return variables


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Profile one or more attrition variables with aggregate Redshift evidence "
            "and calculate all eight availability scores."
        )
    )
    parser.add_argument("--spec", required=True, help="Assessment spec in YAML format.")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="Editable scoring rules YAML.")
    parser.add_argument(
        "--query-helper",
        help=(
            "Project-specific Python adapter exposing validate_readonly(), connect(), "
            "psycopg2, and SENSITIVE_OUTPUT_COLUMNS."
        ),
    )
    parser.add_argument("--output", help="Output profile JSON path.")
    parser.add_argument(
        "--aggregate-results",
        help="Offline aggregate JSON for validation; skips database access.",
    )
    parser.add_argument(
        "--print-sql",
        action="store_true",
        help="Print generated aggregate SQL without connecting to Redshift.",
    )
    args = parser.parse_args()

    configure_query_helper(args.query_helper)

    spec_path = Path(args.spec).resolve()
    rules_path = Path(args.rules).resolve()
    spec = load_yaml(spec_path)
    rules = load_yaml(rules_path)
    variables = validate_spec(spec, rules)
    offline_data = load_json(Path(args.aggregate_results)) if args.aggregate_results else None

    assessments = []
    for variable in variables:
        assessment = profile_one(
            variable,
            rules,
            spec_path,
            offline_data=offline_data,
            print_sql=args.print_sql,
        )
        if assessment is not None:
            assessments.append(assessment)

    if args.print_sql:
        return
    if not args.output:
        raise SystemExit("--output is required unless --print-sql is used.")

    output = {
        "schema_version": 4,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rules_file": str(rules_path),
        "population_default": rules["population"]["display"],
        "minimum_shared_cohort": rules["population"]["minimum_shared_cohort"],
        "assessments": assessments,
    }
    write_json(Path(args.output), output)
    print(f"Wrote {len(assessments)} assessment(s) to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Assessment failed: {exc}") from exc
