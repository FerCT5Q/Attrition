"""Reenfoca el slide 4 en las mejoras que condujeron al CQ elegido."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output/presentations/20261013-0817_revision-modelo-inicial"
OUT = ROOT / "output/presentations/20261013-0850_cq-mejoras-slide4"
TEMPLATE = Path(
    "C:/Users/fcarranz/.codex/skills/html-slide-generator/"
    "templates/fullscreen/base-fullscreen.html"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = BASE / "presentacion-eng.html"
    html = source.read_text(encoding="utf-8")
    old = BeautifulSoup(html, "html.parser")
    changes: list[dict[str, str]] = []

    s05 = json.loads(
        (
            ROOT
            / "output/analysis/engineering/20261008/"
            "qvoice-model-b-annual-lag-v2/comparison-results.json"
        ).read_text(encoding="utf-8")
    )
    s08 = json.loads(
        (
            ROOT
            / "output/analysis/engineering/20261008/"
            "c-group-selection-v1/results.json"
        ).read_text(encoding="utf-8")
    )
    s11 = json.loads(
        (
            ROOT
            / "output/analysis/engineering/20261009/"
            "c-qvoice-mean28-v1/results.json"
        ).read_text(encoding="utf-8")
    )
    q4 = next(v for v in s05["variants"] if v["id"] == "intent_q4")
    q4_checks = sum(q4["decision"]["checks"].values())
    variants_passing_ranking_and_brier = sum(
        v["decision"]["checks"]["ranking_vs_control"]
        and v["decision"]["checks"]["brier_score_vs_control"]
        for v in s05["variants"]
    )
    q4_main_periods = [p for p in q4["periods"] if "response" in p and p.get("main")]
    q4_calibration_delta_bp = 100 * sum(
        p["response"]["calibration_error_pp"]
        - p["control"]["calibration_error_pp"]
        for p in q4_main_periods
    ) / len(q4_main_periods)
    b30 = s08["summary"]["30"]["B_cuts"]["metrics"]
    c30_four = s08["summary"]["30"]["C_Bcuts"]["metrics"]
    bc_group_error_reduction = 100 * (
        1 - c30_four["group_mae_pp"] / b30["group_mae_pp"]
    )
    c = s11["summary"]["C"]
    cq = s11["summary"]["CQ"]
    c30 = c["scenarios"]["30"]
    cq30 = cq["scenarios"]["30"]
    cq_log_loss_reduction = 100 * (
        1 - cq["global"]["log_loss"] / c["global"]["log_loss"]
    )
    cq_brier_reduction = 100 * (
        1 - cq["global"]["brier_score"] / c["global"]["brier_score"]
    )
    cq_group_error_reduction = 100 * (
        1
        - cq30["group_snapshot_mae_pp"]
        / c30["group_snapshot_mae_pp"]
    )
    assert q4_checks == 7
    assert variants_passing_ranking_and_brier == 9
    assert round(q4_calibration_delta_bp) == 2
    assert round(bc_group_error_reduction) == 11

    def replace(selector: str, new_inner: str) -> None:
        nonlocal html
        node = old.select_one(selector)
        assert node is not None, selector
        before = str(node)
        assert html.count(before) == 1, selector
        revised = BeautifulSoup(before, "html.parser").find()
        revised.clear()
        revised.append(BeautifulSoup(new_inner, "html.parser"))
        html = html.replace(before, str(revised))
        changes.append({"selector": selector, "after": new_inner})

    replace(
        "#slide-2 .ag-item:first-child .ag-body",
        "Core HR model B and the evidence path to CQ",
    )
    replace(
        "#slide-2 .flow-branches .flow-branch:first-child",
        "↳ QVoice evidence",
    )
    replace(
        "#slide-4 .slide-title-text",
        "CQ combined a stronger HR base with useful QVoice signal",
    )
    replace(
        "#slide-4 .slide-subtitle",
        "The evidence path from Core HR (B) to the selected C + QVoice model",
    )
    cards = [
        (
            "QVoice signal",
            f"The leading QVoice test passed {q4_checks} of 8 checks",
            f"All {variants_passing_ranking_and_brier} variants improved ranking and Brier vs B",
            f"Only miss: one strict calibration guard by {round(q4_calibration_delta_bp)} basis points",
            "S05",
            "m-part",
            "◐",
        ),
        (
            "Stronger HR base",
            "C reduced estimation error while keeping the same groups",
            f"Group estimation error fell {bc_group_error_reduction:.0f}%",
            f"Capture improved from {b30['capture_percent']:.1f}% to {c30_four['capture_percent']:.1f}%",
            "S08",
            "m-yes",
            "✓",
        ),
        (
            "Selected CQ",
            "CQ improved C across the headline measures",
            f"Capture {c30['capture_percent']:.1f}% → {cq30['capture_percent']:.1f}%; "
            f"PR-AUC {100*c['global']['pr_auc']:.1f}% → {100*cq['global']['pr_auc']:.1f}%",
            f"Log-loss −{cq_log_loss_reduction:.1f}%; Brier −{cq_brier_reduction:.1f}%; "
            f"group error −{cq_group_error_reduction:.1f}%",
            "S11, S12",
            "m-yes",
            "✓",
        ),
    ]
    card_html = []
    for label, head, first, second, source_id, second_class, second_mark in cards:
        card_html.append(
            '<article class="card st4">'
            f'<div class="pipe-num">{label}</div>'
            f'<div class="st4-head">{head}</div>'
            '<div class="st4-row"><span class="mark m-yes">✓</span>'
            f"<span>{first}</span></div>"
            f'<div class="st4-row"><span class="mark {second_class}">{second_mark}</span>'
            f"<span>{second}</span></div>"
            f'<div class="st4-src">{source_id}</div></article>'
        )
    replace("#slide-4 .st4-grid", "".join(card_html))
    replace(
        "#slide-4 .fix",
        "CQ was selected for its stronger overall balance: better ranking, "
        "lower loss and lower group estimation error.",
    )
    replace(
        "#slide-4 .src",
        "Engineering · retrospective comparisons · B→C uses 4 historical periods; "
        "C→CQ uses Aug–Dec 2025 and Jan–Feb 2026 · CQ improved capture in 2025 "
        "and tied C in Jan–Feb 2026; global calibration remains a validation item · "
        "S05, S08, S11, S12",
    )
    replace(".nav-pill[data-slide='3']", "4. Evidence path to CQ")

    new = BeautifulSoup(html, "html.parser")
    assert len(new.select(".slide-stage")) == len(new.select(".nav-pill")) == 9
    assert "julia" not in new.title.get_text().lower()
    assert "julia" not in " ".join(x.get_text() for x in new.select(".slide-stage")).lower()
    for number in [1, 3, 5, 6, 7, 8, 9]:
        assert str(old.select_one(f"#slide-{number}")) == str(
            new.select_one(f"#slide-{number}")
        )
    assert [str(x) for x in old.select("script,style")] == [
        str(x) for x in new.select("script,style")
    ]
    assert "7 of 8" in new.select_one("#slide-4").get_text(" ", strip=True)
    assert "group error −2.3%" in new.select_one("#slide-4").get_text(" ", strip=True)

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "presentacion-eng.html"
    shutil.copy2(TEMPLATE, target)
    target.write_text(html, encoding="utf-8")
    shutil.copy2(TEMPLATE, OUT / "template-origin.html")
    shutil.copytree(
        BASE / "historical-evidence",
        OUT / "historical-evidence",
        dirs_exist_ok=True,
    )

    evidence = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))
    evidence.update(
        revision_base=str(source.relative_to(ROOT)),
        revision_base_sha256=sha(source),
        deck_sha256=sha(target),
        changes=changes,
        unchanged_slides=[1, 3, 5, 6, 7, 8, 9],
        slide2_change="Agenda text aligned with the revised slide 4.",
        slide4_message=(
            "QVoice passed 7 of 8 checks; C strengthened the HR base; "
            "CQ improved ranking, losses, capture and group estimation error."
        ),
        historical_slides_4_5_preserved=False,
        historical_slide5_preserved=True,
        slide4_reframed=True,
        slide4_calculations={
            "qvoice_leading_variant_checks_passed": q4_checks,
            "qvoice_variants_improving_ranking_and_brier": variants_passing_ranking_and_brier,
            "qvoice_only_miss_calibration_basis_points": q4_calibration_delta_bp,
            "B_to_C_capture_percent": [
                b30["capture_percent"],
                c30_four["capture_percent"],
            ],
            "B_to_C_group_error_relative_reduction_percent": bc_group_error_reduction,
            "C_to_CQ_capture_percent": [
                c30["capture_percent"],
                cq30["capture_percent"],
            ],
            "C_to_CQ_PR_AUC_percent": [
                100 * c["global"]["pr_auc"],
                100 * cq["global"]["pr_auc"],
            ],
            "C_to_CQ_log_loss_relative_reduction_percent": cq_log_loss_reduction,
            "C_to_CQ_brier_relative_reduction_percent": cq_brier_reduction,
            "C_to_CQ_group_error_relative_reduction_percent": cq_group_error_reduction,
        },
        replaces_deliverable=str(source.relative_to(ROOT)),
    )
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "guion.md").write_text(
        "# Revisión conjunta del modelo: mejoras que condujeron a CQ\n\n"
        "Modo `presentation`. Se conservan nueve slides, su diseño, orden, idioma y "
        "definiciones de grupos. El slide 4 deja de mezclar la señal QVoice con una "
        "corrección de calibración descartada.\n\n"
        "El mensaje revisado tiene tres evidencias: la mejor prueba inicial de QVoice "
        "pasó 7 de 8 comprobaciones; C redujo 11% el error de estimación por grupos; "
        "y CQ mejoró frente a C en captura, PR-AUC, log-loss, Brier y error por grupos. "
        "La nota conserva que la captura empató en enero–febrero de 2026 y que la "
        "calibración global sigue siendo una validación pendiente.\n\n"
        "No se hicieron nuevos cálculos ni consultas. Las fuentes son S05, S08, S11 y S12.\n",
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
