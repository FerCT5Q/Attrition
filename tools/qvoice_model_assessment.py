"""Adaptador del experimento al assessment v4; artefactos de un concepto por vez."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

from qvoice_model_data import ROOT, DEFAULT_CONFIG, load_config, components_for, primary_components, availability_date, write_json, utc_now, sha256_file

SKILL = ROOT / ".codex/skills/evaluate-attrition-variable"
PYTHON = ROOT / ".venv/Scripts/python.exe"
PLAN_ROOT = ROOT / "config/qvoice_model_plans"
AUDIT_COLUMNS = [
    "survey_year", "snapshot_date", "workbooks_checked", "header_ambiguities", "missing_component_headers",
    "unverified_availability_waves", "unresolved_wording_waves", "invalid_count", "valid_count", "missing_count",
    "absent_count", "status_reconciliation_difference", "comparable_count", "recalculated_match_count", "mismatch_count",
    "eligible_count", "matched_count", "unmatched_count", "duplicate_count", "multi_match_count",
    "full_exceeds_primary_count", "overlap_cohort_difference", "primary_complete_count", "full_complete_count",
    "source_participants", "primary_available_count", "missing_key_rows", "source_duplicate_count",
    "alternative_headers_checked", "alternate_comparable_count", "alternate_disagreement_count",
    "reconciliation_tests", "reconciliation_mismatch_count",
]


def write_yaml(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def query_suffix(config: dict | None = None) -> str:
    return str((config or {}).get("paths", {}).get("query_suffix", "20261006"))


def plan_root(config: dict | None = None) -> Path:
    configured = (config or {}).get("paths", {}).get("plan_root")
    return ROOT / configured if configured else PLAN_ROOT


def plan_path(candidate: dict, config: dict | None = None) -> Path:
    paths = list(plan_root(config).glob(f"*-{candidate['id']}-v*.yaml"))
    if not paths:
        raise ValueError(f"Se necesita un plan explícito para {candidate['id']}.")
    return max(paths, key=lambda path: int(path.stem.rsplit('-v', 1)[1]))


def audit_query_path(candidate: dict, config: dict | None = None) -> Path:
    return ROOT / f"queries/audits/qvoice_model_{candidate['id']}_{query_suffix(config)}.sql"


def coverage_query_path(candidate: dict, config: dict | None = None) -> Path:
    return ROOT / f"queries/profiles/qvoice_model_{candidate['id']}_{query_suffix(config)}.sql"


def create_configuration(config: dict, output: Path) -> tuple[Path, Path, Path]:
    """Materializa contratos desde los planes escritos por Codex, sin inventar validaciones."""
    output.mkdir(parents=True, exist_ok=True)
    annual_lag = config.get("temporal_rules", {}).get("assignment") == "annual_lag"
    variables = []
    for candidate in config["candidates"]:
        plan = yaml.safe_load(plan_path(candidate, config).read_text(encoding="utf-8"))
        audit = audit_query_path(candidate, config)
        coverage = coverage_query_path(candidate, config)
        audit.write_text(
            "-- SQLite read-only sobre agregados actuales del concepto, calculados en memoria.\n"
            "-- El manifest enlaza Excel, SQL Redshift de join, hashes y fecha de ejecución.\n"
            "SELECT " + ", ".join(AUDIT_COLUMNS) + "\nFROM qvoice_variable_audit\nORDER BY survey_year;\n", encoding="utf-8")
        coverage.write_text(
            "-- Cobertura descriptiva del concepto en workforce previo; no acredita fecha predictiva.\n"
            "SELECT snapshot_date, survey_year AS fiscal_year, eligible_count AS eligible_employees,\n"
            "       primary_available_count AS observable_employees\n"
            "FROM qvoice_variable_audit ORDER BY snapshot_date;\n", encoding="utf-8")
        rationale = {
            "definition": {
                "why": ("La representación está especificada; su uso temporal sigue la política anual aprobada y conserva las equivalencias pendientes." if annual_lag else "La representación está especificada; su uso temporal requiere fechas acreditadas y resolver las equivalencias señaladas."),
                "evidence": plan["concept"],
                "recommended_action": ("Mantener la política anual versionada y resolver las brechas específicas antes de promover la señal." if annual_lag else "Resolver la disponibilidad y las brechas específicas; repetir las pruebas predictivas con el mismo contrato."),
            },
            "consistency": {
                "why": "Se normalizan encabezados y valores faltantes por wave y se conserva su procedencia.",
                "evidence": "El audit actual separa dominio inválido, vacío, 255 y ausencia estructural; no hereda scores históricos.",
                "recommended_action": "Mantener las reglas y revisar las anomalías de la ejecución antes de usar nuevas waves.",
            },
            "join": {
                "why": ("El enlace descriptivo por empleado se comprueba y el traslado al snapshot sigue la política Y a Y+1." if annual_lag else "El enlace descriptivo por empleado se comprueba; queda pendiente acreditar cuándo puede trasladarse la respuesta a un snapshot."),
                "evidence": "Se auditan elegibles, enlaces únicos, no enlaces y duplicados para Engineering en la foto previa.",
                "recommended_action": ("Aplicar la asignación Y a Y+1, el reemplazo anual y la continuidad del episodio laboral." if annual_lag else "Acreditar publicación y aplicar reemplazo, vencimiento y continuidad del episodio laboral."),
            },
            "effort": {
                "why": "Se necesita lectura de Excel, mapping versionado, enlace temporal y controles de calidad.",
                "evidence": "El adaptador procesa columnas estructuradas en memoria y publica sólo agregados.",
                "recommended_action": "Ejecutar el pipeline versionado tras incorporar cada nueva wave y conservar su manifest.",
            },
        }
        numerator = (
            "Personas enlazadas con los 33 binarios válidos del conjunto exacto."
            if candidate["id"] == "mean33" else
            "Personas enlazadas con al menos un signo calculable; se requieren 53 ítems y al menos 38 ordinales válidos."
            if candidate["id"] == "heartbeat" else
            "Personas enlazadas con al menos un componente primario válido; completitud total y parcial se informa por separado."
        )
        variables.append({
            "category": "Encuestas QVoice", "variable": candidate["name"], "notes": plan["concept"],
            "definition": plan["concept"],
            "source": {"type": "Excel y Redshift", "detail": "Excel QVoice 2024–2026 y survey_structure.xlsx; enlace agregado a hrda.post_hire_monthly_worker_dtls.", "columns": components_for(candidate), "status": "confirmed_accessible"},
            "profile": {"mode": "aggregate_sql", "aggregate_sql_file": str(coverage.resolve())},
            "level_data": "Agregado por empleado-wave", "measurement": {"type": "survey", "observable_columns": primary_components(candidate)},
            "population": {"mode": "custom", "display": plan["population"]}, "numerator_definition": numerator,
            "evidence": {"definition": "needs_alignment", "consistency": "normalization_needed", "join": "mapping_or_validation", "effort": "moderate_transformation"},
            "rationale": rationale, "blocker": "none",
            "verification": {"semantic_type": candidate["semantic_type"], "source": {
                "method": "approved_external_access_check", "evidence": "Lectura actual del diccionario y los tres archivos; SQL local sobre inventario agregado ejecutado antes del scoring.",
                "result": "El runner determina acceso y ambigüedades desde el resultado congelado actual.",
                "as_of_date": config.get("assessment", {}).get("as_of_date", "2026-10-06"), "query_reference": str(audit.relative_to(ROOT)).replace("\\", "/"),
                "acceptance_rule": "Los tres archivos deben estar accesibles y los encabezados resueltos no deben ser ambiguos.", "outcome": "pending",
                "metric_map": {"workbooks_checked": {"column": "workbooks_checked", "aggregate": "sum"}, "header_ambiguities": {"column": "header_ambiguities", "aggregate": "sum"}},
                "metric_checks": [{"metric": "workbooks_checked", "aggregate": "sum", "operator": "eq", "threshold": 3}, {"metric": "header_ambiguities", "aggregate": "sum", "operator": "eq", "threshold": 0}],
            }},
            "score_overrides": {"history": {
                "score": int(config.get("assessment", {}).get("history_score_override", 0)),
                "reason": config.get("assessment", {}).get("history_reason", "No se acredita aún historia utilizable desde la publicación real de resultados."),
                "evidence": "Las fechas efectivas y los periodos evaluables se registran por wave; los meses replicados no se cuentan como waves independientes.",
                "recommended_action": config.get("assessment", {}).get("history_action", "Acreditar disponibilidad y repetir la evaluación temporal."),
            }},
            "analysis": {
                "language": "es", "semantic_type": candidate["semantic_type"], "definition": plan["concept"],
                "population": plan["population"],
                "display_source": "Excel QVoice 2024–2026; enlace descriptivo agregado a HRDA.",
                "display_data_type": "Signo ordinal (−1, 0, 1)" if candidate["id"] == "heartbeat" else "Seis bandas del promedio binario" if candidate["id"] == "mean33" else "Binaria por componente (0, 1)",
                "readiness_summary": ("La representación y sus componentes están especificados. El uso predictivo se evalúa bajo el rezago anual aprobado y conserva las brechas semánticas de cada wave." if annual_lag else "La representación y sus componentes están especificados. El uso predictivo requiere acreditar la publicación de resultados y resolver las brechas detalladas de cada wave."),
                "numerator_definition": numerator, "intended_use": plan["intended_use"], "source_reasoning": plan["source_reasoning"],
                "prediction_cutoff": plan["knowledge_date"], "prior_evidence_policy": "Contexto histórico únicamente; todas las cifras de esta ejecución se recalculan.",
                "validation_focus": [s["question"] for s in plan["validation_story"]], "validation_story": plan["validation_story"],
                "plan_authorship": "codex_explicit", "depends_on": [], "documentation_path": f"qvoice-model/{candidate['id']}/README.md",
            },
        })
        if "history_score_override" not in config.get("assessment", {}) and all(
            availability_date(wave) is not None for wave in config["sources"]["waves"]
        ):
            variables[-1].pop("score_overrides", None)
        if candidate["semantic_type"] == "derived_feature":
            variables[-1]["source"]["direct_field"] = False
            variables[-1]["selected_derivation"] = "structured_components"
            variables[-1]["derivation_options"] = [{
                "id": "structured_components", "name": "Cálculo desde los componentes estructurados", "status": "testable", "selected": True,
                "fields_and_tables": "Los componentes exactos se toman del Excel de cada wave y se enlazan de forma agregada a hrda.post_hire_monthly_worker_dtls.",
                "formula": plan["concept"], "grain": plan["grain"], "temporal_window": plan["knowledge_date"],
                "deduplication": "Se excluyen todas las llaves duplicadas del Excel; se audita la unicidad del enlace a workforce.",
                "nulls_and_edge_cases": "Se distinguen preguntas ausentes, vacíos, 255 e inválidos. Se aplica el mínimo de componentes indicado en la fórmula.",
                "leakage_controls": ("La wave Y sólo se incorpora en Y+1, con vigencia de 12 meses y continuidad laboral." if annual_lag else "Las respuestas sólo podrán incorporarse desde una publicación acreditada, con vigencia máxima de 12 meses y continuidad laboral."),
                "snapshot_join": "La wave disponible reemplaza a la anterior; una nueva wave sin respuesta no hereda el valor previo.",
                "sensitivity": "La ejecución conserva las respuestas sólo en memoria y publica agregados con los mínimos de personas y eventos.",
                "validations_needed": ("La fórmula, componentes, dominio, completitud, enlaces y asignación anual se auditan con las consultas del plan." if annual_lag else "La fórmula, componentes, dominio, completitud y enlaces se auditan con las consultas del plan; falta acreditar disponibilidad temporal."),
                "estimated_effort": "La transformación requiere lectura de Excel, mapping explícito, cálculo y enlace temporal.",
                "decision_reason": ("Es la ruta especificada en el plan bajo rezago anual; las equivalencias pendientes limitan la interpretación. Los resultados de fórmula se documentan por separado." if annual_lag else "Es la ruta especificada en el plan; permanece testable para predicción mientras existan fechas o equivalencias pendientes. Los resultados de fórmula se documentan por separado."),
            }]
    catalog_path = output / "catalog-v4.yaml"
    write_yaml(catalog_path, {"version": 4, "variables": variables})
    request = {
        "schema_version": 1, "language": "es", "unknown_policy": "conservative",
        "problem_context": {
            "problem_statement": "Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.",
            "decision_or_use_case": "Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.",
            "outcome": "Salida voluntaria en los seis meses siguientes al snapshot.", "population": config["population"]["display"],
            "unit_of_analysis": "Empleado-snapshot; incertidumbre agrupada por persona.", "knowledge_boundary": config["knowledge_boundary"],
            "time_horizon": "Seis meses", "constraints": ["Resultados agregados; ninguna fila individual persistida.", "Asignación temporal declarada antes del ajuste; faltantes no equivalen a desfavorable.", "Assessment secuencial por concepto, con evidencia nueva y planes explícitos."],
            "portfolio_hypotheses": [c["hypothesis"] for c in config["candidates"]],
            "known_relationships": [{"variables": [config["candidates"][0]["name"], config["candidates"][2]["name"]], "relationship": "El promedio contiene Q4/Q12.", "why_relevant": "Comparar también 31 preguntas manteniendo la cohorte completa original de 33."}],
        },
        "variables": [{"name": c["name"], "intended_use": c["hypothesis"], "population": config["population"]["display"], "knowledge_date": ("Wave del año anterior asignada al año calendario del snapshot." if config.get("temporal_rules", {}).get("assignment") == "annual_lag" else "Publicación acreditada anterior al snapshot.")} for c in config["candidates"]],
        "decisions": {
            "dates": ("Aplicar la política anual aprobada: wave Y sólo en snapshots Y+1. Esta regla no certifica la fecha real de publicación." if config.get("temporal_rules", {}).get("assignment") == "annual_lag" else "No asumir publicación desde año, lanzamiento ni fecha del archivo; las waves no acreditadas quedan pendientes."),
            "formula": "Numerador del promedio: respuestas favorables; denominador: 33 respuestas válidas. Ablación: 31, sobre la misma cohorte de 33.",
            "missing": "Mantener toda la población y separar faltantes por componente.",
            "components": "Versionar Workplace Connection y Wellbeing; no equiparar subsets a KPI completo.",
            "access": "Acceso local y procesamiento en memoria autorizados por el usuario y config/attrition_model_in_memory_training_authorization_20261001.json.",
            "conservative_policy": ("Aplicar caps ante historia corta o equivalencias no verificadas; la política temporal y las asociaciones descriptivas no habilitan por sí solas score 2." if annual_lag else "Aplicar caps de 1 o 0 ante fechas o equivalencias no verificadas; ninguna asociación anual habilita score 2."),
        },
    }
    request_path = output / "run-request.yaml"
    write_yaml(request_path, request)
    project = {
        "schema_version": 1, "catalog_spec": str(catalog_path.resolve()),
        "rules": str(SKILL / "references/scoring-rules.yaml"), "semantic_hint_registry": str(SKILL / "references/semantic-hints.yaml"),
        "query_helper": str(ROOT / ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py"),
        "output_root": str(ROOT / "output/assessments"), "audit_sql_root": str(ROOT / "queries/audits"), "profile_sql_root": str(ROOT / "queries/profiles"),
        "documentation": {"enabled": True, "root": str(ROOT / "docs/variables")},
        "metadata": {"default_schema": "hrda", "search_schemas": ["hrda"]},
        "reporting": {"visual_html_v2": {"enabled": True, "renderer": {"script": str(ROOT / "tools/presentations/render_variable_assessment_v2.py"), "args": ["--force"], "timeout_seconds": 300}, "dynamic_slide_count": True, "minimum_slides": 10, "required_markers": ["assessment-v2-metadata", "Scorecard de ocho criterios"], "forbidden_tokens": ["value_label", "query_results"]}},
    }
    project_path = output / "assessment-project.yaml"
    write_yaml(project_path, project)
    return catalog_path, request_path, project_path


def run_preflight(config: dict, output: Path) -> None:
    catalog, request, project = create_configuration(config, output)
    sys.path.insert(0, str(SKILL / "scripts"))
    import run_assessment as runner
    prepared = runner.prepare_portfolio(
        None, SKILL / "references/scoring-rules.yaml", config["experiment_id"], request_path=request,
        catalog_spec_path=catalog, metadata_results_path=output / "redshift-metadata.json", execute_metadata=False,
        persist_metadata_sql=True, reporting_mode="presentation",
    )
    runner.apply_explicit_analysis_plans(prepared, [plan_path(c, config) for c in config["candidates"]], strict=True)
    context = prepared["portfolio_context"]
    context["source_metadata_reference"] = str((output / "source-metadata.json").relative_to(ROOT))
    context["metadata_only"] = True
    context["source_metadata_limitation"] = (
        "La metadata no acredita una fecha real de publicación; esta ejecución usa la política de rezago anual aprobada y la identifica como supuesto de negocio."
        if config.get("temporal_rules", {}).get("assignment") == "annual_lag"
        else "Los resultados de encuesta no tienen fecha de publicación verificada en la metadata revisada."
    )
    write_yaml(output / "portfolio-context.yaml", context)
    # Usar el renderer de preflight del motor, sin construir un deck adicional.
    import portfolio_workflow as workflow
    (output / "portfolio-context.html").write_text(workflow.render_portfolio_html(context), encoding="utf-8")
    for c in config["candidates"]:
        plan = yaml.safe_load(plan_path(c, config).read_text(encoding="utf-8"))
        target = output / "plans" / c["id"] / f"analysis-plan-v{plan['plan_version']}.yaml"
        write_yaml(target, plan)
        runner.write_planned_notebook(target, plan)
    write_json(output / "preflight-manifest.json", {"created_at": utc_now(), "metadata_only": True, "variable_order": [c["id"] for c in config["candidates"]], "plan_sha256": {c["id"]: sha256_file(plan_path(c, config)) for c in config["candidates"]},
               "configuration_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
               "source_metadata_sha256": sha256_file(output / "source-metadata.json"), "reporting_mode": "presentation"})
    print(f"Preflight conjunto y {len(config['candidates'])} planes explícitos congelados antes de consultar agregados.", flush=True)


def execute_local_audit(candidate: dict, rows: list[dict], config: dict | None = None) -> tuple[list[dict], list[dict]]:
    """SQL real sobre métricas agregadas actuales; nunca simula una tabla Redshift."""
    audit = audit_query_path(candidate, config)
    coverage = coverage_query_path(candidate, config)
    with sqlite3.connect(":memory:") as connection:
        declarations = ", ".join(f"{column} {'TEXT' if column == 'snapshot_date' else 'INTEGER'}" for column in AUDIT_COLUMNS)
        connection.execute(f"CREATE TABLE qvoice_variable_audit ({declarations})")
        connection.executemany(f"INSERT INTO qvoice_variable_audit VALUES ({','.join('?' for _ in AUDIT_COLUMNS)})", [[row[c] for c in AUDIT_COLUMNS] for row in rows])
        connection.execute("PRAGMA query_only = ON")
        results = []
        for path in (audit, coverage):
            cursor = connection.execute(path.read_text(encoding="utf-8"))
            columns = [c[0] for c in cursor.description]
            results.append([dict(zip(columns, row)) for row in cursor.fetchall()])
    return tuple(results)


def assess_one(candidate: dict, evidence: dict, run_root: Path, preflight: Path, *, config: dict | None = None, version: int = 1, prepare_only: bool = False) -> Path:
    config = config or load_config()
    audit_rows, coverage = execute_local_audit(candidate, evidence["audit_rows"], config)
    audit = str(audit_query_path(candidate, config).relative_to(ROOT)).replace("\\", "/")
    payload_path = run_root / "aggregate-results.json"
    write_json(payload_path, {"variables": {candidate["name"]: {"coverage": coverage, "queries": {audit: audit_rows, **evidence.get("extra_queries", {})}}}})
    request = yaml.safe_load((preflight / "run-request.yaml").read_text(encoding="utf-8"))
    request["variables"] = [v for v in request["variables"] if v["name"] == candidate["name"]]
    request["decisions"]["joint_preflight"] = str((preflight / "portfolio-context.yaml").relative_to(ROOT))
    request_path = run_root / "run-request.yaml"
    write_yaml(request_path, request)
    run_id = f"qvoice-model-{query_suffix(config)}-{candidate['id']}-v{version}"
    output_root = ROOT / "output/assessments"
    input_hashes = {str(path.relative_to(ROOT)): sha256_file(path) for path in
                    (payload_path, request_path, plan_path(candidate, config), preflight / "assessment-project.yaml", preflight / "catalog-v4.yaml", preflight / "redshift-metadata.json")}
    command_path = run_root / "assessment-command.json"
    if command_path.is_file():
        previous = json.loads(command_path.read_text(encoding="utf-8"))
        completed = output_root / previous["run_id"]
        if previous.get("input_hashes") == input_hashes and (completed / "manifest.json").is_file():
            if json.loads((completed / "manifest.json").read_text(encoding="utf-8")).get("status") == "validated":
                return completed
    base_run_id, attempt = run_id, 1
    while (output_root / run_id).exists() or (output_root / f".{run_id}.working").exists():
        attempt += 1
        run_id = f"{base_run_id}-r{attempt}"
    command = [str(PYTHON), "-B", str(SKILL / "scripts/run_assessment.py"), "--request", str(request_path),
               "--project-config", str(preflight / "assessment-project.yaml"), "--catalog-spec", str(preflight / "catalog-v4.yaml"),
               "--metadata-results", str(preflight / "redshift-metadata.json"), "--aggregate-results", str(payload_path),
               "--analysis-plan", str(plan_path(candidate, config)), "--strict-analysis-plans", "--continue-conservative", "--reporting-mode", "presentation",
               "--run-id", run_id, "--output-root", str(output_root), "--skip-report-data"]
    record = {"run_id": run_id, "command": command, "input_hashes": input_hashes, "created_at": utc_now()}
    write_json(command_path, record)
    write_json(run_root / f"assessment-command-{run_id}.json", record)
    if prepare_only:
        return command_path
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (run_root / "assessment-run.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        # El runner sólo lee evidencia agregada; este error no puede contener filas fuente.
        raise RuntimeError(result.stderr[-4500:] or result.stdout[-4500:])
    return output_root / run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--prepare-candidate")
    parser.add_argument("--register-candidate")
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    selected_candidate = args.prepare_candidate or args.register_candidate
    if selected_candidate:
        if args.run_root is None:
            parser.error("--prepare-candidate requiere --run-root.")
        candidate = next(c for c in config["candidates"] if c["id"] == selected_candidate)
        pointer = json.loads((args.run_root / "variables" / candidate["id"] / "latest-evidence.json").read_text(encoding="utf-8"))
        evidence_root = ROOT / pointer["path"]
        evidence = json.loads((evidence_root / "evidence.json").read_text(encoding="utf-8"))
        result = assess_one(candidate, evidence, evidence_root, args.preflight.resolve(), config=config, version=pointer["version"], prepare_only=True)
        if args.register_candidate:
            if not result.is_dir() or not (result / "manifest.json").is_file():
                raise ValueError("El assessment todavía no está publicado con esos inputs.")
            destination = args.run_root / "variables" / candidate["id"] / "assessment-reference.json"
            if destination.exists():
                previous = json.loads(destination.read_text(encoding="utf-8"))
                write_json(destination.with_name(f"assessment-reference-{Path(previous['path']).name}.json"), previous)
            write_json(destination, {"path": str(result.relative_to(ROOT)), "manifest_sha256": sha256_file(result / "manifest.json"), "evidence_path": str(evidence_root.relative_to(ROOT))})
        print(result)
    else:
        run_preflight(config, args.preflight.resolve())
