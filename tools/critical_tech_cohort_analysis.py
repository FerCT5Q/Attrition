"""Ejecuta y empaqueta el screen agregado de cohortes de Critical Tech.

El script delega el acceso a Redshift en el helper read-only del skill del
proyecto. Sólo persiste el resultado agregado que devuelve la consulta; nunca
solicita ni guarda filas employee-level.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERY = ROOT / "queries" / "audits" / "critical_tech_cohort_discovery_20260907.sql"
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20260907"
HELPER = (
    ROOT
    / ".codex"
    / "skills"
    / "attrition-redshift-db"
    / "scripts"
    / "run_readonly_query.py"
)

SAFE_COLUMNS = {
    "cohort_axis",
    "cohort_value",
    "snapshot_rows",
    "distinct_employees",
    "positive_target_rows",
    "target_rate_percent",
    "critical_tech_rate_percent",
    "lift_vs_critical_tech",
    "first_snapshot",
    "last_snapshot",
    "periods_observed",
    "periods_with_30_positive",
    "reportable_period_rate_range_pp",
    "stability_status",
    "priority_status",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def as_int(value: object) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def md(value: object) -> str:
    """Escapa valores para que una categoría con `|` no rompa la tabla Markdown."""
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def action_for(row: dict[str, object]) -> tuple[str, str, str]:
    value = str(row.get("cohort_value") or "")
    axis = str(row.get("cohort_axis") or "")
    lowered = value.lower()

    if "unknown" in lowered and axis in {
        "manager_change_12m",
        "promotion_12m",
        "transfer_12m",
        "segment_x_manager_change",
        "segment_x_promotion",
        "segment_x_transfer",
    }:
        return (
            "Calidad y observabilidad del evento",
            "No usar como driver; validar fecha, flag y disponibilidad histórica del evento.",
            "Una categoría unknown no demuestra ausencia ni presencia del evento.",
        )

    if "manager change: yes" in lowered:
        return (
            "Transición y enablement de managers",
            "Revisar handoff, claridad de prioridades y apoyo al equipo después del cambio.",
            "Cambio reciente de manager es una señal asociada; no prueba causalidad.",
        )
    if "promotion: yes" in lowered:
        return (
            "Acompañamiento post-promoción",
            "Revisar expectativas del nuevo nivel, carga de rol y plan de desarrollo.",
            "La promoción puede ser un marcador de transición, no una causa demostrada.",
        )
    if "transfer: yes" in lowered:
        return (
            "Movilidad interna y transición",
            "Revisar integración, movilidad de carrera y soporte durante el cambio de rol.",
            "La transferencia es una señal contextual y requiere validar el momento del evento.",
        )
    if "work=onsite" in lowered or axis == "work_arrangement":
        return (
            "Revisión de modalidad de trabajo",
            "Validar si la modalidad es compatible con el rol y ofrecer alternativas gobernadas.",
            "La modalidad puede estar confundida con mercado, rol o política local.",
        )
    if "tenure=<1 year" in lowered:
        return (
            "Retención temprana y onboarding",
            "Reforzar onboarding, mentoría y conversación de expectativas durante el primer año.",
            "La cohorte describe una etapa laboral; no implica que onboarding sea el único driver.",
        )
    if "tenure=1-3 years" in lowered or "tenure=3-7 years" in lowered:
        return (
            "Carrera y movilidad interna",
            "Revisar oportunidades de crecimiento, movilidad y claridad de trayectoria.",
            "La etapa de tenure es un marcador para priorizar la conversación de carrera.",
        )
    if axis == "labor_market" or axis == "region":
        return (
            "Diagnóstico local de mercado y staffing",
            "Revisar capacidad de staffing, movilidad y contexto de mercado sin usar pay exacto.",
            "La geografía es principalmente contexto y puede recoger diferencias de composición.",
        )
    if "level=7" in lowered or "level=8" in lowered or axis in {
        "level_grouped",
        "management_level",
    }:
        return (
            "Carrera, nivel y movilidad técnica",
            "Revisar claridad de carrera, scope del rol, movilidad interna y sucesión técnica.",
            "Nivel y job family pueden ser proxies de composición; validar con modelo ajustado.",
        )
    if axis in {"job_family", "job_family_group", "segment", "job_family_x_level", "segment_x_level"}:
        return (
            "Talent review de la familia técnica",
            "Revisar staffing, movilidad y necesidades de carrera específicas de la familia.",
            "La familia identifica dónde priorizar el diagnóstico, no qué acción funciona.",
        )
    return (
        "Diagnóstico de cohorte",
        "Validar la señal con el equipo de People Analytics y seleccionar una acción gobernada.",
        "La asociación requiere validación temporal y multivariable antes de intervenir.",
    )


def run_query(query_path: Path) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(query_path),
            "--max-rows",
            "1000",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    columns = set(payload.get("columns", []))
    unexpected = columns - SAFE_COLUMNS
    if unexpected:
        raise ValueError(f"La consulta devolvió columnas no permitidas: {sorted(unexpected)}")
    if payload.get("truncated"):
        raise ValueError("El resultado agregado fue truncado; no se publica un screen incompleto.")
    return payload


def write_report(output_dir: Path, payload: dict[str, object], query_path: Path) -> None:
    rows = list(payload.get("rows", []))
    priority = [r for r in rows if r.get("priority_status") == "prioritaria_para_validacion"]
    hypotheses = [r for r in rows if r.get("priority_status") == "hipotesis_accionable"]
    event_candidates = [
        r
        for r in rows
        if r.get("cohort_axis") in {
            "manager_change_12m",
            "promotion_12m",
            "transfer_12m",
            "segment_x_manager_change",
            "segment_x_promotion",
            "segment_x_transfer",
        }
        and "unknown" not in str(r.get("cohort_value") or "").lower()
        and r.get("positive_target_rows") is not None
    ]
    event_candidates.sort(key=lambda r: float(r.get("lift_vs_critical_tech") or 0), reverse=True)
    baseline = rows[0].get("critical_tech_rate_percent") if rows else None

    report_lines = [
        "# Screen de cohortes de Critical Tech",
        "",
        "## Resultado ejecutivo",
        "",
        f"El screen encontró **{len(priority)} cohortes prioritarias para validación** y "
        f"**{len(hypotheses)} hipótesis accionables** bajo las reglas definidas en la consulta.",
        f"El baseline agregado de Critical Tech en esta ventana es **{baseline}%** de target "
        "voluntario a seis meses.",
        "",
        "Estos resultados son asociaciones descriptivas. No son scores individuales ni "
        "demuestran que una acción reduzca attrition.",
        "",
        "## Reglas y evidencia",
        "",
        "- Población: empleados regulares activos cuyo `job_family` coincide con el catálogo vigente `hrda.critical_tech`.",
        "- Ventana: snapshots con seis meses completos de seguimiento hasta 2026-09-07.",
        "- Target: `Voluntary` posterior al snapshot y hasta seis meses después.",
        "- Publicación: al menos 30 employee-snapshots, 30 empleados distintos y 30 eventos positivos.",
        "- Prioridad: lift mínimo de 1.25, al menos 100 empleados y consistencia en dos periodos.",
        f"- SQL: `{query_path.relative_to(ROOT).as_posix()}`.",
        "",
        "## Cohortes prioritarias",
        "",
        "| Eje | Cohorte | Empleados | Eventos | Tasa 6m | Lift | Rango entre periodos (pp) | Acción a validar |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]

    for row in priority[:30]:
        action, _, _ = action_for(row)
        report_lines.append(
            f"| {md(row.get('cohort_axis'))} | {md(row.get('cohort_value'))} | "
            f"{md(row.get('distinct_employees'))} | {md(row.get('positive_target_rows'))} | "
            f"{md(row.get('target_rate_percent'))}% | {md(row.get('lift_vs_critical_tech'))} | "
            f"{md(row.get('reportable_period_rate_range_pp'))} | {md(action)} |"
        )

    report_lines.extend(
        [
            "",
            "## Señales de manager y movilidad",
            "",
            "Estas filas son señales candidatas, no conclusiones. Las categorías `unknown` se excluyeron porque reflejan una brecha de observabilidad y no un evento.",
            "",
            "| Eje | Señal | Empleados | Eventos | Tasa 6m | Lift | Estabilidad | Estado |",
            "|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in event_candidates[:10]:
        report_lines.append(
            f"| {md(row.get('cohort_axis'))} | {md(row.get('cohort_value'))} | "
            f"{md(row.get('distinct_employees'))} | {md(row.get('positive_target_rows'))} | "
            f"{md(row.get('target_rate_percent'))}% | {md(row.get('lift_vs_critical_tech'))} | "
            f"{md(row.get('stability_status'))} | {md(row.get('priority_status'))} |"
        )

    report_lines.extend(
        [
            "",
            "## Lectura de drivers",
            "",
            "El patrón dominante del screen está en combinaciones de segmento/job family con "
            "tenure y nivel. Esto indica dónde concentrar el diagnóstico, pero todavía no "
            "separa composición, mercado, manager, movilidad y carrera. El siguiente paso "
            "es ajustar un hazard discreto pooled con esas señales y validación temporal.",
            "",
            "## Limitaciones",
            "",
            "1. El catálogo actual de Critical Tech se aplicó retrospectivamente; la membership histórica del archive aún no está reconciliada.",
            "2. Las etiquetas `manager_change_12m`, `promotion_12m` y `transfer_12m` usan el evento y fecha reportados en el snapshot; deben pasar una validación histórica específica antes de entrar al champion.",
            "3. La tasa a seis meses usa exposiciones employee-snapshot y puede contener ventanas solapadas; el modelo final usará hazard mensual para evitar interpretar el screen como estimación causal.",
            "4. Una cohorte prioritaria no es todavía una acción aprobada; cada una requiere owner, intervención piloto y métrica de seguimiento.",
            "",
        ]
    )
    (output_dir / "cohort-screen-report.md").write_text("\n".join(report_lines), encoding="utf-8")

    action_lines = [
        "# Registro inicial de palancas y acciones",
        "",
        "Este registro convierte el screen estadístico en hipótesis operativas. Cada acción "
        "debe ser aprobada por HR y evaluada con un diseño temporal o cuasi-experimental.",
        "",
        "| Prioridad | Cohorte | Driver/señal | Palanca candidata | Acción propuesta | Owner sugerido | Métrica de seguimiento |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in priority[:30]:
        action, action_detail, caveat = action_for(row)
        action_lines.append(
            f"| {md(row.get('priority_status'))} | {md(row.get('cohort_value'))} | "
            f"{md(row.get('cohort_axis'))} | {md(action)} | {md(action_detail)} | "
            "People Analytics + HRBP | Tasa de salida voluntaria a 6m y lift out-of-time |"
        )
        action_lines.append(f"<!-- Nota: {caveat} -->")
    action_lines.extend(
        [
            "",
            "## Señales en validación",
            "",
            "Las siguientes señales de manager/movilidad tienen que pasar una validación temporal y multivariable antes de asociarse a una acción:",
            "",
            "| Señal | Lift | Estado | Acción a validar |",
            "|---|---:|---|---|",
        ]
    )
    for row in event_candidates[:10]:
        action, action_detail, _ = action_for(row)
        action_lines.append(
            f"| {md(row.get('cohort_value'))} | {md(row.get('lift_vs_critical_tech'))} | "
            f"{md(row.get('priority_status'))} | {md(action)}: {md(action_detail)} |"
        )
    action_lines.extend(
        [
            "",
            "## Regla de uso",
            "",
            "No se debe convertir una fila en targeting individual. El entregable permitido "
            "es una cohorte agregada, la señal asociada, la acción aprobada y una métrica "
            "de seguimiento.",
        ]
    )
    (output_dir / "action-register.md").write_text("\n".join(action_lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Empaqueta el screen agregado de Critical Tech.")
    parser.add_argument("--query", type=Path, default=DEFAULT_QUERY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--reuse-result",
        action="store_true",
        help="Regenera los documentos desde cohort-screen-results.json sin volver a consultar Redshift.",
    )
    args = parser.parse_args()

    query_path = (ROOT / args.query).resolve() if not args.query.is_absolute() else args.query.resolve()
    output_dir = (ROOT / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    result_path = output_dir / "cohort-screen-results.json"
    if args.reuse_result:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    else:
        payload = run_query(query_path)
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(output_dir, payload, query_path)

    manifest = {
        "artifact": "critical-tech-cohort-screen",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": "2026-09-07",
        "query": str(query_path.relative_to(ROOT)),
        "query_sha256": sha256(query_path),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": sha256(result_path),
        "row_count": len(payload.get("rows", [])),
        "privacy_minimum_shared_cohort": 30,
        "employee_level_rows_persisted": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
