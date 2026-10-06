"""Adapter for the v4 runner that preserves SQL guarding on Redshift.

The Redshift driver rejects `SET TRANSACTION READ ONLY` for some analytic CTE
plans even though the statement has already passed the strict SELECT/WITH
validator. This adapter reuses the project Redshift skill's connection and
validator, enables autocommit as the skill CLI does, and exposes no write path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


SKILL_HELPER = (
    Path(__file__).resolve().parents[1]
    / ".codex"
    / "skills"
    / "attrition-redshift-db"
    / "scripts"
    / "run_readonly_query.py"
)

spec = importlib.util.spec_from_file_location("attrition_redshift_readonly", SKILL_HELPER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load guarded Redshift helper: {SKILL_HELPER}")
_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_helper)

psycopg2 = _helper.psycopg2
validate_readonly = _helper.validate_readonly
SENSITIVE_OUTPUT_COLUMNS = _helper.SENSITIVE_OUTPUT_COLUMNS


class _AutocommitGuardedConnection:
    """Connection facade retaining the helper's SELECT-only validator."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def __enter__(self) -> "_AutocommitGuardedConnection":
        # Do not delegate to psycopg2's context manager.  Its ``__exit__``
        # performs transaction handling that is unnecessary for the
        # autocommit-only, SELECT-validated session used here and can mask a
        # server-side query failure with a second ``connection already
        # closed`` exception.
        return self

    def __exit__(self, *args: Any) -> Any:
        # The assessment runner may surface a server-side cancellation after
        # Redshift has already closed the socket.  Closing an already closed
        # psycopg2 connection is safe, whereas delegating to its context
        # manager can raise a misleading InterfaceError and hide the original
        # database error.
        if not self._connection.closed:
            self._connection.close()
        return False

    def set_session(self, **_: Any) -> None:
        # Match the guarded CLI's execution mode. SQL has already been checked
        # by validate_readonly before this method is called by the v4 runner.
        self._connection.autocommit = True

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        return self._connection.cursor(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


def connect() -> _AutocommitGuardedConnection:
    return _AutocommitGuardedConnection(_helper.connect())
