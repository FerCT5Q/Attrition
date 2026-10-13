"""Create the next review deck using concise, audience-facing model names.

This is intentionally a narrow transformation: it copies the approved
nine-slide review deck, changes only model/comparison labels, and records the
provenance of the new delivery.  It does not alter the selected estimator,
sources, metrics, periods, slide count, or interactive behaviour.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/presentations/20261013-0949_model-names-for-hr"
OUT = ROOT / "output/presentations/20261013-1027_base-enhanced-qvoice"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing delivery: {OUT}")
    shutil.copytree(SOURCE, OUT)

    deck = OUT / "presentacion-eng.html"
    html = deck.read_text(encoding="utf-8")
    replacements = [
        ("Enhanced HR + work city + BU L3 + QVoice", "Enhanced + work city + BU L3 + QVoice"),
        ("Enhanced HR + work city + QVoice", "Enhanced + work city + QVoice"),
        ("Enhanced HR + BU L3 + QVoice", "Enhanced + BU L3 + QVoice"),
        ("Enhanced HR + QVoice", "Enhanced + QVoice"),
        ("Enhanced HR + BU L3", "Enhanced + BU L3"),
        ("Enhanced HR model", "Enhanced model"),
        ("Enhanced HR", "Enhanced"),
        ("enhanced HR", "Enhanced"),
        ("Base HR model", "Base model"),
        ("Base HR", "Base"),
        ("same HR model", "same Base model"),
        ("updating the HR fit", "updating the base"),
        ("August HR fit", "August base"),
        ("Evolución B → CQ", "Model evolution"),
    ]
    applied: list[dict[str, object]] = []
    for before, after in replacements:
        count = html.count(before)
        if count:
            html = html.replace(before, after)
            applied.append({"before": before, "after": after, "occurrences": count})
    deck.write_text(html, encoding="utf-8")

    prohibited = ["Base HR", "Enhanced HR", "same HR model", "updating the HR fit", "August HR fit"]
    remaining = [phrase for phrase in prohibited if phrase in html]
    if remaining:
        raise AssertionError(f"Model labels still contain redundant HR: {remaining}")
    if html.count('<div class="slide-stage') != 9:
        raise AssertionError("The delivery must retain exactly nine slides")
    if "Enhanced + QVoice <span class=\"mark m-yes\">✓ Selected</span>" not in html:
        raise AssertionError("Selected label was lost")

    evidence_path = OUT / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    evidence["revision_base"] = str(SOURCE.relative_to(ROOT) / "presentacion-eng.html").replace("/", "\\")
    evidence["revision_base_sha256"] = sha256(SOURCE / "presentacion-eng.html")
    evidence["deck_sha256"] = sha256(deck)
    evidence["replaces_deliverable"] = str(SOURCE.relative_to(ROOT) / "presentacion-eng.html").replace("/", "\\")
    evidence["audience_facing_model_names"] = {
        "base": "Base",
        "enhanced": "Enhanced",
        "selected": "Enhanced + QVoice",
        "note": "‘HR’ was removed only from model labels; generic references to HR roles and information remain.",
    }
    evidence["model_selection_changed"] = False
    evidence["changes"] = applied
    write_json(evidence_path, evidence)

    (OUT / "guion.md").write_text(
        "# Guion de entrega\n\n"
        "Clasificación: `presentation`. Audiencia: equipo de People/HR.\n\n"
        "La historia conserva nueve diapositivas y la selección vigente: **Base → Enhanced → Enhanced + QVoice**. "
        "Este ajuste elimina la redundancia ‘HR’ de los nombres de modelos; no cambia cifras, fuentes, periodos, variantes ni la decisión de selección.\n",
        encoding="utf-8",
    )
    print(OUT)
    print(f"Applied {len(applied)} label replacements; deck SHA-256 {evidence['deck_sha256']}")


if __name__ == "__main__":
    main()
