#!/usr/bin/env python
"""Run a reproducible v4 variable assessment with project-supplied configuration."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml

import profile_variable as profiler
import portfolio_workflow as workflow
import render_assessment as renderer


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RULES = SKILL_ROOT / "references" / "scoring-rules.yaml"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "output" / "assessments"
DEFAULT_PROJECT_CONFIG = PROJECT_ROOT / "config" / "variable_assessment_project.yaml"
DEFAULT_DOCUMENTATION_ROOT = PROJECT_ROOT / "docs" / "variables"
REPORT_SQL_ROOT = PROJECT_ROOT / "queries" / "profiles"
SAFE_VALUE_TOP_N = 10
SAFE_VALUE_FULL_N = 25
# Baseline de privacidad: nunca se liberan identidad, domicilios, texto libre ni
# compensación exacta. Las etiquetas de categorías protegidas se controlan por
# modo de entrega y sólo pueden verse en agregados internos con n suficiente.
HR_SENSITIVE_VALUE_COLUMNS = {
    "employee_id",
    "emp_name",
    "name",
    "legal_first_name",
    "legal_last_name",
    "preferred_first_name",
    "email",
    "manager_work_email",
    "supervisor_email",
    "supervisor_emplid",
    "supervisor_name",
    "manager_employee_id",
    "manager_name",
    "dept_head_name",
    "gender",
    "race",
    "disability_status",
    "veteran_status_identification",
    "dateofbirth",
    "year_of_birth",
    "month_of_birth",
    "primary_citizenship",
    "secondary_citizenship",
    "country_of_birth_locale_sensitive",
    "annual_base_pay",
    "base_pay_rate",
    "total_base_pay_amount",
    "fte_annual_base_pay",
    "compa_ratio",
    "homeaddresswithcountry",
    "home_city",
    "home_state",
    "postal_code",
}
SENSITIVE_VALUE_COLUMNS = HR_SENSITIVE_VALUE_COLUMNS | set(
    (
        workflow.load_yaml(workflow.DEFAULT_HINTS).get("publication_policies")
        or {}
    ).get("exact_value_suppressed_columns")
    or []
)
REPORTING_MODE = "presentation"
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
SUPPRESSED_VALUE_PATTERNS = (
    "comment",
    "free_text",
    "text",
    "salary",
    "pay",
    "compensation_amount",
    "address",
    "birth",
    "citizenship",
    "gender",
    "race",
    "disability",
    "veteran",
    "email",
    "name",
    "leader",
    "_id",
    "date",
)

SEMANTIC_ANALYSIS_MODULES = {
    "direct_field": [
        "source_schema",
        "domain_profile",
        "longitudinal_stability",
        "employee_date_grain",
    ],
    "precomputed_metric": [
        "source_schema",
        "formula_lineage",
        "safe_numeric_distribution",
        "independent_reconciliation",
        "temporal_stability",
    ],
    "grouped_mapping": [
        "source_schema",
        "domain_profile",
        "mapping_contradictions",
        "unmapped_values",
        "mapping_changes_over_time",
    ],
    "derived_feature": [
        "component_availability",
        "derivation_formula",
        "boundary_cases",
        "future_information_leakage",
        "aggregate_reconciliation",
    ],
    "hierarchy": [
        "same_snapshot_chain",
        "roots_and_convergence",
        "cycle_detection",
        "unresolved_chains",
        "depth_reconciliation",
        "root_semantics",
    ],
    "survey": [
        "wave_eligibility",
        "response_observability",
        "item_or_composite_definition",
        "cross_wave_comparability",
        "time_safe_snapshot_join",
    ],
    "external_source": [
        "approved_access",
        "source_owner",
        "grain_and_history",
        "publication_or_refresh_lag",
        "approved_join",
    ],
}

SEMANTIC_VISUALIZATIONS = {
    "direct_field": ["coverage_history", "safe_value_distribution"],
    "precomputed_metric": ["coverage_history", "safe_numeric_bands", "reconciliation"],
    "grouped_mapping": ["coverage_history", "safe_value_distribution", "mapping_summary"],
    "derived_feature": ["coverage_history", "component_or_event_observability", "derivation_status"],
    "hierarchy": ["coverage_history", "hierarchy_outcomes", "depth_distribution"],
    "survey": ["wave_coverage", "response_observability", "comparability_status"],
    "external_source": ["source_readiness"],
}

SEMANTIC_PUBLIC_REQUIREMENTS = {
    "direct_field": (
        "confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo"
    ),
    "precomputed_metric": (
        "obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia"
    ),
    "grouped_mapping": (
        "validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales"
    ),
    "derived_feature": (
        "aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage"
    ),
    "hierarchy": (
        "reconstruir cadenas por snapshot y validar raíces, ciclos, profundidad, convergencia y semántica de la raíz"
    ),
    "survey": (
        "confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta"
    ),
    "external_source": (
        "confirmar acceso aprobado, propietario, grain, historia, refresh y join de la fuente externa"
    ),
}

VALIDATION_STORY_REQUIRED_FIELDS = (
    "question",
    "why",
    "criterion",
    "evidence_role",
    "fields",
    "population",
    "grain",
    "temporal_boundary",
    "method",
    "sql_references",
    "acceptance_rule",
    "observed_evidence",
    "outcome_label",
    "interpretation",
    "score_effect",
    "limitation",
    "recommended_action",
)

SPANISH_CONTEXT_MARKERS = (
    " el ",
    " la ",
    " los ",
    " las ",
    " de ",
    " del ",
    " que ",
    " para ",
    " por ",
    " porque ",
    " una ",
    " un ",
    " se ",
    " no ",
    " con ",
    " en ",
    " desde ",
    " hasta ",
    " requiere ",
    " reciente",
    " durante ",
    " información ",
)


def spanish_semantic_label(semantic_type: str) -> str:
    return {
        "direct_field": "campo directo",
        "precomputed_metric": "métrica precalculada",
        "grouped_mapping": "mapping agrupado",
        "derived_feature": "feature derivada",
        "hierarchy": "jerarquía",
        "survey": "encuesta",
        "external_source": "fuente externa",
    }.get(semantic_type, semantic_type)


def spanish_configured_rationale(
    variable: dict[str, Any], analysis: dict[str, Any], criterion: str
) -> dict[str, str]:
    source = variable.get("source") or {}
    semantic_type = str(analysis.get("semantic_type") or "")
    requirement = SEMANTIC_PUBLIC_REQUIREMENTS.get(
        semantic_type, "completar la validación semántica correspondiente"
    )
    table = source.get("table") or source.get("detail") or "fuente no validada"
    columns = ", ".join(source_column_list(source)) or "columnas por definir"
    findings = " ".join(str(item) for item in analysis.get("known_findings") or [])
    evidence = (
        f"Tipo semántico: {spanish_semantic_label(semantic_type)}. "
        f"Fuente evaluada: {table}. Campos: {columns}. "
        f"Razonamiento específico: {analysis.get('source_reasoning')}."
    )
    if findings:
        evidence += f" Hallazgos conocidos: {findings}"

    if criterion == "source":
        return {
            "why": "La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.",
            "evidence": evidence,
            "recommended_action": "Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.",
        }
    if criterion == "definition":
        return {
            "why": f"La definición no puede considerarse confirmada hasta {requirement}.",
            "evidence": evidence,
            "recommended_action": f"Aprobar la definición y {requirement}; guardar SQL agregado, regla previa y métricas de reconciliación.",
        }
    if criterion == "consistency":
        return {
            "why": "La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.",
            "evidence": evidence,
            "recommended_action": "Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.",
        }
    if criterion == "join":
        return {
            "why": "La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.",
            "evidence": evidence,
            "recommended_action": "Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.",
        }
    if criterion == "effort":
        return {
            "why": "La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.",
            "evidence": evidence,
            "recommended_action": "Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.",
        }
    raise ValueError(f"Unsupported qualitative criterion for Spanish rationale: {criterion}")


def localize_derivation_plan(
    variable: dict[str, Any], analysis: dict[str, Any]
) -> None:
    translations = analysis.get("publication_translations") or {}
    grain_labels = translations.get("grains") or {}
    options = variable.get("derivation_options") or []
    if not isinstance(options, list):
        return
    selected_name = str(variable.get("selected_derivation") or "")
    translated_selected = selected_name
    for option in options:
        if not isinstance(option, dict):
            continue
        old_name = str(option.get("name") or "")
        status = str(option.get("status") or "proposed")
        option["name"] = (
            "Ruta agregada de encuesta v4"
            if (analysis.get("semantic_type") == "survey")
            else "Ruta de derivación v4 propuesta"
        )
        if old_name == selected_name:
            translated_selected = option["name"]
        option["formula"] = analysis.get("derivation_formula") or analysis.get("definition")
        option["grain"] = grain_labels.get(
            str(option.get("grain") or ""), option.get("grain")
        )
        option["temporal_window"] = "Usar sólo información conocida hasta el snapshot de predicción; la ventana exacta debe quedar aprobada."
        option["deduplication"] = "Deduplicar en el grain empleado-fecha o evento definido antes de unir con snapshots mensuales."
        option["nulls_and_edge_cases"] = "Aplicar la regla de negocio aprobada para nulos y casos límite; lo no resuelto limita Definition por debajo de 2."
        option["leakage_controls"] = "Excluir información futura y cualquier dato perteneciente a la ventana del outcome."
        option["snapshot_join"] = "Unir al snapshot mensual mediante empleado y fecha efectiva, con reconciliación agregada del join."
        option["sensitivity"] = "Publicar sólo agregados; no exponer IDs, nombres, compensación exacta, atributos protegidos ni texto libre."
        option["validations_needed"] = "Validar fórmula, fronteras, deduplicación, leakage, coverage, consistency y join con SQL agregado guardado."
        option["estimated_effort"] = "Transformación moderada, salvo que el propietario confirme un campo directo gobernado."
        option["decision_reason"] = (
            "Los componentes permiten probar la ruta, pero la validación semántica v4 todavía no la confirma."
            if status in {"testable", "proposed"}
            else "El estado de la derivación se conserva según la evidencia ejecutada."
        )
    if translated_selected:
        variable["selected_derivation"] = translated_selected


def localize_verification(variable: dict[str, Any]) -> None:
    verification = variable.get("verification") or {}
    if not isinstance(verification, dict):
        return
    rule_by_criterion = {
        "source": "Todas las tablas y columnas requeridas deben existir y ser accesibles mediante una ruta read-only aprobada.",
        "definition": "La definición documentada y sus invariantes deben coincidir con la auditoría agregada.",
        "consistency": "No deben quedar valores inválidos, contradicciones o cambios longitudinales sin explicar.",
        "join": "Cada registro elegible debe reconciliarse una sola vez en el grain empleado-fecha objetivo.",
        "effort": "No debe existir una dependencia o transformación no resuelta para la ruta evaluada.",
    }
    for criterion, item in verification.items():
        if criterion == "semantic_type" or not isinstance(item, dict):
            continue
        item["evidence"] = "Se ejecutó la auditoría agregada guardada para la población, grain y fuente de esta variable."
        item["result"] = "La evidencia registrada cumplió la regla de aceptación declarada para este criterio."
        item["acceptance_rule"] = rule_by_criterion.get(
            criterion, "La auditoría agregada debe cumplir la regla declarada sin excepciones pendientes."
        )


def apply_spanish_publication_narrative(
    variable: dict[str, Any], analysis: dict[str, Any], rules: dict[str, Any]
) -> None:
    use = analysis.get("intended_use") or analysis.get("attrition_use")
    if use:
        analysis["intended_use"] = use
        analysis.setdefault("attrition_use", use)
    required = (
        "definition",
        "numerator_definition",
        "intended_use",
        "source_reasoning",
        "validation_focus",
    )
    missing = [key for key in required if not analysis.get(key)]
    if missing:
        raise ValueError(
            f"{variable.get('variable')}: Spanish analysis is missing {missing}."
        )

    translations = analysis.get("publication_translations") or {}
    category_labels = translations.get("categories") or {}
    grain_labels = translations.get("grains") or {}
    frequency_labels = translations.get("frequencies") or {}
    configured_descriptions = translations.get("column_descriptions") or {}
    variable["narrative_language"] = "es"
    variable["category"] = category_labels.get(
        str(variable.get("category") or ""), variable.get("category")
    )
    variable["definition"] = analysis["definition"]
    variable["numerator_definition"] = analysis["numerator_definition"]
    variable["notes"] = analysis.get("notes") or analysis["source_reasoning"]
    variable["level_data"] = grain_labels.get(
        str(variable.get("level_data") or ""), variable.get("level_data")
    )

    population = variable.setdefault("population", {"mode": "default"})
    population["display"] = analysis.get("population") or analysis.get(
        "default_population"
    ) or "Empleados regulares activos en el snapshot aplicable."

    source = variable.setdefault("source", {})
    if not source.get("table"):
        source["detail"] = f"Fuente no validada o externa: {analysis['source_reasoning']}"

    measurement = variable.setdefault("measurement", {})
    override = measurement.get("frequency_override")
    if override:
        measurement["frequency_override"] = frequency_labels.get(
            str(override), "Frecuencia definida por el proceso fuente"
        )

    report = variable.setdefault("report", {})
    related = list(report.get("related_columns") or [])
    for column in analysis.get("related_columns") or []:
        if column not in related:
            related.append(column)
    if related:
        report["related_columns"] = related
    descriptions = dict(report.get("column_descriptions") or {})
    for column, description in configured_descriptions.items():
        if column in source_column_list(source) or column in related:
            descriptions[column] = description
    if descriptions:
        report["column_descriptions"] = descriptions

    evidence = variable.get("evidence") or {}
    rationale: dict[str, Any] = {}
    for criterion in profiler.QUALITATIVE_CRITERIA:
        status = source.get("status") if criterion == "source" else evidence.get(criterion)
        if not status:
            continue
        try:
            score = profiler.status_score(
                criterion, status, rules, str(variable.get("variable"))
            )
        except Exception:
            continue
        if score < 2:
            rationale[criterion] = spanish_configured_rationale(
                variable, analysis, criterion
            )
    variable["rationale"] = rationale

    if analysis.get("score_overrides"):
        existing_overrides = copy.deepcopy(variable.get("score_overrides") or {})
        localized_overrides = copy.deepcopy(analysis["score_overrides"])
        for criterion, override in localized_overrides.items():
            if not isinstance(override, dict):
                continue
            existing = existing_overrides.get(criterion) or {}
            if "score" not in override and "score" in existing:
                override["score"] = existing["score"]
        variable["score_overrides"] = localized_overrides
    localize_derivation_plan(variable, analysis)
    if variable.get("no_derivation_reason"):
        variable["no_derivation_reason"] = (
            "No existe un campo directo ni una derivación validada con las fuentes y permisos actuales."
        )
    localize_verification(variable)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def default_run_id(output_root: Path) -> str:
    base = datetime.now().strftime("%Y%m%d-v4")
    candidate = base
    index = 2
    while (output_root / candidate).exists():
        candidate = f"{base}-{index:02d}"
        index += 1
    return candidate


def resolve_relative_path(reference: str, base_path: Path) -> Path:
    path = Path(reference)
    if not path.is_absolute():
        path = base_path.parent / path
    return path.resolve()


def merge_settings(
    base: dict[str, Any], override: dict[str, Any] | None
) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_settings(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def runtime_settings_from_document(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    document = profiler.load_yaml(path)
    settings = copy.deepcopy(document.get("runtime") or {})
    for key in (
        "semantic_hint_registry",
        "query_helper",
        "audit_sql_root",
        "profile_sql_root",
    ):
        value = document.get(key) or settings.get(key)
        if value:
            settings[key] = str(resolve_relative_path(str(value), path))
    return settings


def project_configuration(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    document = profiler.load_yaml(path)
    result = copy.deepcopy(document)
    for key in (
        "catalog_spec",
        "rules",
        "output_root",
        "semantic_hint_registry",
        "query_helper",
        "audit_sql_root",
        "profile_sql_root",
    ):
        value = result.get(key)
        if value:
            result[key] = str(resolve_relative_path(str(value), path))
    documentation = dict(result.get("documentation") or {})
    if documentation.get("root"):
        documentation["root"] = str(
            resolve_relative_path(str(documentation["root"]), path)
        )
    if documentation:
        result["documentation"] = documentation
    reporting = dict(result.get("reporting") or {})
    visual_html = dict(reporting.get("visual_html_v2") or {})
    for adapter_key in ("metrics_builder", "renderer"):
        adapter = visual_html.get(adapter_key)
        if isinstance(adapter, str):
            visual_html[adapter_key] = str(resolve_relative_path(adapter, path))
        elif isinstance(adapter, dict) and adapter.get("script"):
            adapter = copy.deepcopy(adapter)
            adapter["script"] = str(
                resolve_relative_path(str(adapter["script"]), path)
            )
            visual_html[adapter_key] = adapter
    if visual_html.get("template"):
        visual_html["template"] = str(
            resolve_relative_path(str(visual_html["template"]), path)
        )
    if visual_html:
        reporting["visual_html_v2"] = visual_html
    if reporting:
        result["reporting"] = reporting
    return result


def variables_with_analysis(
    spec: dict[str, Any], spec_path: Path, rules: dict[str, Any],
    require_explicit_stories: bool = False,
) -> tuple[list[dict[str, Any]], Path | None]:
    variables = profiler.validate_spec(spec, rules)
    catalog_reference = str(spec.get("analysis_catalog") or "").strip()
    catalog_path = (
        resolve_relative_path(catalog_reference, spec_path)
        if catalog_reference
        else None
    )
    catalog: dict[str, Any] = {}
    defaults: dict[str, Any] = {}
    if catalog_path:
        if not catalog_path.is_file():
            raise ValueError(f"Analysis catalog not found: {catalog_path}")
        catalog_document = profiler.load_yaml(catalog_path)
        catalog = catalog_document.get("variables") or {}
        defaults = dict(catalog_document.get("defaults") or {})
        defaults["language"] = catalog_document.get("language") or defaults.get(
            "language"
        )
        if not isinstance(catalog, dict):
            raise ValueError("Analysis catalog variables must be a mapping.")
        expected = {str(item.get("variable") or "") for item in variables}
        extra = sorted(set(catalog) - expected)
        missing = sorted(expected - set(catalog))
        if extra or missing:
            raise ValueError(
                f"Analysis catalog mismatch. Missing={missing}; extra={extra}."
            )

    allowed_types = set((rules.get("verification") or {}).get("semantic_types") or [])
    merged_variables: list[dict[str, Any]] = []
    for variable in variables:
        merged = copy.deepcopy(variable)
        name = str(merged.get("variable") or "").strip()
        inline = merged.get("analysis") or {}
        catalog_item = catalog.get(name) or {}
        if not isinstance(inline, dict) or not isinstance(catalog_item, dict):
            raise ValueError(f"{name}: analysis configuration must be an object.")
        analysis = {**defaults, **catalog_item, **inline}
        semantic_type = str(analysis.get("semantic_type") or "").strip()
        if not semantic_type:
            raise ValueError(f"{name}: analysis.semantic_type is required.")
        if semantic_type not in allowed_types:
            raise ValueError(
                f"{name}: unsupported analysis.semantic_type {semantic_type!r}."
            )
        use = analysis.get("intended_use") or analysis.get("attrition_use")
        if not use or not analysis.get("source_reasoning"):
            raise ValueError(
                f"{name}: analysis requires intended_use (or legacy attrition_use) "
                "and source_reasoning."
            )
        analysis["intended_use"] = use
        analysis.setdefault("attrition_use", use)
        focus = analysis.get("validation_focus") or []
        if not isinstance(focus, list) or not focus:
            raise ValueError(f"{name}: analysis.validation_focus must be a non-empty list.")
        story = analysis.get("validation_story") or []
        if not isinstance(story, list):
            raise ValueError(f"{name}: analysis.validation_story must be a list.")
        if require_explicit_stories and not story:
            raise ValueError(
                f"{name}: strict analysis requires a non-empty explicit "
                "analysis.validation_story; validation_focus is only a hypothesis aid."
            )
        if not story and not require_explicit_stories:
            # Compatibility path for historical catalogs. New guided runs must
            # opt into strict plans and never reach this fallback.
            analysis["allow_legacy_story_materialization"] = True
        for index, item in enumerate(story, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{name}: validation_story item {index} must be an object."
                )
            required_story = (
                "id", "criterion", "evidence_role", "question", "why",
                "method", "acceptance_rule",
            )
            missing_story = [key for key in required_story if not item.get(key)]
            if missing_story:
                raise ValueError(
                    f"{name}: validation_story item {index} is missing {missing_story}."
                )
            if item["criterion"] not in rules["criteria_order"]:
                raise ValueError(
                    f"{name}: validation_story item {index} has invalid criterion."
                )
            if item["evidence_role"] not in {
                "defining", "supporting", "contextual"
            }:
                raise ValueError(
                    f"{name}: validation_story item {index} has invalid evidence_role."
                )
        merged["analysis"] = analysis
        if analysis.get("language") == "es":
            apply_spanish_publication_narrative(merged, analysis, rules)
        verification = merged.setdefault("verification", {})
        verification["semantic_type"] = semantic_type
        merged_variables.append(merged)

    return merged_variables, catalog_path


def variables_from_run_request(
    request_path: Path,
    catalog_spec_path: Path,
    rules: dict[str, Any],
    require_explicit_stories: bool = False,
) -> tuple[list[dict[str, Any]], Path | None, dict[str, Any]]:
    request = profiler.load_yaml(request_path)
    requested = workflow.validate_run_request(request)
    catalog_spec = profiler.load_yaml(catalog_spec_path)
    catalog_variables, catalog_path = variables_with_analysis(
        catalog_spec, catalog_spec_path, rules, require_explicit_stories
    )
    by_name = {
        str(variable.get("variable")): variable
        for variable in catalog_variables
    }
    missing = [item["name"] for item in requested if item["name"] not in by_name]
    if missing:
        raise ValueError(f"run-request variables are absent from the catalog: {missing}.")
    variables: list[dict[str, Any]] = []
    for item in requested:
        variable = copy.deepcopy(by_name[item["name"]])
        analysis = variable.setdefault("analysis", {})
        requested_use = item.get("intended_use") or item.get("attrition_use")
        if requested_use:
            analysis["intended_use"] = requested_use
            analysis["attrition_use"] = requested_use
        if item.get("knowledge_date"):
            analysis["prediction_cutoff"] = item["knowledge_date"]
        if item.get("population"):
            variable.setdefault("population", {})["display"] = item["population"]
            analysis["population"] = item["population"]
        for field in (
            "context_role",
            "context_relevance",
            "linked_problem_elements",
            "related_variables",
        ):
            if item.get(field):
                analysis[field] = copy.deepcopy(item[field])
        variables.append(variable)
    return variables, catalog_path, request


def apply_explicit_analysis_plans(
    prepared: dict[str, Any], plan_paths: list[Path], *, strict: bool
) -> list[dict[str, Any]]:
    """Overlay Codex-authored immutable plans before any aggregate SQL runs."""
    if not plan_paths:
        if strict:
            raise ValueError(
                "--strict-analysis-plans requires one --analysis-plan for every requested variable."
            )
        return []

    variables = {
        str(variable.get("variable") or ""): variable
        for variable in prepared.get("variables") or []
    }
    supplied: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for path in plan_paths:
        if not path.is_file():
            raise ValueError(f"Analysis plan not found: {path}")
        document = profiler.load_yaml(path)
        variable_name = str(document.get("variable") or "").strip()
        if not variable_name or variable_name not in variables:
            raise ValueError(
                f"{path}: plan variable must be one of the requested variables."
            )
        if variable_name in supplied:
            raise ValueError(f"Multiple analysis plans were supplied for {variable_name}.")
        if not document.get("created_before_execution"):
            raise ValueError(f"{path}: created_before_execution must be true.")
        story = document.get("validation_story") or []
        if not isinstance(story, list) or not story:
            raise ValueError(f"{path}: validation_story must be a non-empty list.")
        for index, item in enumerate(story, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"{path}: validation_story item {index} must be an object.")
            missing = [
                key for key in (
                    "id", "criterion", "evidence_role", "question", "why",
                    "method", "sql_reference", "acceptance_rule",
                ) if not item.get(key)
            ]
            if missing:
                raise ValueError(
                    f"{path}: validation_story item {index} is missing {missing}."
                )
        plan_version = int(document.get("plan_version") or 1)
        if plan_version < 1:
            raise ValueError(f"{path}: plan_version must be positive.")
        if plan_version > 1 and not document.get("plan_revision_reason"):
            raise ValueError(
                f"{path}: plan_version > 1 requires plan_revision_reason."
            )
        supplied[variable_name] = document
        records.append(
            {
                "variable": variable_name,
                "path": str(path.resolve()),
                "sha256": workflow.canonical_json_hash(document),
                "plan_version": plan_version,
            }
        )

    if strict:
        missing = sorted(set(variables) - set(supplied))
        if missing:
            raise ValueError(
                "Strict analysis plans are missing for: " + ", ".join(missing)
            )

    for variable_name, document in supplied.items():
        variable = variables[variable_name]
        analysis = variable.setdefault("analysis", {})
        analysis["validation_story"] = copy.deepcopy(document["validation_story"])
        analysis["validation_focus"] = [
            str(item["question"]) for item in document["validation_story"]
        ]
        analysis["plan_version"] = int(document.get("plan_version") or 1)
        analysis["plan_revision_reason"] = document.get("plan_revision_reason")
        analysis["plan_authorship"] = "codex_explicit"
        analysis.pop("allow_legacy_story_materialization", None)
        for plan_key, analysis_key in (
            ("concept", "definition"),
            ("intended_use", "intended_use"),
            ("knowledge_date", "prediction_cutoff"),
            ("source_reasoning", "source_reasoning"),
        ):
            if document.get(plan_key):
                analysis[analysis_key] = document[plan_key]
        if document.get("population"):
            variable.setdefault("population", {})["display"] = document["population"]
        if document.get("semantic_type"):
            current = str(analysis.get("semantic_type") or "")
            if current and current != str(document["semantic_type"]):
                raise ValueError(
                    f"{variable_name}: plan semantic_type conflicts with the catalog."
                )
        workflow.materialize_validation_stories(variable, allow_legacy_focus=False)
    return records


def metadata_rows_from_file(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = profiler.load_json(path)
    if isinstance(data, dict):
        data = data.get("rows") or data.get("metadata") or data.get("_metadata") or []
    if not isinstance(data, list):
        raise ValueError("Metadata results must be a list or an object containing rows.")
    return [dict(row) for row in data if isinstance(row, dict)]


def prepare_portfolio(
    spec_path: Path | None,
    rules_path: Path,
    run_id: str,
    request_path: Path | None = None,
    catalog_spec_path: Path | None = None,
    metadata_results_path: Path | None = None,
    execute_metadata: bool = False,
    persist_metadata_sql: bool = False,
    runtime_config: dict[str, Any] | None = None,
    semantic_hints_path: Path | None = None,
    query_helper_path: Path | None = None,
    require_explicit_stories: bool = False,
    reporting_mode: str = "presentation",
) -> dict[str, Any]:
    rules = profiler.load_yaml(rules_path)
    if request_path:
        if catalog_spec_path is None:
            raise ValueError(
                "--catalog-spec or project catalog_spec is required with --request."
            )
        variables, catalog_path, run_request = variables_from_run_request(
            request_path,
            catalog_spec_path.resolve(),
            rules,
            require_explicit_stories,
        )
        source_spec_path = catalog_spec_path.resolve()
    else:
        if spec_path is None:
            raise ValueError("Either spec_path or request_path is required.")
        spec = profiler.load_yaml(spec_path)
        variables, catalog_path = variables_with_analysis(
            spec, spec_path, rules, require_explicit_stories
        )
        run_request = workflow.build_run_request(variables)
        source_spec_path = spec_path

    runtime: dict[str, Any] = {}
    for document_path in (catalog_path, source_spec_path, request_path):
        runtime = merge_settings(
            runtime, runtime_settings_from_document(document_path)
        )
    runtime = merge_settings(runtime, runtime_config)
    metadata_config = dict(runtime.get("metadata") or {})
    resolved_hints_path = Path(
        semantic_hints_path
        or runtime.get("semantic_hint_registry")
        or workflow.DEFAULT_HINTS
    ).resolve()
    if not resolved_hints_path.is_file():
        raise ValueError(f"Semantic hint registry not found: {resolved_hints_path}")
    hints = workflow.load_yaml(resolved_hints_path)
    configure_publication_policy(hints, reporting_mode)
    resolved_query_helper = Path(
        query_helper_path
        or runtime.get("query_helper")
        or profiler.QUERY_HELPER
    ).resolve()
    profiler.configure_query_helper(resolved_query_helper)

    metadata_sql = workflow.build_metadata_discovery_sql(
        variables, metadata_config
    )
    metadata_reference: str | None = None
    if persist_metadata_sql:
        audit_sql_root = Path(
            runtime.get("audit_sql_root")
            or PROJECT_ROOT / "queries" / "audits"
        ).resolve()
        metadata_path = audit_sql_root / f"{renderer.slugify(run_id)}_portfolio_metadata.sql"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(metadata_sql.rstrip() + "\n", encoding="utf-8")
        metadata_reference = str(metadata_path.relative_to(PROJECT_ROOT))
    metadata_rows = metadata_rows_from_file(metadata_results_path)
    if execute_metadata and not metadata_rows:
        metadata_rows = profiler.run_aggregate_query(metadata_sql, max_rows=10000)
    context = workflow.build_portfolio_context(
        variables,
        run_request,
        metadata_rows=metadata_rows,
        metadata_query_reference=metadata_reference,
        hints=hints,
        metadata_config=metadata_config,
    )
    return {
        "rules": rules,
        "variables": variables,
        "catalog_path": catalog_path,
        "source_spec_path": source_spec_path,
        "run_request": run_request,
        "portfolio_context": context,
        "metadata_sql": metadata_sql,
        "metadata_rows": metadata_rows,
        "metadata_query_reference": metadata_reference,
        "runtime": runtime,
        "semantic_hints_path": resolved_hints_path,
        "query_helper_path": resolved_query_helper,
    }


def offline_variable_payload(data: Any, variable_name: str) -> dict[str, Any]:
    if data is None:
        return {}
    root = data.get("variables") if isinstance(data, dict) and "variables" in data else data
    if isinstance(root, dict):
        payload = root.get(variable_name)
        if payload is None:
            payload = root.get(profiler.slugify(variable_name))
        if isinstance(payload, list):
            return {"coverage": payload, "queries": {}}
        if isinstance(payload, dict):
            coverage = payload.get("coverage") or payload.get("rows") or []
            queries = payload.get("queries") or {}
            return {"coverage": coverage, "queries": queries}
    if isinstance(root, list):
        return {"coverage": root, "queries": {}}
    return {}


def offline_query_rows(
    data: Any, variable_name: str, reference: str
) -> list[dict[str, Any]] | None:
    payload = offline_variable_payload(data, variable_name)
    queries = payload.get("queries") or {}
    candidates = (
        reference,
        Path(reference).as_posix(),
        Path(reference).name,
        Path(reference).stem,
    )
    for candidate in candidates:
        rows = queries.get(candidate) if isinstance(queries, dict) else None
        if rows is not None:
            return [dict(row) for row in rows if isinstance(row, dict)]
    if isinstance(data, dict):
        global_queries = data.get("queries") or {}
        for candidate in candidates:
            rows = global_queries.get(candidate) if isinstance(global_queries, dict) else None
            if rows is not None:
                return [dict(row) for row in rows if isinstance(row, dict)]
    return None


def persist_coverage_sql(
    variable: dict[str, Any], rules: dict[str, Any], spec_path: Path,
    run_id: str, evaluation_number: int,
) -> tuple[str | None, str | None, str]:
    mode = str((variable.get("profile") or {}).get("mode", "standard")).lower()
    if mode == "standard":
        sql, population_display = profiler.build_standard_sql(variable, rules)
    elif mode == "aggregate_sql":
        sql = profiler.resolve_custom_sql(variable, spec_path)
        population_display = str(
            (variable.get("population") or {}).get("display")
            or "Defined by aggregate SQL"
        )
    elif mode in {"external", "unavailable"}:
        return None, None, str((variable.get("population") or {}).get("display") or rules["population"]["display"])
    else:
        raise ValueError(f"{variable.get('variable')}: unknown profile mode {mode!r}.")
    prefix = query_prefix(run_id, evaluation_number, str(variable.get("variable")))
    path = REPORT_SQL_ROOT / f"{prefix}_coverage.sql"
    reference = write_report_sql(path, sql)
    return reference, sql, population_display


def planned_evidence_items(
    variable: dict[str, Any], coverage_reference: str | None
) -> list[tuple[str, str, dict[str, Any]]]:
    items: list[tuple[str, str, dict[str, Any]]] = []
    if coverage_reference:
        items.append((
            coverage_reference,
            "coverage",
            {
                "claim": "Medir elegibles y observables por fecha para Coverage, Missingness e History.",
                "acceptance_rule": "La consulta debe devolver una fila agregada por fecha con elegibles y observables.",
            },
        ))
    for criterion, item in (variable.get("verification") or {}).items():
        if criterion == "semantic_type" or not isinstance(item, dict):
            continue
        reference = str(item.get("query_reference") or "").split("#", 1)[0].strip()
        if reference:
            items.append((reference, f"verification:{criterion}", item))
    validations = variable.get("scoring_validations") or variable.get("validations") or []
    if isinstance(validations, dict):
        validations = validations.get("items") or []
    for item in validations if isinstance(validations, list) else []:
        if not isinstance(item, dict):
            continue
        reference = str(item.get("sql_reference") or item.get("query_reference") or "").split("#", 1)[0].strip()
        if reference:
            items.append((reference, f"scoring_validation:{item.get('id')}", item))
    for item in (variable.get("analysis") or {}).get("validation_story") or []:
        if not isinstance(item, dict):
            continue
        reference = str(item.get("sql_reference") or "").split("#", 1)[0].strip()
        if reference:
            items.append((reference, f"validation_story:{item.get('id')}", item))
    return items


def collect_variable_evidence(
    variable: dict[str, Any],
    rules: dict[str, Any],
    spec_path: Path,
    run_id: str,
    evaluation_number: int,
    offline_data: Any,
    evidence_cache: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], str, dict[str, Any]]:
    coverage_reference, coverage_sql, population_display = persist_coverage_sql(
        variable, rules, spec_path, run_id, evaluation_number
    )
    records: dict[str, dict[str, Any]] = {}
    ordered_records: list[dict[str, Any]] = []
    variable_name = str(variable.get("variable"))
    payload = offline_variable_payload(offline_data, variable_name)
    for reference, purpose, item in planned_evidence_items(variable, coverage_reference):
        if reference in records:
            record = records[reference]
            purposes = record.setdefault("purposes", [record.get("purpose")])
            if purpose not in purposes:
                purposes.append(purpose)
            continue
        if reference == coverage_reference:
            sql = coverage_sql or ""
            if offline_data is not None:
                rows = [dict(row) for row in payload.get("coverage") or [] if isinstance(row, dict)]
                source = "offline_frozen_result"
            else:
                rows = profiler.run_aggregate_query(sql)
                source = "executed_redshift_sql"
        else:
            sql_path = (PROJECT_ROOT / reference).resolve()
            if not sql_path.is_file():
                raise ValueError(f"{variable_name}: evidence SQL not found: {reference}")
            sql = sql_path.read_text(encoding="utf-8-sig")
            offline_rows = offline_query_rows(offline_data, variable_name, reference)
            if offline_data is not None:
                if offline_rows is None:
                    continue
                rows = offline_rows
                source = "offline_frozen_result"
            else:
                rows = profiler.run_aggregate_query(sql, max_rows=1000)
                source = "executed_redshift_sql"
        identity = workflow.evidence_identity(variable, item, workflow.sql_hash(sql))
        reused_from = None
        if identity in evidence_cache:
            cached = evidence_cache[identity]
            rows = copy.deepcopy(cached["rows"])
            source = "reused_frozen_evidence"
            reused_from = str(cached.get("query_reference"))
        record = workflow.make_query_record(
            reference, sql, rows, purpose, variable, item, source, reused_from
        )
        records[reference] = record
        ordered_records.append(record)
        if record.get("source") != "reused_frozen_evidence":
            evidence_cache[identity] = copy.deepcopy(record)
    coverage_rows = (
        list((records.get(coverage_reference or "") or {}).get("rows") or [])
        if coverage_reference else []
    )
    frozen_variable, caps = workflow.freeze_variable_evidence(
        variable,
        records,
        rules,
        "offline_frozen_result" if offline_data is not None else "executed_redshift_sql",
    )
    ledger = {
        "schema_version": 1,
        "variable": variable_name,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "coverage_query_reference": coverage_reference,
        "query_count": len(ordered_records),
        "queries": ordered_records,
        "computed_verification_caps": caps,
    }
    return frozen_variable, coverage_rows, population_display, ledger


def inherited_dependency_conditions(
    variable: dict[str, Any],
    dependencies: dict[str, list[str]],
    completed: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    name = str(variable.get("variable"))
    conditions: list[dict[str, Any]] = []
    caps: list[dict[str, Any]] = []
    for dependency in dependencies.get(name, []):
        assessment = completed.get(dependency)
        if assessment is None:
            conditions.append({"dependency": dependency, "status": "pending"})
            ready = False
        else:
            definition_score = int((assessment.get("scores") or {}).get("definition", 0))
            source_score = int((assessment.get("scores") or {}).get("source", 0))
            ready = definition_score == 2 and source_score == 2 and assessment.get("blocker_key") == "none"
            conditions.append({
                "dependency": dependency,
                "status": "ready" if ready else "limited",
                "source_score": source_score,
                "definition_score": definition_score,
                "blocker": assessment.get("blocker_key"),
            })
        if not ready:
            caps.append({
                "criterion": "definition",
                "max_score": 1,
                "status_rule": f"La dependencia base {dependency} no está confirmada y limita Definition a 1",
                "reason": "Una variable derivada no puede superar la definición de su componente base pendiente.",
                "evidence": f"Condición heredada desde {dependency}: {conditions[-1]}.",
                "recommended_action": f"Completar y aprobar {dependency}, luego repetir {name}.",
                "scoring_method": "Condición heredada de dependencia",
            })
    return conditions, caps


def triggered_adaptive_stories(
    variable: dict[str, Any], evidence_ledger: dict[str, Any]
) -> list[dict[str, Any]]:
    configured = (variable.get("analysis") or {}).get("adaptive_validations") or []
    if not isinstance(configured, list):
        raise ValueError(
            f"{variable.get('variable')}: analysis.adaptive_validations must be a list."
        )
    records = {
        str(item.get("query_reference")): item
        for item in evidence_ledger.get("queries") or []
    }
    stories: list[dict[str, Any]] = []
    for item in configured:
        if not isinstance(item, dict):
            continue
        trigger = item.get("trigger") or {}
        reference = str(trigger.get("query_reference") or "")
        metric = str(trigger.get("metric") or "")
        operator = str(trigger.get("operator") or "")
        threshold = trigger.get("threshold")
        observed = (records.get(reference) or {}).get("metrics", {}).get(metric)
        if (
            isinstance(observed, (int, float))
            and not isinstance(observed, bool)
            and isinstance(threshold, (int, float))
            and not isinstance(threshold, bool)
            and operator in workflow.COMPARISON_OPERATORS
            and workflow.compare(float(observed), operator, float(threshold))
        ):
            story = item.get("story")
            if not isinstance(story, dict):
                raise ValueError(
                    f"{variable.get('variable')}: triggered adaptive validation requires a story object."
                )
            stories.append(copy.deepcopy(story))
    return stories


def unique_slug(value: str, used: set[str]) -> str:
    base = renderer.slugify(value)
    slug = base
    index = 2
    while slug in used:
        slug = f"{base}-{index}"
        index += 1
    used.add(slug)
    return slug


def copy_input(path: Path | None, target_dir: Path) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    destination = target_dir / resolved.name
    shutil.copy2(resolved, destination)
    return str(destination.relative_to(PROJECT_ROOT))


def evidence_references(assessment: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in (assessment.get("score_verification") or {}).values():
        reference = str(item.get("query_reference") or "").split("#", 1)[0].strip()
        if reference:
            refs.append(reference)
    for item in assessment.get("executable_validations") or []:
        reference = str(item.get("sql_reference") or "").split("#", 1)[0].strip()
        if reference:
            refs.append(reference)
    report_evidence = ((assessment.get("report_detail") or {}).get("evidence") or {})
    for reference in report_evidence.get("sql_references") or []:
        reference = str(reference).split("#", 1)[0].strip()
        if reference:
            refs.append(reference)
    for item in (assessment.get("evidence_ledger") or {}).get("queries") or []:
        reference = str(item.get("query_reference") or "").split("#", 1)[0].strip()
        if reference:
            refs.append(reference)
    return sorted(set(refs))

def copy_evidence(assessments: list[dict[str, Any]], evidence_dir: Path) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    seen: set[str] = set()
    for assessment in assessments:
        for reference in evidence_references(assessment):
            if reference in seen:
                continue
            seen.add(reference)
            source = (PROJECT_ROOT / reference).resolve()
            if not source.is_file():
                raise ValueError(f"Evidence SQL not found: {reference}")
            destination = evidence_dir / source.name
            shutil.copy2(source, destination)
            copied.append(
                {
                    "source": reference,
                    "copy": str(destination.relative_to(PROJECT_ROOT)),
                }
            )
    return copied


def notebook_cell_id(kind: str, source: str) -> str:
    return hashlib.sha1(f"{kind}\n{source}".encode("utf-8")).hexdigest()[:12]


def markdown_cell(source: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "id": notebook_cell_id("markdown", source),
        "metadata": {},
        "source": source.splitlines(True),
    }


def code_cell(label: str, variable_name: str, output: Any, execution_count: int) -> dict[str, Any]:
    text = json.dumps(output, ensure_ascii=False, indent=2, default=str)
    text_literal = json.dumps(text, ensure_ascii=False)
    source = (
        f"# {label}\n"
        "import json\n"
        f"{variable_name} = json.loads({text_literal})\n"
        f"print(json.dumps({variable_name}, ensure_ascii=False, indent=2))\n"
    )
    return {
        "cell_type": "code",
        "id": notebook_cell_id("legacy-code", source),
        "execution_count": execution_count,
        "metadata": {},
        "outputs": [
            {
                "name": "stdout",
                "output_type": "stream",
                "text": text.splitlines(True) or ["{}\n"],
            }
        ],
        "source": source.splitlines(True),
    }


def executable_code_cell(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "id": notebook_cell_id("code", source),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip().splitlines(True),
    }


def execute_notebook_to_html(notebook_path: Path, html_path: Path) -> None:
    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import nbformat
        from nbclient import NotebookClient
        from nbconvert import HTMLExporter
    except ImportError as exc:
        raise RuntimeError(
            "Executed notebooks require nbformat, nbclient, and nbconvert from requirements.txt."
        ) from exc

    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
        allow_errors=False,
    )
    client.execute()
    nbformat.write(notebook, notebook_path)

    exporter = HTMLExporter(template_name="lab")
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    body, _ = exporter.from_notebook_node(notebook)
    html_path.write_text(body, encoding="utf-8")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def source_column_list(source: dict[str, Any]) -> list[str]:
    return [str(item) for item in as_list(source.get("columns")) if str(item).strip()]


def report_config(variable: dict[str, Any]) -> dict[str, Any]:
    config = variable.get("report") or {}
    return config if isinstance(config, dict) else {}


def report_columns(variable: dict[str, Any]) -> list[dict[str, str]]:
    source = variable.get("source") or {}
    config = report_config(variable)
    source_columns = source_column_list(source)
    related_columns = [str(item) for item in as_list(config.get("related_columns")) if str(item).strip()]
    descriptions = config.get("column_descriptions") or {}
    if not isinstance(descriptions, dict):
        descriptions = {}
    columns: list[dict[str, str]] = []
    seen: set[str] = set()
    for role, values in (("scoring", source_columns), ("related", related_columns)):
        for column in values:
            if column in seen:
                continue
            seen.add(column)
            columns.append(
                {
                    "column": column,
                    "role": role,
                    "role_label": "Scoring" if role == "scoring" else "Relacionado",
                    "description": str(
                        descriptions.get(column)
                        or ("Campo usado directamente para scoring." if role == "scoring" else "Campo relacionado usado para explicar diferencias.")
                    ),
                }
            )
    return columns


def comparison_pairs(variable: dict[str, Any], available_columns: set[str]) -> list[tuple[str, str]]:
    config = report_config(variable)
    configured = config.get("comparison_pairs") or []
    pairs: list[tuple[str, str]] = []
    for item in configured:
        if isinstance(item, dict):
            left, right = item.get("left"), item.get("right")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            left, right = item[0], item[1]
        else:
            continue
        if left and right:
            pairs.append((str(left), str(right)))
    if not pairs:
        source_columns = source_column_list(variable.get("source") or {})
        related = [item["column"] for item in report_columns(variable) if item["role"] == "related"]
        pairs = [(left, right) for left in source_columns for right in related]
        if not pairs and len(source_columns) >= 2:
            pairs = [(source_columns[index], source_columns[index + 1]) for index in range(len(source_columns) - 1)]
    clean: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for left, right in pairs:
        key = (left, right)
        if left in available_columns and right in available_columns and left != right and key not in seen:
            seen.add(key)
            clean.append(key)
    return clean


def configure_publication_policy(
    hints: dict[str, Any], reporting_mode: str = "presentation"
) -> None:
    global SENSITIVE_VALUE_COLUMNS, REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError(
            "reporting_mode must be 'presentation' or 'internal_analysis'."
        )
    REPORTING_MODE = reporting_mode
    policies = hints.get("publication_policies") or {}
    configured = policies.get("exact_value_suppressed_columns") or []
    SENSITIVE_VALUE_COLUMNS = HR_SENSITIVE_VALUE_COLUMNS | {
        str(column).strip().lower()
        for column in configured
        if str(column).strip()
    }


def is_value_display_safe(column: str) -> tuple[bool, str]:
    lowered = column.lower()
    if (
        REPORTING_MODE == "internal_analysis"
        and lowered in INTERNAL_ANALYSIS_CATEGORY_COLUMNS
    ):
        return (
            True,
            "Etiquetas categóricas reales permitidas sólo para análisis interno; "
            "cada bucket debe cumplir la cohorte mínima.",
        )
    if lowered in SENSITIVE_VALUE_COLUMNS:
        return False, "Valores suprimidos porque la columna es sensible o restringida."
    for pattern in SUPPRESSED_VALUE_PATTERNS:
        if pattern in lowered:
            return False, "Valores suprimidos por privacidad: identidad, datos sensibles, fechas, compensación o texto libre."
    return True, "Los valores categóricos agregados pueden mostrarse cuando cada bucket cumple la cohorte mínima."


def table_parts(table: str) -> tuple[str, str]:
    parts = table.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "public", parts[0]


def write_report_sql(path: Path, sql: str) -> str:
    REPORT_SQL_ROOT.mkdir(parents=True, exist_ok=True)
    path.write_text(sql.rstrip() + "\n", encoding="utf-8")
    return str(path.relative_to(PROJECT_ROOT))


def query_prefix(run_id: str, number: int, variable_name: str) -> str:
    return f"{run_id}_{number:02d}_{renderer.slugify(variable_name)}"


def build_metadata_sql(table: str, columns: list[str]) -> str:
    schema, table_name = table_parts(table)
    column_values = ", ".join(profiler.sql_literal(column) for column in columns)
    return f"""
SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = {profiler.sql_literal(schema)}
  AND table_name = {profiler.sql_literal(table_name)}
  AND column_name IN ({column_values})
ORDER BY ordinal_position
""".strip()


def build_column_profile_sql(variable: dict[str, Any], columns: list[str], rules: dict[str, Any]) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    selects = []
    for column in columns:
        quoted = profiler.quoted_identifier(column, "report column")
        nonblank = profiler.nonblank_expression(column)
        selects.append(
            f"""
SELECT
  {profiler.sql_literal(column)} AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT {employee_column}) AS eligible_employees,
  SUM(CASE WHEN {nonblank} THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN {nonblank} THEN {employee_column} END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN {nonblank} THEN CAST({quoted} AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN {nonblank} THEN CAST({date_column} AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN {nonblank} THEN CAST({date_column} AS DATE) END) AS latest_populated_date
FROM {profiler.quoted_table(table)}
WHERE {where}
  AND {date_column} IS NOT NULL
""".strip()
        )
    return "\nUNION ALL\n".join(selects)


def build_single_top_values_sql(variable: dict[str, Any], column: str, rules: dict[str, Any]) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    minimum = int(rules["population"]["minimum_shared_cohort"])
    quoted = profiler.quoted_identifier(column, "report value column")
    nonblank = profiler.nonblank_expression(column)
    return f"""
SELECT
  {profiler.sql_literal(column)} AS column_name,
  CAST({quoted} AS VARCHAR(512)) AS value_label,
  COUNT(DISTINCT {employee_column}) AS employee_count,
  COUNT(*) AS row_count
FROM {profiler.quoted_table(table)}
WHERE {where}
  AND {date_column} = (
    SELECT MAX({date_column})
    FROM {profiler.quoted_table(table)}
    WHERE {where}
      AND {date_column} IS NOT NULL
  )
  AND {nonblank}
GROUP BY 1, 2
HAVING COUNT(DISTINCT {employee_column}) >= {minimum}
ORDER BY employee_count DESC, value_label
LIMIT {SAFE_VALUE_FULL_N}
""".strip()


def build_numeric_bands_sql(
    variable: dict[str, Any], band_config: dict[str, Any], rules: dict[str, Any]
) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    column = str(band_config.get("column") or "")
    edges = sorted(float(item) for item in (band_config.get("edges") or []))
    if not column or not edges:
        raise ValueError(f"{variable.get('variable')}: numeric_bands requires column and edges.")
    quoted = profiler.quoted_identifier(column, "numeric band column")
    date_column = profiler.quoted_identifier(
        measurement.get("date_column", "fis_mo_end_dt"), "date column"
    )
    employee_column = profiler.quoted_identifier(
        measurement.get("employee_id_column", "employee_id"), "employee ID column"
    )
    where, _ = profiler.population_clause(variable, rules)
    minimum = int(rules["population"]["minimum_shared_cohort"])
    clauses: list[str] = []
    for index, edge in enumerate(edges):
        if index == 0:
            label = f"< {edge:g}"
            clauses.append(f"WHEN {quoted} < {edge:g} THEN {profiler.sql_literal(label)}")
        else:
            previous = edges[index - 1]
            label = f"{previous:g} to < {edge:g}"
            clauses.append(f"WHEN {quoted} < {edge:g} THEN {profiler.sql_literal(label)}")
    clauses.append(f"ELSE {profiler.sql_literal(f'>= {edges[-1]:g}')}")
    case_expression = "CASE " + " ".join(clauses) + " END"
    return f"""
SELECT
  {profiler.sql_literal(column)} AS column_name,
  {case_expression} AS band_label,
  COUNT(DISTINCT {employee_column}) AS employee_count,
  COUNT(*) AS row_count
FROM {profiler.quoted_table(table)}
WHERE {where}
  AND {date_column} = (
    SELECT MAX({date_column})
    FROM {profiler.quoted_table(table)}
    WHERE {where}
      AND {date_column} IS NOT NULL
  )
  AND {quoted} IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT {employee_column}) >= {minimum}
ORDER BY MIN({quoted})
""".strip()

def build_top_values_sql(variable: dict[str, Any], columns: list[str], rules: dict[str, Any]) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    minimum = int(rules["population"]["minimum_shared_cohort"])
    selects = []
    for column in columns:
        quoted = profiler.quoted_identifier(column, "report value column")
        nonblank = profiler.nonblank_expression(column)
        selects.append(
            f"""
SELECT
  {profiler.sql_literal(column)} AS column_name,
  CAST({quoted} AS VARCHAR(512)) AS value_label,
  COUNT(DISTINCT {employee_column}) AS employee_count,
  COUNT(*) AS row_count
FROM {profiler.quoted_table(table)} source_rows
WHERE {where}
  AND {date_column} = (
    SELECT MAX({date_column})
    FROM {profiler.quoted_table(table)} latest_rows
    WHERE {where.replace('source_rows.', 'latest_rows.')}
      AND {date_column} IS NOT NULL
  )
  AND {nonblank}
GROUP BY 1, 2
HAVING COUNT(DISTINCT {employee_column}) >= {minimum}
""".strip()
        )
    return f"""
WITH base AS (
{' UNION ALL '.join(selects)}
), ranked AS (
  SELECT
    column_name,
    value_label,
    employee_count,
    row_count,
    ROW_NUMBER() OVER (PARTITION BY column_name ORDER BY employee_count DESC, value_label) AS rn
  FROM base
)
SELECT column_name, value_label, employee_count, row_count, rn
FROM ranked
WHERE rn <= {SAFE_VALUE_FULL_N}
ORDER BY column_name, rn
""".strip()


def build_pair_summary_sql(variable: dict[str, Any], pairs: list[tuple[str, str]], rules: dict[str, Any]) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    statements = []
    for index, (left, right) in enumerate(pairs, start=1):
        left_q = profiler.quoted_identifier(left, "left report column")
        right_q = profiler.quoted_identifier(right, "right report column")
        left_nonblank = profiler.nonblank_expression(left)
        right_nonblank = profiler.nonblank_expression(right)
        pair_name = f"{left} -> {right}"
        statements.append(
            f"""
pair_{index} AS (
  SELECT
    CAST({left_q} AS VARCHAR(512)) AS left_value,
    CAST({right_q} AS VARCHAR(512)) AS right_value,
    {employee_column} AS employee_key
  FROM {profiler.quoted_table(table)}
  WHERE {where}
    AND {date_column} = (
      SELECT MAX({date_column})
      FROM {profiler.quoted_table(table)}
      WHERE {where}
        AND {date_column} IS NOT NULL
    )
    AND {left_nonblank}
    AND {right_nonblank}
),
pair_{index}_summary AS (
  SELECT
    {profiler.sql_literal(pair_name)} AS pair,
    COUNT(DISTINCT employee_key) AS paired_employees,
    COUNT(DISTINCT left_value) AS left_distinct_values,
    COUNT(DISTINCT right_value) AS right_distinct_values,
    (SELECT COUNT(*) FROM (SELECT left_value FROM pair_{index} GROUP BY left_value HAVING COUNT(DISTINCT right_value) > 1) s) AS left_values_with_multiple_right_values,
    (SELECT COUNT(*) FROM (SELECT right_value FROM pair_{index} GROUP BY right_value HAVING COUNT(DISTINCT left_value) > 1) s) AS right_values_with_multiple_left_values
  FROM pair_{index}
),
pair_{index}_top AS (
  SELECT
    {profiler.sql_literal(pair_name)} AS pair,
    left_value,
    right_value,
    COUNT(DISTINCT employee_key) AS employee_count,
    ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT employee_key) DESC, left_value, right_value) AS rn
  FROM pair_{index}
  GROUP BY 1, 2, 3
  HAVING COUNT(DISTINCT employee_key) >= {int(rules['population']['minimum_shared_cohort'])}
)
""".strip()
        )
    with_clause = ",\n".join(statements)
    summary_selects = "\nUNION ALL\n".join(
        "SELECT pair, paired_employees, left_distinct_values, right_distinct_values, "
        "left_values_with_multiple_right_values, right_values_with_multiple_left_values "
        f"FROM pair_{index}_summary"
        for index in range(1, len(pairs) + 1)
    )
    top_selects = "\nUNION ALL\n".join(
        f"SELECT pair, left_value, right_value, employee_count FROM pair_{index}_top WHERE rn <= {SAFE_VALUE_FULL_N}"
        for index in range(1, len(pairs) + 1)
    )
    return f"""
WITH {with_clause}
SELECT 'summary' AS row_type, pair, CAST(NULL AS VARCHAR(512)) AS left_value, CAST(NULL AS VARCHAR(512)) AS right_value,
       paired_employees AS employee_count, left_distinct_values, right_distinct_values,
       left_values_with_multiple_right_values, right_values_with_multiple_left_values
FROM ({summary_selects}) summaries
UNION ALL
SELECT 'top_mapping' AS row_type, pair, left_value, right_value, employee_count,
       CAST(NULL AS BIGINT) AS left_distinct_values, CAST(NULL AS BIGINT) AS right_distinct_values,
       CAST(NULL AS BIGINT) AS left_values_with_multiple_right_values, CAST(NULL AS BIGINT) AS right_values_with_multiple_left_values
FROM ({top_selects}) mappings
ORDER BY row_type, pair, employee_count DESC
""".strip()


def score_application(assessment: dict[str, Any], rules: dict[str, Any]) -> list[dict[str, Any]]:
    rationales = {item.get("criterion_key"): item for item in assessment.get("score_rationales") or []}
    verifications = assessment.get("score_verification") or {}
    diagnostics = assessment.get("diagnostics") or {}
    rows: list[dict[str, Any]] = []
    for criterion in rules["criteria_order"]:
        score = int((assessment.get("scores") or {}).get(criterion, 0))
        label = profiler.CRITERION_LABELS.get(criterion, criterion.title())
        rationale = rationales.get(criterion)
        verification = verifications.get(criterion)
        outcome = "pass" if score == 2 else ("warning" if score == 1 else "fail")
        status_rule = ""
        observed = ""
        why = ""
        action = ""
        method = "Threshold calculado" if criterion in {"coverage", "missingness", "history"} else "Estado cualitativo configurado"
        sql_reference = None
        metrics = {}
        if rationale:
            status_rule = str(rationale.get("status_rule") or "")
            observed = str(rationale.get("supporting_evidence") or "")
            why = str(rationale.get("why_below_2") or "")
            action = str(rationale.get("recommended_action") or "")
            method = str(rationale.get("scoring_method") or method)
        elif verification:
            status_rule = str(verification.get("acceptance_rule") or "La verificación de score 2 cumplió la regla declarada.")
            observed = str(verification.get("result") or verification.get("evidence") or "")
            why = "Se cumplieron todos los requisitos v4 para este score cualitativo."
            action = "No se requiere acción inmediata; repetir la validación si cambia la fuente o definición."
            method = str(verification.get("method") or "Verificación de score 2")
            sql_reference = verification.get("query_reference")
            metrics = verification.get("metrics") or {}
        elif criterion == "coverage":
            status_rule = (
                f"Score 2 requiere coverage reciente ponderado >= {rules['coverage']['score_2_min_percent']}%; "
                f"score 1 requiere >= {rules['coverage']['score_1_min_percent']}%."
            )
            observed = f"Coverage reciente ponderado: {diagnostics.get('recent_coverage_percent')}%."
            why = "Coverage reciente cumplió el threshold del score." if score == 2 else "Coverage reciente no cumplió el threshold de score 2."
            action = "No se requiere acción inmediata." if score == 2 else "Mejorar observabilidad de la fuente y repetir el perfil de coverage."
        elif criterion == "missingness":
            status_rule = (
                f"Score 2 requiere missingness <= {rules['missingness']['score_2_max_percent']}% sin patrón sistemático; "
                f"score 1 permite <= {rules['missingness']['score_1_max_percent']}%."
            )
            observed = (
                f"Missingness reciente: {diagnostics.get('recent_missingness_percent')}%; "
                f"systematic_missingness={diagnostics.get('systematic_missingness')}."
            )
            why = "Missingness cumplió el threshold del score." if score == 2 else "Missingness o un patrón sistemático limitó el score."
            action = "No se requiere acción inmediata." if score == 2 else "Investigar causas de nulos y repetir el perfil de missingness."
        elif criterion == "history":
            status_rule = (
                f"Score 2 requiere >= {rules['history']['score_2_min_months']} meses utilizables; "
                f"score 1 requiere >= {rules['history']['score_1_min_months']} meses; leakage fuerza 0."
            )
            observed = (
                f"Utilizable desde {assessment.get('usable_since_date')}; última {assessment.get('latest_observation_date')}; "
                f"history_months={diagnostics.get('history_months')}; leakage={diagnostics.get('leakage_risk')}."
            )
            why = "La historia utilizable cumplió el threshold del score." if score == 2 else "La historia utilizable no cumplió el threshold de score 2."
            action = "No se requiere acción inmediata." if score == 2 else "Hacer backfill o validar más observaciones históricas sin leakage."
        rows.append(
            {
                "criterion": label,
                "criterion_key": criterion,
                "score": score,
                "status_rule": status_rule,
                "observed_evidence": observed,
                "outcome": outcome,
                "outcome_label": spanish_outcome(outcome),
                "why": why,
                "recommended_action": action,
                "scoring_method": method,
                "sql_reference": sql_reference,
                "metrics": metrics,
            }
        )
    return rows


def spanish_outcome(value: str) -> str:
    return {
        "pass": "Cumple",
        "warning": "Cumple parcialmente",
        "fail": "No cumple",
        "pending": "Pendiente",
        "blocked": "Bloqueada",
        "informative": "Informativa",
    }.get(str(value), str(value))


def split_focus_story(focus: Any) -> tuple[str, str]:
    if isinstance(focus, dict):
        return str(focus.get("question") or ""), str(focus.get("why") or "")
    text_value = str(focus).strip().rstrip(".")
    prefix = "Validamos "
    content = text_value[len(prefix):] if text_value.startswith(prefix) else text_value
    if " porque " in content:
        claim, reason = content.split(" porque ", 1)
        question = f"¿{claim[:1].upper() + claim[1:]}?"
        why = f"Esta comprobación es necesaria porque {reason}."
        return question, why
    return (
        f"¿Qué demuestra la comprobación sobre {content}?",
        "Esta comprobación forma parte del razonamiento específico requerido para interpretar la variable.",
    )


def focus_criterion(focus: Any, semantic_type: str) -> str:
    if isinstance(focus, dict) and focus.get("criterion"):
        return str(focus["criterion"])
    text_value = str(focus).lower()
    if any(token in text_value for token in (
        "fuente", "proveedor", "licencia", "acceso", "propietario"
    )):
        return "source"
    if any(token in text_value for token in (
        "join", "self-join", "empleado-snapshot", "empleado-fecha", "matched", "cardinalidad"
    )):
        return "join"
    if any(token in text_value for token in (
        "nulo", "alias", "contradic", "normaliz", "dominio", "deduplic", "solap", "estabilidad", "transici"
    )):
        return "consistency"
    if any(token in text_value for token in (
        "historia", "continuidad", "longitudinal", "vintage", "wave", "comparabilidad", "backfill"
    )):
        return "history"
    if any(token in text_value for token in (
        "ingeniería", "desarrollo", "pipeline", "trabajo manual"
    )):
        return "effort"
    if semantic_type == "external_source" and "mapping" not in text_value:
        return "source"
    return "definition"


def focus_evidence_role(focus: Any, criterion: str) -> str:
    if isinstance(focus, dict) and focus.get("evidence_role"):
        return str(focus["evidence_role"])
    text_value = str(focus).lower()
    if "context" in text_value or "sólo" in text_value or "solo" in text_value:
        return "contextual"
    if criterion in {"definition", "consistency"}:
        return "defining"
    return "supporting"


def story_query_rows(
    report_detail: dict[str, Any], reference: str | None
) -> list[dict[str, Any]]:
    if not reference:
        return []
    wanted = Path(reference).as_posix().lower()
    query_results = (report_detail.get("evidence") or {}).get("query_results") or {}
    for saved_reference, rows in query_results.items():
        if Path(saved_reference).as_posix().lower() == wanted:
            return list(rows or [])
        if Path(saved_reference).name.lower() == Path(reference).name.lower():
            return list(rows or [])
    return []


def aggregate_story_metric(
    rows: list[dict[str, Any]], metric: str, aggregate: str = "sum"
) -> float | int | None:
    values = [
        row.get(metric) for row in rows
        if isinstance(row.get(metric), (int, float))
        and not isinstance(row.get(metric), bool)
    ]
    if not values:
        return None
    if aggregate == "max":
        return max(values)
    if aggregate == "min":
        return min(values)
    if aggregate == "latest":
        return values[-1]
    return sum(values)


def story_metrics(
    item: dict[str, Any], report_detail: dict[str, Any]
) -> dict[str, Any]:
    rows = story_query_rows(report_detail, item.get("sql_reference"))
    metrics: dict[str, Any] = {}
    checks = item.get("metric_checks") or []
    for check in checks:
        metric = str(check.get("metric") or "")
        if metric:
            metrics[metric] = aggregate_story_metric(
                rows, metric, str(check.get("aggregate") or "sum")
            )
    for metric in item.get("metric_fields") or []:
        metric_name = str(metric)
        metrics[metric_name] = aggregate_story_metric(rows, metric_name, "sum")
    return metrics


def evaluate_story_checks(
    item: dict[str, Any], metrics: dict[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    checks = item.get("metric_checks") or []
    if not checks:
        return (
            "informative" if item.get("evidence_role") == "contextual" else "pending",
            [],
        )
    evaluated = []
    all_pass = True
    for check in checks:
        metric = str(check.get("metric") or "")
        observed = metrics.get(metric)
        threshold = check.get("threshold")
        operator = str(check.get("operator") or "eq")
        passed = bool(
            isinstance(observed, (int, float))
            and isinstance(threshold, (int, float))
            and profiler.compare_numeric(float(observed), operator, float(threshold))
        )
        all_pass = all_pass and passed
        evaluated.append(
            {
                "metric": metric,
                "aggregate": check.get("aggregate") or "sum",
                "observed": observed,
                "operator": operator,
                "threshold": threshold,
                "passed": passed,
            }
        )
    return ("pass" if all_pass else "fail"), evaluated


def historical_story(
    assessment: dict[str, Any], analysis: dict[str, Any]
) -> dict[str, Any]:
    diagnostics = assessment.get("diagnostics") or {}
    coverage = assessment.get("coverage") or []
    first = assessment.get("first_observed_date")
    usable = assessment.get("usable_since_date")
    latest = assessment.get("latest_observation_date")
    phases = [
        {
            "stage": "Fuente y concepto",
            "narrative": (
                f"Partimos de {assessment.get('source_table')} y de los campos "
                f"{assessment.get('source_columns')}. {analysis.get('source_reasoning')}"
            ),
        },
        {
            "stage": "Inicio de observabilidad",
            "narrative": (
                f"La primera observación agregada fue {first or 'no establecida'}; "
                f"la historia se vuelve utilizable desde {usable or 'no establecida'} y "
                f"la última observación es {latest or 'no disponible'}."
            ),
        },
        {
            "stage": "Calidad reciente",
            "narrative": (
                f"En la ventana reciente, Coverage fue "
                f"{diagnostics.get('recent_coverage_percent')}% y Missingness "
                f"{diagnostics.get('recent_missingness_percent')}%. Se evaluaron "
                f"{len(coverage)} observaciones agregadas."
            ),
        },
    ]
    for finding in analysis.get("known_findings") or []:
        phases.append({"stage": "Hallazgo material", "narrative": str(finding)})
    phases.append(
        {
            "stage": "Decisión",
            "narrative": (
                f"El resultado final es {assessment.get('result')} con "
                f"{assessment.get('total')} puntos. Los criterios inferiores a 2 "
                "conservan su limitación y acción en las pruebas siguientes."
            ),
        }
    )
    return {
        "summary": (
            "Seguimos la variable desde la confirmación de la fuente hasta la "
            "historia utilizable, los hallazgos de calidad y la decisión de scoring."
        ),
        "phases": phases,
    }


def build_validation_story(
    variable: dict[str, Any],
    assessment: dict[str, Any],
    report_detail: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    analysis = variable.get("analysis") or {}
    semantic_type = str(analysis.get("semantic_type") or "")
    configured = analysis.get("validation_story") or []
    focus_items = configured or analysis.get("validation_focus") or []
    score_rows = {
        item["criterion_key"]: item
        for item in score_application(assessment, rules)
    }
    source_columns = source_column_list(variable.get("source") or {})
    sql_references = list(
        ((report_detail.get("evidence") or {}).get("sql_references") or [])
    )
    stories: list[dict[str, Any]] = []
    for index, raw_item in enumerate(focus_items, start=1):
        item = copy.deepcopy(raw_item) if isinstance(raw_item, dict) else {}
        question, why = split_focus_story(raw_item)
        criterion = focus_criterion(raw_item, semantic_type)
        role = focus_evidence_role(raw_item, criterion)
        score_row = score_rows.get(criterion) or {}
        reference = item.get("sql_reference")
        metrics = story_metrics(item, report_detail) if item else {}
        check_outcome, checks = evaluate_story_checks(item, metrics) if item else ("pending", [])
        if not configured:
            check_outcome = str(score_row.get("outcome") or "pending")
        elif check_outcome == "pending" and story_query_rows(report_detail, reference):
            check_outcome = str(score_row.get("outcome") or "pending")

        fields = list(item.get("fields") or source_columns)
        if reference:
            method = str(item.get("method"))
            observed = (
                "Métricas agregadas ejecutadas: "
                + ", ".join(f"{key}={value}" for key, value in metrics.items())
                if metrics else
                "La consulta se ejecutó, pero no devolvió las métricas esperadas para esta prueba."
            )
        else:
            method = (
                "Revisamos el perfil agregado, la historia, las relaciones de columnas "
                "y la evidencia de scoring disponible para esta variable."
            )
            observed = str(score_row.get("observed_evidence") or "Sin evidencia agregada suficiente.")

        if role == "contextual":
            interpretation = (
                "La prueba aporta contexto para interpretar el concepto, pero no es "
                "un requisito definitorio y no puede elevar el score."
            )
            limitation = "El patrón observado no demuestra por sí solo la variable solicitada."
            score_effect = (
                f"Evidencia contextual para {profiler.CRITERION_LABELS.get(criterion, criterion)}; "
                "sin capacidad de aumentar el score."
            )
        else:
            interpretation = (
                f"{score_row.get('why') or 'La evidencia debe interpretarse contra la regla declarada.'} "
                f"Resultado de la prueba: {spanish_outcome(check_outcome)}."
            )
            limitation = (
                str(score_row.get("why"))
                if int(score_row.get("score", 0)) < 2
                else "No se identificó una limitación que reduzca este criterio."
            )
            score_effect = (
                f"{profiler.CRITERION_LABELS.get(criterion, criterion)} quedó en "
                f"{score_row.get('score')} de acuerdo con la evidencia y los límites v4."
            )

        stories.append(
            {
                "order": index,
                "id": item.get("id") or f"focus_{index:02d}",
                "question": item.get("question") or question,
                "why": item.get("why") or why,
                "criterion": criterion,
                "evidence_role": role,
                "fields": fields,
                "population": assessment.get("population_filter"),
                "grain": assessment.get("level_data"),
                "temporal_boundary": analysis.get("prediction_cutoff"),
                "method": method,
                "sql_references": [reference] if reference else sql_references,
                "acceptance_rule": item.get("acceptance_rule") or score_row.get("status_rule"),
                "observed_metrics": metrics,
                "metric_checks": checks,
                "observed_evidence": observed,
                "outcome": check_outcome,
                "outcome_label": spanish_outcome(check_outcome),
                "interpretation": interpretation,
                "score_effect": score_effect,
                "limitation": limitation,
                "recommended_action": score_row.get("recommended_action") or "Completar la validación y repetir el assessment.",
            }
        )
    return stories


def normalized_source_columns(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return {
        item.strip()
        for item in str(value or "").split(",")
        if item.strip()
    }


def project_display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def documentation_target_path(
    variable: dict[str, Any], documentation_root: Path
) -> Path:
    root = documentation_root.resolve()
    configured = str(
        (variable.get("analysis") or {}).get("documentation_path") or ""
    ).strip()
    relative = (
        Path(configured)
        if configured
        else Path(renderer.slugify(str(variable.get("variable") or "variable")))
        / "README.md"
    )
    if relative.is_absolute():
        raise ValueError("analysis.documentation_path must be relative to the documentation root.")
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or target.suffix.lower() != ".md":
        raise ValueError(
            f"Invalid variable documentation path outside {root}: {relative}"
        )
    return target


def documentation_context_for_variable(
    variable: dict[str, Any], documentation_root: Path | None
) -> dict[str, Any]:
    if documentation_root is None:
        return {
            "status": "disabled",
            "context_is_evidence": False,
        }
    target = documentation_target_path(variable, documentation_root)
    text = target.read_text(encoding="utf-8") if target.is_file() else ""
    excerpt_limit = 6000
    return {
        "status": "loaded" if text else "new_document",
        "path": project_display_path(target),
        "existing_document": target.is_file(),
        "excerpt": text[:excerpt_limit],
        "excerpt_truncated": len(text) > excerpt_limit,
        "context_is_evidence": False,
        "usage_rule": (
            "Usar la documentación para orientar relaciones, caveats e hipótesis; "
            "revalidar todo hallazgo dependiente de datos."
        ),
    }


def assessment_knowledge_summary(
    assessment: dict[str, Any]
) -> dict[str, Any]:
    plan = assessment.get("analysis_plan") or {}
    report = assessment.get("report_detail") or {}
    stories = report.get("validation_story") or plan.get("validation_story") or []
    findings = list(
        dict.fromkeys(
            str(item.get("interpretation")).strip()
            for item in stories
            if str(item.get("interpretation") or "").strip()
        )
    )[:4]
    unresolved = (plan.get("gap_review") or {}).get("unresolved") or []
    limitations = list(
        dict.fromkeys(
            str(item.get("reason")).strip()
            for item in unresolved
            if str(item.get("reason") or "").strip()
        )
    )[:4]
    actions = list(
        dict.fromkeys(
            str(item.get("recommended_action") or item.get("next_action")).strip()
            for item in [*stories, *unresolved]
            if str(item.get("recommended_action") or item.get("next_action") or "").strip()
        )
    )[:5]
    diagnostics = assessment.get("diagnostics") or {}
    return {
        "variable": assessment.get("variable"),
        "semantic_type": plan.get("semantic_type"),
        "result": assessment.get("result"),
        "total": assessment.get("total"),
        "source_table": assessment.get("source_table"),
        "source_columns": sorted(normalized_source_columns(assessment.get("source_columns"))),
        "recent_coverage_percent": diagnostics.get("recent_coverage_percent"),
        "history_months": diagnostics.get("history_months"),
        "key_findings": findings,
        "limitations": limitations,
        "recommended_actions": actions,
        "documentation": assessment.get("documentation") or {},
        "context_is_evidence": False,
    }


def accumulated_knowledge_for_variable(
    variable: dict[str, Any],
    prior_assessments: list[dict[str, Any]],
    portfolio_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    current_name = str(variable.get("variable") or "")
    directly_related = set(portfolio_entry.get("dependencies") or [])
    directly_related.update(
        (portfolio_entry.get("context_alignment") or {}).get("related_variables")
        or []
    )
    accumulated: list[dict[str, Any]] = []
    for prior in prior_assessments:
        item = assessment_knowledge_summary(prior)
        prior_name = str(item.get("variable") or "")
        item["relevance_to_current_variable"] = (
            "directly_related"
            if prior_name in directly_related
            else "portfolio_background"
        )
        item["current_variable"] = current_name
        accumulated.append(item)
    return accumulated


def _markdown_bullets(values: list[Any], empty: str) -> str:
    clean = [str(value).strip() for value in values if str(value or "").strip()]
    return "\n".join(f"- {value}" for value in clean) if clean else f"- {empty}"


def render_variable_documentation_block(
    assessment: dict[str, Any], run_id: str
) -> tuple[str, str, str]:
    variable_name = str(assessment.get("variable") or "Variable")
    slug = renderer.slugify(variable_name)
    start = f"<!-- BEGIN evaluate-attrition-variable:{slug} -->"
    end = f"<!-- END evaluate-attrition-variable:{slug} -->"
    plan = assessment.get("analysis_plan") or {}
    context = plan.get("context_isolation") or {}
    problem = context.get("problem_context") or {}
    alignment = context.get("current_variable_alignment") or {}
    knowledge = assessment_knowledge_summary(assessment)
    scores = assessment.get("scores") or {}
    score_text = ", ".join(
        f"{profiler.CRITERION_LABELS.get(key, key)}={value}"
        for key, value in scores.items()
    )
    relationships = [
        item.get("relationship")
        for item in alignment.get("relationships") or []
        if item.get("relationship")
    ]
    evidence_refs = list(
        dict.fromkeys(
            str(item.get("query_reference"))
            for item in (assessment.get("evidence_ledger") or {}).get("queries") or []
            if item.get("query_reference")
        )
    )
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    block = f"""{start}
## Conocimiento acumulado: {variable_name}

_Actualizado por el assessment v4 `{run_id}` el {generated_at}._

### Contexto del problema

- **Problema:** {problem.get('problem_statement') or 'Por confirmar.'}
- **Decisión / caso de uso:** {problem.get('decision_or_use_case') or 'Por confirmar.'}
- **Outcome:** {problem.get('outcome') or 'Por confirmar.'}
- **Población:** {problem.get('population') or plan.get('population') or 'Por confirmar.'}
- **Límite de conocimiento:** {problem.get('knowledge_boundary') or plan.get('prediction_cutoff') or 'Por confirmar.'}
- **Rol de la variable:** {alignment.get('role') or 'candidate_variable'}
- **Relevancia:** {alignment.get('relevance') or plan.get('intended_use') or 'Por confirmar.'}

### Definición y fuente evaluadas

- **Definición vigente:** {assessment.get('definition_text') or plan.get('concept') or 'Por confirmar.'}
- **Tipo semántico:** {plan.get('semantic_type') or 'Por confirmar.'}
- **Tabla / fuente:** {assessment.get('source_table') or 'No validada.'}
- **Columnas:** {assessment.get('source_columns') or 'No validadas.'}
- **Grain:** {assessment.get('level_data') or plan.get('grain') or 'Por confirmar.'}

### Relaciones con el portafolio

{_markdown_bullets(relationships, 'No se documentaron relaciones contextuales adicionales.')}

### Resultado y evidencia agregada

- **Resultado:** {assessment.get('result')} ({assessment.get('total')} puntos).
- **Scores:** {score_text or 'No calculados.'}
- **Coverage reciente:** {knowledge.get('recent_coverage_percent')}%.
- **Historia utilizable:** {knowledge.get('history_months')} meses.

**Hallazgos principales**

{_markdown_bullets(knowledge.get('key_findings') or [], 'No se consolidaron hallazgos adicionales.')}

**Limitaciones vigentes**

{_markdown_bullets(knowledge.get('limitations') or [], 'No se registraron limitaciones que reduzcan el score.')}

**Acciones recomendadas**

{_markdown_bullets(knowledge.get('recommended_actions') or [], 'Mantener monitoreo y revalidar cuando cambie la fuente o definición.')}

**SQL y evidencia trazable**

{_markdown_bullets([f'`{value}`' for value in evidence_refs], 'No existe SQL ejecutable para esta fuente.')}

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** {(plan.get('plan_authorship') or {}).get('mode') or 'Por confirmar'}.
- **Versiones de plan:** {', '.join(str(item.get('plan_version')) for item in assessment.get('pre_execution_plans') or [assessment.get('pre_execution_plan') or {}])}.
- **Revisión de suficiencia:** {'Hay brechas pendientes.' if (plan.get('gap_review') or {}).get('requires_follow_up') else 'No se registraron brechas adicionales al cerrar el assessment.'}

{end}"""
    return start, end, block


def render_documentation_history_entry(assessment: dict[str, Any], run_id: str) -> str:
    """Create an append-only, factual decision record for future context."""
    variable_name = str(assessment.get("variable") or "Variable")
    slug = renderer.slugify(variable_name)
    start = f"<!-- BEGIN evaluate-attrition-variable-run:{slug}:{run_id} -->"
    end = f"<!-- END evaluate-attrition-variable-run:{slug}:{run_id} -->"
    report = assessment.get("report_detail") or {}
    stories = report.get("validation_story") or []
    plan_versions = assessment.get("pre_execution_plans") or [
        assessment.get("pre_execution_plan") or {}
    ]
    version_lines = []
    for plan_item in plan_versions:
        reason = (plan_item.get("plan_authorship") or {}).get("revision_reason")
        version_lines.append(
            f"- Plan v{plan_item.get('plan_version')}: "
            f"{reason or 'plan inicial antes de ejecutar evidencia agregada.'}"
        )
    story_lines = []
    for story in stories:
        story_lines.append(
            f"- **{story.get('criterion')}:** {story.get('question')} "
            f"— resultado {story.get('outcome_label') or story.get('outcome')}; "
            f"impacto: {story.get('score_effect')}"
        )
    ledger = assessment.get("evidence_ledger") or {}
    references = [
        str(item.get("query_reference"))
        for item in ledger.get("queries") or []
        if item.get("query_reference")
    ]
    version_text = "\n".join(version_lines) or "- No se registró una versión de plan."
    story_text = "\n".join(story_lines) or "- No se registraron historias de validación."
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    return f"""{start}

### Historial de decisión — run `{run_id}`

_Registrado el {stamp}. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** {assessment.get('result')} ({assessment.get('total')} puntos).

**Evolución del plan**

{version_text}

**Validaciones y efecto observado**

{story_text}

**Evidencia SQL agregada**

{_markdown_bullets([f'`{reference}`' for reference in references], 'No se registró SQL ejecutado.')}

{end}"""


def update_variable_documentation(
    variable: dict[str, Any],
    assessment: dict[str, Any],
    documentation_root: Path,
    run_id: str,
) -> dict[str, Any]:
    target = documentation_target_path(variable, documentation_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    start, end, block = render_variable_documentation_block(assessment, run_id)
    if start in existing and end in existing:
        prefix, remainder = existing.split(start, 1)
        _, suffix = remainder.split(end, 1)
        updated = prefix.rstrip() + "\n\n" + block + suffix
    else:
        heading = existing.rstrip() or f"# {assessment.get('variable')}"
        updated = heading + "\n\n" + block + "\n"
    history = render_documentation_history_entry(assessment, run_id)
    history_marker = history.splitlines()[0]
    if history_marker not in updated:
        updated = updated.rstrip() + "\n\n" + history + "\n"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(updated.rstrip() + "\n", encoding="utf-8")
    temporary.replace(target)
    return {
        "status": "updated",
        "path": project_display_path(target),
        "run_id": run_id,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "managed_section": renderer.slugify(str(assessment.get("variable") or "variable")),
        "context_is_evidence": False,
    }


def prior_context_for_variable(
    variable: dict[str, Any], prior_assessments: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    analysis = variable.get("analysis") or {}
    source = variable.get("source") or {}
    current_table = str(source.get("table") or "").strip()
    current_columns = normalized_source_columns(source.get("columns"))
    explicit = {
        str(item).strip()
        for item in (analysis.get("related_prior_variables") or [])
        if str(item).strip()
    }
    relevant: list[dict[str, Any]] = []
    for prior in reversed(prior_assessments):
        prior_name = str(prior.get("variable") or "").strip()
        prior_table = str(prior.get("source_table") or "").strip()
        prior_columns = normalized_source_columns(prior.get("source_columns"))
        shared_columns = sorted(current_columns & prior_columns)
        explicitly_related = prior_name in explicit
        shares_source = bool(
            current_table
            and current_table == prior_table
            and shared_columns
        )
        if not explicitly_related and not shares_source:
            continue
        relevant.append(
            {
                "variable": prior_name,
                "result": prior.get("result"),
                "total": prior.get("total"),
                "shared_source_table": current_table if shares_source else None,
                "shared_columns": shared_columns,
                "use": (
                    "Sólo contexto. Revalidar la afirmación, población, grain, "
                    "ventana y regla de aceptación de la variable actual."
                ),
            }
        )
        if len(relevant) == 5:
            break
    return list(reversed(relevant))


def build_analysis_plan(
    variable: dict[str, Any],
    assessment: dict[str, Any],
    rules: dict[str, Any],
    prior_assessments: list[dict[str, Any]] | None = None,
    report_detail: dict[str, Any] | None = None,
    portfolio_context: dict[str, Any] | None = None,
    documentation_context: dict[str, Any] | None = None,
    accumulated_knowledge: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    analysis = copy.deepcopy(variable.get("analysis") or {})
    semantic_type = str(analysis.get("semantic_type") or "")
    measurement = variable.get("measurement") or {}
    modules = list(SEMANTIC_ANALYSIS_MODULES.get(semantic_type, []))
    measurement_type = str(measurement.get("type") or "")
    if measurement_type == "event":
        modules.extend(["flag_date_alignment", "event_deduplication"])
    if measurement_type == "rolling_derived":
        modules.extend(["rolling_window_boundaries", "future_information_leakage"])
    modules.extend(["coverage_missingness_history", "criterion_score_trace"])
    modules = list(dict.fromkeys(modules))

    visualizations = [
        "score_overview",
        "coverage_history",
        "annual_coverage_by_fiscal_year",
        *SEMANTIC_VISUALIZATIONS.get(semantic_type, []),
    ]
    if (report_detail or assessment.get("report_detail") or {}).get("columns"):
        visualizations.append("column_completeness")
    if measurement_type in {"event", "rolling_derived"}:
        visualizations.append("event_prevalence")
    visualizations = list(dict.fromkeys(visualizations))

    score_rows = score_application(assessment, rules)
    unresolved = [
        {
            "criterion": item["criterion_key"],
            "score": item["score"],
            "reason": item["why"],
            "next_action": item["recommended_action"],
        }
        for item in score_rows
        if int(item.get("score", 0)) < 2
    ]
    derivation = assessment.get("derivation") or {}
    derivation_status = derivation.get("selected_status") or derivation.get("status")
    directness = (
        "direct"
        if semantic_type == "direct_field" and not derivation
        else str(derivation_status or semantic_type)
    )
    prior_context = prior_context_for_variable(
        variable, prior_assessments or []
    )
    detail = report_detail or assessment.get("report_detail") or {}
    validation_stories = build_validation_story(
        variable, assessment, detail, rules
    )
    history_story = historical_story(assessment, analysis)
    portfolio_context = portfolio_context or {}
    portfolio_entry = next(
        (
            item
            for item in portfolio_context.get("variables") or []
            if str(item.get("variable")) == str(assessment.get("variable"))
        ),
        {},
    )
    accumulated_knowledge = list(accumulated_knowledge or [])
    return {
        "schema_version": 1,
        "language": analysis.get("language") or "es",
        "variable": assessment.get("variable"),
        "intended_use": analysis.get("intended_use") or analysis.get("attrition_use"),
        "attrition_use": analysis.get("attrition_use") or analysis.get("intended_use"),
        "prediction_cutoff": analysis.get("prediction_cutoff"),
        "population": assessment.get("population_filter"),
        "grain": assessment.get("level_data"),
        "semantic_type": semantic_type,
        "plan_version": int(analysis.get("plan_version") or 1),
        "plan_authorship": {
            "mode": analysis.get("plan_authorship") or (
                "legacy_catalog" if analysis.get("allow_legacy_story_materialization") else "codex_explicit"
            ),
            "revision_reason": analysis.get("plan_revision_reason"),
        },
        "directness": directness,
        "source_reasoning": analysis.get("source_reasoning"),
        "validation_focus": list(analysis.get("validation_focus") or []),
        "analysis_modules": modules,
        "planned_visualizations": visualizations,
        "visualization_policy": {
            "priority": "graph_first",
            "rule": (
                "Mostrar primero una visualización segura cuando una relación, "
                "tendencia o distribución pueda comunicarse gráficamente; usar "
                "tablas como detalle complementario."
            ),
        },
        "numeric_bands": analysis.get("numeric_bands"),
        "prior_evidence_policy": analysis.get("prior_evidence_policy"),
        "context_isolation": {
            "mode": "secuencial_con_contexto_compartido",
            "fresh_inputs": [
                "spec de la variable actual",
                "evidencia agregada actual",
                "módulos de validación semántica actuales",
            ],
            "problem_context": portfolio_context.get("problem_context") or {},
            "portfolio_overview": portfolio_context.get("portfolio_overview") or {},
            "current_variable_alignment": portfolio_entry.get("context_alignment") or {},
            "documentation_context": documentation_context or {},
            "accumulated_knowledge": accumulated_knowledge,
            "prior_context": prior_context,
            "prior_context_is_evidence": False,
            "accumulated_knowledge_is_evidence": False,
            "usage_rule": (
                "El contexto del problema y el conocimiento acumulado orientan "
                "hipótesis y relaciones; la variable actual conserva sus propias "
                "consultas, población, grain, ventana y reglas de aceptación."
            ),
        },
        "derivation": derivation,
        "historical_story": history_story,
        "validation_story": validation_stories,
        "score_rules": [
            {
                "criterion": item["criterion_key"],
                "rule": item["status_rule"],
                "score": item["score"],
                "outcome": item["outcome"],
            }
            for item in score_rows
        ],
        "gap_review": {
            "requires_follow_up": bool(unresolved),
            "unresolved": unresolved,
            "review_rule": (
                "Añadir o revisar una validación agregada cuando la evidencia revele "
                "una condición semántica, temporal, de privacidad o de join no resuelta."
            ),
        },
    }


def annual_coverage_by_fiscal_year(
    assessment: dict[str, Any],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in assessment.get("coverage") or []:
        fiscal_year = row.get("fiscal_year")
        if fiscal_year in (None, ""):
            continue
        key = str(fiscal_year)
        item = grouped.setdefault(
            key,
            {
                "fiscal_year": key,
                "first_snapshot_date": None,
                "last_snapshot_date": None,
                "snapshot_count": 0,
                "eligible_employee_snapshots": 0,
                "observable_employee_snapshots": 0,
                "missing_employee_snapshots": 0,
                "event_employee_snapshots": 0,
                "has_event_counts": False,
            },
        )
        snapshot_date = row.get("snapshot_date")
        snapshot_text = str(snapshot_date) if snapshot_date not in (None, "") else None
        if snapshot_text:
            if not item["first_snapshot_date"] or snapshot_text < item["first_snapshot_date"]:
                item["first_snapshot_date"] = snapshot_text
            if not item["last_snapshot_date"] or snapshot_text > item["last_snapshot_date"]:
                item["last_snapshot_date"] = snapshot_text
        item["snapshot_count"] += 1
        eligible = int(row.get("eligible_employees") or 0)
        observable = int(row.get("observable_employees") or 0)
        missing = row.get("missing_employees")
        item["eligible_employee_snapshots"] += eligible
        item["observable_employee_snapshots"] += observable
        item["missing_employee_snapshots"] += (
            int(missing) if missing is not None else max(eligible - observable, 0)
        )
        event_count = row.get("event_employees")
        if event_count is not None:
            item["has_event_counts"] = True
            item["event_employee_snapshots"] += int(event_count or 0)

    result = []
    for item in grouped.values():
        eligible = item["eligible_employee_snapshots"]
        observable = item["observable_employee_snapshots"]
        item["observable_coverage_percent"] = (
            round(observable * 100.0 / eligible, 4) if eligible else None
        )
        item["missingness_percent"] = (
            round(item["missing_employee_snapshots"] * 100.0 / eligible, 4)
            if eligible
            else None
        )
        item["event_prevalence_percent"] = (
            round(item["event_employee_snapshots"] * 100.0 / observable, 4)
            if item.pop("has_event_counts") and observable
            else None
        )
        result.append(item)
    return sorted(
        result,
        key=lambda item: (
            str(item.get("first_snapshot_date") or ""),
            str(item.get("fiscal_year") or ""),
        ),
    )


def coverage_summary(assessment: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    diagnostics = assessment.get("diagnostics") or {}
    return {
        "recent_coverage_percent": diagnostics.get("recent_coverage_percent"),
        "recent_missingness_percent": diagnostics.get("recent_missingness_percent"),
        "systematic_missingness": diagnostics.get("systematic_missingness"),
        "history_months": diagnostics.get("history_months"),
        "first_observed_date": assessment.get("first_observed_date"),
        "usable_since_date": assessment.get("usable_since_date"),
        "latest_observation_date": assessment.get("latest_observation_date"),
        "annual_by_fiscal_year": annual_coverage_by_fiscal_year(assessment),
        "explanation": (
            f"Coverage usa las últimas {rules['coverage']['assessment_window_observations']} observaciones ponderadas por denominador. "
            f"Missingness usa las últimas {rules['missingness']['assessment_window_observations']} observaciones. "
            "El resumen por fiscal_year suma empleados-snapshot elegibles y observables antes de calcular porcentajes, por lo que no promedia meses de distinto tamaño. "
            f"History usa meses desde la primera racha utilizable de {rules['usable_history']['consecutive_observations']} observaciones con "
            f">= {rules['usable_history']['coverage_threshold_percent']}% coverage."
        ),
    }


def merge_column_profiles(base_columns: list[dict[str, str]], metadata_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metadata = {str(row.get("column_name")): row for row in metadata_rows}
    profiles = {str(row.get("column_name")): row for row in profile_rows}
    merged = []
    for item in base_columns:
        column = item["column"]
        meta = metadata.get(column, {})
        profile = profiles.get(column, {})
        eligible = int(profile.get("eligible_employees") or 0)
        populated = int(profile.get("populated_employees") or 0)
        safe, reason = is_value_display_safe(column)
        distinct = profile.get("distinct_values")
        display = reason
        if safe and distinct is not None:
            try:
                display = "Se muestran todos los valores seguros porque la cardinalidad es pequeña." if int(distinct) <= SAFE_VALUE_FULL_N else "Se muestran los 10 valores seguros principales; la cola larga sólo se resume."
            except Exception:
                pass
        merged.append(
            {
                "column": column,
                "role": item.get("role"),
                "role_label": item.get("role_label"),
                "description": item.get("description"),
                "data_type": meta.get("data_type") or "No encontrada en information_schema",
                "is_nullable": meta.get("is_nullable"),
                "eligible_employees": eligible or None,
                "populated_employees": populated or None,
                "missing_employees": (eligible - populated) if eligible else None,
                "distinct_values": distinct,
                "first_populated_date": profile.get("first_populated_date"),
                "latest_populated_date": profile.get("latest_populated_date"),
                "value_display": display,
                "exists_in_source": bool(meta),
            }
        )
    return merged


def attach_value_distributions(columns: list[dict[str, Any]], value_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_column: dict[str, list[dict[str, Any]]] = {}
    for row in value_rows:
        by_column.setdefault(str(row.get("column_name")), []).append(
            {
                "value_label": row.get("value_label"),
                "employee_count": row.get("employee_count"),
                "row_count": row.get("row_count"),
            }
        )
    distributions = []
    for column in columns:
        safe, reason = is_value_display_safe(str(column.get("column")))
        if not safe:
            distributions.append({"column": column.get("column"), "suppressed": True, "reason": reason})
            continue
        distinct = column.get("distinct_values")
        try:
            display_mode = "all_safe_values" if int(distinct or 0) <= SAFE_VALUE_FULL_N else "top_10"
        except Exception:
            display_mode = "top_10"
        values = by_column.get(str(column.get("column")), [])
        if display_mode == "top_10":
            values = values[:SAFE_VALUE_TOP_N]
        distributions.append(
            {
                "column": column.get("column"),
                "suppressed": False,
                "display_mode": display_mode,
                "values": values,
            }
        )
    return distributions


def build_single_pair_summary_queries(
    variable: dict[str, Any], left: str, right: str, rules: dict[str, Any]
) -> list[tuple[str, str]]:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    left_q = profiler.quoted_identifier(left, "left report column")
    right_q = profiler.quoted_identifier(right, "right report column")
    left_nonblank = profiler.nonblank_expression(left)
    right_nonblank = profiler.nonblank_expression(right)
    table_q = profiler.quoted_table(table)
    latest_filter = f"""{where}
    AND {date_column} = (
      SELECT MAX({date_column})
      FROM {table_q}
      WHERE {where}
        AND {date_column} IS NOT NULL
    )
    AND {left_nonblank}
    AND {right_nonblank}"""
    return [
        (
            "employee_count",
            f"""
SELECT 'employee_count' AS metric,
       COUNT(DISTINCT {employee_column}) AS metric_value
FROM {table_q}
WHERE {latest_filter}
""".strip(),
        ),
        (
            "left_distinct_values",
            f"""
SELECT 'left_distinct_values' AS metric,
       COUNT(DISTINCT CAST({left_q} AS VARCHAR(512))) AS metric_value
FROM {table_q}
WHERE {latest_filter}
""".strip(),
        ),
        (
            "right_distinct_values",
            f"""
SELECT 'right_distinct_values' AS metric,
       COUNT(DISTINCT CAST({right_q} AS VARCHAR(512))) AS metric_value
FROM {table_q}
WHERE {latest_filter}
""".strip(),
        ),
        (
            "left_values_with_multiple_right_values",
            f"""
SELECT 'left_values_with_multiple_right_values' AS metric,
       COUNT(*) AS metric_value
FROM (
  SELECT left_value
  FROM (
    SELECT DISTINCT
      CAST({left_q} AS VARCHAR(512)) AS left_value,
      CAST({right_q} AS VARCHAR(512)) AS right_value
    FROM {table_q}
    WHERE {latest_filter}
  ) unique_pairs
  GROUP BY left_value
  HAVING COUNT(*) > 1
) left_many
""".strip(),
        ),
        (
            "right_values_with_multiple_left_values",
            f"""
SELECT 'right_values_with_multiple_left_values' AS metric,
       COUNT(*) AS metric_value
FROM (
  SELECT right_value
  FROM (
    SELECT DISTINCT
      CAST({left_q} AS VARCHAR(512)) AS left_value,
      CAST({right_q} AS VARCHAR(512)) AS right_value
    FROM {table_q}
    WHERE {latest_filter}
  ) unique_pairs
  GROUP BY right_value
  HAVING COUNT(*) > 1
) right_many
""".strip(),
        ),
    ]


def relationship_summary_row(
    left: str, right: str, metric_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    expected = (
        "employee_count",
        "left_distinct_values",
        "right_distinct_values",
        "left_values_with_multiple_right_values",
        "right_values_with_multiple_left_values",
    )
    metrics = {
        str(row.get("metric")): row.get("metric_value")
        for row in metric_rows
        if row.get("metric") is not None
    }
    missing = [name for name in expected if name not in metrics]
    if missing:
        raise ValueError(
            f"Relationship summary is missing aggregate metrics: {', '.join(missing)}"
        )
    return {
        "row_type": "summary",
        "pair": f"{left} -> {right}",
        "left_value": None,
        "right_value": None,
        **{name: metrics[name] for name in expected},
    }


def build_single_pair_top_sql(variable: dict[str, Any], left: str, right: str, rules: dict[str, Any]) -> str:
    source = variable.get("source") or {}
    measurement = variable.get("measurement") or {}
    table = str(source.get("table") or "")
    date_column = profiler.quoted_identifier(measurement.get("date_column", "fis_mo_end_dt"), "date column")
    employee_column = profiler.quoted_identifier(measurement.get("employee_id_column", "employee_id"), "employee ID column")
    where, _ = profiler.population_clause(variable, rules)
    left_q = profiler.quoted_identifier(left, "left report column")
    right_q = profiler.quoted_identifier(right, "right report column")
    left_nonblank = profiler.nonblank_expression(left)
    right_nonblank = profiler.nonblank_expression(right)
    pair_name = f"{left} -> {right}"
    minimum = int(rules["population"]["minimum_shared_cohort"])
    return f"""
SELECT
  'top_mapping' AS row_type,
  {profiler.sql_literal(pair_name)} AS pair,
  CAST({left_q} AS VARCHAR(512)) AS left_value,
  CAST({right_q} AS VARCHAR(512)) AS right_value,
  COUNT(DISTINCT {employee_column}) AS employee_count,
  CAST(NULL AS BIGINT) AS left_distinct_values,
  CAST(NULL AS BIGINT) AS right_distinct_values,
  CAST(NULL AS BIGINT) AS left_values_with_multiple_right_values,
  CAST(NULL AS BIGINT) AS right_values_with_multiple_left_values
FROM {profiler.quoted_table(table)}
WHERE {where}
  AND {date_column} = (
    SELECT MAX({date_column})
    FROM {profiler.quoted_table(table)}
    WHERE {where}
      AND {date_column} IS NOT NULL
  )
  AND {left_nonblank}
  AND {right_nonblank}
GROUP BY 1, 2, 3, 4
HAVING COUNT(DISTINCT {employee_column}) >= {minimum}
ORDER BY employee_count DESC, left_value, right_value
LIMIT {SAFE_VALUE_FULL_N}
""".strip()

def split_relationship_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = []
    top_mappings = []
    for row in rows:
        if row.get("row_type") == "summary":
            summary.append(
                {
                    "pair": row.get("pair"),
                    "paired_employees": row.get("employee_count"),
                    "left_distinct_values": row.get("left_distinct_values"),
                    "right_distinct_values": row.get("right_distinct_values"),
                    "left_values_with_multiple_right_values": row.get("left_values_with_multiple_right_values"),
                    "right_values_with_multiple_left_values": row.get("right_values_with_multiple_left_values"),
                }
            )
        elif row.get("row_type") == "top_mapping":
            top_mappings.append(
                {
                    "pair": row.get("pair"),
                    "left_value": row.get("left_value"),
                    "right_value": row.get("right_value"),
                    "employee_count": row.get("employee_count"),
                }
            )
    return {"summary": summary, "top_mappings": top_mappings, "notes": []}


def run_report_query(
    detail: dict[str, Any], sql: str, max_rows: int, sql_reference: str
) -> list[dict[str, Any]] | None:
    transient_markers = (
        "transaction is read-only",
        "timeout",
        "timed out",
        "connection",
        "serialization",
        "server closed",
        "could not connect",
    )
    delays = (0, 2, 5)
    last_error: Exception | None = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            rows = profiler.run_aggregate_query(sql, max_rows=max_rows)
            evidence = detail.setdefault("evidence", {})
            evidence.setdefault("query_results", {})[sql_reference] = rows
            if attempt > 1:
                evidence.setdefault("retries", []).append(
                    {
                        "sql_reference": sql_reference,
                        "attempts": attempt,
                        "result": "succeeded",
                    }
                )
            return rows
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            transient = any(marker in message for marker in transient_markers)
            if not transient or attempt == len(delays):
                break

    evidence = detail.setdefault("evidence", {})
    evidence["status"] = "partial_failed"
    evidence.setdefault("errors", []).append(
        {"sql_reference": sql_reference, "error": str(last_error)}
    )
    detail.setdefault("column_relationships", {}).setdefault("notes", []).append(
        f"La consulta de reporte falló para {sql_reference}: {last_error}"
    )
    return None


def execute_story_queries(
    detail: dict[str, Any], variable: dict[str, Any]
) -> None:
    analysis = variable.get("analysis") or {}
    seen = {
        Path(reference).as_posix().lower()
        for reference in (detail.get("evidence") or {}).get("sql_references") or []
    }
    for item in analysis.get("validation_story") or []:
        reference = str(item.get("sql_reference") or "").strip()
        if not reference:
            continue
        normalized = Path(reference).as_posix().lower()
        if normalized in seen:
            continue
        sql_path = (PROJECT_ROOT / reference).resolve()
        allowed_roots = (
            (PROJECT_ROOT / "queries" / "audits").resolve(),
            (PROJECT_ROOT / "queries" / "profiles").resolve(),
        )
        if (
            not sql_path.is_file()
            or sql_path.suffix.lower() != ".sql"
            or not any(sql_path.is_relative_to(root) for root in allowed_roots)
        ):
            raise ValueError(
                f"{variable.get('variable')}: validation story SQL is invalid: {reference}"
            )
        sql = sql_path.read_text(encoding="utf-8")
        saved_reference = str(sql_path.relative_to(PROJECT_ROOT))
        rows = run_report_query(detail, sql, 500, saved_reference)
        detail.setdefault("evidence", {}).setdefault("sql_references", []).append(
            saved_reference
        )
        seen.add(normalized)
        if rows is not None and detail["evidence"].get("status") != "partial_failed":
            detail["evidence"]["status"] = "executed"

def build_report_detail(
    variable: dict[str, Any],
    assessment: dict[str, Any],
    rules: dict[str, Any],
    run_id: str,
    number: int,
    include_report_data: bool,
    execution_ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = variable.get("source") or {}
    profile_mode = str((variable.get("profile") or {}).get("mode", "standard")).lower()
    measurement = variable.get("measurement") or {}
    base_columns = report_columns(variable)
    ledger_queries = list((execution_ledger or {}).get("queries") or [])
    frozen_references = [
        str(item.get("query_reference"))
        for item in ledger_queries
        if item.get("query_reference")
    ]
    frozen_results = {
        str(item.get("query_reference")): copy.deepcopy(item.get("rows") or [])
        for item in ledger_queries
        if item.get("query_reference")
    }
    detail: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_discovery": {
            "source_type": source.get("type", "Database"),
            "source_table": source.get("table") or source.get("detail") or "No validada",
            "scoring_columns": source_column_list(source),
            "report_columns": [item["column"] for item in base_columns],
            "measurement_type": measurement.get("type", assessment.get("measurement_type")),
            "date_column": measurement.get("date_column"),
            "employee_id_column": measurement.get("employee_id_column"),
            "population": assessment.get("population_filter"),
            "semantic_type": (
                (variable.get("analysis") or {}).get("semantic_type")
                or (variable.get("verification") or {}).get("semantic_type")
            ),
        },
        "score_application": score_application(assessment, rules),
        "coverage_summary": coverage_summary(assessment, rules),
        "columns": [
            {
                **item,
                "data_type": "No perfilada",
                "value_display": "No se ejecutó el detalle agregado para esta fuente.",
                "exists_in_source": None,
            }
            for item in base_columns
        ],
        "value_distributions": [],
        "numeric_bands": [],
        "column_relationships": {"summary": [], "top_mappings": [], "notes": []},
        "evidence": {
            "sql_references": frozen_references,
            "query_results": frozen_results,
            "status": "frozen_execution" if ledger_queries else "not_applicable",
        },
        "privacy_note": (
            "Análisis interno agregado: las categorías protegidas pueden mostrar "
            "su etiqueta almacenada sólo cuando cada bucket cumple la cohorte "
            "mínima. No se muestran empleados, IDs, nombres, emails, compensación "
            "exacta ni texto libre."
            if REPORTING_MODE == "internal_analysis"
            else "Presentación agregada: no se muestran empleados, IDs, nombres, "
            "emails, categorías protegidas, compensación exacta, texto libre ni "
            "buckets con cohorte menor al mínimo compartido."
        ),
        "reporting_mode": REPORTING_MODE,
    }
    table = source.get("table")
    if not include_report_data:
        if not ledger_queries:
            detail["evidence"]["status"] = "skipped_offline_or_disabled"
        return detail
    execute_story_queries(detail, variable)
    if profile_mode != "standard" or not table or not base_columns:
        if not detail["evidence"].get("query_results"):
            detail["evidence"]["status"] = "skipped_non_standard_source"
        return detail

    prefix = query_prefix(run_id, number, str(variable.get("variable") or "variable"))
    requested_columns = [item["column"] for item in base_columns]
    metadata_sql = build_metadata_sql(str(table), requested_columns)
    metadata_ref = write_report_sql(REPORT_SQL_ROOT / f"{prefix}_report_metadata.sql", metadata_sql)
    metadata_rows = run_report_query(detail, metadata_sql, max(100, len(requested_columns) + 5), metadata_ref)
    if metadata_rows is None:
        return detail
    existing = {str(row.get("column_name")) for row in metadata_rows}
    existing_columns = [column for column in requested_columns if column in existing]
    detail["evidence"]["sql_references"].append(metadata_ref)
    if not existing_columns:
        detail["evidence"]["status"] = "no_report_columns_found"
        return detail

    profile_sql = build_column_profile_sql(variable, existing_columns, rules)
    profile_ref = write_report_sql(REPORT_SQL_ROOT / f"{prefix}_report_column_profile.sql", profile_sql)
    profile_rows = run_report_query(detail, profile_sql, max(100, len(existing_columns) + 5), profile_ref) or []
    detail["evidence"]["sql_references"].append(profile_ref)
    detail["columns"] = merge_column_profiles(base_columns, metadata_rows, profile_rows)

    safe_value_columns = [column for column in existing_columns if is_value_display_safe(column)[0]]
    top_rows: list[dict[str, Any]] = []
    for column in safe_value_columns:
        top_sql = build_single_top_values_sql(variable, column, rules)
        top_ref = write_report_sql(
            REPORT_SQL_ROOT / f"{prefix}_{renderer.slugify(column)}_report_top_values.sql",
            top_sql,
        )
        query_rows = run_report_query(detail, top_sql, SAFE_VALUE_FULL_N, top_ref)
        if query_rows is not None:
            top_rows.extend(query_rows)
        detail["evidence"]["sql_references"].append(top_ref)
    detail["value_distributions"] = attach_value_distributions(detail["columns"], top_rows)

    band_config = (variable.get("analysis") or {}).get("numeric_bands")
    if isinstance(band_config, dict):
        band_column = str(band_config.get("column") or "")
        if band_column in existing:
            band_sql = build_numeric_bands_sql(variable, band_config, rules)
            band_ref = write_report_sql(
                REPORT_SQL_ROOT
                / f"{prefix}_{renderer.slugify(band_column)}_report_numeric_bands.sql",
                band_sql,
            )
            band_rows = run_report_query(detail, band_sql, SAFE_VALUE_FULL_N, band_ref)
            if band_rows is not None:
                detail["numeric_bands"] = band_rows
            detail["evidence"]["sql_references"].append(band_ref)

    pairs = [pair for pair in comparison_pairs(variable, existing) if is_value_display_safe(pair[0])[0] and is_value_display_safe(pair[1])[0]]
    relationship_rows: list[dict[str, Any]] = []
    for left, right in pairs:
        pair_slug = f"{renderer.slugify(left)}_to_{renderer.slugify(right)}"
        summary_metric_rows: list[dict[str, Any]] = []
        summary_references: list[str] = []
        for metric, summary_sql in build_single_pair_summary_queries(
            variable, left, right, rules
        ):
            summary_ref = write_report_sql(
                REPORT_SQL_ROOT
                / f"{prefix}_{pair_slug}_report_relationship_{renderer.slugify(metric)}.sql",
                summary_sql,
            )
            metric_rows = run_report_query(detail, summary_sql, 2, summary_ref)
            if metric_rows is not None:
                summary_metric_rows.extend(metric_rows)
            summary_references.append(summary_ref)
            detail["evidence"]["sql_references"].append(summary_ref)
        if len(summary_metric_rows) == 5:
            try:
                relationship_rows.append(
                    relationship_summary_row(left, right, summary_metric_rows)
                )
            except ValueError as exc:
                evidence = detail.setdefault("evidence", {})
                evidence.setdefault("errors", []).append(
                    {
                        "sql_reference": ", ".join(summary_references),
                        "error": str(exc),
                    }
                )
                evidence["status"] = "partial_failed"
        top_sql = build_single_pair_top_sql(variable, left, right, rules)
        top_ref = write_report_sql(
            REPORT_SQL_ROOT / f"{prefix}_{pair_slug}_report_relationship_top.sql",
            top_sql,
        )
        top_relationship_rows = run_report_query(detail, top_sql, SAFE_VALUE_FULL_N, top_ref)
        if top_relationship_rows is not None:
            relationship_rows.extend(top_relationship_rows)
        detail["evidence"]["sql_references"].append(top_ref)
    if relationship_rows:
        detail["column_relationships"] = split_relationship_rows(relationship_rows)
    else:
        detail["column_relationships"]["notes"].append(
            "No se configuraron o encontraron pares de columnas comparables y publicables para esta variable."
        )
    missing = [column for column in requested_columns if column not in existing]
    if missing:
        detail["column_relationships"]["notes"].append(
            "Columnas no encontradas en information_schema: " + ", ".join(missing)
        )
    if detail["evidence"].get("status") != "partial_failed":
        detail["evidence"]["status"] = "executed"
    return detail


def report_query_purpose(reference: str) -> str:
    lowered = str(reference).lower()
    if "report_metadata" in lowered:
        return "report_metadata"
    if "report_column_profile" in lowered:
        return "report_column_profile"
    if "report_top_values" in lowered:
        return "report_safe_value_distribution"
    if "report_numeric_bands" in lowered:
        return "report_safe_numeric_bands"
    if "report_relationship" in lowered:
        return "report_relationship"
    return "report_contextual_validation"


def merge_report_queries_into_ledger(
    variable: dict[str, Any],
    report_detail: dict[str, Any],
    evidence_ledger: dict[str, Any],
) -> dict[str, Any]:
    ledger = evidence_ledger
    queries = ledger.setdefault("queries", [])
    existing = {
        Path(str(item.get("query_reference") or "")).as_posix().lower()
        for item in queries
        if item.get("query_reference")
    }
    query_results = (
        (report_detail.get("evidence") or {}).get("query_results") or {}
    )
    allowed_roots = (
        (PROJECT_ROOT / "queries" / "audits").resolve(),
        (PROJECT_ROOT / "queries" / "profiles").resolve(),
    )
    for reference, rows in query_results.items():
        normalized = Path(str(reference)).as_posix().lower()
        if normalized in existing:
            continue
        sql_path = (PROJECT_ROOT / str(reference)).resolve()
        if (
            not sql_path.is_file()
            or sql_path.suffix.lower() != ".sql"
            or not any(sql_path.is_relative_to(root) for root in allowed_roots)
        ):
            raise ValueError(
                f"{variable.get('variable')}: report evidence SQL is invalid: {reference}"
            )
        item = {
            "claim": (
                "Aportar evidencia agregada contextual y segura para explicar "
                f"el assessment de {variable.get('variable')}."
            ),
            "acceptance_rule": (
                "La consulta debe ejecutarse en modo read-only, devolver sólo "
                "resultados agregados permitidos y no puede elevar un score."
            ),
        }
        record = workflow.make_query_record(
            str(reference),
            sql_path.read_text(encoding="utf-8"),
            list(rows or []),
            report_query_purpose(str(reference)),
            variable,
            item,
            "executed_redshift_sql",
        )
        record["evidence_role"] = "contextual"
        record["score_eligible"] = False
        queries.append(record)
        existing.add(normalized)
    ledger["query_count"] = len(queries)
    return ledger

def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def rows_to_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], empty: str) -> str:
    if not rows:
        return f"<p class='muted'>{html_escape(empty)}</p>"
    header = "".join(f"<th>{html_escape(label)}</th>" for _, label in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html_escape(row.get(key))}</td>" for key, _ in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<div class='table-scroll'><table><tr>{header}</tr>{''.join(body)}</table></div>"


def score_class(score: Any) -> str:
    try:
        return {2: "score-good", 1: "score-warn", 0: "score-bad"}[int(score)]
    except Exception:
        return "score-unknown"


def write_notebook_legacy(path: Path, assessment: dict[str, Any]) -> None:
    report_detail = assessment.get("report_detail") or {}
    cells = [
        markdown_cell(
            f"# {assessment['variable']}\n\n"
            "Notebook ejecutado para assessment v4. La narrativa está en español; "
            "los nombres canónicos del scoring permanecen en inglés."
        ),
        markdown_cell(
            "## Definición y uso esperado\n\n"
            f"Categoría: {assessment.get('category') or 'Por definir'}\n\n"
            f"Definición: {assessment.get('definition_text') or 'Por definir'}\n\n"
            f"Población: {assessment.get('population_filter') or 'Por definir'}\n\n"
            f"Nivel/grain: {assessment.get('level_data') or 'TBD'}\n\n"
            f"Resultado: {assessment.get('result')} ({assessment.get('total')} puntos)."
        ),
        code_cell("Fuentes, derivaciones y alternativa seleccionada", "assessment_derivation", {
            "source_table": assessment.get("source_table"),
            "source_columns": assessment.get("source_columns"),
            "derivation": assessment.get("derivation") or {},
            "source_discovery": report_detail.get("source_discovery") or {},
        }, 1),
        code_cell("Perfil de columnas y relaciones", "assessment_columns", {
            "columns": report_detail.get("columns") or [],
            "value_distributions": report_detail.get("value_distributions") or [],
            "column_relationships": report_detail.get("column_relationships") or {},
        }, 2),
        code_cell("Coverage, Missingness e History", "assessment_coverage", {
            "coverage_summary": report_detail.get("coverage_summary") or {},
            "coverage": assessment.get("coverage") or [],
            "diagnostics": assessment.get("diagnostics") or {},
        }, 3),
        code_cell("Aplicación visible de reglas 2/1/0", "assessment_scores", {
            "score_application": report_detail.get("score_application") or [],
            "scores": assessment.get("scores") or {},
            "total": assessment.get("total"),
            "point_result": assessment.get("point_result"),
            "result": assessment.get("result"),
            "score_rationales": assessment.get("score_rationales") or [],
            "score_verification": assessment.get("score_verification") or {},
            "executable_validations": assessment.get("executable_validations") or [],
        }, 4),
        markdown_cell(
            "## Resultado, limitaciones y acciones recomendadas\n\n"
            f"Resultado final: {assessment.get('result')}\n\n"
            "Los scores 0/1 se explican en `score_application` y `score_rationales`; "
            "los scores 2 cualitativos estan respaldados en `score_verification`."
        ),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_planned_notebook(plan_path: Path, plan: dict[str, Any]) -> Path:
    """Create the reproducible notebook scaffold when Codex freezes a plan.

    It deliberately does not execute SQL. Execution remains the responsibility of
    the guarded runner; the notebook later reads frozen aggregate rows only.
    """
    notebook_path = plan_path.with_suffix(".ipynb")
    references = [
        str(item.get("sql_reference"))
        for item in plan.get("validation_story") or []
        if isinstance(item, dict) and item.get("sql_reference")
    ]
    cells = [
        markdown_cell(
            f"# Plan reproducible: {plan.get('variable') or 'Variable'}\n\n"
            "Este notebook se creó al congelar el plan, antes de ejecutar SQL. "
            "No decide scores ni ejecuta consultas por sí mismo; documenta las "
            "pruebas que el runner debe ejecutar y cuyos resultados agregados "
            "quedarán congelados para la conclusión."
        ),
        executable_code_cell(
            f"""
from pathlib import Path
import yaml
from IPython.display import Markdown, display

PLAN_PATH = Path.cwd() / {plan_path.name!r}
plan = yaml.safe_load(PLAN_PATH.read_text(encoding='utf-8'))
display(Markdown(
    f"**Variable:** {{plan.get('variable')}}  \\n"
    f"**Versión de plan:** {{plan.get('plan_version')}}  \\n"
    f"**Concepto:** {{plan.get('concept')}}  \\n"
    f"**Población:** {{plan.get('population')}}  \\n"
    f"**Grain:** {{plan.get('grain')}}  \\n"
    f"**Fecha de conocimiento:** {{plan.get('knowledge_date')}}"
))
"""
        ),
        markdown_cell("## Validaciones planeadas antes de la evidencia"),
        executable_code_cell(
            """
for story in plan.get('validation_story') or []:
    display(Markdown(
        f"### {story.get('id')}: {story.get('question')}\\n\\n"
        f"**Motivo:** {story.get('why')}\\n\\n"
        f"**Método:** {story.get('method')}\\n\\n"
        f"**Regla de aceptación:** {story.get('acceptance_rule')}\\n\\n"
        f"**SQL planeado:** `{story.get('sql_reference') or 'Por definir antes de ejecutar'}`"
    ))
"""
        ),
        markdown_cell(
            "## Regla de ejecución\n\n"
            "El siguiente paso es ejecutar únicamente SQL agregado, revisar los resultados "
            "y, si aparece una brecha material, congelar `analysis-plan-vN+1.yaml` antes "
            "de cerrar la variable."
        ),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "attrition_assessment": {
                "schema_version": 4,
                "stage": "pre_execution_plan",
                "variable": plan.get("variable"),
                "plan_version": plan.get("plan_version"),
                "planned_sql": references,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return notebook_path


def write_notebook(path: Path, assessment: dict[str, Any]) -> None:
    plan = assessment.get("analysis_plan") or {}
    semantic_type = str(plan.get("semantic_type") or "")
    variable_name = str(assessment.get("variable") or "Variable")
    cells: list[dict[str, Any]] = [
        markdown_cell(
            f"# {variable_name}\n\n"
            "Assessment v4 ejecutado con evidencia agregada. El notebook contiene "
            "el procedimiento, las reglas aplicadas y los resultados que originan el reporte."
        ),
        executable_code_cell(
            """
from pathlib import Path
import json
import sys
import yaml
import pandas as pd
from IPython import get_ipython
get_ipython().run_line_magic("matplotlib", "inline")
import matplotlib.pyplot as plt
from matplotlib_inline.backend_inline import set_matplotlib_formats
set_matplotlib_formats("png")
from IPython.display import Markdown, display

BASE = Path.cwd()
CHARTS_DIR = BASE / "charts"
CHARTS_DIR.mkdir(exist_ok=True)
CHART_MANIFEST_PATH = BASE / "charts-manifest.json"
_original_show = plt.show
_chart_counter = 0

def _save_and_show(*args, **kwargs):
    # Persist each notebook figure so the reader-facing HTML can reuse it.
    global _chart_counter
    manifest = []
    if CHART_MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(CHART_MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    for figure_number in plt.get_fignums():
        figure = plt.figure(figure_number)
        _chart_counter += 1
        filename = f"chart-{_chart_counter:02d}.png"
        destination = CHARTS_DIR / filename
        figure.savefig(destination, dpi=150, bbox_inches="tight")
        manifest.append({"file": f"charts/{filename}", "title": figure.axes[0].get_title() if figure.axes else "Gráfico agregado"})
    CHART_MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    result = _original_show(*args, **kwargs)
    plt.close("all")
    return result

plt.show = _save_and_show
assessment = json.loads((BASE / "assessment.json").read_text(encoding="utf-8"))
report = json.loads((BASE / "report_detail.json").read_text(encoding="utf-8"))
analysis_plan = yaml.safe_load((BASE / "analysis-plan.yaml").read_text(encoding="utf-8"))
query_results = (report.get("evidence") or {}).get("query_results") or {}

# Deterministic by default: the executed report uses captured aggregate evidence.
# Set this to True only when a fresh, approved Redshift refresh is required.
REFRESH_FROM_REDSHIFT = False

def load_or_refresh(sql_name):
    for reference, rows in query_results.items():
        if Path(reference).name == sql_name and not REFRESH_FROM_REDSHIFT:
            return rows
    if not REFRESH_FROM_REDSHIFT:
        raise KeyError(f"No cached evidence for {sql_name}")
    project_root = next(
        parent for parent in [BASE, *BASE.parents]
        if (parent / ".codex" / "skills" / "evaluate-attrition-variable").exists()
    )
    sys.path.insert(
        0,
        str(project_root / ".codex" / "skills" / "evaluate-attrition-variable" / "scripts"),
    )
    import profile_variable
    sql = (BASE / "queries" / sql_name).read_text(encoding="utf-8")
    return profile_variable.run_aggregate_query(sql)

print(
    f"Variable cargada: {assessment['variable']} | semantic_type={analysis_plan['semantic_type']} "
    f"| consultas agregadas congeladas={len(query_results)}"
)
"""
        ),
        markdown_cell("## Definición, uso y corte temporal"),
        executable_code_cell(
            """
display(Markdown(
    f"**Definición:** {assessment.get('definition_text') or 'Por definir'}\\n\\n"
    f"**Uso previsto:** {analysis_plan.get('intended_use') or analysis_plan.get('attrition_use')}\\n\\n"
    f"**Momento de conocimiento:** {analysis_plan.get('prediction_cutoff')}\\n\\n"
    f"**Población:** {analysis_plan.get('population')}\\n\\n"
    f"**Grain:** {analysis_plan.get('grain')}\\n\\n"
    f"**Tipo semántico:** {analysis_plan.get('semantic_type')}"
))
"""
        ),
        markdown_cell("## Contexto del problema y del portafolio"),
        executable_code_cell(
            """
context = analysis_plan.get("context_isolation") or {}
problem = context.get("problem_context") or {}
alignment = context.get("current_variable_alignment") or {}
display(Markdown(
    f"**Problema:** {problem.get('problem_statement') or 'Por confirmar.'}  \\n"
    f"**Decisión / caso de uso:** {problem.get('decision_or_use_case') or 'Por confirmar.'}  \\n"
    f"**Outcome:** {problem.get('outcome') or 'Por confirmar.'}  \\n"
    f"**Población global:** {problem.get('population') or analysis_plan.get('population')}  \\n"
    f"**Límite de conocimiento:** {problem.get('knowledge_boundary') or analysis_plan.get('prediction_cutoff')}  \\n"
    f"**Rol de esta variable:** {alignment.get('role') or 'candidate_variable'}  \\n"
    f"**Relevancia:** {alignment.get('relevance') or analysis_plan.get('intended_use')}"
))
relationships = pd.DataFrame(alignment.get("relationships") or [])
if not relationships.empty:
    display(Markdown("### Relaciones que orientan el análisis"))
    display(relationships[[column for column in ["type", "variables", "relationship", "why_relevant"] if column in relationships]])
knowledge = pd.DataFrame(context.get("accumulated_knowledge") or [])
if not knowledge.empty:
    display(Markdown("### Conocimiento acumulado de variables ya completadas"))
    columns = [
        column for column in [
            "variable", "relevance_to_current_variable", "result", "total",
            "key_findings", "limitations", "documentation"
        ] if column in knowledge
    ]
    display(knowledge[columns])
display(Markdown(
    "El contexto y la documentación acumulada orientan hipótesis; no se usan "
    "como evidencia para elevar scores de la variable actual."
))
"""
        ),
        markdown_cell("## Resumen visual"),
        executable_code_cell(
            """
score_rows = pd.DataFrame(report.get("score_application") or [])
if score_rows.empty:
    display(Markdown("No existen scores para visualizar."))
else:
    plot_scores = score_rows[["criterion", "score"]].copy()
    plot_scores["score"] = pd.to_numeric(plot_scores["score"], errors="coerce").fillna(0)
    colors = plot_scores["score"].map({2: "#13795b", 1: "#d59b1b", 0: "#b42318"}).fillna("#60717d")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(plot_scores["criterion"], plot_scores["score"], color=colors)
    ax.set_xlim(0, 2.05)
    ax.set_xticks([0, 1, 2])
    ax.set_xlabel("Score")
    ax.set_title("Readiness por criterio")
    ax.grid(axis="x", alpha=.2)
    plt.tight_layout()
    plt.show()
"""
        ),
        markdown_cell("## Resumen histórico y flujo del análisis"),
        executable_code_cell(
            """
history_story = analysis_plan.get("historical_story") or {}
display(Markdown(history_story.get("summary") or "No se generó un resumen histórico."))
for phase in history_story.get("phases") or []:
    display(Markdown(
        f"### {phase.get('stage')}\\n\\n{phase.get('narrative')}"
    ))
"""
        ),
        markdown_cell("## Plan de análisis específico"),
        executable_code_cell(
            """
display(Markdown(f"**Razonamiento de fuente:** {analysis_plan.get('source_reasoning')}"))
display(pd.DataFrame({"Foco de validación": analysis_plan.get("validation_focus") or []}))
display(pd.DataFrame({"Módulo técnico": analysis_plan.get("analysis_modules") or []}))
display(pd.DataFrame({"Visualización planeada": analysis_plan.get("planned_visualizations") or []}))
context = analysis_plan.get("context_isolation") or {}
display(Markdown(
    f"**Modo de integración contextual:** {context.get('mode')}  \\n"
    f"**Resultados previos usados como evidencia:** {'Sí' if context.get('prior_context_is_evidence') else 'No'}"
))
prior_context = pd.DataFrame(context.get("prior_context") or [])
if not prior_context.empty:
    display(Markdown("Contexto previo relevante, sujeto a revalidación:"))
    display(prior_context)
"""
        ),
        markdown_cell("## Descubrimiento de fuentes y columnas"),
        executable_code_cell(
            """
display(pd.DataFrame([report.get("source_discovery") or {}]).T.rename(columns={0: "valor"}))
columns = pd.DataFrame(report.get("columns") or [])
if columns.empty:
    display(Markdown("No hay columnas directas perfilables para esta fuente."))
else:
    completeness = columns.copy()
    for field in ["populated_employees", "missing_employees"]:
        if field not in completeness:
            completeness[field] = 0
        else:
            completeness[field] = pd.to_numeric(completeness[field], errors="coerce").fillna(0)
    completeness = completeness.head(15)
    fig, ax = plt.subplots(figsize=(9, max(2.8, len(completeness) * .38)))
    ax.barh(completeness["column"], completeness["populated_employees"], color="#13795b", label="Poblados")
    ax.barh(
        completeness["column"],
        completeness["missing_employees"],
        left=completeness["populated_employees"],
        color="#d9dee3",
        label="Faltantes",
    )
    ax.set_title("Completitud agregada de columnas")
    ax.set_xlabel("Empleados")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.show()
    display(Markdown("### Detalle tabular complementario"))
    display(columns)
"""
        ),
        markdown_cell("## SQL y evidencia agregada ejecutada"),
        executable_code_cell(
            """
query_files = sorted((BASE / "queries").glob("*.sql"))
if not query_files:
    display(Markdown("No existe SQL ejecutable porque la fuente esta bloqueada o no validada."))
else:
    display(pd.DataFrame([
        {"query": item.name, "bytes": item.stat().st_size}
        for item in query_files
    ]))
    for item in query_files:
        sql_text = item.read_text(encoding="utf-8")
        display(Markdown(f"### {item.name}\\n~~~sql\\n{sql_text}\\n~~~"))

if query_results:
    display(Markdown("### Resultados agregados congelados"))
    for reference, rows in query_results.items():
        display(Markdown(f"**{Path(reference).name}**"))
        display(pd.DataFrame(rows))
"""
        ),
        markdown_cell("## Coverage, Missingness e History"),
        executable_code_cell(
            """
coverage = pd.DataFrame(assessment.get("coverage") or [])
if coverage.empty:
    display(Markdown("No existe una fuente fechada validada; no se fabricaron observaciones."))
else:
    coverage["snapshot_date"] = pd.to_datetime(coverage["snapshot_date"])
    coverage = coverage.sort_values("snapshot_date")
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(
        coverage["snapshot_date"],
        coverage["observable_coverage_percent"],
        color="#13795b",
        linewidth=2,
    )
    ax.axhline(95, color="#b7791f", linestyle="--", linewidth=1, label="umbral score 2")
    ax.axhline(70, color="#b42318", linestyle=":", linewidth=1, label="umbral score 1")
    ax.set_ylim(0, 102)
    ax.set_ylabel("Coverage %")
    ax.set_title("Coverage a través del tiempo")
    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=.2)
    plt.tight_layout()
    plt.show()
    if "event_prevalence_percent" in coverage and coverage["event_prevalence_percent"].notna().any():
        fig, ax = plt.subplots(figsize=(10, 3.2))
        ax.plot(coverage["snapshot_date"], coverage["event_prevalence_percent"], color="#2563a6", linewidth=2)
        ax.set_ylabel("Prevalencia del evento %")
        ax.set_title("Prevalencia del evento entre empleados observables")
        ax.grid(axis="y", alpha=.2)
        plt.tight_layout()
        plt.show()
    if "fiscal_year" in coverage and coverage["fiscal_year"].notna().any():
        annual_source = coverage.dropna(subset=["fiscal_year"]).copy()
        annual_source["fiscal_year"] = annual_source["fiscal_year"].astype(str)
        has_event_counts = (
            "event_employees" in annual_source
            and annual_source["event_employees"].notna().any()
        )
        for column in ["eligible_employees", "observable_employees", "missing_employees", "event_employees"]:
            if column in annual_source:
                annual_source[column] = pd.to_numeric(annual_source[column], errors="coerce").fillna(0)
        annual = annual_source.groupby("fiscal_year", as_index=False).agg(
            first_snapshot_date=("snapshot_date", "min"),
            last_snapshot_date=("snapshot_date", "max"),
            snapshot_count=("snapshot_date", "count"),
            eligible_employee_snapshots=("eligible_employees", "sum"),
            observable_employee_snapshots=("observable_employees", "sum"),
            missing_employee_snapshots=("missing_employees", "sum"),
        )
        annual["observable_coverage_percent"] = (
            annual["observable_employee_snapshots"] * 100.0
            / annual["eligible_employee_snapshots"].replace(0, pd.NA)
        )
        annual["missingness_percent"] = (
            annual["missing_employee_snapshots"] * 100.0
            / annual["eligible_employee_snapshots"].replace(0, pd.NA)
        )
        if has_event_counts:
            annual_events = annual_source.groupby("fiscal_year")["event_employees"].sum()
            annual["event_employee_snapshots"] = annual["fiscal_year"].map(annual_events)
            annual["event_prevalence_percent"] = (
                annual["event_employee_snapshots"] * 100.0
                / annual["observable_employee_snapshots"].replace(0, pd.NA)
            )
        annual = annual.sort_values(["first_snapshot_date", "fiscal_year"])
        fig, ax = plt.subplots(figsize=(max(8, len(annual) * .8), 3.8))
        ax.bar(annual["fiscal_year"], annual["observable_coverage_percent"], color="#0f6b78")
        ax.axhline(95, color="#b7791f", linestyle="--", linewidth=1, label="umbral score 2")
        ax.axhline(70, color="#b42318", linestyle=":", linewidth=1, label="umbral score 1")
        ax.set_ylim(0, 102)
        ax.set_ylabel("Coverage ponderado %")
        ax.set_title("Coverage ponderado por fiscal_year")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="lower right")
        ax.grid(axis="y", alpha=.2)
        plt.tight_layout()
        plt.show()
        display(Markdown("### Resumen ponderado por fiscal_year"))
        display(annual.round(4))
    else:
        display(Markdown("No existe `fiscal_year` validado; no se infirió desde el año calendario."))
    display(Markdown("### Detalle tabular complementario"))
    display(coverage.tail(12))
"""
        ),
        markdown_cell("## Valores y distribuciones seguras"),
        executable_code_cell(
            """
safe_rows = []
for item in report.get("value_distributions") or []:
    if item.get("suppressed"):
        display(Markdown(f"**{item.get('column')}:** {item.get('reason')}"))
        continue
    for value in item.get("values") or []:
        safe_rows.append({"column": item.get("column"), **value})
values = pd.DataFrame(safe_rows)
if values.empty:
    display(Markdown("No hay categorias publicables o la politica de privacidad las suprime."))
else:
    for column, frame in values.groupby("column", sort=False):
        plot_data = frame.head(10).sort_values("employee_count")
        fig, ax = plt.subplots(figsize=(8, max(2.6, len(plot_data) * .32)))
        ax.barh(plot_data["value_label"].astype(str), plot_data["employee_count"], color="#2f6f8f")
        ax.set_title(f"Top valores seguros: {column}")
        ax.set_xlabel("Empleados")
        plt.tight_layout()
        plt.show()
    display(Markdown("### Detalle tabular complementario"))
    display(values)
"""
        ),
    ]

    if semantic_type in {"grouped_mapping", "hierarchy"}:
        cells.extend([
            markdown_cell("## Comparación entre columnas y mappings"),
            executable_code_cell(
                """
relationships = report.get("column_relationships") or {}
summary = pd.DataFrame(relationships.get("summary") or [])
mappings = pd.DataFrame(relationships.get("top_mappings") or [])
if summary.empty:
    display(Markdown("No se obtuvo una comparacion publicable."))
if not mappings.empty:
    plot_mappings = mappings.head(12).copy()
    plot_mappings["mapping"] = (
        plot_mappings["left_value"].astype(str)
        + " → "
        + plot_mappings["right_value"].astype(str)
    )
    plot_mappings = plot_mappings.sort_values("employee_count")
    fig, ax = plt.subplots(figsize=(9, max(3, len(plot_mappings) * .34)))
    ax.barh(plot_mappings["mapping"], plot_mappings["employee_count"], color="#0f766e")
    ax.set_title("Mappings agregados principales")
    ax.set_xlabel("Empleados")
    plt.tight_layout()
    plt.show()
if not summary.empty:
    display(Markdown("### Resumen tabular complementario"))
    display(summary)
if not mappings.empty:
    display(mappings)
for note in relationships.get("notes") or []:
    display(Markdown(f"- {note}"))
"""
            ),
        ])

    if semantic_type == "precomputed_metric":
        cells.extend([
            markdown_cell("## Fórmula, bandas y reconciliación"),
            executable_code_cell(
                """
bands = pd.DataFrame(report.get("numeric_bands") or [])
if bands.empty:
    display(Markdown("No hay bandas numericas validadas. Esto no confirma la formula del campo."))
else:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(bands["band_label"], bands["employee_count"], color="#6b5b3e")
    ax.set_ylabel("Empleados")
    ax.set_title("Distribución agregada por bandas seguras")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.show()
    display(Markdown("### Detalle tabular complementario"))
    display(bands)
display(Markdown(
    "**Regla:** una distribución plausible no sustituye el lineage ni la "
    "reconciliación independiente exigida para Definition 2."
))
"""
            ),
        ])

    if semantic_type in {"derived_feature", "survey", "external_source"}:
        cells.extend([
            markdown_cell("## Alternativas, derivación y condiciones pendientes"),
            executable_code_cell(
                """
derivation = analysis_plan.get("derivation") or {}
if derivation:
    display(pd.DataFrame([derivation]).T.rename(columns={0: "valor"}))
else:
    display(Markdown("No existe una derivación validada; revise el razonamiento de fuente."))
gaps = (analysis_plan.get("gap_review") or {}).get("unresolved") or []
if gaps:
    display(pd.DataFrame(gaps))
"""
            ),
        ])

    cells.extend([
        markdown_cell("## Historia de cada validación"),
        executable_code_cell(
            """
stories = analysis_plan.get("validation_story") or []
if not stories:
    display(Markdown("No se generaron historias de validación."))
for story in stories:
    fields = ", ".join(str(value) for value in story.get("fields") or [])
    sql_refs = ", ".join(str(value) for value in story.get("sql_references") or [])
    display(Markdown(
        f"### {story.get('order')}. {story.get('question')}\\n\\n"
        f"**Por qué lo validamos:** {story.get('why')}\\n\\n"
        f"**Rol de la evidencia:** `{story.get('evidence_role')}`  \\n"
        f"**Criterio afectado:** `{story.get('criterion')}`  \\n"
        f"**Campos:** `{fields}`  \\n"
        f"**Población y grain:** {story.get('population')} | {story.get('grain')}  \\n"
        f"**Límite temporal:** {story.get('temporal_boundary')}\\n\\n"
        f"**Cómo lo validamos:** {story.get('method')}\\n\\n"
        f"**Regla de aceptación:** {story.get('acceptance_rule')}\\n\\n"
        f"**Evidencia observada:** {story.get('observed_evidence')}\\n\\n"
        f"**Resultado:** **{story.get('outcome_label')}**\\n\\n"
        f"**Interpretación:** {story.get('interpretation')}\\n\\n"
        f"**Impacto en score:** {story.get('score_effect')}\\n\\n"
        f"**Limitación:** {story.get('limitation')}\\n\\n"
        f"**Acción recomendada:** {story.get('recommended_action')}\\n\\n"
        f"**SQL agregado:** `{sql_refs or 'No aplica'}`"
    ))
    metrics = story.get("observed_metrics") or {}
    if metrics:
        display(pd.DataFrame([
            {"Métrica": key, "Valor agregado": value}
            for key, value in metrics.items()
        ]))
    checks = story.get("metric_checks") or []
    if checks:
        display(pd.DataFrame(checks).rename(columns={
            "metric": "Métrica",
            "aggregate": "Agregación",
            "observed": "Observado",
            "operator": "Operador",
            "threshold": "Límite",
            "passed": "Cumple",
        }))
"""
        ),
        markdown_cell("## Aplicación visible de reglas 2/1/0"),
        executable_code_cell(
            """
scores = pd.DataFrame(report.get("score_application") or [])
score_view = scores[[
    "criterion", "score", "status_rule", "observed_evidence", "outcome_label",
    "why", "recommended_action", "scoring_method", "sql_reference"
]].rename(columns={
    "criterion": "Criterio",
    "score": "Score",
    "status_rule": "Regla aplicada",
    "observed_evidence": "Evidencia observada",
    "outcome_label": "Resultado",
    "why": "Conclusión",
    "recommended_action": "Acción recomendada",
    "scoring_method": "Método",
    "sql_reference": "SQL",
})
display(score_view)
"""
        ),
        markdown_cell("## Revisión de suficiencia y brechas"),
        executable_code_cell(
            """
review = analysis_plan.get("gap_review") or {}
display(Markdown(
    f"**Requiere seguimiento:** {review.get('requires_follow_up')}  \\n"
    f"**Regla de revisión:** {review.get('review_rule')}  \\n"
    f"**Estado de evidencia auxiliar:** {(report.get('evidence') or {}).get('status')}"
))
unresolved = pd.DataFrame(review.get("unresolved") or [])
if unresolved.empty:
    display(Markdown("No se detectaron brechas de score pendientes."))
else:
    display(unresolved)
"""
        ),
        markdown_cell("## Resultado, limitaciones y acciones recomendadas"),
        executable_code_cell(
            """
display(Markdown(
    f"**Resultado final:** {assessment.get('result')}  \\n"
    f"**Total:** {assessment.get('total')}  \\n"
    f"**Evidencia auxiliar:** {(report.get('evidence') or {}).get('status')}  \\n\\n"
    "Los scores 0/1 conservan la limitación y la acción concreta. "
    "Los scores 2 cualitativos requieren SQL guardado, regla previa y outcome pass."
))
"""
        ),
    ])
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "attrition_assessment": {
                "schema_version": 4,
                "semantic_type": semantic_type,
                "variable": variable_name,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def score_audit_table(report_detail: dict[str, Any]) -> str:
    rows = report_detail.get("score_application") or []
    table_rows = []
    for row in rows:
        score = row.get("score")
        table_rows.append(
            "<tr>"
            f"<td><b>{html_escape(row.get('criterion'))}</b></td>"
            f"<td><span class='score-pill {score_class(score)}'>{html_escape(score)}</span></td>"
            f"<td>{html_escape(row.get('status_rule'))}</td>"
            f"<td>{html_escape(row.get('observed_evidence'))}</td>"
            f"<td>{html_escape(row.get('outcome_label'))}</td>"
            f"<td>{html_escape(row.get('why'))}</td>"
            f"<td>{html_escape(row.get('recommended_action'))}</td>"
            "</tr>"
        )
    if not table_rows:
        table_rows.append("<tr><td colspan='7'>No se generó detalle de aplicación del score.</td></tr>")
    return (
        "<div class='table-scroll'><table><tr><th>Criterio</th><th>Score</th>"
        "<th>Regla / threshold</th><th>Evidencia observada</th><th>Resultado</th>"
        "<th>Conclusión</th><th>Acción recomendada</th></tr>"
        + "".join(table_rows)
        + "</table></div>"
    )


def score_overview_chart(report_detail: dict[str, Any]) -> str:
    rows = []
    for item in report_detail.get("score_application") or []:
        score = max(0, min(2, int(item.get("score") or 0)))
        width = 100.0 * score / 2
        rows.append(
            "<div class='metric-row'>"
            f"<span>{html_escape(item.get('criterion'))}</span>"
            f"<div class='metric-track'><i class='{score_class(score)}' style='width:{width:.2f}%'></i></div>"
            f"<b>{score}</b></div>"
        )
    return "".join(rows) or "<p class='muted'>No se generaron scores.</p>"


def column_completeness_chart(report_detail: dict[str, Any]) -> str:
    rows = []
    for item in (report_detail.get("columns") or [])[:15]:
        populated = int(item.get("populated_employees") or 0)
        missing = int(item.get("missing_employees") or 0)
        total = populated + missing
        percent = 100.0 * populated / total if total else 0
        rows.append(
            "<div class='metric-row'>"
            f"<span>{html_escape(item.get('column'))}</span>"
            f"<div class='metric-track'><i style='width:{percent:.2f}%'></i></div>"
            f"<b>{percent:.1f}%</b></div>"
        )
    return "".join(rows) or "<p class='muted'>No existe completitud agregada publicable.</p>"


def numeric_band_chart(report_detail: dict[str, Any]) -> str:
    bands = report_detail.get("numeric_bands") or []
    maximum = max([int(item.get("employee_count") or 0) for item in bands] or [1])
    rows = []
    for item in bands:
        count = int(item.get("employee_count") or 0)
        width = 100.0 * count / maximum if maximum else 0
        rows.append(
            "<div class='metric-row'>"
            f"<span>{html_escape(item.get('band_label'))}</span>"
            f"<div class='metric-track'><i style='width:{width:.2f}%'></i></div>"
            f"<b>{count}</b></div>"
        )
    return "".join(rows) or "<p class='muted'>No existen bandas numéricas publicables.</p>"


def relationship_chart(report_detail: dict[str, Any]) -> str:
    mappings = (report_detail.get("column_relationships") or {}).get("top_mappings") or []
    maximum = max([int(item.get("employee_count") or 0) for item in mappings] or [1])
    rows = []
    for item in mappings[:12]:
        count = int(item.get("employee_count") or 0)
        width = 100.0 * count / maximum if maximum else 0
        label = f"{item.get('left_value')} → {item.get('right_value')}"
        rows.append(
            "<div class='metric-row'>"
            f"<span>{html_escape(label)}</span>"
            f"<div class='metric-track'><i style='width:{width:.2f}%'></i></div>"
            f"<b>{count}</b></div>"
        )
    return "".join(rows) or "<p class='muted'>No existen mappings agregados publicables.</p>"


def shared_context_sections(assessment: dict[str, Any]) -> str:
    context = (assessment.get("analysis_plan") or {}).get("context_isolation") or {}
    problem = context.get("problem_context") or {}
    alignment = context.get("current_variable_alignment") or {}
    relationships = "".join(
        f"<li>{html_escape(item.get('relationship'))}</li>"
        for item in alignment.get("relationships") or []
    ) or "<li>No se documentaron relaciones adicionales.</li>"
    knowledge = "".join(
        "<li>"
        f"<b>{html_escape(item.get('variable'))}</b>: {html_escape(item.get('result'))}; "
        f"relevancia {html_escape(item.get('relevance_to_current_variable'))}."
        "</li>"
        for item in context.get("accumulated_knowledge") or []
    ) or "<li>No había variables previas completadas.</li>"
    return (
        f"<p><b>Problema:</b> {html_escape(problem.get('problem_statement'))}<br>"
        f"<b>Decisión / caso de uso:</b> {html_escape(problem.get('decision_or_use_case'))}<br>"
        f"<b>Outcome:</b> {html_escape(problem.get('outcome') or 'Por confirmar')}<br>"
        f"<b>Rol de la variable:</b> {html_escape(alignment.get('role') or 'candidate_variable')}<br>"
        f"<b>Relevancia:</b> {html_escape(alignment.get('relevance'))}</p>"
        f"<h3>Relaciones contextuales</h3><ul>{relationships}</ul>"
        f"<h3>Conocimiento acumulado</h3><ul>{knowledge}</ul>"
        "<p class='muted'>Este contexto orienta hipótesis; no sustituye evidencia de score.</p>"
    )


def coverage_chart(assessment: dict[str, Any]) -> str:
    rows = assessment.get("coverage") or []
    if not rows:
        return "<p class='muted'>No existen observaciones validadas de coverage.</p>"
    bars = []
    for row in rows[-36:]:
        pct = row.get("observable_coverage_percent")
        height = 0 if pct is None else max(1, min(100, float(pct)))
        bars.append(
            f"<span title='{html_escape(row.get('snapshot_date'))}: {html_escape(pct)}%' "
            f"style='height:{height:.2f}%'></span>"
        )
    return "<div class='coverage-chart'>" + "".join(bars) + "</div>"


def annual_coverage_chart(assessment: dict[str, Any]) -> str:
    rows = annual_coverage_by_fiscal_year(assessment)
    if not rows:
        return "<p class='muted'>No existe fiscal_year validado para construir el resumen anual.</p>"
    bars = []
    for row in rows:
        pct = row.get("observable_coverage_percent")
        width = 0 if pct is None else max(0, min(100, float(pct)))
        bars.append(
            "<div class='metric-row'>"
            f"<span>{html_escape(row.get('fiscal_year'))}</span>"
            f"<div class='metric-track'><i style='width:{width:.2f}%'></i></div>"
            f"<b>{'' if pct is None else f'{float(pct):.1f}%'}</b>"
            "</div>"
        )
    return "".join(bars)


def annual_coverage_detail_table(assessment: dict[str, Any]) -> str:
    return rows_to_table(
        annual_coverage_by_fiscal_year(assessment),
        [
            ("fiscal_year", "Fiscal year"),
            ("first_snapshot_date", "Primer snapshot"),
            ("last_snapshot_date", "Último snapshot"),
            ("snapshot_count", "Snapshots"),
            ("eligible_employee_snapshots", "Empleados-snapshot elegibles"),
            ("observable_employee_snapshots", "Empleados-snapshot observables"),
            ("missing_employee_snapshots", "Empleados-snapshot faltantes"),
            ("observable_coverage_percent", "Coverage ponderado %"),
            ("missingness_percent", "Missingness ponderado %"),
            ("event_prevalence_percent", "Prevalencia de evento %"),
        ],
        "No existe fiscal_year validado para construir el resumen anual.",
    )


def coverage_detail_table(assessment: dict[str, Any]) -> str:
    rows = []
    for row in assessment.get("coverage") or []:
        pct = row.get("observable_coverage_percent")
        width = 0 if pct is None else max(0, min(100, float(pct)))
        rows.append(
            "<tr>"
            f"<td>{html_escape(row.get('snapshot_date'))}</td>"
            f"<td>{html_escape(row.get('eligible_employees'))}</td>"
            f"<td>{html_escape(row.get('observable_employees'))}</td>"
            f"<td>{html_escape(row.get('missing_employees'))}</td>"
            f"<td>{'' if pct is None else f'{float(pct):.2f}%'}</td>"
            f"<td><div class='bar'><span style='width:{width:.2f}%'></span></div></td>"
            f"<td>{html_escape(row.get('coverage_score'))}</td>"
            f"<td>{html_escape(row.get('notes'))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='8'>No existen observaciones validadas de coverage.</td></tr>")
    return (
        "<div class='table-scroll'><table><tr><th>Fecha de snapshot</th><th>Elegibles</th>"
        "<th>Observables</th><th>Faltantes</th><th>Coverage</th><th>Grafico</th><th>Score de Coverage</th><th>Componentes y notas</th></tr>"
        + "".join(rows)
        + "</table></div>"
    )


def column_profile_table(report_detail: dict[str, Any]) -> str:
    return rows_to_table(
        report_detail.get("columns") or [],
        [
            ("column", "Columna"),
            ("role_label", "Rol"),
            ("description", "Representa"),
            ("data_type", "Tipo de dato"),
            ("populated_employees", "Empleados poblados"),
            ("missing_employees", "Empleados faltantes"),
            ("distinct_values", "Valores distintos"),
            ("first_populated_date", "Primera observación"),
            ("latest_populated_date", "Última observación"),
            ("value_display", "Publicación de valores"),
        ],
        "No se generó un perfil agregado de columnas.",
    )


def value_distribution_sections(report_detail: dict[str, Any]) -> str:
    sections = []
    for item in report_detail.get("value_distributions") or []:
        column = item.get("column")
        if item.get("suppressed"):
            sections.append(
                f"<h3>{html_escape(column)}</h3><p class='muted'>{html_escape(item.get('reason'))}</p>"
            )
            continue
        values = item.get("values") or []
        max_count = max([int(v.get("employee_count") or 0) for v in values] or [1])
        rows = []
        for value in values:
            count = int(value.get("employee_count") or 0)
            width = 100.0 * count / max_count if max_count else 0
            rows.append(
                "<tr>"
                f"<td>{html_escape(value.get('value_label'))}</td>"
                f"<td>{html_escape(count)}</td>"
                f"<td><div class='bar wide'><span style='width:{width:.2f}%'></span></div></td>"
                "</tr>"
            )
        if not rows:
            rows.append("<tr><td colspan='3'>No se devolvieron valores publicables.</td></tr>")
        label = "Todos los valores distintos publicables" if item.get("display_mode") == "all_safe_values" else "Valores publicables principales"
        sections.append(
            f"<h3>{html_escape(column)} <span class='muted'>({label})</span></h3>"
            "<div class='table-scroll'><table><tr><th>Valor</th><th>Empleados</th><th>Gráfico</th></tr>"
            + "".join(rows)
            + "</table></div>"
        )
    if not sections:
        return "<p class='muted'>No se generaron distribuciones de valores.</p>"
    return "".join(sections)


def relationship_sections(report_detail: dict[str, Any]) -> str:
    relationships = report_detail.get("column_relationships") or {}
    summary = rows_to_table(
        relationships.get("summary") or [],
        [
            ("pair", "Par"),
            ("paired_employees", "Empleados comparables"),
            ("left_distinct_values", "Distintos a la izquierda"),
            ("right_distinct_values", "Distintos a la derecha"),
            ("left_values_with_multiple_right_values", "Valores izquierdos con múltiples valores derechos"),
            ("right_values_with_multiple_left_values", "Valores derechos con múltiples valores izquierdos"),
        ],
        "No se generaron resúmenes de relación entre columnas.",
    )
    mapping = rows_to_table(
        relationships.get("top_mappings") or [],
        [
            ("pair", "Par"),
            ("left_value", "Valor izquierdo"),
            ("right_value", "Valor derecho"),
            ("employee_count", "Empleados"),
        ],
        "No se generaron mappings principales publicables.",
    )
    notes = "".join(
        f"<li>{html_escape(item)}</li>" for item in relationships.get("notes") or []
    )
    notes_html = f"<ul>{notes}</ul>" if notes else ""
    return summary + mapping + notes_html


def historical_story_sections(report_detail: dict[str, Any]) -> str:
    story = report_detail.get("historical_story") or {}
    phases = []
    for item in story.get("phases") or []:
        phases.append(
            f"<h3>{html_escape(item.get('stage'))}</h3>"
            f"<p>{html_escape(item.get('narrative'))}</p>"
        )
    return (
        f"<p>{html_escape(story.get('summary'))}</p>" + "".join(phases)
        if phases else "<p class='muted'>No se generó una historia temporal.</p>"
    )


def validation_story_sections(report_detail: dict[str, Any]) -> str:
    sections = []
    for item in report_detail.get("validation_story") or []:
        fields = ", ".join(str(value) for value in item.get("fields") or [])
        sql_refs = ", ".join(
            str(value) for value in item.get("sql_references") or []
        )
        metrics = rows_to_table(
            [
                {"metric": key, "value": value}
                for key, value in (item.get("observed_metrics") or {}).items()
            ],
            [("metric", "Métrica"), ("value", "Valor agregado")],
            "Sin métricas adicionales.",
        )
        sections.append(
            f"<article class='validation-story'><h3>{html_escape(item.get('order'))}. "
            f"{html_escape(item.get('question'))}</h3>"
            f"<p><b>Por qué lo validamos:</b> {html_escape(item.get('why'))}</p>"
            f"<p><b>Rol de la evidencia:</b> <code>{html_escape(item.get('evidence_role'))}</code><br>"
            f"<b>Criterio:</b> <code>{html_escape(item.get('criterion'))}</code><br>"
            f"<b>Campos:</b> <code>{html_escape(fields)}</code><br>"
            f"<b>Población y grain:</b> {html_escape(item.get('population'))} | {html_escape(item.get('grain'))}</p>"
            f"<p><b>Cómo lo validamos:</b> {html_escape(item.get('method'))}</p>"
            f"<p><b>Regla de aceptación:</b> {html_escape(item.get('acceptance_rule'))}</p>"
            f"<p><b>Evidencia observada:</b> {html_escape(item.get('observed_evidence'))}</p>"
            f"<p><b>Resultado:</b> {html_escape(item.get('outcome_label'))}</p>"
            f"<p><b>Interpretación:</b> {html_escape(item.get('interpretation'))}</p>"
            f"<p><b>Impacto en score:</b> {html_escape(item.get('score_effect'))}</p>"
            f"<p><b>Limitación:</b> {html_escape(item.get('limitation'))}</p>"
            f"<p><b>Acción recomendada:</b> {html_escape(item.get('recommended_action'))}</p>"
            f"<p><b>SQL agregado:</b> <code>{html_escape(sql_refs or 'No aplica')}</code></p>"
            f"{metrics}</article>"
        )
    return "".join(sections) or "<p class='muted'>No se generaron historias de validación.</p>"


def write_html(path: Path, assessment: dict[str, Any]) -> None:
    report_detail = assessment.get("report_detail") or {}
    diagnostics = assessment.get("diagnostics") or {}
    coverage_summary = report_detail.get("coverage_summary") or {}
    content = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{html_escape(assessment.get('variable'))}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #17212b; line-height: 1.35; }}
h1 {{ margin-bottom: 4px; }}
h2 {{ margin-top: 32px; border-bottom: 2px solid #d7dee4; padding-bottom: 6px; }}
h3 {{ margin-top: 22px; }}
section {{ margin-top: 24px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin: 18px 0; }}
.kpi {{ border: 1px solid #c8d0d8; border-radius: 6px; padding: 10px; background: #f8fafb; }}
.kpi b {{ display: block; font-size: 20px; margin-top: 4px; }}
.table-scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
th, td {{ border: 1px solid #c8d0d8; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #183642; color: white; }}
pre {{ background: #f4f6f8; border: 1px solid #d7dee4; padding: 12px; overflow-x: auto; }}
code {{ background: #edf1f4; padding: 2px 4px; }}
.muted {{ color: #60717d; font-size: 12px; }}
.score-pill {{ display: inline-block; min-width: 24px; text-align: center; border-radius: 999px; padding: 2px 8px; font-weight: bold; }}
.score-good {{ background: #dceee6; color: #175b39; }}
.score-warn {{ background: #fff0c7; color: #755300; }}
.score-bad {{ background: #f8d7da; color: #7a1f29; }}
.score-unknown {{ background: #e7ebef; color: #3e4d57; }}
.bar {{ width: 160px; height: 12px; background: #edf1f4; }}
.bar.wide {{ width: 260px; }}
.bar span {{ display: block; height: 12px; background: #0f6b78; }}
.coverage-chart {{ height: 120px; display: flex; align-items: end; gap: 3px; padding: 10px; background: #f4f6f8; border: 1px solid #d7dee4; }}
.coverage-chart span {{ flex: 1; min-width: 4px; background: #0f6b78; }}
.visual-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
.visual-card {{ border: 1px solid #d7dee4; border-radius: 8px; padding: 14px; background: #f8fafb; }}
.visual-card h3 {{ margin-top: 0; }}
.metric-row {{ display: grid; grid-template-columns: minmax(120px, 1fr) 2fr 52px; align-items: center; gap: 8px; margin: 8px 0; }}
.metric-track {{ height: 14px; background: #e5e9ed; border-radius: 8px; overflow: hidden; }}
.metric-track i {{ display: block; height: 100%; background: #0f6b78; }}
.metric-track i.score-good {{ background: #13795b; }}
.metric-track i.score-warn {{ background: #d59b1b; }}
.metric-track i.score-bad {{ background: #b42318; }}
.validation-story {{ border-left: 4px solid #0f6b78; padding-left: 16px; margin: 24px 0; }}
</style>
</head>
<body>
<h1>{html_escape(assessment.get('variable'))}</h1>
<p>Evaluación v4 ejecutada. Resultado: <b>{html_escape(assessment.get('result'))}</b>.</p>
<div class="kpis">
  <div class="kpi">Score total<b>{html_escape(assessment.get('total'))}</b></div>
  <div class="kpi">Definition<b>{html_escape((assessment.get('scores') or {}).get('definition'))}</b></div>
  <div class="kpi">Coverage reciente<b>{html_escape(diagnostics.get('recent_coverage_percent'))}%</b></div>
  <div class="kpi">Meses de History<b>{html_escape(diagnostics.get('history_months'))}</b></div>
</div>
<section><h2>Definición y uso esperado</h2>
<p>{html_escape(assessment.get('definition_text') or 'Por definir')}</p>
<p><b>Población:</b> {html_escape(assessment.get('population_filter') or 'Por definir')}<br>
<b>Grain:</b> {html_escape(assessment.get('level_data') or 'TBD')}<br>
<b>Tabla fuente:</b> <code>{html_escape(assessment.get('source_table'))}</code><br>
<b>Columnas scoring:</b> <code>{html_escape(assessment.get('source_columns'))}</code></p></section>
<section><h2>Contexto del problema y del portafolio</h2>{shared_context_sections(assessment)}</section>
<section><h2>Resumen visual</h2><div class="visual-grid">
<div class="visual-card"><h3>Readiness por criterio</h3>{score_overview_chart(report_detail)}</div>
<div class="visual-card"><h3>Coverage histórico</h3>{coverage_chart(assessment)}</div>
<div class="visual-card"><h3>Coverage ponderado por fiscal_year</h3>{annual_coverage_chart(assessment)}</div>
<div class="visual-card"><h3>Completitud de columnas</h3>{column_completeness_chart(report_detail)}</div>
<div class="visual-card"><h3>Bandas numéricas seguras</h3>{numeric_band_chart(report_detail)}</div>
<div class="visual-card"><h3>Relaciones principales</h3>{relationship_chart(report_detail)}</div>
</div></section>
<section><h2>Resumen histórico y flujo del análisis</h2>{historical_story_sections(report_detail)}</section>
<section><h2>Historia de cada validación</h2>{validation_story_sections(report_detail)}</section>
<section><h2>Aplicación visible de reglas 2/1/0 — detalle tabular</h2>{score_audit_table(report_detail)}</section>
<section><h2>Coverage, Missingness e History — detalle tabular</h2>
<p>{html_escape(coverage_summary.get('explanation'))}</p>
<h3>Resumen ponderado por fiscal_year</h3>
{annual_coverage_detail_table(assessment)}
<h3>Detalle mensual</h3>
{coverage_detail_table(assessment)}</section>
<section><h2>Columnas involucradas — detalle tabular</h2>{column_profile_table(report_detail)}</section>
<section><h2>Valores y distribuciones seguras</h2>{value_distribution_sections(report_detail)}</section>
<section><h2>Comparación entre columnas — detalle tabular</h2>{relationship_sections(report_detail)}</section>
<section><h2>Derivaciones y validaciones</h2>
<pre>{html_escape(json.dumps({
    'derivation': assessment.get('derivation') or {},
    'score_verification': assessment.get('score_verification') or {},
    'executable_validations': assessment.get('executable_validations') or [],
    'report_evidence': report_detail.get('evidence') or {},
}, ensure_ascii=False, indent=2, default=str))}</pre></section>
<section><h2>Privacidad</h2><p>{html_escape(report_detail.get('privacy_note'))}</p></section>
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def copy_variable_queries(assessment: dict[str, Any], queries_dir: Path) -> list[str]:
    queries_dir.mkdir(parents=True, exist_ok=False)
    copied: list[str] = []
    used: set[str] = set()
    for reference in evidence_references(assessment):
        source = (PROJECT_ROOT / reference).resolve()
        if not source.is_file():
            raise ValueError(f"Evidence SQL not found: {reference}")
        name = source.name
        if name in used:
            name = f"{source.stem}-{len(used) + 1}{source.suffix}"
        used.add(name)
        destination = queries_dir / name
        shutil.copy2(source, destination)
        copied.append(name)
    return copied


def write_variable_outputs(
    profile: dict[str, Any],
    variables_dir: Path,
    start_number: int = 1,
    used_slugs: set[str] | None = None,
) -> list[dict[str, Any]]:
    variables_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, Any]] = []
    used = used_slugs if used_slugs is not None else set()
    for number, assessment in enumerate(
        profile["assessments"], start=start_number
    ):
        variable_name = str(assessment.get("variable") or "variable")
        slug = unique_slug(variable_name, used)
        numbered_slug = f"{number:02d}-{slug}"
        variable_dir = variables_dir / numbered_slug
        variable_dir.mkdir(parents=True, exist_ok=False)

        ipynb = variable_dir / f"{slug}.ipynb"
        html_path = variable_dir / f"{slug}.html"
        assessment_json = variable_dir / "assessment.json"
        coverage_json = variable_dir / "coverage.json"
        rationales_json = variable_dir / "score_rationales.json"
        report_detail_json = variable_dir / "report_detail.json"
        analysis_plan_yaml = variable_dir / "analysis-plan.yaml"
        primary_pre_plan = (
            assessment.get("pre_execution_plan")
            or assessment.get("analysis_plan")
            or {}
        )
        pre_execution_plan_yaml = variable_dir / (
            f"analysis-plan-v{primary_pre_plan.get('plan_version', 1)}.yaml"
        )
        evidence_ledger_json = variable_dir / "evidence-ledger.json"
        decision_json = variable_dir / "decision.json"
        variable_spec_yaml = variable_dir / "variable-spec.yaml"
        checkpoint_json = variable_dir / "checkpoint.json"
        evidence_dir = variable_dir / "evidence"
        queries_dir = variable_dir / "queries"
        query_results_json = evidence_dir / "query-results.json"
        charts_dir = variable_dir / "charts"
        charts_manifest_json = variable_dir / "charts-manifest.json"

        evidence_dir.mkdir(parents=True, exist_ok=False)
        copied_queries = copy_variable_queries(assessment, queries_dir)
        assessment_json.write_text(
            json.dumps(assessment, ensure_ascii=True, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        coverage_json.write_text(
            json.dumps(assessment.get("coverage") or [], ensure_ascii=True, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        rationales_json.write_text(
            json.dumps(assessment.get("score_rationales") or [], ensure_ascii=True, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        report_detail_json.write_text(
            json.dumps(assessment.get("report_detail") or {}, ensure_ascii=True, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        analysis_plan_yaml.write_text(
            yaml.safe_dump(
                assessment.get("analysis_plan") or {},
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        pre_execution_plan = primary_pre_plan
        pre_execution_plan_paths: list[str] = []
        for plan in assessment.get("pre_execution_plans") or [pre_execution_plan]:
            plan_path = variable_dir / f"analysis-plan-v{plan.get('plan_version', 1)}.yaml"
            plan_path.write_text(
                yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            pre_execution_plan_paths.append(
                str(plan_path.relative_to(PROJECT_ROOT))
            )
        pre_execution_plan_yaml.write_text(
            yaml.safe_dump(
                pre_execution_plan,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        evidence_ledger_json.write_text(
            json.dumps(
                assessment.get("evidence_ledger") or {},
                ensure_ascii=True,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        decision = assessment.get("decision") or workflow.decision_document(assessment)
        decision_json.write_text(
            json.dumps(decision, ensure_ascii=True, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        variable_spec_yaml.write_text(
            yaml.safe_dump(
                {"version": 4, "variables": [assessment.get("variable_spec") or {}]},
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        query_results = (
            ((assessment.get("report_detail") or {}).get("evidence") or {}).get(
                "query_results"
            )
            or {}
        )
        query_results_json.write_text(
            json.dumps(
                query_results,
                ensure_ascii=True,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        write_notebook(ipynb, assessment)
        execute_notebook_to_html(ipynb, html_path)
        chart_entries = []
        if charts_manifest_json.is_file():
            chart_entries = profiler.load_json(charts_manifest_json)
            if not isinstance(chart_entries, list):
                raise ValueError(f"{variable_name}: charts-manifest.json must be a list.")
        for entry in chart_entries:
            if not isinstance(entry, dict) or not entry.get("file"):
                raise ValueError(f"{variable_name}: invalid chart manifest entry.")
            chart_path = variable_dir / str(entry["file"])
            if not chart_path.is_file() or not chart_path.is_relative_to(charts_dir):
                raise ValueError(f"{variable_name}: chart artifact is missing or outside charts/: {chart_path}")
        checkpoint = {
            "schema_version": 1,
            "number": number,
            "variable": variable_name,
            "status": "complete",
            "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "semantic_type": (assessment.get("analysis_plan") or {}).get(
                "semantic_type"
            ),
            "pre_execution_plan_sha256": workflow.canonical_json_hash(
                pre_execution_plan
            ),
            "evidence_ledger_sha256": workflow.canonical_json_hash(
                assessment.get("evidence_ledger") or {}
            ),
            "context_mode": (
                (assessment.get("analysis_plan") or {}).get("context_isolation")
                or {}
            ).get("mode"),
            "result": assessment.get("result"),
            "total": assessment.get("total"),
            "evidence_status": (
                (assessment.get("report_detail") or {}).get("evidence") or {}
            ).get("status"),
            "queries": copied_queries,
            "notebook_executed": True,
            "html_exported_from_notebook": True,
            "charts_generated": len(chart_entries),
        }
        checkpoint_json.write_text(
            json.dumps(checkpoint, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        artifacts.append(
            {
                "number": number,
                "variable": variable_name,
                "folder": str(variable_dir.relative_to(PROJECT_ROOT)),
                "assessment_json": str(assessment_json.relative_to(PROJECT_ROOT)),
                "coverage_json": str(coverage_json.relative_to(PROJECT_ROOT)),
                "score_rationales_json": str(rationales_json.relative_to(PROJECT_ROOT)),
                "report_detail_json": str(report_detail_json.relative_to(PROJECT_ROOT)),
                "analysis_plan": str(analysis_plan_yaml.relative_to(PROJECT_ROOT)),
                "pre_execution_plan": str(pre_execution_plan_yaml.relative_to(PROJECT_ROOT)),
                "pre_execution_plans": pre_execution_plan_paths,
                "evidence_ledger": str(evidence_ledger_json.relative_to(PROJECT_ROOT)),
                "decision": str(decision_json.relative_to(PROJECT_ROOT)),
                "variable_spec": str(variable_spec_yaml.relative_to(PROJECT_ROOT)),
                "checkpoint": str(checkpoint_json.relative_to(PROJECT_ROOT)),
                "query_results": str(query_results_json.relative_to(PROJECT_ROOT)),
                "charts": str(charts_dir.relative_to(PROJECT_ROOT)),
                "charts_manifest": str(charts_manifest_json.relative_to(PROJECT_ROOT)),
                "notebook": str(ipynb.relative_to(PROJECT_ROOT)),
                "html": str(html_path.relative_to(PROJECT_ROOT)),
            }
        )
    return artifacts


def attach_documentation_update(
    assessment: dict[str, Any],
    artifact: dict[str, Any],
    documentation_root: Path,
    run_id: str,
) -> dict[str, Any]:
    variable_spec = assessment.get("variable_spec") or {
        "variable": assessment.get("variable"),
        "analysis": assessment.get("analysis") or {},
    }
    documentation = update_variable_documentation(
        variable_spec,
        assessment,
        documentation_root,
        run_id,
    )
    assessment["documentation"] = documentation
    artifact["documentation"] = documentation["path"]

    assessment_path = PROJECT_ROOT / str(artifact["assessment_json"])
    assessment_path.write_text(
        json.dumps(assessment, ensure_ascii=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    checkpoint_path = PROJECT_ROOT / str(artifact["checkpoint"])
    checkpoint = profiler.load_json(checkpoint_path)
    checkpoint["documentation_updated"] = True
    checkpoint["documentation_path"] = documentation["path"]
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return documentation


def build_profile(
    spec_path: Path,
    rules_path: Path,
    aggregate_results: Path | None,
    run_id: str,
    include_report_data: bool,
    on_assessment: Callable[[int, int, dict[str, Any]], None] | None = None,
    on_plan: Callable[[int, int, dict[str, Any]], None] | None = None,
    prepared_portfolio: dict[str, Any] | None = None,
    documentation_root: Path | None = None,
) -> dict[str, Any]:
    prepared = prepared_portfolio or prepare_portfolio(
        spec_path,
        rules_path,
        run_id,
        execute_metadata=False,
        persist_metadata_sql=False,
    )
    rules = prepared["rules"]
    variables = [copy.deepcopy(variable) for variable in prepared["variables"]]
    catalog_path = prepared.get("catalog_path")
    source_spec_path = Path(prepared.get("source_spec_path") or spec_path)
    portfolio_context = prepared["portfolio_context"]
    offline_data = profiler.load_json(aggregate_results) if aggregate_results else None
    variables_by_name = {
        str(variable.get("variable")): variable for variable in variables
    }
    original_position = {
        name: index for index, name in enumerate(portfolio_context["original_order"], start=1)
    }
    portfolio_entries = {
        str(item.get("variable")): item
        for item in portfolio_context.get("variables") or []
    }
    assessments_in_evaluation_order: list[dict[str, Any]] = []
    completed: dict[str, dict[str, Any]] = {}
    evidence_cache: dict[str, dict[str, Any]] = {}
    evaluation_order = list(portfolio_context["evaluation_order"])
    dependencies = portfolio_context.get("dependencies") or {}
    for number, variable_name in enumerate(evaluation_order, start=1):
        variable = copy.deepcopy(variables_by_name[variable_name])
        portfolio_entry = portfolio_entries[variable_name]
        documentation_context = documentation_context_for_variable(
            variable, documentation_root
        )
        accumulated_knowledge = accumulated_knowledge_for_variable(
            variable,
            assessments_in_evaluation_order,
            portfolio_entry,
        )
        conditions, dependency_caps = inherited_dependency_conditions(
            variable, dependencies, completed
        )
        variable["dependency_caps"] = dependency_caps
        pre_execution_plan = workflow.build_pre_execution_plan(
            variable,
            portfolio_entry,
            version=1,
            inherited_conditions=conditions,
            shared_context=portfolio_context,
            documentation_context=documentation_context,
            accumulated_knowledge=accumulated_knowledge,
        )
        if on_plan:
            on_plan(number, len(variables), pre_execution_plan)
        pre_execution_plans = [copy.deepcopy(pre_execution_plan)]
        variable.setdefault("analysis", {})["validation_story"] = copy.deepcopy(
            pre_execution_plan["validation_story"]
        )
        frozen_variable, coverage_rows, population_display, evidence_ledger = (
            collect_variable_evidence(
                variable,
                rules,
                source_spec_path,
                run_id,
                number,
                offline_data,
                evidence_cache,
            )
        )
        # A detected anomaly is a signal for Codex to review the evidence, not
        # permission for the engine to invent a new material validation. The
        # automatic path remains opt-in only for migrating historical runs.
        adaptive_stories = (
            triggered_adaptive_stories(variable, evidence_ledger)
            if (variable.get("analysis") or {}).get("allow_automatic_adaptive_stories")
            else []
        )
        if adaptive_stories:
            variable["analysis"]["validation_story"].extend(adaptive_stories)
            variable["analysis"].setdefault("validation_focus", []).extend(
                [story.get("question") for story in adaptive_stories]
            )
            variable["analysis"]["plan_version"] = int(
                pre_execution_plan.get("plan_version") or 1
            ) + 1
            variable["analysis"]["plan_revision_reason"] = (
                "Compatibilidad histórica: una regla preconfigurada detectó una "
                "anomalía. En un run guiado, Codex debe crear esta revisión explícitamente."
            )
            pre_execution_plan = workflow.build_pre_execution_plan(
                variable,
                portfolio_entry,
                version=int(variable["analysis"]["plan_version"]),
                inherited_conditions=conditions,
                shared_context=portfolio_context,
                documentation_context=documentation_context,
                accumulated_knowledge=accumulated_knowledge,
            )
            pre_execution_plans.append(copy.deepcopy(pre_execution_plan))
            if on_plan:
                on_plan(number, len(variables), pre_execution_plan)
            frozen_variable, coverage_rows, population_display, evidence_ledger = (
                collect_variable_evidence(
                    variable,
                    rules,
                    source_spec_path,
                    run_id,
                    number,
                    offline_data,
                    evidence_cache,
                )
            )
        frozen_variable.setdefault("population", {})["display"] = population_display
        assessment = profiler.profile_one(
            frozen_variable,
            rules,
            source_spec_path,
            offline_data={variable_name: coverage_rows},
        )
        if assessment is None:
            continue
        assessment["original_index"] = original_position[variable_name]
        assessment["evaluation_index"] = number
        assessment["run_id"] = run_id
        assessment["inherited_conditions"] = conditions
        assessment["reused_evidence"] = [
            {
                "query_reference": item.get("query_reference"),
                "reused_from": item.get("reused_from"),
                "evidence_identity": item.get("evidence_identity"),
            }
            for item in evidence_ledger.get("queries") or []
            if item.get("reused_from")
        ]
        assessment["analysis"] = copy.deepcopy(frozen_variable.get("analysis") or {})
        assessment["variable_spec"] = copy.deepcopy(frozen_variable)
        assessment["pre_execution_plan"] = pre_execution_plan
        assessment["pre_execution_plans"] = pre_execution_plans
        assessment["evidence_ledger"] = evidence_ledger
        assessment["report_detail"] = build_report_detail(
            frozen_variable,
            assessment,
            rules,
            run_id,
            number,
            include_report_data=include_report_data and offline_data is None,
            execution_ledger=evidence_ledger,
        )
        assessment["evidence_ledger"] = merge_report_queries_into_ledger(
            frozen_variable,
            assessment["report_detail"],
            evidence_ledger,
        )
        assessment["analysis_plan"] = build_analysis_plan(
            frozen_variable,
            assessment,
            rules,
            prior_assessments=assessments_in_evaluation_order,
            report_detail=assessment["report_detail"],
            portfolio_context=portfolio_context,
            documentation_context=documentation_context,
            accumulated_knowledge=accumulated_knowledge,
        )
        assessment["analysis_plan"]["pre_execution_plan_sha256"] = (
            workflow.canonical_json_hash(pre_execution_plan)
        )
        assessment["report_detail"]["analysis_plan"] = copy.deepcopy(
            assessment["analysis_plan"]
        )
        assessment["report_detail"]["historical_story"] = copy.deepcopy(
            assessment["analysis_plan"].get("historical_story") or {}
        )
        assessment["report_detail"]["validation_story"] = copy.deepcopy(
            assessment["analysis_plan"].get("validation_story") or []
        )
        assessment["decision"] = workflow.decision_document(assessment)
        assessments_in_evaluation_order.append(assessment)
        completed[variable_name] = assessment
        if on_assessment:
            on_assessment(number, len(variables), assessment)
    assessments = sorted(
        assessments_in_evaluation_order,
        key=lambda item: int(item.get("original_index") or 0),
    )
    return {
        "schema_version": 4,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rules_file": str(rules_path),
        "spec_file": str(spec_path),
        "analysis_catalog": str(catalog_path) if catalog_path else None,
        "run_request": prepared.get("run_request"),
        "portfolio_context": portfolio_context,
        "problem_context": portfolio_context.get("problem_context") or {},
        "portfolio_overview": portfolio_context.get("portfolio_overview") or {},
        "contextual_relationships": portfolio_context.get("contextual_relationships") or [],
        "original_order": portfolio_context.get("original_order") or [],
        "evaluation_order": evaluation_order,
        "dependencies": dependencies,
        "cycles": portfolio_context.get("cycles") or [],
        "population_default": rules["population"]["display"],
        "minimum_shared_cohort": rules["population"]["minimum_shared_cohort"],
        "assessments": assessments,
    }


def rebase_artifact_paths(
    value: Any, physical_root: Path, published_root: Path
) -> Any:
    physical = str(physical_root.relative_to(PROJECT_ROOT))
    published = str(published_root.relative_to(PROJECT_ROOT))
    if isinstance(value, str) and (
        value == physical
        or value.startswith(physical + "\\")
        or value.startswith(physical + "/")
    ):
        return published + value[len(physical) :]
    if isinstance(value, list):
        return [
            rebase_artifact_paths(item, physical_root, published_root)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: rebase_artifact_paths(item, physical_root, published_root)
            for key, item in value.items()
        }
    return value


def rebase_artifact_json_file(
    path: Path, physical_root: Path, published_root: Path
) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Expected artifact manifest is missing: {path}")
    payload = profiler.load_json(path)
    rebased = rebase_artifact_paths(payload, physical_root, published_root)
    if isinstance(rebased, dict) and rebased.get("run_id") == physical_root.name:
        rebased["run_id"] = published_root.name
    profiler.write_json(path, rebased)


def visual_html_v2_configuration(project_settings: dict[str, Any]) -> dict[str, Any]:
    reporting = dict(project_settings.get("reporting") or {})
    configuration = dict(reporting.get("visual_html_v2") or {})
    if not configuration or not configuration.get("enabled", False):
        return {}
    renderer_config = configuration.get("renderer")
    if isinstance(renderer_config, str):
        renderer_config = {"script": renderer_config}
    if not isinstance(renderer_config, dict) or not renderer_config.get("script"):
        raise ValueError(
            "reporting.visual_html_v2 requires a renderer script when enabled."
        )
    configuration["renderer"] = renderer_config
    metrics_config = configuration.get("metrics_builder")
    if isinstance(metrics_config, str):
        metrics_config = {"script": metrics_config}
    if metrics_config is not None:
        if not isinstance(metrics_config, dict) or not metrics_config.get("script"):
            raise ValueError(
                "reporting.visual_html_v2.metrics_builder must declare a script."
            )
        configuration["metrics_builder"] = metrics_config
    return configuration


def run_visual_report_adapter(
    label: str,
    adapter: dict[str, Any],
    run_dir: Path,
    variable_folder: str,
    template: str | None = None,
) -> None:
    script = Path(str(adapter.get("script") or "")).resolve()
    if not script.is_file():
        raise FileNotFoundError(f"Visual report adapter not found: {script}")
    command = [sys.executable, "-B", str(script), "--run-dir", str(run_dir)]
    command.extend(str(value) for value in (adapter.get("args") or []))
    if template and label == "renderer":
        command.extend(["--template", template])
    selector_flag = str(adapter.get("variable_selector_flag") or "--variables")
    if selector_flag:
        command.extend([selector_flag, variable_folder])
    timeout_seconds = int(adapter.get("timeout_seconds") or 300)
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(
            f"Visual report adapter '{label}' failed for {variable_folder}: "
            + detail[-2000:]
        )


def visual_report_path_from_manifest(
    run_dir: Path, variable_folder: str
) -> Path:
    manifest_path = run_dir / "html-v2-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Visual HTML manifest was not created: {manifest_path}"
        )
    manifest = profiler.load_json(manifest_path)
    entry = next(
        (
            item
            for item in (manifest.get("reports") or [])
            if str(item.get("variable_folder") or "") == variable_folder
        ),
        None,
    )
    if not isinstance(entry, dict) or not entry.get("report"):
        raise ValueError(
            f"Visual HTML manifest has no report for {variable_folder}."
        )
    report = Path(str(entry["report"]))
    if not report.is_absolute():
        report = PROJECT_ROOT / report
    report = report.resolve()
    if not report.is_relative_to(run_dir.resolve()) or not report.is_file():
        raise ValueError(
            f"Visual HTML report must exist inside the active run: {report}"
        )
    return report


def validate_visual_html_v2(
    path: Path, configuration: dict[str, Any]
) -> None:
    document = path.read_text(encoding="utf-8")
    if len(document) < 1000:
        raise ValueError(f"Visual HTML report is unexpectedly short: {path}")
    dynamic_slide_count = bool(configuration.get("dynamic_slide_count"))
    if dynamic_slide_count:
        visible_document = re.sub(r"<!--.*?-->", "", document, flags=re.DOTALL)
        actual_slides = visible_document.count('class="slide-stage"')
        minimum_slides = int(configuration.get("minimum_slides") or 1)
        if actual_slides < minimum_slides:
            raise ValueError(
                f"Visual HTML slide count is {actual_slides}, below the configured "
                f"minimum of {minimum_slides}: {path}"
            )
        nav_start = visible_document.find('<div class="nav-ctrl" id="slide-nav">')
        nav_end = visible_document.find('<div class="side-controls" id="theme-selector">')
        nav_section = (
            visible_document[nav_start:nav_end]
            if nav_start >= 0 and nav_end > nav_start
            else ""
        )
        nav_values = [
            int(value)
            for value in re.findall(r'data-slide="(\d+)"', nav_section)
        ]
        if nav_values != list(range(actual_slides)):
            raise ValueError(
                f"Visual HTML navigation does not match the {actual_slides} slides: {path}"
            )
        for index in range(1, actual_slides + 1):
            if f'id="slide-{index}"' not in visible_document:
                raise ValueError(
                    f"Visual HTML is missing sequential slide-{index}: {path}"
                )
    expected_slides = configuration.get("expected_slides")
    if expected_slides is not None and not dynamic_slide_count:
        actual_slides = document.count('class="slide-stage"')
        if actual_slides != int(expected_slides):
            raise ValueError(
                f"Visual HTML slide count is {actual_slides}, expected {expected_slides}: {path}"
            )
    expected_nav = configuration.get("expected_nav_pills")
    if expected_nav is not None and not dynamic_slide_count:
        visible_document = re.sub(r"<!--.*?-->", "", document, flags=re.DOTALL)
        nav_start = visible_document.find('<div class="nav-ctrl" id="slide-nav">')
        nav_end = visible_document.find('<div class="side-controls" id="theme-selector">')
        nav_section = (
            visible_document[nav_start:nav_end]
            if nav_start >= 0 and nav_end > nav_start
            else ""
        )
        actual_nav = nav_section.count('class="nav-pill')
        if actual_nav != int(expected_nav):
            raise ValueError(
                f"Visual HTML navigation count is {actual_nav}, expected {expected_nav}: {path}"
            )
    for marker in configuration.get("required_markers") or []:
        if str(marker) not in document:
            raise ValueError(f"Visual HTML is missing required marker '{marker}': {path}")
    for token in configuration.get("forbidden_tokens") or []:
        if str(token) in document:
            raise ValueError(f"Visual HTML includes forbidden token '{token}': {path}")


def promote_visual_html_v2_artifact(
    artifact: dict[str, Any], run_dir: Path, configuration: dict[str, Any]
) -> dict[str, Any]:
    variable_folder = Path(str(artifact.get("folder") or "")).name
    report_path = visual_report_path_from_manifest(run_dir, variable_folder)
    validate_visual_html_v2(report_path, configuration)
    visual_path = str(report_path.relative_to(PROJECT_ROOT))
    notebook_html = str(artifact["html"])
    artifact["html_notebook"] = notebook_html
    artifact["html_v2"] = visual_path
    artifact["html"] = visual_path
    artifact["html_contract"] = "visual_html_v2_primary"
    checkpoint_path = PROJECT_ROOT / str(artifact["checkpoint"])
    checkpoint = profiler.load_json(checkpoint_path)
    checkpoint["html_exported_from_notebook"] = True
    checkpoint["visual_html_v2"] = {
        "primary": True,
        "path": visual_path,
        "manifest": str((run_dir / "html-v2-manifest.json").relative_to(PROJECT_ROOT)),
    }
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact


def render_visual_html_v2_for_variable(
    assessment: dict[str, Any],
    artifact: dict[str, Any],
    run_dir: Path,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    variable_folder = Path(str(artifact.get("folder") or "")).name
    metrics_builder = configuration.get("metrics_builder")
    if isinstance(metrics_builder, dict):
        blocker = str(metrics_builder.get("only_when_blocker") or "")
        if not blocker or str(assessment.get("blocker_key") or "") == blocker:
            metrics_builder = copy.deepcopy(metrics_builder)
            metrics_builder["args"] = [
                *(metrics_builder.get("args") or []),
                "--reporting-mode",
                REPORTING_MODE,
            ]
            run_visual_report_adapter(
                "metrics_builder", metrics_builder, run_dir, variable_folder
            )
    renderer_adapter = dict(configuration["renderer"])
    run_visual_report_adapter(
        "renderer",
        renderer_adapter,
        run_dir,
        variable_folder,
        template=configuration.get("template"),
    )
    return promote_visual_html_v2_artifact(artifact, run_dir, configuration)


def text_has_spanish_context(value: Any) -> bool:
    narrative = str(value or "").strip()
    if len(narrative) < 40:
        return True
    if any(character in narrative.lower() for character in "áéíóúñ¿¡"):
        return True
    padded = f" {narrative.lower()} "
    return any(marker in padded for marker in SPANISH_CONTEXT_MARKERS)


def validate_public_narrative(
    assessment: dict[str, Any], detail: dict[str, Any]
) -> None:
    variable_name = str(assessment.get("variable") or "Variable")
    plan = detail.get("analysis_plan") or assessment.get("analysis_plan") or {}
    if plan.get("language") != "es":
        raise ValueError(
            f"{variable_name}: public narrative language must be Spanish."
        )

    historical = (
        detail.get("historical_story")
        if "historical_story" in detail
        else plan.get("historical_story")
    ) or {}
    phases = historical.get("phases") or []
    if not historical.get("summary") or len(phases) < 4:
        raise ValueError(
            f"{variable_name}: historical story must include a summary and at least four phases."
        )
    if any(not item.get("stage") or not item.get("narrative") for item in phases):
        raise ValueError(
            f"{variable_name}: every historical phase requires a stage and narrative."
        )

    stories = (
        detail.get("validation_story")
        if "validation_story" in detail
        else plan.get("validation_story")
    ) or []
    expected_story_count = len(plan.get("validation_focus") or [])
    if not stories or len(stories) != expected_story_count:
        raise ValueError(
            f"{variable_name}: validation story count must match validation_focus."
        )
    for index, story in enumerate(stories, start=1):
        missing = []
        for field in VALIDATION_STORY_REQUIRED_FIELDS:
            if field not in story:
                missing.append(field)
            elif field not in {"fields", "sql_references"} and story.get(field) in {
                None,
                "",
            }:
                missing.append(field)
        if missing:
            raise ValueError(
                f"{variable_name}: validation story {index} is missing {missing}."
            )
        if not isinstance(story.get("fields"), list) or not isinstance(
            story.get("sql_references"), list
        ):
            raise ValueError(
                f"{variable_name}: validation story {index} fields and SQL references must be lists."
            )
        if not str(story.get("question")).startswith("¿"):
            raise ValueError(
                f"{variable_name}: validation story {index} must state a Spanish question."
            )
        if story.get("evidence_role") == "contextual" and not any(
            phrase in str(story.get("score_effect") or "").lower()
            for phrase in ("sin capacidad de aumentar", "no puede elevar")
        ):
            raise ValueError(
                f"{variable_name}: contextual evidence must explicitly state that it cannot raise a score."
            )

    score_rows = detail.get("score_application") or []
    if len(score_rows) != 8:
        raise ValueError(
            f"{variable_name}: public report must explain all eight scoring criteria."
        )

    narrative_values: list[tuple[str, Any]] = [
        ("definition", assessment.get("definition_text")),
        ("population", assessment.get("population_filter")),
        ("numerator", assessment.get("numerator_definition")),
        ("history", assessment.get("history_available")),
        ("intended use", plan.get("intended_use") or plan.get("attrition_use")),
        ("prediction cutoff", plan.get("prediction_cutoff")),
        ("source reasoning", plan.get("source_reasoning")),
        ("historical summary", historical.get("summary")),
    ]
    narrative_values.extend(
        (f"historical phase {index}", item.get("narrative"))
        for index, item in enumerate(phases, start=1)
    )
    for index, story in enumerate(stories, start=1):
        for field in (
            "question",
            "why",
            "method",
            "acceptance_rule",
            "observed_evidence",
            "interpretation",
            "score_effect",
            "limitation",
            "recommended_action",
        ):
            narrative_values.append(
                (f"validation story {index}.{field}", story.get(field))
            )
    for index, row in enumerate(score_rows, start=1):
        for field in (
            "status_rule",
            "observed_evidence",
            "why",
            "recommended_action",
        ):
            narrative_values.append(
                (f"score explanation {index}.{field}", row.get(field))
            )
    for index, rationale in enumerate(
        assessment.get("score_rationales") or [], start=1
    ):
        for field in (
            "status_rule",
            "why_below_2",
            "supporting_evidence",
            "recommended_action",
        ):
            narrative_values.append(
                (f"score rationale {index}.{field}", rationale.get(field))
            )
    for criterion, verification in (
        assessment.get("score_verification") or {}
    ).items():
        for field in ("evidence", "result", "acceptance_rule"):
            narrative_values.append(
                (f"verification {criterion}.{field}", verification.get(field))
            )

    missing_text = [label for label, value in narrative_values if not str(value or "").strip()]
    if missing_text:
        raise ValueError(
            f"{variable_name}: public narrative contains empty fields {missing_text}."
        )
    non_spanish = [
        label
        for label, value in narrative_values
        if not text_has_spanish_context(value)
    ]
    if non_spanish:
        raise ValueError(
            f"{variable_name}: public narrative is not Spanish in {non_spanish}."
        )


def validate_variable_artifacts(
    profile: dict[str, Any],
    artifacts: list[dict[str, Any]],
    visual_html_configuration: dict[str, Any] | None = None,
) -> None:
    assessments = profile.get("assessments") or []
    if len(assessments) != len(artifacts):
        raise ValueError(
            "Variable artifact count does not match assessment count."
        )
    assessment_by_name = {
        str(assessment.get("variable")): assessment
        for assessment in assessments
    }
    if set(assessment_by_name) != {
        str(artifact.get("variable")) for artifact in artifacts
    }:
        raise ValueError("Variable artifact names do not match assessment names.")
    for artifact in artifacts:
        assessment = assessment_by_name[str(artifact.get("variable"))]
        required = [
            "assessment_json",
            "coverage_json",
            "score_rationales_json",
            "report_detail_json",
            "analysis_plan",
            "pre_execution_plan",
            "evidence_ledger",
            "decision",
            "variable_spec",
            "checkpoint",
            "query_results",
            "charts_manifest",
            "notebook",
            "html",
        ]
        if artifact.get("html_notebook"):
            required.append("html_notebook")
        if artifact.get("html_v2"):
            required.append("html_v2")
        paths = {
            key: PROJECT_ROOT / str(artifact.get(key) or "")
            for key in required
        }
        missing = [key for key, path in paths.items() if not path.is_file()]
        if missing:
            raise ValueError(
                f"{assessment.get('variable')}: missing artifacts {missing}."
            )
        charts_dir = PROJECT_ROOT / str(artifact.get("charts") or "")
        if not charts_dir.is_dir():
            raise ValueError(f"{assessment.get('variable')}: charts directory is missing.")
        chart_entries = profiler.load_json(paths["charts_manifest"])
        if not isinstance(chart_entries, list) or not chart_entries:
            raise ValueError(
                f"{assessment.get('variable')}: charts manifest must contain at least one graph."
            )
        for chart in chart_entries:
            chart_path = charts_dir / str((chart or {}).get("file") or "").removeprefix("charts/")
            if not chart_path.is_file():
                raise ValueError(
                    f"{assessment.get('variable')}: missing chart listed in manifest: {chart_path.name}."
                )

        saved = profiler.load_json(paths["assessment_json"])
        if (
            saved.get("variable") != assessment.get("variable")
            or saved.get("scores") != assessment.get("scores")
            or saved.get("total") != assessment.get("total")
        ):
            raise ValueError(
                f"{assessment.get('variable')}: assessment JSON differs from profile."
            )
        detail = profiler.load_json(paths["report_detail_json"])
        validate_public_narrative(assessment, detail)
        if len(detail.get("score_application") or []) != 8:
            raise ValueError(
                f"{assessment.get('variable')}: report must explain all eight criteria."
            )
        if (detail.get("evidence") or {}).get("status") == "partial_failed":
            raise ValueError(
                f"{assessment.get('variable')}: one or more detailed evidence queries failed."
            )
        pre_plan = profiler.load_yaml(paths["pre_execution_plan"])
        if not pre_plan.get("created_before_execution") or not pre_plan.get(
            "acceptance_rules_frozen"
        ):
            raise ValueError(
                f"{assessment.get('variable')}: pre-execution plan is not frozen."
            )
        if not pre_plan.get("validation_story"):
            raise ValueError(
                f"{assessment.get('variable')}: pre-execution plan has no explicit stories."
            )
        analysis_plan = profiler.load_yaml(paths["analysis_plan"])
        if (
            (analysis_plan.get("visualization_policy") or {}).get("priority")
            != "graph_first"
            or "score_overview"
            not in (analysis_plan.get("planned_visualizations") or [])
        ):
            raise ValueError(
                f"{assessment.get('variable')}: report plan is not graph-first."
            )
        ledger = profiler.load_json(paths["evidence_ledger"])
        for query in ledger.get("queries") or []:
            if not query.get("sql_sha256") or not query.get("result_sha256"):
                raise ValueError(
                    f"{assessment.get('variable')}: evidence ledger has an unhashed query."
                )
        ledger_references = {
            Path(str(query.get("query_reference") or "")).as_posix().lower()
            for query in ledger.get("queries") or []
            if query.get("query_reference")
        }
        report_references = {
            Path(str(reference)).as_posix().lower()
            for reference in (
                ((detail.get("evidence") or {}).get("query_results") or {}).keys()
            )
        }
        missing_report_ledger = sorted(report_references - ledger_references)
        if missing_report_ledger:
            raise ValueError(
                f"{assessment.get('variable')}: report SQL is missing from the evidence ledger: "
                + ", ".join(missing_report_ledger)
            )
        decision = profiler.load_json(paths["decision"])
        if decision.get("scores") != assessment.get("scores"):
            raise ValueError(
                f"{assessment.get('variable')}: decision scores differ from assessment."
            )

        notebook = profiler.load_json(paths["notebook"])
        code_cells = [
            cell
            for cell in notebook.get("cells") or []
            if cell.get("cell_type") == "code"
        ]
        if not code_cells or any(
            cell.get("execution_count") is None for cell in code_cells
        ):
            raise ValueError(
                f"{assessment.get('variable')}: notebook is not fully executed."
            )
        errors = [
            output
            for cell in code_cells
            for output in (cell.get("outputs") or [])
            if output.get("output_type") == "error"
        ]
        if errors:
            raise ValueError(
                f"{assessment.get('variable')}: notebook contains execution errors."
            )
        legacy_html_path = paths.get("html_notebook", paths["html"])
        html_text = legacy_html_path.read_text(encoding="utf-8")
        required_html_sections = (
            "Contexto del problema y del portafolio",
            "Resumen visual",
            "Resumen histórico y flujo del análisis",
            "Historia de cada validación",
            "Por qué lo validamos",
            "Aplicación visible de reglas 2/1/0",
        )
        if len(html_text) < 1000 or any(
            section not in html_text for section in required_html_sections
        ):
            raise ValueError(
                f"{assessment.get('variable')}: HTML report is incomplete."
            )
        if artifact.get("html_v2"):
            if paths["html"] != paths["html_v2"]:
                raise ValueError(
                    f"{assessment.get('variable')}: visual HTML must be the primary report."
                )
            validate_visual_html_v2(
                paths["html_v2"], visual_html_configuration or {}
            )


def main() -> None:
    global REPORT_SQL_ROOT
    parser = argparse.ArgumentParser(description="Run a complete reproducible v4 assessment.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--spec", help="Assessment spec YAML.")
    source_group.add_argument("--request", help="Minimal run-request YAML.")
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help=(
            "Optional project adapter YAML defining catalog, database helper, "
            "metadata schemas, hints, and output paths."
        ),
    )
    parser.add_argument(
        "--catalog-spec",
        help="Version-4 catalog spec used to resolve --request variable names.",
    )
    parser.add_argument(
        "--analysis-plan",
        action="append",
        default=[],
        help=(
            "Codex-authored analysis-plan-vN.yaml to apply before SQL. Repeat once "
            "per requested variable when using --strict-analysis-plans."
        ),
    )
    parser.add_argument("--rules", help="Editable scoring rules YAML.")
    parser.add_argument("--semantic-hints", help="Editable semantic hint registry YAML.")
    parser.add_argument("--query-helper", help="Project read-only database adapter Python file.")
    parser.add_argument("--aggregate-results", help="Offline aggregate JSON; skips Redshift.")
    parser.add_argument("--metadata-results", help="Offline information_schema rows for preflight.")
    parser.add_argument("--output-root")
    parser.add_argument(
        "--documentation-root",
        help="Project variable-documentation root; defaults to the project adapter.",
    )
    parser.add_argument(
        "--skip-documentation-update",
        action="store_true",
        help="Do not update cumulative project documentation after each completed variable.",
    )
    parser.add_argument("--run-id", help="Optional run folder name under output-root.")
    parser.add_argument(
        "--reporting-mode",
        choices=("presentation", "internal_analysis"),
        help=(
            "Modo del entregable. presentation es el valor por defecto; "
            "internal_analysis requiere que el usuario haya indicado un uso interno."
        ),
    )
    parser.add_argument("--print-sql", action="store_true", help="Print SQL through profile_variable and exit.")
    parser.add_argument("--skip-report-data", action="store_true", help="Skip extra aggregate report-detail queries.")
    parser.add_argument("--skip-metadata", action="store_true", help="Do not connect for metadata; intended for offline tests.")
    parser.add_argument("--preflight-only", action="store_true", help="Write run request and portfolio context, then stop before aggregate profiling.")
    parser.add_argument("--continue-conservative", action="store_true", help="Continue with unresolved questions capped conservatively at 1 or 0.")
    parser.add_argument(
        "--strict-analysis-plans",
        action="store_true",
        help=(
            "Require an explicit validation_story for every variable. "
            "Use for new guided assessments; legacy validation_focus fallback is rejected."
        ),
    )
    args = parser.parse_args()

    project_config_path = (
        Path(args.project_config).resolve() if args.project_config else None
    )
    project_settings = project_configuration(project_config_path)
    visual_html_configuration = visual_html_v2_configuration(project_settings)
    reporting_settings = dict(project_settings.get("reporting") or {})
    configured_mode = str(
        reporting_settings.get("default_deliverable_mode") or "presentation"
    )
    if configured_mode not in {"presentation", "internal_analysis"}:
        raise SystemExit(
            "reporting.default_deliverable_mode must be presentation or internal_analysis."
        )
    reporting_mode = args.reporting_mode or configured_mode

    def configured_path(
        cli_value: str | None, key: str, default: Path | None = None
    ) -> Path | None:
        value = cli_value or project_settings.get(key)
        if value:
            return Path(value).resolve()
        return default.resolve() if default is not None else None

    spec_path = Path(args.spec).resolve() if args.spec else None
    request_path = Path(args.request).resolve() if args.request else None
    catalog_spec_path = configured_path(args.catalog_spec, "catalog_spec")
    rules_path = configured_path(args.rules, "rules", DEFAULT_RULES)
    assert rules_path is not None
    semantic_hints_path = configured_path(
        args.semantic_hints, "semantic_hint_registry"
    )
    query_helper_path = configured_path(args.query_helper, "query_helper")
    runtime_config = merge_settings(
        dict(project_settings.get("runtime") or {}),
        {
            key: project_settings[key]
            for key in ("audit_sql_root", "profile_sql_root")
            if project_settings.get(key)
        },
    )
    if project_settings.get("metadata"):
        runtime_config = merge_settings(
            runtime_config, {"metadata": project_settings["metadata"]}
        )
    if project_settings.get("profile_sql_root"):
        REPORT_SQL_ROOT = Path(project_settings["profile_sql_root"]).resolve()
    documentation_config = dict(project_settings.get("documentation") or {})
    documentation_enabled = bool(
        documentation_config.get("enabled", True)
    ) and not args.skip_documentation_update
    documentation_root = (
        Path(
            args.documentation_root
            or documentation_config.get("root")
            or DEFAULT_DOCUMENTATION_ROOT
        ).resolve()
        if documentation_enabled
        else None
    )
    if documentation_root is not None and not documentation_root.is_relative_to(
        PROJECT_ROOT
    ):
        raise SystemExit(
            f"Documentation root must stay inside the project: {documentation_root}"
    )
    aggregate_path = Path(args.aggregate_results).resolve() if args.aggregate_results else None
    metadata_results_path = Path(args.metadata_results).resolve() if args.metadata_results else None
    analysis_plan_paths = [Path(value).resolve() for value in args.analysis_plan]
    if request_path and catalog_spec_path is None:
        raise SystemExit(
            "--request requires --catalog-spec or catalog_spec in --project-config."
        )
    if args.print_sql:
        prepared = prepare_portfolio(
            spec_path,
            rules_path,
            "print-sql",
            request_path=request_path,
            catalog_spec_path=catalog_spec_path,
            execute_metadata=False,
            persist_metadata_sql=False,
            runtime_config=runtime_config,
            semantic_hints_path=semantic_hints_path,
            query_helper_path=query_helper_path,
            require_explicit_stories=(
                args.strict_analysis_plans and not analysis_plan_paths
            ),
            reporting_mode=reporting_mode,
        )
        apply_explicit_analysis_plans(
            prepared, analysis_plan_paths, strict=args.strict_analysis_plans
        )
        for variable in prepared["variables"]:
            profiler.profile_one(
                variable,
                prepared["rules"],
                Path(prepared["source_spec_path"]),
                print_sql=True,
            )
        return

    output_root = configured_path(
        args.output_root, "output_root", DEFAULT_OUTPUT_ROOT
    )
    assert output_root is not None
    run_id = args.run_id or default_run_id(output_root)
    run_dir = output_root / run_id
    working_dir = output_root / f".{run_id}.working"
    if run_dir.exists() or working_dir.exists():
        raise SystemExit(f"Run directory already exists: {run_dir}")
    inputs_dir = working_dir / "inputs"
    evidence_dir = working_dir / "evidence"
    variables_dir = working_dir / "vars"
    plans_dir = working_dir / "plans"
    for directory in (inputs_dir, evidence_dir, variables_dir, plans_dir):
        directory.mkdir(parents=True, exist_ok=False)

    state_path = working_dir / "run-state.json"
    run_state: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "completed_variables": [],
    }
    profiler.write_json(state_path, run_state)
    variable_outputs: list[dict[str, Any]] = []
    frozen_plans: list[dict[str, Any]] = []
    used_slugs: set[str] = set()

    def freeze_plan(number: int, total: int, plan: dict[str, Any]) -> None:
        name = f"{number:02d}-{renderer.slugify(str(plan.get('variable') or 'variable'))}-analysis-plan-v{plan.get('plan_version', 1)}.yaml"
        path = plans_dir / name
        with path.open("x", encoding="utf-8") as handle:
            yaml.safe_dump(plan, handle, sort_keys=False, allow_unicode=True)
        notebook_path = write_planned_notebook(path, plan)
        frozen_plans.append({
            "number": number,
            "variable": plan.get("variable"),
            "path": str(path.relative_to(PROJECT_ROOT)),
            "notebook": str(notebook_path.relative_to(PROJECT_ROOT)),
            "sha256": workflow.canonical_json_hash(plan),
        })
        run_state["planned_count"] = number
        run_state["current_plan"] = plan.get("variable")
        profiler.write_json(state_path, run_state)

    def complete_one(
        number: int, total: int, assessment: dict[str, Any]
    ) -> None:
        artifact = write_variable_outputs(
            {"assessments": [assessment]},
            variables_dir,
            start_number=number,
            used_slugs=used_slugs,
        )[0]
        validate_variable_artifacts(
            {"assessments": [assessment]}, [artifact]
        )
        documentation = None
        if documentation_root is not None:
            documentation = attach_documentation_update(
                assessment,
                artifact,
                documentation_root,
                run_id,
            )
            validate_variable_artifacts(
                {"assessments": [assessment]}, [artifact]
            )
        if visual_html_configuration:
            artifact = render_visual_html_v2_for_variable(
                assessment,
                artifact,
                working_dir,
                visual_html_configuration,
            )
            validate_variable_artifacts(
                {"assessments": [assessment]},
                [artifact],
                visual_html_configuration,
            )
        variable_outputs.append(artifact)
        run_state["total_variables"] = total
        run_state["completed_count"] = number
        run_state["current_variable"] = assessment.get("variable")
        run_state["completed_variables"].append(
            {
                "number": number,
                "variable": assessment.get("variable"),
                "checkpoint": artifact["checkpoint"],
                "documentation": documentation,
            }
        )
        profiler.write_json(state_path, run_state)
        print(
            f"[{number:02d}/{total:02d}] completed "
            f"{assessment.get('variable')}",
            flush=True,
        )

    try:
        prepared = prepare_portfolio(
            spec_path,
            rules_path,
            run_id,
            request_path=request_path,
            catalog_spec_path=catalog_spec_path,
            metadata_results_path=metadata_results_path,
            execute_metadata=(
                not args.skip_metadata
                and metadata_results_path is None
                and aggregate_path is None
            ),
            persist_metadata_sql=True,
            runtime_config=runtime_config,
            semantic_hints_path=semantic_hints_path,
            query_helper_path=query_helper_path,
            require_explicit_stories=(
                args.strict_analysis_plans
                and not analysis_plan_paths
                and not args.preflight_only
            ),
            reporting_mode=reporting_mode,
        )
        supplied_analysis_plans = apply_explicit_analysis_plans(
            prepared,
            analysis_plan_paths,
            strict=(args.strict_analysis_plans and not args.preflight_only),
        )
        run_request_path = working_dir / "run-request.yaml"
        portfolio_context_path = working_dir / "portfolio-context.yaml"
        portfolio_html_path = working_dir / "portfolio-context.html"
        run_request_path.write_text(
            yaml.safe_dump(
                prepared["run_request"], sort_keys=False, allow_unicode=True
            ),
            encoding="utf-8",
        )
        portfolio_context_path.write_text(
            yaml.safe_dump(
                prepared["portfolio_context"], sort_keys=False, allow_unicode=True
            ),
            encoding="utf-8",
        )
        portfolio_html_path.write_text(
            workflow.render_portfolio_html(prepared["portfolio_context"]),
            encoding="utf-8",
        )
        unresolved = int(
            prepared["portfolio_context"].get(
                "unresolved_material_question_count", 0
            )
        )
        unknown_policy = str(
            prepared["run_request"].get("unknown_policy") or "pause"
        ).lower()
        should_pause = args.preflight_only or (
            unresolved > 0
            and not args.continue_conservative
            and unknown_policy != "conservative"
        )
        if should_pause:
            run_state["status"] = "preflight_complete"
            run_state["completed_at"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            run_state["unresolved_material_questions"] = unresolved
            profiler.write_json(state_path, run_state)
            working_dir.rename(run_dir)
            print(f"Preflight created: {run_dir}")
            print(f"Portfolio context: {run_dir / 'portfolio-context.html'}")
            return

        profile = build_profile(
            Path(prepared["source_spec_path"]),
            rules_path,
            aggregate_path,
            run_id,
            include_report_data=not args.skip_report_data,
            on_assessment=complete_one,
            on_plan=freeze_plan,
            prepared_portfolio=prepared,
            documentation_root=documentation_root,
        )
        copied_inputs = {
            "spec": copy_input(spec_path, inputs_dir) if spec_path else None,
            "request": copy_input(request_path, inputs_dir) if request_path else None,
            "catalog_spec": copy_input(catalog_spec_path, inputs_dir) if request_path else None,
            "rules": copy_input(rules_path, inputs_dir),
            "analysis_catalog": copy_input(
                (
                    Path(profile["analysis_catalog"])
                    if profile.get("analysis_catalog")
                    else None
                ),
                inputs_dir,
            ),
            "aggregate_results": (
                copy_input(aggregate_path, inputs_dir)
                if aggregate_path
                else None
            ),
            "metadata_results": (
                copy_input(metadata_results_path, inputs_dir)
                if metadata_results_path
                else None
            ),
            "semantic_hints": copy_input(
                Path(prepared["semantic_hints_path"]), inputs_dir
            ),
            "project_config": (
                copy_input(project_config_path, inputs_dir)
                if project_config_path and project_config_path.is_file()
                else None
            ),
        }
        copied_evidence = copy_evidence(
            profile["assessments"], evidence_dir
        )
        profile["run_id"] = run_id
        profile["artifact_root"] = str(run_dir.relative_to(PROJECT_ROOT))

        profile_path = working_dir / "profile.json"
        profiler.write_json(profile_path, profile)
        run_evidence_ledger = {
            "schema_version": 1,
            "run_id": run_id,
            "generated_at": profile["generated_at"],
            "evaluation_order": profile.get("evaluation_order") or [],
            "variables": [
                assessment.get("evidence_ledger") or {}
                for assessment in sorted(
                    profile["assessments"],
                    key=lambda item: int(item.get("evaluation_index") or 0),
                )
            ],
        }
        run_evidence_ledger_path = working_dir / "evidence-ledger.json"
        profiler.write_json(run_evidence_ledger_path, run_evidence_ledger)
        workbook_path = working_dir / "assessment.xlsx"
        renderer.render(profile, renderer.DEFAULT_TEMPLATE, workbook_path)
        validate_variable_artifacts(
            profile, variable_outputs, visual_html_configuration or None
        )
        renderer.validate_workbook(workbook_path, profile)

        visual_html_manifest_path = working_dir / "html-v2-manifest.json"
        if visual_html_configuration:
            rebase_artifact_json_file(
                visual_html_manifest_path, working_dir, run_dir
            )

        published_outputs = rebase_artifact_paths(
            variable_outputs, working_dir, run_dir
        )
        published_inputs = rebase_artifact_paths(
            copied_inputs, working_dir, run_dir
        )
        published_evidence = rebase_artifact_paths(
            copied_evidence, working_dir, run_dir
        )
        index_json = variables_dir / "index.json"
        index_csv = variables_dir / "index.csv"
        index_json.write_text(
            json.dumps(
                published_outputs,
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with index_csv.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = [
                "number",
                "variable",
                "folder",
                "notebook",
                "html",
                "html_notebook",
                "html_v2",
                "html_contract",
                "assessment_json",
                "report_detail_json",
                "analysis_plan",
                "pre_execution_plan",
                "evidence_ledger",
                "decision",
                "variable_spec",
                "checkpoint",
                "documentation",
                "result",
                "total",
            ]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            assessment_by_name = {
                str(item.get("variable")): item
                for item in profile["assessments"]
            }
            for artifact in published_outputs:
                assessment = assessment_by_name[str(artifact["variable"])]
                writer.writerow(
                    {
                        "number": artifact["number"],
                        "variable": artifact["variable"],
                        "folder": artifact["folder"],
                        "notebook": artifact["notebook"],
                        "html": artifact["html"],
                        "html_notebook": artifact.get("html_notebook"),
                        "html_v2": artifact.get("html_v2"),
                        "html_contract": artifact.get("html_contract"),
                        "assessment_json": artifact["assessment_json"],
                        "report_detail_json": artifact["report_detail_json"],
                        "analysis_plan": artifact["analysis_plan"],
                        "pre_execution_plan": artifact["pre_execution_plan"],
                        "evidence_ledger": artifact["evidence_ledger"],
                        "decision": artifact["decision"],
                        "variable_spec": artifact["variable_spec"],
                        "checkpoint": artifact["checkpoint"],
                        "documentation": artifact.get("documentation"),
                        "result": assessment.get("result"),
                        "total": assessment.get("total"),
                    }
                )

        manifest = {
            "manifest_version": 4,
            "run_id": run_id,
            "generated_at": profile["generated_at"],
            "status": "validated",
            "execution_mode": "sequential_variables_with_shared_context",
            "schema_version": profile["schema_version"],
            "python_executable": sys.executable,
            "inputs": published_inputs,
            "artifacts": {
                "profile": str(
                    (run_dir / "profile.json").relative_to(PROJECT_ROOT)
                ),
                "run_request": str(
                    (run_dir / "run-request.yaml").relative_to(PROJECT_ROOT)
                ),
                "portfolio_context_yaml": str(
                    (run_dir / "portfolio-context.yaml").relative_to(PROJECT_ROOT)
                ),
                "portfolio_context_html": str(
                    (run_dir / "portfolio-context.html").relative_to(PROJECT_ROOT)
                ),
                "evidence_ledger": str(
                    (run_dir / "evidence-ledger.json").relative_to(PROJECT_ROOT)
                ),
                "workbook": str(
                    (run_dir / "assessment.xlsx").relative_to(PROJECT_ROOT)
                ),
                "variables_root": str(
                    (run_dir / "vars").relative_to(PROJECT_ROOT)
                ),
                "pre_execution_plans": rebase_artifact_paths(
                    frozen_plans, working_dir, run_dir
                ),
                "variable_folders": published_outputs,
                "variable_index_json": str(
                    (run_dir / "vars" / "index.json").relative_to(PROJECT_ROOT)
                ),
                "variable_index_csv": str(
                    (run_dir / "vars" / "index.csv").relative_to(PROJECT_ROOT)
                ),
                "visual_html_v2_manifest": (
                    str((run_dir / "html-v2-manifest.json").relative_to(PROJECT_ROOT))
                    if visual_html_configuration
                    else None
                ),
                "evidence": published_evidence,
            },
            "variables": [
                item.get("variable")
                for item in profile["assessments"]
            ],
            "original_order": profile.get("original_order") or [],
            "evaluation_order": profile.get("evaluation_order") or [],
            "dependencies": profile.get("dependencies") or {},
            "cycles": profile.get("cycles") or [],
            "problem_context": profile.get("problem_context") or {},
            "portfolio_overview": profile.get("portfolio_overview") or {},
            "contextual_relationships": profile.get("contextual_relationships") or [],
            "evidence_reused": {
                item.get("variable"): item.get("reused_evidence") or []
                for item in profile["assessments"]
            },
            "inherited_conditions": {
                item.get("variable"): item.get("inherited_conditions") or []
                for item in profile["assessments"]
            },
            "project_documentation": {
                item.get("variable"): item.get("documentation") or {}
                for item in profile["assessments"]
            },
            "reporting": {
                "deliverable_mode": reporting_mode,
                "primary_html_contract": (
                    "visual_html_v2" if visual_html_configuration else "notebook_html"
                ),
                "visual_html_v2_enabled": bool(visual_html_configuration),
            },
        }
        manifest_path = working_dir / "manifest.json"
        profiler.write_json(manifest_path, manifest)
        run_state["status"] = "validated"
        run_state["completed_at"] = (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )
        run_state["published_path"] = str(
            run_dir.relative_to(PROJECT_ROOT)
        )
        profiler.write_json(state_path, run_state)
        working_dir.rename(run_dir)
    except Exception as exc:
        run_state["status"] = "failed"
        run_state["failed_at"] = (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )
        run_state["error"] = str(exc)
        profiler.write_json(state_path, run_state)
        raise

    print(f"Created assessment run: {run_dir}")
    print(f"Manifest: {run_dir / 'manifest.json'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Assessment run failed: {exc}") from exc










