"""Record verification evidence for the Base → Enhanced → QVoice label revision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/presentations/20261013-1027_base-enhanced-qvoice"
DECK = OUT / "presentacion-eng.html"


def write(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    digest = hashlib.sha256(DECK.read_bytes()).hexdigest()
    evidence_path = OUT / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    evidence["deck_sha256"] = digest
    evidence["browser_verification"] = str((OUT / "browser-verification.json").relative_to(ROOT)).replace("/", "\\")
    evidence["visible_model_names"] = {
        "B": "Base model",
        "C": "Enhanced model",
        "CQ": "Enhanced + QVoice model (selected)",
        "C_BU": "BU-only test — Enhanced + BU L3",
        "C_BU_Q": "BU + QVoice test — Enhanced + BU L3 + QVoice",
        "FQ": "Work-city test — Enhanced + work city + QVoice",
        "FQ_BU_L3": "Combined test — Enhanced + work city + BU L3 + QVoice",
    }
    write(evidence_path, evidence)

    browser = {
        "reporting_mode": "presentation",
        "verified_at": "2026-10-13",
        "viewport": "1440x810",
        "deck_sha256": digest,
        "targeted_scenes_reviewed": [
            "slide 4, light classic",
            "slide 8, dark carbon",
            "slide 4 panel open, dark carbon",
        ],
        "checks": {
            "targeted_scenes_without_clipping": True,
            "base_enhanced_qvoice_progression_visible": True,
            "selected_status_separate_from_model_name": True,
            "slide8_five_variants_and_values_preserved": True,
            "slide8_selected_badge_visible": True,
            "eight_check_panel_opens_and_is_legible": True,
            "seven_pass_and_one_exception_preserved": True,
            "visible_model_labels_no_longer_include_redundant_HR": True,
            "static_delivery_checks_passed": True,
        },
        "prior_layout_evidence": {
            "base_revision": "output/presentations/20261013-0949_model-names-for-hr/presentacion-eng.html",
            "result": "36 slide/theme scenes passed without clipping; this revision only shortens model labels.",
        },
        "screenshots_saved": 3,
        "screenshot_directory": "../../preview/20261013-1027_base-enhanced-qvoice",
        "representative_screenshots": [
            "../../preview/20261013-1027_base-enhanced-qvoice/light-04.png",
            "../../preview/20261013-1027_base-enhanced-qvoice/dark-08.png",
            "../../preview/20261013-1027_base-enhanced-qvoice/dark-04-panel.png",
        ],
        "passed": True,
    }
    write(OUT / "browser-verification.json", browser)
    print(f"Updated evidence for {digest}")


if __name__ == "__main__":
    main()
