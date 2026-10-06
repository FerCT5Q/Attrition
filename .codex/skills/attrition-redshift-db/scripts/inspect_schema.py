import argparse
import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


DEFAULT_SLIDES_ROOT = Path(r"C:\Dev\Python\Slides")
DEFAULT_SCHEMA = "hrda"
DEFAULT_TABLE = "post_hire_monthly_worker_dtls"


SAFE_DISTRIBUTION_COLUMNS = [
    "employee_type",
    "worker_type",
    "job_family_group",
    "job_family",
    "level_grouped",
    "management_level",
    "region",
    "country",
]


CANDIDATE_TABLE_PATTERN_SQL = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = %s
  AND (
    table_name ILIKE '%%attr%%'
    OR table_name ILIKE '%%turn%%'
    OR table_name ILIKE '%%term%%'
    OR table_name ILIKE '%%worker%%'
    OR table_name ILIKE '%%hire%%'
    OR table_name ILIKE '%%emp%%'
  )
ORDER BY table_name
LIMIT 100
"""


def load_env() -> None:
    env_path = os.getenv("ATTRITION_REDSHIFT_ENV")
    if env_path:
        load_dotenv(env_path)
        return
    slides_root = Path(os.getenv("ATTRITION_SLIDES_ROOT", str(DEFAULT_SLIDES_ROOT)))
    load_dotenv(slides_root / ".env")


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


def query(conn, sql, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect HRDA Redshift schema without employee-level rows.")
    parser.add_argument("--schema", default=os.getenv("REDSHIFT_SCHEMA", DEFAULT_SCHEMA))
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--include-distributions", action="store_true")
    args = parser.parse_args()

    output = {"schema": args.schema, "table": args.table}

    with connect() as conn:
        conn.set_session(readonly=True, autocommit=True)
        output["columns"] = query(
            conn,
            """
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (args.schema, args.table),
        )
        output["candidate_tables"] = query(conn, CANDIDATE_TABLE_PATTERN_SQL, (args.schema,))

        column_names = {row["column_name"] for row in output["columns"]}
        if {"fis_mo_end_dt"}.issubset(column_names):
            output["profile"] = query(
                conn,
                f"""
                SELECT
                  COUNT(*) AS row_count,
                  MIN(fis_mo_end_dt) AS min_fis_mo_end_dt,
                  MAX(fis_mo_end_dt) AS max_fis_mo_end_dt
                FROM {args.schema}.{args.table}
                """,
            )

        if args.include_distributions:
            output["safe_distributions"] = {}
            for column in SAFE_DISTRIBUTION_COLUMNS:
                if column not in column_names:
                    continue
                output["safe_distributions"][column] = query(
                    conn,
                    f"""
                    SELECT {column}, COUNT(*) AS n
                    FROM {args.schema}.{args.table}
                    GROUP BY {column}
                    ORDER BY n DESC
                    LIMIT 20
                    """,
                )

    print(json.dumps(output, default=str, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
