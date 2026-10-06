import argparse
import json
import os
import re
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


DEFAULT_SLIDES_ROOT = Path(r"C:\Dev\Python\Slides")
DEFAULT_MAX_ROWS = 100
ALLOWED_START = {"select", "with", "explain", "show"}
FORBIDDEN_TOKENS = {
    "insert", "update", "delete", "merge", "truncate", "drop", "alter", "create",
    "grant", "revoke", "copy", "unload", "call", "execute", "vacuum", "analyze",
    "begin", "commit", "rollback", "set", "reset",
}
SENSITIVE_OUTPUT_COLUMNS = {
    "employee_id", "emp_name", "name", "legal_first_name", "legal_last_name",
    "preferred_first_name", "email", "manager_work_email", "supervisor_email",
    "supervisor_emplid", "supervisor_name", "manager_employee_id", "manager_name",
    "dept_head_name",
    "homeaddresswithcountry", "home_city", "home_state", "postal_code",
    "gender", "race", "disability_status", "veteran_status_identification",
    "dateofbirth", "year_of_birth", "month_of_birth", "primary_citizenship",
    "secondary_citizenship", "country_of_birth_locale_sensitive",
    "annual_base_pay", "base_pay_rate", "total_base_pay_amount", "fte_annual_base_pay",
    "compa_ratio",
}

# Estas categorías pueden aparecer con su etiqueta almacenada únicamente en
# un análisis interno explícito y siempre como resultados agregados. Los demás
# campos sensibles (identidad, domicilio y compensación) nunca se liberan.
INTERNAL_ANALYSIS_CATEGORY_COLUMNS = {
    "gender",
    "race",
    "disability_status",
    "veteran_status_identification",
    "primary_citizenship",
    "secondary_citizenship",
    "country_of_birth_locale_sensitive",
    "compensation_grade",
    "compensation_grade_profile",
}
MINIMUM_INTERNAL_ANALYSIS_COHORT = 30


def load_env() -> None:
    env_path = os.getenv("ATTRITION_REDSHIFT_ENV")
    if env_path:
        load_dotenv(env_path)
        return
    slides_root = Path(os.getenv("ATTRITION_SLIDES_ROOT", str(DEFAULT_SLIDES_ROOT)))
    load_dotenv(slides_root / ".env")


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--.*?$", " ", sql, flags=re.M)
    return sql.strip()


def validate_readonly(sql: str) -> str:
    cleaned = strip_comments(sql)
    stripped = cleaned.strip().rstrip(";").strip()
    if not stripped:
        raise ValueError("Empty SQL.")
    if ";" in stripped:
        raise ValueError("Multiple SQL statements are not allowed.")

    first = re.match(r"^\s*([a-zA-Z]+)", stripped)
    if not first or first.group(1).lower() not in ALLOWED_START:
        raise ValueError("Only SELECT/WITH/EXPLAIN/SHOW statements are allowed.")

    tokens = {token.lower() for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", stripped)}
    forbidden = sorted(tokens & FORBIDDEN_TOKENS)
    if forbidden:
        raise ValueError(f"Forbidden SQL token(s): {', '.join(forbidden)}")

    if re.search(r"\bselect\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?\*", stripped, flags=re.I):
        raise ValueError("SELECT * is blocked. Select explicit aggregate or non-sensitive columns.")

    return stripped


def connect():
    load_env()
    return psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        dbname=os.environ["REDSHIFT_DATABASE"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
        sslmode=os.getenv("REDSHIFT_SSLMODE", "require"),
        connect_timeout=int(os.getenv("REDSHIFT_CONNECT_TIMEOUT", "30")),
    )


def read_sql(args) -> str:
    if args.sql_file:
        return Path(args.sql_file).read_text(encoding="utf-8")
    if args.sql:
        return args.sql
    return sys.stdin.read()


def validate_internal_analysis_output(
    sql: str, columns: list[str], rows: list[dict]
) -> None:
    """Require a distinct-employee aggregate and a visible-safe cohort count."""
    if not re.search(r"\bcount\s*\(\s*distinct\b", sql, flags=re.I):
        raise ValueError(
            "internal_analysis with protected-category labels requires "
            "COUNT(DISTINCT employee_id) or an equivalent distinct-employee aggregate."
        )
    normalized = {str(column).lower() for column in columns}
    cohort_columns = (
        "employee_count",
        "eligible_employees",
        "population_count",
        "headcount",
    )
    cohort_column = next((column for column in cohort_columns if column in normalized), None)
    if cohort_column is None:
        raise ValueError(
            "internal_analysis with protected-category labels requires a cohort "
            "count column named employee_count, eligible_employees, population_count, "
            "or headcount."
        )
    too_small = []
    for row in rows:
        try:
            count = int(row.get(cohort_column))
        except (TypeError, ValueError):
            raise ValueError(
                f"The internal-analysis cohort column {cohort_column} must be numeric."
            )
        if count < MINIMUM_INTERNAL_ANALYSIS_COHORT:
            too_small.append(count)
    if too_small:
        raise ValueError(
            "internal_analysis returned a protected-category bucket below "
            f"n={MINIMUM_INTERNAL_ANALYSIS_COHORT}."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run guarded read-only Redshift SQL and print JSON.")
    parser.add_argument("--sql", help="SQL text. If omitted, stdin is used unless --sql-file is set.")
    parser.add_argument("--sql-file", help="Path to a .sql file.")
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument(
        "--reporting-mode",
        choices=("presentation", "internal_analysis"),
        default="presentation",
        help=(
            "presentation suppresses protected labels (default). "
            "internal_analysis permits approved protected-category labels only "
            "with distinct-employee aggregates and n >= 30."
        ),
    )
    args = parser.parse_args()

    if args.max_rows < 1 or args.max_rows > 1000:
        raise SystemExit("--max-rows must be between 1 and 1000.")

    try:
        sql = validate_readonly(read_sql(args))
    except Exception as exc:
        raise SystemExit(f"SQL rejected: {exc}")

    with connect() as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            if cur.description is None:
                print(json.dumps({"columns": [], "rows": [], "truncated": False}, indent=2))
                return
            columns = [desc.name for desc in cur.description]
            sensitive = sorted({col.lower() for col in columns} & SENSITIVE_OUTPUT_COLUMNS)
            rows = [dict(row) for row in cur.fetchmany(args.max_rows + 1)]

    if sensitive:
        allowed_internal = set(sensitive) <= INTERNAL_ANALYSIS_CATEGORY_COLUMNS
        if args.reporting_mode != "internal_analysis" or not allowed_internal:
            raise SystemExit(
                "Query result contains protected or restricted columns: "
                + ", ".join(sensitive)
                + ". Presentation outputs must suppress them. For an explicitly "
                "internal aggregate analysis, use --reporting-mode internal_analysis "
                "only for approved categorical fields."
            )
        try:
            validate_internal_analysis_output(sql, columns, rows)
        except ValueError as exc:
            raise SystemExit(f"Internal-analysis output rejected: {exc}")

    truncated = len(rows) > args.max_rows
    rows = rows[: args.max_rows]
    print(json.dumps({"columns": columns, "rows": rows, "truncated": truncated}, default=str, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()


