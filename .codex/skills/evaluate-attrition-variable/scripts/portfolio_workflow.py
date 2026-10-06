#!/usr/bin/env python
"""Deterministic portfolio preflight and frozen-evidence contracts.

This module does not decide what a variable means. It validates and materializes
the semantic reasoning recorded in the run request and analysis catalog, builds
the dependency order, and derives evidence fields only from frozen query rows.
"""

from __future__ import annotations

import hashlib
import heapq
import html
import json
import math
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_HINTS = SKILL_ROOT / "references" / "semantic-hints.yaml"
QUALITATIVE_CRITERIA = ("source", "definition", "consistency", "join", "effort")
COMPARISON_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte"}
SENSITIVE_PATTERNS = (
    "employee_id", "empl_id", "emp_id", "name", "email", "gender", "race",
    "disability", "veteran", "citizenship", "birth", "address", "salary",
    "base_pay", "compensation_amount", "free_text", "comment",
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML object in {path}")
    return data


def normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(character for character in text if not unicodedata.combining(character))


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sql_hash(sql: str) -> str:
    return hashlib.sha256(sql.replace("\r\n", "\n").strip().encode("utf-8")).hexdigest()


def source_columns(variable: dict[str, Any]) -> list[str]:
    columns = (variable.get("source") or {}).get("columns") or []
    if isinstance(columns, str):
        columns = [columns]
    return [str(column).strip() for column in columns if str(column).strip()]


def intended_use(analysis: dict[str, Any]) -> Any:
    """Return the portable HR-use field while accepting the Attrition v4 alias."""
    return analysis.get("intended_use") or analysis.get("attrition_use")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return list(
        dict.fromkeys(
            str(item).strip()
            for item in values
            if item is not None and str(item).strip()
        )
    )


def normalize_problem_context(
    request: dict[str, Any],
    request_variables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize business context without inventing semantic evidence."""
    raw = request.get("problem_context")
    if raw is None:
        raw = request.get("context")
    if raw is None:
        raw = {}
    if isinstance(raw, str):
        raw = {"problem_statement": raw}
    if not isinstance(raw, dict):
        raise ValueError("run-request problem_context must be an object or string.")

    variables = list(request_variables or request.get("variables") or [])
    intended_uses = _string_list(
        [
            item.get("intended_use") or item.get("attrition_use")
            for item in variables
            if isinstance(item, dict)
        ]
    )
    populations = _string_list(
        [item.get("population") for item in variables if isinstance(item, dict)]
    )
    knowledge_dates = _string_list(
        [item.get("knowledge_date") for item in variables if isinstance(item, dict)]
    )

    scalar_aliases = {
        "problem_statement": ("problem_statement", "problem", "objective"),
        "decision_or_use_case": ("decision_or_use_case", "use_case", "decision"),
        "outcome": ("outcome", "target", "business_outcome"),
        "population": ("population",),
        "unit_of_analysis": ("unit_of_analysis", "grain"),
        "time_horizon": ("time_horizon",),
        "knowledge_boundary": ("knowledge_boundary", "prediction_cutoff"),
        "stakeholders": ("stakeholders", "owners"),
    }
    context: dict[str, Any] = {}
    for canonical, aliases in scalar_aliases.items():
        value = next((raw.get(alias) for alias in aliases if raw.get(alias)), None)
        if value is not None:
            context[canonical] = str(value).strip()

    source = "provided" if raw else "derived_from_variable_requests"
    context.setdefault(
        "problem_statement",
        "Evaluar conjuntamente un portafolio de variables de RH para determinar su utilidad, relación y preparación para el caso de uso configurado.",
    )
    context.setdefault(
        "decision_or_use_case",
        "; ".join(intended_uses[:6])
        or "Priorizar y diseñar variables de People Analytics con evidencia reproducible.",
    )
    if populations:
        context.setdefault("population", "; ".join(populations[:4]))
    if knowledge_dates:
        context.setdefault("knowledge_boundary", "; ".join(knowledge_dates[:4]))

    for field in (
        "constraints",
        "assumptions",
        "stakeholder_questions",
        "success_criteria",
        "portfolio_hypotheses",
        "linked_problem_elements",
    ):
        context[field] = _string_list(raw.get(field))

    relationships: list[dict[str, Any]] = []
    for index, item in enumerate(raw.get("known_relationships") or [], start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"problem_context known_relationships item {index} must be an object."
            )
        members = _string_list(item.get("variables") or item.get("concepts"))
        relationship = str(item.get("relationship") or "").strip()
        if len(members) < 2 or not relationship:
            raise ValueError(
                "Each known relationship requires at least two variables/concepts and a relationship."
            )
        relationships.append(
            {
                **item,
                "variables": members,
                "relationship": relationship,
                "why_relevant": str(item.get("why_relevant") or "").strip(),
                "source": item.get("source") or "problem_context",
            }
        )
    context["known_relationships"] = relationships
    context["source"] = raw.get("source") or source
    context["missing_fields"] = [
        field
        for field in (
            "problem_statement",
            "decision_or_use_case",
            "population",
            "knowledge_boundary",
        )
        if not context.get(field)
    ]
    context["completeness"] = (
        "complete" if not context["missing_fields"] else "partial"
    )
    return context


def normalized_metadata_config(
    variables: list[dict[str, Any]], config: dict[str, Any] | None = None
) -> dict[str, Any]:
    config = dict(config or {})
    default_schema = str(config.get("default_schema") or "public").strip()
    source_schemas = {
        str((variable.get("source") or {}).get("table") or "").split(".", 1)[0]
        for variable in variables
        if "." in str((variable.get("source") or {}).get("table") or "")
    }
    configured = config.get("search_schemas") or []
    if isinstance(configured, str):
        configured = [configured]
    search_schemas = list(
        dict.fromkeys(
            str(value).strip()
            for value in [*configured, *sorted(source_schemas), default_schema]
            if str(value).strip()
        )
    )
    return {
        "default_schema": default_schema,
        "search_schemas": search_schemas,
    }


def semantic_document(variable: dict[str, Any]) -> str:
    analysis = variable.get("analysis") or {}
    values: list[Any] = [
        variable.get("variable"), variable.get("definition"), variable.get("notes"),
        analysis.get("definition"), analysis.get("source_reasoning"),
        analysis.get("derivation_formula"), intended_use(analysis),
        " ".join(source_columns(variable)),
    ]
    values.extend(analysis.get("validation_focus") or [])
    return normalized_text(" ".join(str(value) for value in values if value))


def detected_cues(variable: dict[str, Any], hints: dict[str, Any]) -> list[dict[str, Any]]:
    document = semantic_document(variable)
    matches: list[dict[str, Any]] = []
    for cue in hints.get("cues") or []:
        terms = [normalized_text(value) for value in cue.get("match_any") or []]
        matched = sorted({term for term in terms if term and term in document})
        if matched:
            matches.append({
                "id": cue.get("id"),
                "labels": cue.get("labels") or [],
                "matched_terms": matched,
                "required_topics": cue.get("required_topics") or [],
                "material_question": cue.get("material_question"),
                "why_it_matters": cue.get("why_it_matters"),
                "recommended_hypothesis": cue.get("recommended_hypothesis"),
            })
    return matches


def privacy_classification(variable: dict[str, Any], hints: dict[str, Any]) -> dict[str, Any]:
    columns = source_columns(variable)
    sensitive = sorted({
        column for column in columns
        if any(pattern in column.lower() for pattern in SENSITIVE_PATTERNS)
    })
    exact_suppressed = set(
        ((hints.get("publication_policies") or {}).get("exact_value_suppressed_columns") or [])
    )
    exact = sorted(set(columns) & exact_suppressed)
    blocker = str(variable.get("blocker") or "none")
    return {
        "classification": (
            "restricted" if blocker == "sensitive_restricted" or sensitive
            else "external" if blocker == "external_third_party"
            else "standard_aggregate"
        ),
        "sensitive_columns": sensitive,
        "exact_value_suppressed_columns": exact,
        "publication_policy": (
            "Sólo bandas o percentiles agregados."
            if exact else "Sólo resultados agregados con cohortes permitidas."
        ),
    }


def metadata_requirements(
    variables: list[dict[str, Any]], metadata_config: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    settings = normalized_metadata_config(variables, metadata_config)
    requirements: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for variable in variables:
        source = variable.get("source") or {}
        table = str(source.get("table") or "").strip()
        if not table:
            continue
        parts = table.split(".", 1)
        schema, table_name = (
            parts if len(parts) == 2 else (settings["default_schema"], parts[0])
        )
        for column in source_columns(variable):
            key = (str(variable.get("variable")), schema, table_name, column)
            if key in seen:
                continue
            seen.add(key)
            requirements.append({
                "variable": key[0], "table_schema": schema,
                "table_name": table_name, "column_name": column,
            })
    return requirements


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_like_token(value: str) -> str:
    return value.replace("'", "''")


def build_metadata_discovery_sql(
    variables: list[dict[str, Any]], metadata_config: dict[str, Any] | None = None
) -> str:
    settings = normalized_metadata_config(variables, metadata_config)
    requirements = metadata_requirements(variables, settings)
    if not requirements:
        return (
            "SELECT CAST(NULL AS VARCHAR(128)) AS table_schema, "
            "CAST(NULL AS VARCHAR(128)) AS table_name, "
            "CAST(NULL AS VARCHAR(128)) AS column_name, "
            "CAST(NULL AS VARCHAR(128)) AS data_type, "
            "CAST(NULL AS INTEGER) AS ordinal_position, "
            "CAST('no_database_sources' AS VARCHAR(32)) AS discovery_reason WHERE 1 = 0"
        )
    tables = sorted({(item["table_schema"], item["table_name"]) for item in requirements})
    table_clause = " OR\n    ".join(
        f"(c.table_schema = {_sql_literal(schema)} AND c.table_name = {_sql_literal(table)})"
        for schema, table in tables
    )
    stop = {"employee", "manager", "field", "data", "status", "date", "item", "within", "from", "than", "past"}
    tokens: set[str] = set()
    for variable in variables:
        for token in re.findall(r"[a-z0-9]+", normalized_text(variable.get("variable"))):
            if len(token) >= 4 and token not in stop:
                tokens.add(token)
        for column in source_columns(variable):
            tokens.update(part for part in column.lower().split("_") if len(part) >= 4 and part not in stop)
    synonym_tokens = sorted(tokens)[:60]
    synonym_clause = " OR\n      ".join(
        f"LOWER(c.column_name) LIKE '%{_sql_like_token(token)}%'"
        for token in synonym_tokens
    ) or "1 = 0"
    search_schema_clause = ", ".join(
        _sql_literal(schema) for schema in settings["search_schemas"]
    )
    return f"""
SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ({table_clause}) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ({table_clause})
   OR (
      c.table_schema IN ({search_schema_clause})
      AND ({synonym_clause})
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
""".strip()


def summarize_metadata(
    variable: dict[str, Any], rows: list[dict[str, Any]],
    metadata_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = variable.get("source") or {}
    table = str(source.get("table") or "")
    if not table:
        return {"status": "not_applicable", "required": [], "found": [], "missing": [], "candidates": []}
    settings = normalized_metadata_config([variable], metadata_config)
    parts = table.split(".", 1)
    schema, table_name = (
        parts if len(parts) == 2 else (settings["default_schema"], parts[0])
    )
    available = {
        (str(row.get("table_schema")), str(row.get("table_name")), str(row.get("column_name")))
        for row in rows
    }
    required = source_columns(variable)
    found = [column for column in required if (schema, table_name, column) in available]
    missing = [column for column in required if column not in found]
    terms = {
        token for token in re.findall(r"[a-z0-9]+", semantic_document(variable))
        if len(token) >= 5
    }
    candidates: list[dict[str, Any]] = []
    for row in rows:
        column = str(row.get("column_name") or "")
        if column in required:
            continue
        column_terms = set(re.findall(r"[a-z0-9]+", normalized_text(column)))
        if terms & column_terms:
            candidates.append({
                "table": f"{row.get('table_schema')}.{row.get('table_name')}",
                "column": column,
                "data_type": row.get("data_type"),
            })
        if len(candidates) >= 12:
            break
    return {
        "status": "complete" if rows else "not_executed",
        "required": required,
        "found": found,
        "missing": missing,
        "candidates": candidates,
    }


def dependency_map(variables: list[dict[str, Any]]) -> dict[str, list[str]]:
    names = [str(variable.get("variable") or "") for variable in variables]
    known = set(names)
    dependencies: dict[str, list[str]] = {}
    for variable in variables:
        name = str(variable.get("variable") or "")
        analysis = variable.get("analysis") or {}
        raw = analysis.get("depends_on") or variable.get("depends_on") or []
        if isinstance(raw, str):
            raw = [raw]
        values = list(dict.fromkeys(str(value).strip() for value in raw if str(value).strip()))
        unknown = [value for value in values if value not in known]
        if unknown:
            raise ValueError(f"{name}: unknown dependencies {unknown}.")
        dependencies[name] = values
    return dependencies


def _strongly_connected_components(names: list[str], dependencies: dict[str, list[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        low[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for dependency in dependencies.get(node, []):
            if dependency not in indices:
                visit(dependency)
                low[node] = min(low[node], low[dependency])
            elif dependency in on_stack:
                low[node] = min(low[node], indices[dependency])
        if low[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(component)

    for name in names:
        if name not in indices:
            visit(name)
    return components


def stable_dependency_order(names: list[str], dependencies: dict[str, list[str]]) -> tuple[list[str], list[list[str]]]:
    position = {name: index for index, name in enumerate(names)}
    components = _strongly_connected_components(names, dependencies)
    component_of = {name: index for index, members in enumerate(components) for name in members}
    component_members = {
        index: sorted(members, key=position.get) for index, members in enumerate(components)
    }
    prerequisites: dict[int, set[int]] = {index: set() for index in component_members}
    dependents: dict[int, set[int]] = {index: set() for index in component_members}
    for name, deps in dependencies.items():
        dependent_component = component_of[name]
        for dependency in deps:
            prerequisite_component = component_of[dependency]
            if prerequisite_component == dependent_component:
                continue
            prerequisites[dependent_component].add(prerequisite_component)
            dependents[prerequisite_component].add(dependent_component)
    heap: list[tuple[int, int]] = []
    for component, required in prerequisites.items():
        if not required:
            heapq.heappush(heap, (min(position[name] for name in component_members[component]), component))
    ordered_components: list[int] = []
    while heap:
        _, component = heapq.heappop(heap)
        ordered_components.append(component)
        for dependent in sorted(dependents[component], key=lambda item: min(position[name] for name in component_members[item])):
            prerequisites[dependent].discard(component)
            if not prerequisites[dependent]:
                heapq.heappush(heap, (min(position[name] for name in component_members[dependent]), dependent))
    if len(ordered_components) != len(components):
        raise ValueError("Dependency condensation graph is unexpectedly cyclic.")
    order = [name for component in ordered_components for name in component_members[component]]
    cycles = [
        members for index, members in component_members.items()
        if len(members) > 1 or any(name in dependencies.get(name, []) for name in members)
    ]
    return order, cycles


def related_groups(variables: list[dict[str, Any]], cue_by_variable: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    column_members: dict[str, list[str]] = {}
    cue_members: dict[str, list[str]] = {}
    for variable in variables:
        name = str(variable.get("variable"))
        for column in source_columns(variable):
            column_members.setdefault(column, []).append(name)
        for cue in cue_by_variable.get(name, []):
            cue_members.setdefault(str(cue.get("id")), []).append(name)
    for column, members in sorted(column_members.items()):
        unique = list(dict.fromkeys(members))
        if len(unique) > 1:
            groups.append({"type": "shared_source_column", "key": column, "variables": unique})
    for cue, members in sorted(cue_members.items()):
        unique = list(dict.fromkeys(members))
        if len(unique) > 1:
            groups.append({"type": "shared_semantic_cue", "key": cue, "variables": unique})
    return groups


def contextual_relationships(
    variables: list[dict[str, Any]],
    dependencies: dict[str, list[str]],
    related: list[dict[str, Any]],
    problem_context: dict[str, Any],
) -> list[dict[str, Any]]:
    names = {str(variable.get("variable")) for variable in variables}
    relationships: list[dict[str, Any]] = []
    for item in problem_context.get("known_relationships") or []:
        members = [str(value) for value in item.get("variables") or []]
        relationships.append(
            {
                "type": "problem_context",
                "variables": members,
                "relationship": item.get("relationship"),
                "why_relevant": item.get("why_relevant"),
                "source": item.get("source") or "problem_context",
                "requested_variables": [value for value in members if value in names],
            }
        )
    for variable, prerequisites in dependencies.items():
        for prerequisite in prerequisites:
            relationships.append(
                {
                    "type": "dependency",
                    "variables": [prerequisite, variable],
                    "relationship": f"{variable} depende de {prerequisite}.",
                    "why_relevant": (
                        "La definición o disponibilidad del concepto base puede limitar "
                        "la evaluación de la variable derivada."
                    ),
                    "source": "analysis_catalog",
                    "requested_variables": [prerequisite, variable],
                }
            )
    for item in related:
        members = [str(value) for value in item.get("variables") or []]
        relationships.append(
            {
                "type": item.get("type"),
                "variables": members,
                "relationship": (
                    f"Comparten {item.get('key')} ({item.get('type')})."
                ),
                "why_relevant": (
                    "Puede orientar hipótesis conjuntas, pero cada variable conserva "
                    "su propia puerta de evidencia."
                ),
                "source": "portfolio_preflight",
                "requested_variables": members,
            }
        )
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in relationships:
        key = canonical_json_hash(
            {
                "type": item.get("type"),
                "variables": item.get("variables"),
                "relationship": item.get("relationship"),
            }
        )
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _count_values(values: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        label = str(value or "Por definir")
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def build_run_request(
    variables: list[dict[str, Any]],
    unknown_policy: str = "pause",
    problem_context: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    request_variables: list[dict[str, Any]] = []
    for variable in variables:
        analysis = variable.get("analysis") or {}
        population = variable.get("population") or {}
        request_item = {
            "name": variable.get("variable"),
            "intended_use": intended_use(analysis) or "Uso previsto por confirmar.",
            "population": population.get("display") or analysis.get("population") or "Población por confirmar.",
            "knowledge_date": analysis.get("prediction_cutoff") or "Fecha de conocimiento por confirmar.",
        }
        for field in (
            "context_role",
            "context_relevance",
            "linked_problem_elements",
            "related_variables",
        ):
            if analysis.get(field):
                request_item[field] = analysis[field]
        request_variables.append(request_item)
    request = {
        "schema_version": 1,
        "language": (
            ((variables[0].get("analysis") or {}).get("language"))
            if variables else "es"
        ) or "es",
        "unknown_policy": unknown_policy,
        "variables": request_variables,
        "decisions": {},
    }
    if problem_context is not None:
        request["problem_context"] = problem_context
    request["problem_context"] = normalize_problem_context(
        request, request_variables
    )
    return request


def validate_run_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    if int(request.get("schema_version") or 0) != 1:
        raise ValueError("run-request schema_version must be 1.")
    variables = request.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError("run-request requires a non-empty variables list.")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(variables, start=1):
        if isinstance(item, str):
            item = {"name": item}
        if not isinstance(item, dict):
            raise ValueError(f"run-request variable {index} must be a string or object.")
        name = str(item.get("name") or item.get("variable") or "").strip()
        if not name or name in seen:
            raise ValueError(f"run-request variable {index} has a missing or duplicate name.")
        seen.add(name)
        normalized_item = {**item, "name": name}
        for field in ("linked_problem_elements", "related_variables"):
            if field in normalized_item:
                normalized_item[field] = _string_list(normalized_item[field])
        normalized.append(normalized_item)
    request["problem_context"] = normalize_problem_context(request, normalized)
    return normalized


def build_portfolio_context(
    variables: list[dict[str, Any]],
    run_request: dict[str, Any],
    metadata_rows: list[dict[str, Any]] | None = None,
    metadata_query_reference: str | None = None,
    hints: dict[str, Any] | None = None,
    metadata_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hints = hints or load_yaml(DEFAULT_HINTS)
    metadata_config = normalized_metadata_config(variables, metadata_config)
    metadata_rows = list(metadata_rows or [])
    names = [str(variable.get("variable")) for variable in variables]
    if len(names) != len(set(names)):
        raise ValueError("Every portfolio variable must appear exactly once.")
    requested_variables = validate_run_request(run_request)
    request_by_name = {str(item.get("name")): item for item in requested_variables}
    problem_context = normalize_problem_context(run_request, requested_variables)
    dependencies = dependency_map(variables)
    evaluation_order, cycles = stable_dependency_order(names, dependencies)
    cue_by_variable = {name: detected_cues(variable, hints) for name, variable in zip(names, variables)}
    related = related_groups(variables, cue_by_variable)
    relationships = contextual_relationships(
        variables, dependencies, related, problem_context
    )
    entries: list[dict[str, Any]] = []
    for index, variable in enumerate(variables, start=1):
        name = names[index - 1]
        analysis = variable.get("analysis") or {}
        request_item = request_by_name.get(name) or {}
        variable_relationships = [
            item
            for item in relationships
            if name in (item.get("requested_variables") or item.get("variables") or [])
        ]
        entries.append({
            "original_index": index,
            "evaluation_index": evaluation_order.index(name) + 1,
            "variable": name,
            "probable_meaning": analysis.get("definition") or variable.get("definition"),
            "initial_semantic_type": analysis.get("semantic_type") or (variable.get("verification") or {}).get("semantic_type"),
            "components": {
                "source_table": (variable.get("source") or {}).get("table"),
                "source_columns": source_columns(variable),
                "derivation_formula": analysis.get("derivation_formula"),
            },
            "dependencies": dependencies[name],
            "semantic_cues": cue_by_variable[name],
            "privacy": privacy_classification(variable, hints),
            "metadata": summarize_metadata(variable, metadata_rows, metadata_config),
            "material_uncertainties": list(analysis.get("material_questions") or []),
            "context_alignment": {
                "role": request_item.get("context_role") or analysis.get("context_role") or "candidate_variable",
                "relevance": request_item.get("context_relevance") or intended_use(analysis),
                "linked_problem_elements": _string_list(
                    request_item.get("linked_problem_elements")
                    or analysis.get("linked_problem_elements")
                ),
                "related_variables": sorted(
                    {
                        member
                        for item in variable_relationships
                        for member in (item.get("requested_variables") or [])
                        if member != name
                    }
                ),
                "relationships": variable_relationships,
            },
        })
    decisions = run_request.get("decisions") or {}
    question_groups: list[dict[str, Any]] = []
    for cue in hints.get("cues") or []:
        affected = [name for name in names if any(item.get("id") == cue.get("id") for item in cue_by_variable[name])]
        if not affected:
            continue
        question_id = f"semantic:{cue.get('id')}"
        decision = decisions.get(question_id) or {}
        question_groups.append({
            "id": question_id,
            "variables": affected,
            "question": cue.get("material_question"),
            "why_it_matters": cue.get("why_it_matters"),
            "recommended_hypothesis": cue.get("recommended_hypothesis"),
            "decision": decision,
            "status": decision.get("status") or "unresolved",
        })
    for index, question in enumerate(
        problem_context.get("stakeholder_questions") or [], start=1
    ):
        question_id = f"context:stakeholder:{index:02d}"
        decision = decisions.get(question_id) or {}
        question_groups.append(
            {
                "id": question_id,
                "variables": names,
                "question": question,
                "why_it_matters": (
                    "La respuesta puede cambiar la relevancia, la ventana temporal, "
                    "la población o las relaciones que deben validarse."
                ),
                "recommended_hypothesis": (
                    "Usar el contexto declarado y mantener la pregunta como hipótesis "
                    "hasta que el stakeholder confirme la decisión."
                ),
                "decision": decision,
                "status": decision.get("status") or "context_input",
            }
        )
    semantic_counts = _count_values(
        [entry.get("initial_semantic_type") for entry in entries]
    )
    role_counts = _count_values(
        [(entry.get("context_alignment") or {}).get("role") for entry in entries]
    )
    source_tables = sorted(
        {
            str((entry.get("components") or {}).get("source_table"))
            for entry in entries
            if (entry.get("components") or {}).get("source_table")
        }
    )
    portfolio_overview = {
        "problem_statement": problem_context.get("problem_statement"),
        "decision_or_use_case": problem_context.get("decision_or_use_case"),
        "outcome": problem_context.get("outcome"),
        "population": problem_context.get("population"),
        "unit_of_analysis": problem_context.get("unit_of_analysis"),
        "knowledge_boundary": problem_context.get("knowledge_boundary"),
        "semantic_type_counts": semantic_counts,
        "context_role_counts": role_counts,
        "source_table_count": len(source_tables),
        "source_tables": source_tables,
        "relationship_count": len(relationships),
        "portfolio_hypotheses": problem_context.get("portfolio_hypotheses") or [],
        "success_criteria": problem_context.get("success_criteria") or [],
    }
    return {
        "schema_version": 1,
        "language": run_request.get("language") or "es",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "preflight_scope": "semántica, documentación y metadata; sin perfiles agregados de empleados",
        "problem_context": problem_context,
        "portfolio_overview": portfolio_overview,
        "variable_count": len(entries),
        "variables": entries,
        "original_order": names,
        "evaluation_order": evaluation_order,
        "dependencies": dependencies,
        "cycles": cycles,
        "related_concepts": related,
        "contextual_relationships": relationships,
        "material_questions": question_groups,
        "unresolved_material_question_count": sum(item["status"] == "unresolved" for item in question_groups),
        "metadata": {
            "query_reference": metadata_query_reference,
            "row_count": len(metadata_rows),
            "status": "executed" if metadata_rows else "not_executed",
            "default_schema": metadata_config["default_schema"],
            "search_schemas": metadata_config["search_schemas"],
        },
        "publication_policy": hints.get("publication_policies") or {},
    }


def render_portfolio_html(context: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value if value is not None else ""))

    variable_rows = "".join(
        "<tr>"
        f"<td>{entry['original_index']}</td><td>{entry['evaluation_index']}</td>"
        f"<td>{esc(entry['variable'])}</td><td>{esc(entry['initial_semantic_type'])}</td>"
        f"<td>{esc((entry.get('context_alignment') or {}).get('role'))}</td>"
        f"<td>{esc((entry.get('context_alignment') or {}).get('relevance'))}</td>"
        f"<td>{esc(', '.join(entry['dependencies']) or 'Ninguna')}</td>"
        f"<td>{esc(entry['metadata']['status'])}</td>"
        f"<td>{esc(entry['privacy']['classification'])}</td>"
        "</tr>"
        for entry in context.get("variables") or []
    )
    questions = "".join(
        "<section class='question'>"
        f"<h3>{esc(item['question'])}</h3>"
        f"<p><strong>Variables:</strong> {esc(', '.join(item['variables']))}</p>"
        f"<p><strong>Por qué cambia el assessment:</strong> {esc(item['why_it_matters'])}</p>"
        f"<p><strong>Hipótesis recomendada:</strong> {esc(item['recommended_hypothesis'])}</p>"
        f"<p><strong>Estado:</strong> {esc(item['status'])}</p>"
        "</section>"
        for item in context.get("material_questions") or []
    ) or "<p>No se detectaron preguntas materiales compartidas.</p>"
    problem = context.get("problem_context") or {}
    overview = context.get("portfolio_overview") or {}

    def list_html(values: list[Any], empty: str) -> str:
        items = "".join(f"<li>{esc(value)}</li>" for value in values)
        return f"<ul>{items}</ul>" if items else f"<p class='muted'>{esc(empty)}</p>"

    def count_bars(values: dict[str, Any]) -> str:
        maximum = max([int(value) for value in values.values()] or [1])
        rows = []
        for label, value in values.items():
            width = 100.0 * int(value) / maximum if maximum else 0
            rows.append(
                "<div class='count-row'>"
                f"<span>{esc(label)}</span><div class='count-track'><i style='width:{width:.2f}%'></i></div>"
                f"<b>{esc(value)}</b></div>"
            )
        return "".join(rows) or "<p class='muted'>Sin categorías.</p>"

    relationship_cards = "".join(
        "<article class='relationship'>"
        f"<div class='nodes'>{' <span>→</span> '.join(f'<b>{esc(value)}</b>' for value in item.get('variables') or [])}</div>"
        f"<p>{esc(item.get('relationship'))}</p>"
        f"<small>{esc(item.get('why_relevant'))}</small>"
        "</article>"
        for item in context.get("contextual_relationships") or []
    ) or "<p class='muted'>No se declararon relaciones contextuales.</p>"
    semantic_bars = count_bars(overview.get("semantic_type_counts") or {})
    role_bars = count_bars(overview.get("context_role_counts") or {})
    cycles = context.get("cycles") or []
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Preflight del portafolio</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:32px;color:#172033;line-height:1.4}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d7dce5;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f8}}.question{{border-left:4px solid #2b6cb0;padding:4px 16px;margin:18px 0;background:#f7f9fc}}.muted{{color:#5f6b7a}}.context-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.context-card{{border:1px solid #d7dce5;border-radius:8px;padding:14px;background:#f8fafc}}.context-card h3{{margin-top:0}}.overview-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}}.count-row{{display:grid;grid-template-columns:minmax(120px,1fr) 2fr 34px;align-items:center;gap:8px;margin:8px 0}}.count-track{{height:14px;background:#e8edf3;border-radius:8px;overflow:hidden}}.count-track i{{display:block;height:100%;background:#2b6cb0}}.relationship-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}.relationship{{border-left:4px solid #0f766e;background:#f3faf9;padding:12px}}.relationship p{{margin:8px 0}}.nodes{{color:#0f4c5c}}</style></head>
<body><h1>Preflight del portafolio de variables</h1>
<p>{esc(context.get('preflight_scope'))}. Variables: {context.get('variable_count')}.</p>
<p class="muted">Orden de evaluación: {esc(' → '.join(context.get('evaluation_order') or []))}</p>
<h2>Contexto del problema</h2><div class="context-grid">
<div class="context-card"><h3>Problema</h3><p>{esc(problem.get('problem_statement'))}</p></div>
<div class="context-card"><h3>Decisión / caso de uso</h3><p>{esc(problem.get('decision_or_use_case'))}</p></div>
<div class="context-card"><h3>Outcome y población</h3><p><b>Outcome:</b> {esc(problem.get('outcome') or 'Por confirmar')}<br><b>Población:</b> {esc(problem.get('population') or 'Por confirmar')}</p></div>
<div class="context-card"><h3>Tiempo y conocimiento</h3><p><b>Horizonte:</b> {esc(problem.get('time_horizon') or 'Por confirmar')}<br><b>Límite:</b> {esc(problem.get('knowledge_boundary') or 'Por confirmar')}</p></div>
</div>
<h2>Overview visual del portafolio</h2><div class="overview-grid">
<div><h3>Tipos semánticos</h3>{semantic_bars}</div>
<div><h3>Roles en el problema</h3>{role_bars}</div>
</div>
<h3>Hipótesis globales</h3>{list_html(overview.get('portfolio_hypotheses') or [], 'No se declararon hipótesis globales.')}
<h2>Mapa contextual de relaciones</h2><div class="relationship-grid">{relationship_cards}</div>
<h2>Inventario y dependencias</h2><table><thead><tr><th>Original</th><th>Evaluación</th><th>Variable</th><th>Tipo inicial</th><th>Rol contextual</th><th>Relevancia</th><th>Dependencias</th><th>Metadata</th><th>Privacidad</th></tr></thead><tbody>{variable_rows}</tbody></table>
<h2>Dudas materiales agrupadas</h2>{questions}
<h2>Ciclos</h2><p>{esc(cycles if cycles else 'No se detectaron ciclos.')}</p>
</body></html>"""


def _focus_criterion(focus: str, semantic_type: str) -> str:
    text = normalized_text(focus)
    if any(word in text for word in ("join", "grain", "unicidad", "employee-date", "snapshot")):
        return "join"
    if any(word in text for word in ("historia", "continuidad", "wave", "refresh", "vigencia")):
        return "history"
    if any(word in text for word in ("coverage", "observabilidad", "observable", "nulos", "missing")):
        return "coverage"
    if any(word in text for word in ("consistencia", "contradic", "mapping", "dominio", "alias", "ciclo", "transicion")):
        return "consistency"
    if any(word in text for word in ("esfuerzo", "ingenieria", "transformacion")):
        return "effort"
    if semantic_type == "external_source" and "defin" not in text:
        return "source"
    return "definition"


def _story_method_and_rule(focus: str, semantic_type: str, criterion: str) -> tuple[str, str]:
    text = normalized_text(focus)
    if any(word in text for word in ("flag", "fecha", "event", "evento")):
        return (
            "Reconciliación agregada del flag, la fecha efectiva y el snapshot.",
            "No deben quedar flags sin fecha, fechas sin flag, eventos futuros ni duplicados sin explicar.",
        )
    if any(word in text for word in ("ventana", "12 meses", "trailing", "leakage", "futuro", "frontera")):
        return (
            "Recálculo agregado con pruebas de frontera y fecha de conocimiento.",
            "Todos los eventos deben caer dentro de la ventana aprobada y conocerse al snapshot; los casos límite deben reconciliarse.",
        )
    if any(word in text for word in ("mapping", "grupo", "nivel", "family", "contradic")):
        return (
            "Cruce agregado detalle-grupo por snapshot y comparación longitudinal del mapping.",
            "No deben quedar contradicciones, valores sin mapping ni cambios de versión sin explicación.",
        )
    if any(word in text for word in ("manager", "jerarquia", "raiz", "ciclo", "cadena", "ceo")):
        return (
            "Reconstrucción agregada de cadenas dentro del mismo snapshot.",
            "Las cadenas deben resolver sin ciclos; raíces, convergencia y semántica gobernada de la raíz deben validarse por separado.",
        )
    if any(word in text for word in ("ratio", "formula", "componente", "lineage", "promedio", "index")):
        return (
            "Recálculo independiente o lineage autoritativo con reconciliación agregada.",
            "La fórmula, componentes, población, unidad, tolerancia y redondeo deben estar definidos y cumplir la reconciliación.",
        )
    if criterion == "join":
        return (
            "Reconciliación agregada del join en el grain empleado-fecha objetivo.",
            "Cada elegible debe producir exactamente un match temporal, sin unmatched, duplicados ni multi-match.",
        )
    if criterion in {"coverage", "history"}:
        return (
            "Perfil agregado por fecha con elegibles, observables e historia utilizable.",
            "Coverage e historia deben cumplir los umbrales v4 en la población y frecuencia declaradas.",
        )
    contracts = {
        "direct_field": ("Auditoría agregada del campo directo, dominio y grain.", "El campo debe corresponder al concepto, tener dominio interpretable y grain temporal único."),
        "precomputed_metric": ("Reconciliación agregada de la métrica almacenada.", "El cálculo independiente o lineage reconciliado debe cumplir la tolerancia declarada."),
        "grouped_mapping": ("Auditoría agregada del mapping y su vigencia.", "El mapping debe ser completo, no contradictorio y estable o versionado."),
        "derived_feature": ("Recálculo agregado time-safe de la derivación.", "La fórmula completa debe reconciliar fronteras, deduplicación, nulos y leakage."),
        "hierarchy": ("Reconstrucción agregada de la jerarquía por snapshot.", "Raíces, ciclos, cadenas no resueltas, profundidad y semántica de raíz deben pasar."),
        "survey": ("Auditoría agregada de waves, elegibilidad y join temporal.", "Acceso, waves, codificación, comparabilidad y join deben estar confirmados."),
        "external_source": ("Confirmación documentada y agregada de acceso, owner, refresh y join.", "La fuente y su ruta aprobada deben estar vigentes antes de asignar score 2."),
    }
    return contracts.get(semantic_type, ("Validación agregada específica del concepto.", "La regla declarada debe cumplirse sin excepciones pendientes."))


def materialize_validation_stories(
    variable: dict[str, Any], *, allow_legacy_focus: bool = False
) -> list[dict[str, Any]]:
    analysis = variable.get("analysis") or {}
    semantic_type = str(analysis.get("semantic_type") or "")
    configured = analysis.get("validation_story") or []
    if configured:
        stories = [dict(item) for item in configured]
    else:
        if not allow_legacy_focus:
            raise ValueError(
                f"{variable.get('variable')}: an explicit validation_story is required. "
                "validation_focus may orient Codex but cannot become a validation automatically."
            )
        focus = analysis.get("validation_focus") or []
        if not isinstance(focus, list) or not focus:
            raise ValueError(f"{variable.get('variable')}: an explicit validation story or validation_focus is required.")
        stories = []
        for index, raw in enumerate(focus, start=1):
            if isinstance(raw, dict):
                item = dict(raw)
                sentence = str(item.get("question") or item.get("focus") or "")
            else:
                item = {}
                sentence = str(raw).strip()
            if not sentence:
                raise ValueError(f"{variable.get('variable')}: validation focus {index} is empty.")
            criterion = str(item.get("criterion") or _focus_criterion(sentence, semantic_type))
            method, rule = _story_method_and_rule(sentence, semantic_type, criterion)
            if " porque " in sentence:
                question_body, reason = sentence.split(" porque ", 1)
                generated_why = (
                    "Esta comprobación es necesaria porque "
                    f"{reason.strip().rstrip('.')}."
                )
            else:
                question_body = sentence
                reason = str(analysis.get("source_reasoning") or sentence)
                generated_why = (
                    "Esta comprobación es necesaria para interpretar la variable: "
                    f"{reason.strip().rstrip('.')}."
                )
            if normalized_text(question_body).startswith("validamos "):
                question_body = question_body[len("Validamos "):]
            stories.append({
                "id": item.get("id") or f"focus_{index:02d}",
                "criterion": criterion,
                "evidence_role": item.get("evidence_role") or ("contextual" if "contexto" in normalized_text(sentence) else "defining"),
                "question": item.get("question") or f"¿Cómo validamos {question_body.rstrip('.')}?",
                "why": item.get("why") or generated_why,
                "fields": item.get("fields") or source_columns(variable),
                "method": item.get("method") or method,
                "sql_reference": item.get("sql_reference"),
                "acceptance_rule": item.get("acceptance_rule") or rule,
                "metric_checks": item.get("metric_checks") or [],
                "story_source": "legacy_catalog_validation_focus",
            })
    for index, story in enumerate(stories, start=1):
        required = ("id", "criterion", "evidence_role", "question", "why", "method", "acceptance_rule")
        missing = [field for field in required if not story.get(field)]
        if missing:
            raise ValueError(f"{variable.get('variable')}: validation story {index} is missing {missing}.")
        if story["evidence_role"] not in {"defining", "supporting", "contextual"}:
            raise ValueError(f"{variable.get('variable')}: validation story {index} has invalid evidence_role.")
        if not str(story["question"]).startswith("¿"):
            raise ValueError(f"{variable.get('variable')}: validation story {index} must be an explicit Spanish question.")
    return stories


def build_pre_execution_plan(
    variable: dict[str, Any], portfolio_entry: dict[str, Any], version: int = 1,
    inherited_conditions: list[dict[str, Any]] | None = None,
    shared_context: dict[str, Any] | None = None,
    documentation_context: dict[str, Any] | None = None,
    accumulated_knowledge: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    analysis = variable.get("analysis") or {}
    stories = materialize_validation_stories(
        variable,
        allow_legacy_focus=bool(analysis.get("allow_legacy_story_materialization")),
    )
    return {
        "schema_version": 1,
        "plan_version": int(analysis.get("plan_version") or version),
        "language": analysis.get("language") or "es",
        "created_before_execution": True,
        "variable": variable.get("variable"),
        "concept": analysis.get("definition") or variable.get("definition"),
        "intended_use": intended_use(analysis),
        "attrition_use": analysis.get("attrition_use") or intended_use(analysis),
        "knowledge_date": analysis.get("prediction_cutoff"),
        "population": (variable.get("population") or {}).get("display") or analysis.get("population"),
        "grain": variable.get("level_data"),
        "semantic_type": analysis.get("semantic_type"),
        "source_reasoning": analysis.get("source_reasoning"),
        "plan_authorship": {
            "mode": analysis.get("plan_authorship") or (
                "legacy_catalog" if analysis.get("allow_legacy_story_materialization") else "codex_explicit"
            ),
            "revision_reason": analysis.get("plan_revision_reason"),
            "generated_story_fallback": bool(
                analysis.get("allow_legacy_story_materialization")
                and not analysis.get("validation_story")
            ),
        },
        "dependencies": portfolio_entry.get("dependencies") or [],
        "inherited_conditions": inherited_conditions or [],
        "shared_context": {
            "problem_context": (shared_context or {}).get("problem_context") or {},
            "portfolio_overview": (shared_context or {}).get("portfolio_overview") or {},
            "current_variable_alignment": portfolio_entry.get("context_alignment") or {},
            "contextual_relationships": (
                (portfolio_entry.get("context_alignment") or {}).get("relationships")
                or []
            ),
            "documentation_context": documentation_context or {},
            "accumulated_knowledge": accumulated_knowledge or [],
            "context_is_evidence": False,
            "usage_rule": (
                "Usar el contexto compartido y la documentación acumulada para orientar "
                "hipótesis y validaciones; revalidar cada claim con evidencia propia."
            ),
        },
        "validation_story": stories,
        "planned_sql": sorted({str(item.get("sql_reference")) for item in stories if item.get("sql_reference")}),
        "acceptance_rules_frozen": True,
    }


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _aggregate(values: list[float], operation: str) -> float | int | None:
    if not values:
        return None
    if operation == "sum":
        result = sum(values)
    elif operation == "min":
        result = min(values)
    elif operation == "max":
        result = max(values)
    elif operation == "average":
        result = sum(values) / len(values)
    elif operation == "first":
        result = values[0]
    elif operation == "last":
        result = values[-1]
    else:
        raise ValueError(f"Unsupported metric aggregation: {operation}")
    return int(result) if float(result).is_integer() else round(float(result), 8)


def rows_for_variable(rows: list[dict[str, Any]], variable_name: str) -> list[dict[str, Any]]:
    if any("variable_name" in row for row in rows):
        selected = [row for row in rows if str(row.get("variable_name")) == variable_name]
        return selected
    return rows


def calculate_metrics(rows: list[dict[str, Any]], item: dict[str, Any], variable_name: str) -> dict[str, Any]:
    selected = rows_for_variable(rows, variable_name)
    metrics: dict[str, Any] = {}
    metric_map = item.get("metric_map") or {}
    if metric_map:
        for output_name, spec in metric_map.items():
            if isinstance(spec, str):
                spec = {"column": spec, "aggregate": "sum"}
            column = str(spec.get("column") or output_name)
            operation = str(spec.get("aggregate") or "sum")
            values = [float(row[column]) for row in selected if _numeric(row.get(column))]
            metrics[str(output_name)] = _aggregate(values, operation)
    checks = item.get("metric_checks") or item.get("acceptance_checks") or []
    for check in checks:
        metric = str(check.get("metric") or "")
        if not metric:
            continue
        values = [float(row[metric]) for row in selected if _numeric(row.get(metric))]
        metrics[metric] = _aggregate(values, str(check.get("aggregate") or "sum"))
    if not metric_map:
        numeric_columns = sorted({key for row in selected for key, value in row.items() if _numeric(value)})
        for column in numeric_columns:
            if column in metrics:
                continue
            values = [float(row[column]) for row in selected if _numeric(row.get(column))]
            if len(selected) <= 1:
                operation = "first"
            elif column.endswith(("_percent", "_rate", "_ratio")):
                operation = "min"
            else:
                operation = "sum"
            metrics[column] = _aggregate(values, operation)
    return metrics


def compare(observed: float, operator: str, threshold: float) -> bool:
    if operator == "eq": return observed == threshold
    if operator == "ne": return observed != threshold
    if operator == "gt": return observed > threshold
    if operator == "gte": return observed >= threshold
    if operator == "lt": return observed < threshold
    if operator == "lte": return observed <= threshold
    raise ValueError(f"Unsupported comparison operator: {operator}")


def computed_outcome(
    variable: dict[str, Any], criterion: str, item: dict[str, Any],
    rows: list[dict[str, Any]], metrics: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    checks = item.get("metric_checks") or item.get("acceptance_checks") or []
    evaluated: list[dict[str, Any]] = []
    if checks:
        pending = False
        for check in checks:
            metric = str(check.get("metric") or "")
            operator = str(check.get("operator") or "")
            threshold = check.get("threshold")
            observed = metrics.get(metric)
            if not _numeric(observed) or operator not in COMPARISON_OPERATORS or not _numeric(threshold):
                pending = True
                passed = False
            else:
                passed = compare(float(observed), operator, float(threshold))
            evaluated.append({"metric": metric, "observed": observed, "operator": operator, "threshold": threshold, "passed": passed})
        if pending:
            return "pending", evaluated
        return ("pass" if all(check["passed"] for check in evaluated) else "fail"), evaluated

    selected = rows_for_variable(rows, str(variable.get("variable")))
    if not selected:
        return "pending", evaluated
    method = str(item.get("method") or "")
    semantic_type = str(((variable.get("verification") or {}).get("semantic_type") or (variable.get("analysis") or {}).get("semantic_type") or ""))
    if method == "schema_access_check":
        if _numeric(metrics.get("missing_items")):
            return ("pass" if float(metrics["missing_items"]) == 0 else "fail"), evaluated
        return "pending", evaluated
    if criterion == "definition":
        if semantic_type in {"precomputed_metric", "derived_feature"}:
            mismatch = metrics.get("mismatch_count", metrics.get("discrepancy_count"))
            rate = metrics.get("match_rate_percent")
            tolerance = item.get("minimum_match_rate_percent")
            if _numeric(mismatch) and _numeric(rate) and _numeric(tolerance):
                return ("pass" if float(mismatch) == 0 and float(rate) >= float(tolerance) else "fail"), evaluated
            return "pending", evaluated
        if semantic_type == "hierarchy":
            required = ("unresolved_count", "cycle_count", "root_semantics_pass")
            if all(_numeric(metrics.get(key)) for key in required):
                passed = float(metrics["unresolved_count"]) == 0 and float(metrics["cycle_count"]) == 0 and float(metrics["root_semantics_pass"]) == 1
                return ("pass" if passed else "fail"), evaluated
            return "pending", evaluated
        if semantic_type == "grouped_mapping":
            contradiction = metrics.get("contradiction_count", metrics.get("mismatch_count"))
            unmapped = metrics.get("unmapped_count")
            if _numeric(contradiction) and _numeric(unmapped):
                return ("pass" if float(contradiction) == 0 and float(unmapped) == 0 else "fail"), evaluated
            return "pending", evaluated
        eligible = metrics.get("eligible_count", metrics.get("eligible_rows"))
        populated = metrics.get("populated_count", metrics.get("populated_rows"))
        distinct = metrics.get("distinct_count", metrics.get("distinct_values"))
        if all(_numeric(value) for value in (eligible, populated, distinct)):
            passed = float(eligible) > 0 and 0 < float(populated) <= float(eligible) and float(distinct) > 0
            return ("pass" if passed else "fail"), evaluated
        return "pending", evaluated
    if criterion == "consistency":
        anomaly_keys = [key for key in metrics if key.endswith(("anomaly_count", "invalid_count", "unexplained_change_count", "contradiction_count"))]
        if anomaly_keys:
            return ("pass" if all(float(metrics[key]) == 0 for key in anomaly_keys) else "fail"), evaluated
        return "pending", evaluated
    if criterion == "join":
        blockers = [metrics.get(key) for key in ("unmatched_count", "unmatched_rows", "duplicate_count", "duplicate_rows", "multi_match_count") if key in metrics]
        matched = metrics.get("matched_count", metrics.get("matched_rows"))
        if blockers and _numeric(matched):
            return ("pass" if float(matched) > 0 and all(_numeric(value) and float(value) == 0 for value in blockers) else "fail"), evaluated
        return "pending", evaluated
    if criterion == "effort" and method == "direct_field_inspection":
        direct = semantic_type == "direct_field" and not (variable.get("derivation_options") or variable.get("derivations"))
        return ("pass" if direct else "fail"), evaluated
    return "pending", evaluated


def freeze_variable_evidence(
    variable: dict[str, Any], query_records: dict[str, dict[str, Any]],
    rules: dict[str, Any], execution_source: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    frozen = json.loads(json.dumps(variable, default=str))
    verification = frozen.setdefault("verification", {})
    caps: list[dict[str, Any]] = []
    outcomes = rules.get("validation_outcomes") or {"pass": 2, "warning": 1, "pending": 1, "fail": 0, "blocked": 0}
    variable_name = str(frozen.get("variable"))
    for criterion in QUALITATIVE_CRITERIA:
        item = verification.get(criterion)
        if not isinstance(item, dict):
            continue
        reference = str(item.get("query_reference") or "").split("#", 1)[0].strip()
        record = query_records.get(reference)
        declared_metrics = item.get("metrics")
        declared_outcome = item.get("outcome")
        rows = list((record or {}).get("rows") or [])
        metrics = calculate_metrics(rows, item, variable_name) if record else {}
        outcome, checks = computed_outcome(frozen, criterion, item, rows, metrics) if record else ("pending", [])
        item["declared_metrics_ignored"] = declared_metrics
        item["declared_outcome_ignored"] = declared_outcome
        item["metrics"] = metrics
        item["outcome"] = outcome
        item["as_of_date"] = str((record or {}).get("executed_at") or datetime.now().date().isoformat())[:10]
        item["result"] = (
            "La regla calculada con resultados congelados se cumplió."
            if outcome == "pass" else
            "La regla calculada con resultados congelados no se cumplió."
            if outcome == "fail" else
            "Los resultados congelados no permiten confirmar la regla."
        )
        item["computed_checks"] = checks
        item["_provenance"] = {
            "executed": bool(record),
            "source": execution_source,
            "query_reference": reference,
            "sql_sha256": (record or {}).get("sql_sha256"),
            "result_sha256": (record or {}).get("result_sha256"),
            "reused_from": (record or {}).get("reused_from"),
        }
        if outcome != "pass":
            max_score = int(outcomes.get(outcome, 1))
            caps.append({
                "criterion": criterion,
                "max_score": max_score,
                "status_rule": f"La evidencia ejecutada de {criterion} tuvo outcome {outcome} y limita el score a {max_score}",
                "reason": "La evidencia definitoria ejecutada no pasó o permanece pendiente.",
                "evidence": f"Consulta {reference or 'no disponible'}; métricas calculadas: {metrics}.",
                "recommended_action": "Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.",
                "scoring_method": "Outcome calculado desde SQL congelado",
                "query_reference": reference or None,
                "outcome": outcome,
            })
    validations = frozen.get("scoring_validations") or frozen.get("validations") or []
    if isinstance(validations, dict):
        validations = validations.get("items") or []
    for validation in validations if isinstance(validations, list) else []:
        if not isinstance(validation, dict):
            continue
        reference = str(validation.get("sql_reference") or validation.get("query_reference") or "").split("#", 1)[0].strip()
        record = query_records.get(reference)
        rows = list((record or {}).get("rows") or [])
        metrics = calculate_metrics(rows, validation, variable_name) if record else {}
        metric = str(validation.get("metric") or "")
        if metric:
            validation["declared_observed_ignored"] = validation.get("observed")
            validation["observed"] = metrics.get(metric)
        if (
            record
            and metric
            and str(validation.get("operator") or "") in COMPARISON_OPERATORS
            and _numeric(validation.get("observed"))
            and _numeric(validation.get("threshold"))
        ):
            passed = compare(
                float(validation["observed"]),
                str(validation["operator"]),
                float(validation["threshold"]),
            )
            outcome = "pass" if passed else "fail"
            checks = [{
                "metric": metric,
                "observed": validation["observed"],
                "operator": validation["operator"],
                "threshold": validation["threshold"],
                "passed": passed,
            }]
        else:
            outcome, checks = computed_outcome(
                frozen,
                str(validation.get("criterion") or "definition"),
                validation,
                rows,
                metrics,
            ) if record else ("pending", [])
        validation["declared_outcome_ignored"] = validation.get("outcome")
        validation["outcome"] = outcome
        calculated_max = int(outcomes.get(outcome, 1))
        if "max_score" in validation:
            validation["max_score"] = min(int(validation["max_score"]), calculated_max)
        else:
            validation["max_score"] = calculated_max
        validation["computed_metrics"] = metrics
        validation["computed_checks"] = checks
        validation["_provenance"] = {
            "executed": bool(record), "source": execution_source,
            "sql_sha256": (record or {}).get("sql_sha256"),
            "result_sha256": (record or {}).get("result_sha256"),
        }
    frozen["_computed_verification_caps"] = caps
    return frozen, caps


def evidence_identity(variable: dict[str, Any], item: dict[str, Any], sql_sha256: str) -> str:
    analysis = variable.get("analysis") or {}
    population = variable.get("population") or {}
    payload = {
        "claim": item.get("claim") or item.get("acceptance_rule"),
        "population": population.get("display") or population,
        "grain": variable.get("level_data"),
        "window": analysis.get("prediction_cutoff"),
        "sql_sha256": sql_sha256,
    }
    return canonical_json_hash(payload)


def make_query_record(
    reference: str, sql: str, rows: list[dict[str, Any]], purpose: str,
    variable: dict[str, Any], item: dict[str, Any], source: str,
    reused_from: str | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    sql_sha = sql_hash(sql)
    selected_rows = rows_for_variable(rows, str(variable.get("variable")))
    metrics = calculate_metrics(rows, item, str(variable.get("variable")))
    return {
        "query_reference": reference,
        "purpose": purpose,
        "claim": item.get("claim") or item.get("acceptance_rule"),
        "population": (variable.get("population") or {}).get("display") or variable.get("population"),
        "grain": variable.get("level_data"),
        "window": (variable.get("analysis") or {}).get("prediction_cutoff"),
        "executed_at": executed_at,
        "source": source,
        "sql_sha256": sql_sha,
        "result_sha256": canonical_json_hash(rows),
        "evidence_identity": evidence_identity(variable, item, sql_sha),
        "row_count": len(rows),
        "selected_row_count": len(selected_rows),
        "metrics": metrics,
        "rows": rows,
        "reused_from": reused_from,
    }


def decision_document(assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "variable": assessment.get("variable"),
        "scores": assessment.get("scores"),
        "total": assessment.get("total"),
        "point_result": assessment.get("point_result"),
        "blocker": {"key": assessment.get("blocker_key"), "label": assessment.get("blocker_label")},
        "final_result": assessment.get("result"),
        "automatic_caps": (assessment.get("diagnostics") or {}).get("score_cap_details") or {},
        "inherited_conditions": assessment.get("inherited_conditions") or [],
        "reused_evidence": assessment.get("reused_evidence") or [],
        "limitations": [item for item in assessment.get("score_rationales") or []],
        "recommended_actions": [item.get("recommended_action") for item in assessment.get("score_rationales") or [] if item.get("recommended_action")],
    }
