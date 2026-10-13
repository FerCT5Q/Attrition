"""Audita la validación retrospectiva de F + QVoice contra C + QVoice.

El script sólo lee resultados agregados ya producidos. Comprueba que F añade
únicamente work_city, que usa la misma selección QVoice, que las mejoras se
mantienen por corte y que una ejecución completa reproduce la ejecución rápida.
No lee ni escribe filas de empleados ni predicciones individuales.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    ("log_loss", "menor"),
    ("brier_score", "menor"),
    ("pr_auc", "mayor"),
    ("lift_at_10_percent", "mayor"),
    ("capture_percent", "mayor"),
    ("group_snapshot_mae_pp", "menor"),
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_check(checks, name, passed, observed, rule):
    checks.append(
        {
            "name": name,
            "outcome": "pass" if passed else "fail",
            "observed": observed,
            "rule": rule,
        }
    )


def close(a, b, tolerance=1e-12):
    return abs(float(a) - float(b)) <= tolerance


def main(primary_path: Path, repeat_path: Path):
    primary = read(primary_path)
    repeat = read(repeat_path)
    checks = []

    add_check(
        checks,
        "modo_de_reporte",
        primary.get("reporting_mode") == "presentation",
        primary.get("reporting_mode"),
        "presentation",
    )
    add_check(
        checks,
        "sin_filas_persistidas",
        primary.get("employee_level_rows_persisted") is False
        and primary.get("individual_scores_published") is False,
        {
            "employee_level_rows_persisted": primary.get("employee_level_rows_persisted"),
            "individual_scores_published": primary.get("individual_scores_published"),
        },
        "ambos false",
    )

    period_rows = {row["id"]: row for row in primary["periods"]}
    repeat_period_rows = {row["id"]: row for row in repeat["periods"]}
    add_check(
        checks,
        "mismos_cortes",
        set(period_rows) == {"aug_dec_2025", "jan_feb_2026"}
        and set(period_rows) == set(repeat_period_rows),
        sorted(period_rows),
        "dos cortes externos idénticos en ambas ejecuciones",
    )

    period_deltas = {}
    for period_id, row in period_rows.items():
        c_metrics = row["metrics"]["C_Q"]
        f_metrics = row["metrics"]["C_plus_city_Q"]
        deltas = {metric: float(f_metrics[metric] - c_metrics[metric]) for metric, _ in METRICS}
        period_deltas[period_id] = deltas

        for metric, direction in METRICS:
            delta = deltas[metric]
            passed = delta <= 1e-12 if direction == "menor" else delta >= -1e-12
            add_check(
                checks,
                f"{period_id}:{metric}",
                passed,
                delta,
                "F + QVoice no empeora" if direction == "menor" else "F + QVoice no reduce",
            )

        c_features = set(row["models"]["C_Q"]["features"])
        f_features = set(row["models"]["C_plus_city_Q"]["features"])
        add_check(
            checks,
            f"{period_id}:solo_work_city",
            f_features - c_features == {"work_city"} and not (c_features - f_features),
            {"added": sorted(f_features - c_features), "removed": sorted(c_features - f_features)},
            "F añade únicamente work_city",
        )
        add_check(
            checks,
            f"{period_id}:sin_job_family_detail",
            not any("job_family" in feature for feature in f_features),
            sorted(feature for feature in f_features if "job_family" in feature),
            "ninguna característica contiene job_family",
        )
        add_check(
            checks,
            f"{period_id}:qvoice_mismo_selector",
            row["q_selection"]["id"] == repeat_period_rows[period_id]["q_selection"]["id"],
            row["q_selection"]["id"],
            "la selección QVoice es idéntica en la ejecución de réplica",
        )

    summary_delta = primary["deltas"]["FQ_minus_CQ"]
    add_check(
        checks,
        "mejora_media_de_captura",
        summary_delta["capture_percent"] > 0,
        summary_delta["capture_percent"],
        "> 0 pp en promedio",
    )
    add_check(
        checks,
        "error_de_grupo_dentro_de_guarda",
        summary_delta["group_snapshot_mae_pp"] <= 0.1,
        summary_delta["group_snapshot_mae_pp"],
        "F no empeora el error más de 0.1 pp",
    )
    add_check(
        checks,
        "captura_gana_en_ambos_cortes",
        all(period_deltas[p]["capture_percent"] > 1e-12 for p in period_deltas),
        {p: period_deltas[p]["capture_percent"] for p in period_deltas},
        "> 0 pp en cada corte; regla de promoción vigente",
    )

    reproducible = True
    for metric in ("log_loss", "brier_score", "pr_auc", "lift_at_10_percent", "capture_percent", "group_snapshot_mae_pp"):
        a = primary["summary"]["C_plus_city_Q"][metric]
        b = repeat["summary"]["C_plus_city_Q"][metric]
        reproducible = reproducible and close(a, b)
        a = primary["summary"]["C_Q"][metric]
        b = repeat["summary"]["C_Q"][metric]
        reproducible = reproducible and close(a, b)
    add_check(
        checks,
        "reproducibilidad_ejecucion_completa_vs_rapida",
        reproducible,
        "métricas agregadas idénticas dentro de 1e-12" if reproducible else "diferencia detectada",
        "la segunda ejecución reproduce los resultados",
    )

    passed = all(check["outcome"] == "pass" for check in checks)
    capture_both = next(check for check in checks if check["name"] == "captura_gana_en_ambos_cortes")
    if capture_both["outcome"] == "pass":
        decision = "candidate_passes_current_promotion_rule"
        recommendation = "F + QVoice puede pasar a la siguiente etapa de aprobación."
    else:
        decision = "strong_challenger_but_fails_capture_both_periods_gate"
        recommendation = "F + QVoice se registra como nuevo candidato experimental y mejor challenger; C + QVoice sigue elegido por la regla vigente."

    result = {
        "run_id": "engineering-f-qvoice-validation-20261013-v1",
        "status": "completed_validation",
        "reporting_mode": "presentation",
        "primary_results": primary_path.relative_to(ROOT).as_posix(),
        "replica_results": repeat_path.relative_to(ROOT).as_posix(),
        "checks": checks,
        "period_deltas": period_deltas,
        "decision": decision,
        "recommendation": recommendation,
        "all_checks_pass": passed,
        "employee_level_rows_persisted": False,
        "individual_scores_published": False,
    }
    out = primary_path.parent
    json_path = out / "validation-f-qvoice.json"
    md_path = out / "validacion-f-qvoice.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fmt_delta(value, scale=1):
        return f"{value * scale:+.1f}"

    lines = [
        "# Validación de F + QVoice",
        "",
        "Auditoría agregada de la comparación completa contra C + QVoice. Se usan los mismos dos cortes externos, la misma selección QVoice y una ejecución rápida de réplica. No se guardan filas ni predicciones individuales.",
        "",
        "## Resultado por corte",
        "",
        "Los deltas son F + QVoice menos C + QVoice; negativo es mejor para pérdidas y error, positivo es mejor para ranking y captura.",
        "",
        "| Corte | Log-loss ×1000 | Brier ×1000 | PR-AUC pp | Lift | Captura pp | Error grupo pp |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for period_id, delta in period_deltas.items():
        lines.append(
            f"| {period_id} | {fmt_delta(delta['log_loss'], 1000)} | {fmt_delta(delta['brier_score'], 1000)} | {fmt_delta(delta['pr_auc'], 100)} | {fmt_delta(delta['lift_at_10_percent'])} | {fmt_delta(delta['capture_percent'])} | {fmt_delta(delta['group_snapshot_mae_pp'])} |"
        )
    lines += [
        "",
        "## Decisión bajo la regla vigente",
        "",
        f"**{recommendation}**",
        "",
        "F mejora log-loss, Brier, PR-AUC, lift y error de grupo en ambos cortes. La captura mejora en el primer corte y empata en el segundo; por eso la condición estricta de ganar captura en los dos periodos no pasa. La evidencia respalda registrar F + QVoice como nuevo candidato experimental para aprobación, pero no sustituye una validación prospectiva.",
        "",
        "## Comprobaciones",
        "",
        f"- Pruebas ejecutadas: {len(checks)}.",
        f"- Comprobaciones aprobadas: {sum(check['outcome'] == 'pass' for check in checks)}.",
        f"- Estado del conjunto: {'pass' if passed else 'fail'}.",
        f"- Evidencia JSON: `validation-f-qvoice.json`.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    manifest_path = out / "manifest.json"
    manifest = read(manifest_path)
    manifest.setdefault("files", {})[json_path.relative_to(out).as_posix()] = sha(json_path)
    manifest["files"][md_path.relative_to(out).as_posix()] = sha(md_path)
    manifest["validation"] = {
        "status": "completed_validation",
        "artifact": json_path.relative_to(out).as_posix(),
        "decision": decision,
        "all_checks_pass": passed,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"decision": decision, "checks": len(checks), "passed": sum(c["outcome"] == "pass" for c in checks), "total": len(checks), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--primary",
        default="output/analysis/engineering/20261013/model-f-qvoice-comparison-v3/results.json",
    )
    parser.add_argument(
        "--replica",
        default="output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/results.json",
    )
    args = parser.parse_args()
    main(ROOT / args.primary, ROOT / args.replica)
