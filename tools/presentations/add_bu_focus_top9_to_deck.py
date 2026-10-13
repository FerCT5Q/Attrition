"""Añade el resultado agregado de BU Focus al slide 8, sin alterar las nueve diapositivas."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/presentations/20261013-1215_b-reference"
OUT = ROOT / "output/presentations/20261013-1305_bu-focus-top9"
RESULTS = ROOT / "output/analysis/engineering/20261013/model-j-bu-top9-without-transfers-v4/results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite a delivery: {OUT}")
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    s = data["summary"]
    jq, cq = s["JQ"], s["CQ"]
    if round(jq["global"]["log_loss"] * 1000, 1) != 137.5 or round(cq["global"]["log_loss"] * 1000, 1) != 137.7:
        raise AssertionError("Unexpected J/CQ evidence.")
    shutil.copytree(SOURCE, OUT)
    deck = OUT / "presentacion-eng.html"
    html = deck.read_text(encoding="utf-8")
    before = ("Base comparison: in these two periods, Base captured 41.6% vs 42.4% for Enhanced; its group gap was 0.8 vs 1.0 per 100 people. Removing Transfers from Enhanced raised log-loss from 138.8 to 140.5 and reduced exits captured from 42.4% to 41.6%. Removing it from Enhanced + QVoice raised log-loss from 137.7 to 139.4 and reduced exits captured from 43.1% to 42.4%. Enhanced + QVoice remains selected.")
    after = ("BU Focus test: removing Transfers and using BU L3 Top 9 + Other gave 137.5 vs 137.7 log-loss x 1,000 with QVoice. In the shared 10-BU groups, it matched 32.6% exits captured at 30% capacity and reduced the group gap to 0.5 vs 0.7 pp. This uses a different group definition, so it does not replace the 43.1% capture shown above. Enhanced + QVoice remains selected.")
    if html.count(before) != 1:
        raise AssertionError("Expected one Slide 8 note.")
    html = html.replace(before, after)
    html = html.replace("J03, S12, H01, B01 · Retrospective comparisons", "J03, S12, H01, B01, J04 · Retrospective comparisons")
    if html.count('<div class="slide-stage') != 9:
        raise AssertionError("Slide count changed.")
    deck.write_text(html, encoding="utf-8")
    evidence = {
        "reporting_mode": "presentation",
        "revision_base": str((SOURCE / "presentacion-eng.html").relative_to(ROOT)).replace("/", "\\\\"),
        "revision_base_sha256": sha(SOURCE / "presentacion-eng.html"),
        "sources": {"J04": {"path": str(RESULTS.relative_to(ROOT)).replace("/", "\\\\"), "sha256": sha(RESULTS)}},
        "change": "Slide 8 only: adds BU Focus (J + QVoice) Top 9 + Other result; nine slides preserved.",
        "model_selection_changed": False,
        "deck_sha256": sha(deck),
    }
    write(OUT / "evidence.json", evidence)
    print(OUT)


if __name__ == "__main__":
    main()
