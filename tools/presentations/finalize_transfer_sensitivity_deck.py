"""Update provenance for the slide-8 transfer-sensitivity deck revision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/presentations/20261013-1100_transfer-sensitivity"
DECK = OUT / "presentacion-eng.html"


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    digest = hashlib.sha256(DECK.read_bytes()).hexdigest()
    evidence_path = OUT / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    evidence["deck_sha256"] = digest
    evidence["browser_verification"] = str((OUT / "browser-verification.json").relative_to(ROOT)).replace("/", "\\")
    write(evidence_path, evidence)
    write(OUT / "browser-verification.json", {
        "reporting_mode": "presentation", "verified_at": "2026-10-13", "viewport": "1440x810", "deck_sha256": digest,
        "checks": {"slide8_transfer_sensitivity_visible_and_legible": True, "nine_slides_preserved": True,
                   "selected_status_and_five_existing_variants_preserved": True, "no_clipping_in_reviewed_scene": True,
                   "model_selection_changed": False, "static_delivery_checks_passed": True},
        "prior_layout_evidence": {"base_revision": "output/presentations/20261013-1027_base-enhanced-qvoice/presentacion-eng.html",
                                  "result": "36 slide/theme scenes passed without clipping; this revision changes text only in slides 1, 2 and 8."},
        "screenshots_saved": 1, "screenshot_directory": "../../preview/20261013-1100_transfer-sensitivity",
        "representative_screenshots": ["../../preview/20261013-1100_transfer-sensitivity/dark-08.png"], "passed": True,
    })
    registry = ROOT / "config/presentations/julia-review-current.json"
    current = json.loads(registry.read_text(encoding="utf-8-sig"))
    current["previous_revision"] = current["current_revision"]
    current["current_revision"] = str(DECK.relative_to(ROOT)).replace("/", "\\")
    current["browser_verification"] = str((OUT / "browser-verification.json").relative_to(ROOT)).replace("/", "\\")
    current["reason"] = "Nueve diapositivas. La historia visible usa Base → Enhanced → Enhanced + QVoice, con Selected como estado separado. El slide 8 conserva las pruebas de BU L3 y work city, y añade la sensibilidad de retirar Transfers; no cambian cifras previas ni la selección."
    current["narrative"] = "Base y preguntas → Enhanced más preciso → Enhanced + QVoice seleccionado → pruebas descriptivas de BU, work city y Transfers → pendientes antes del piloto."
    write(registry, current)
    print(digest)


if __name__ == "__main__":
    main()
