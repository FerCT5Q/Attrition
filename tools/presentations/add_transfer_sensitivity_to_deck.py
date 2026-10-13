"""Add the H transfer-removal sensitivity to the existing nine-slide deck."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/presentations/20261013-1027_base-enhanced-qvoice"
OUT = ROOT / "output/presentations/20261013-1100_transfer-sensitivity"
H_RESULTS = ROOT / "output/analysis/engineering/20261013/model-h-without-transfers-v3/results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite a delivery: {OUT}")
    shutil.copytree(SOURCE, OUT)
    deck = OUT / "presentacion-eng.html"
    html = deck.read_text(encoding="utf-8")
    replacements = [
        ("New BU and city results are on slide 8;", "New BU, city and transfer-removal results are on slide 8;"),
        ("BU L3 with and without QVoice; work city", "BU L3, work city and transfer removal"),
        ("Later work-city tests improved estimates, but did not change the selected model", "Further tests changed estimates, but did not change the selected model"),
        ("Same group definitions · later tests add BU L3, work city or both · lower log-loss is better", "Same group definitions · tests add BU L3, work city or remove Transfers · lower log-loss is better"),
        ("Earlier alternative-method + QVoice tests did not improve the selected model’s capture/error balance. The selected model retains its August base in January; later candidates use the January cutoff. Enhanced + QVoice remains selected pending review.",
         "Transfer removal test: without Transfers, the Base model changed from 138.8 to 140.5 log-loss × 1,000 and from 42.4% to 41.6% exits captured. Enhanced + QVoice changed from 137.7 to 139.4 and from 43.1% to 42.4%. Enhanced + QVoice remains selected."),
        ("J03, S12 · Retrospective comparisons", "J03, S12, H01 · Retrospective comparisons"),
    ]
    changes = []
    for before, after in replacements:
        count = html.count(before)
        if count != 1:
            raise AssertionError(f"Expected one occurrence of {before!r}, found {count}")
        html = html.replace(before, after)
        changes.append({"before": before, "after": after, "occurrences": count})
    if html.count('<div class="slide-stage') != 9:
        raise AssertionError("Slide count changed")
    deck.write_text(html, encoding="utf-8")

    evidence_path = OUT / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    evidence["revision_base"] = str((SOURCE / "presentacion-eng.html").relative_to(ROOT)).replace("/", "\\")
    evidence["revision_base_sha256"] = sha(SOURCE / "presentacion-eng.html")
    evidence["deck_sha256"] = sha(deck)
    evidence["replaces_deliverable"] = str((SOURCE / "presentacion-eng.html").relative_to(ROOT)).replace("/", "\\")
    evidence["sources"]["H01"] = {"path": str(H_RESULTS.relative_to(ROOT)).replace("/", "\\"), "sha256": sha(H_RESULTS)}
    evidence["transfer_sensitivity"] = {"model_name": "H = C − Transfers", "result": "removal worsened historical loss; no selection change"}
    evidence["changes"] = changes
    evidence["model_selection_changed"] = False
    evidence["browser_verification"] = str((OUT / "browser-verification.json").relative_to(ROOT)).replace("/", "\\")
    write(evidence_path, evidence)
    (OUT / "guion.md").write_text(
        "# Actualización: sensibilidad de Transfers\n\n"
        "Clasificación: `presentation`. Se conservan nueve diapositivas. El slide 8 muestra que retirar Transfers empeoró la estimación y la captura; no cambia la selección de Enhanced + QVoice.\n",
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
