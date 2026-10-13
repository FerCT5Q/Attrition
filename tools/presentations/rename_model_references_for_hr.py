"""Renombra los modelos del deck vigente con etiquetas comprensibles para RH."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output/presentations/20261013-0920_checks-panel-hr-language"
OUT = ROOT / "output/presentations/20261013-0949_model-names-for-hr"
TEMPLATE = Path(
    "C:/Users/fcarranz/.codex/skills/html-slide-generator/"
    "templates/fullscreen/base-fullscreen.html"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_numbers(html: str) -> Counter[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(x.get_text(" ", strip=True) for x in soup.select(".slide-stage"))
    return Counter(re.findall(r"(?<![A-Za-z])(?:[+−-]?\d[\d,]*(?:\.\d+)?(?:%| pp)?)", text))


def visible_content(soup: BeautifulSoup) -> str:
    pieces = [x.get_text(" ", strip=True) for x in soup.select(".slide-stage")]
    for element in soup.select(".slide-stage [aria-label], #slide-nav [aria-label]"):
        pieces.append(element.get("aria-label", ""))
    pieces.extend(x.get_text(" ", strip=True) for x in soup.select("#slide-nav [data-slide]"))
    return " ".join(pieces)


def main() -> None:
    source = BASE / "presentacion-eng.html"
    html = source.read_text(encoding="utf-8")
    original_numbers = visible_numbers(html)
    changes: list[dict[str, object]] = []

    def replace(old: str, new: str, minimum: int = 1) -> None:
        nonlocal html
        count = html.count(old)
        assert count >= minimum, (old, count)
        html = html.replace(old, new)
        changes.append({"before": old, "after": new, "occurrences": count})

    # Slide 1: decisión vigente.
    replace(
        "vs expanded HR (C) · CQ's average gap per group: ~1 exit per 100 people",
        "vs Enhanced HR · the selected model's average gap per group: ~1 exit per 100 people",
    )
    replace("compared with expanded HR (C)", "compared with Enhanced HR")
    replace(
        "HR + employee feedback (CQ). New BU and city results are on slide 8;",
        "Enhanced HR + QVoice (employee feedback). New BU and city results are on slide 8;",
    )

    # Slide 2: una progresión acumulativa, sin códigos internos.
    replace(
        "Core HR model B and the evidence path to CQ",
        "Base HR model and the path to the selected model",
    )
    replace(
        "Expanded HR model (C) and employee feedback (CQ)",
        "Enhanced HR model and QVoice",
    )
    replace("BU L3 with and without feedback; work city", "BU L3 with and without QVoice; work city")
    replace(
        "Work path: Core HR model B, then expanded HR model C, then HR plus employee feedback CQ, selected. Related tests branch off in grey.",
        "Work path: Base HR model, then Enhanced HR model, then Enhanced HR plus QVoice, selected. Related tests branch off in grey.",
    )
    replace('<div class="flow-node">Core HR (B)</div>', '<div class="flow-node">Base HR</div>')
    replace('<div class="flow-node">Expanded HR (C)</div>', '<div class="flow-node">Enhanced HR</div>')
    replace(
        'HR + feedback (CQ) <span class="mark m-yes">✓ Selected</span>',
        'Enhanced HR + QVoice <span class="mark m-yes">✓ Selected</span>',
    )

    # Slide 3: el punto de partida es el modelo base.
    replace("How the Core HR model (B) forms groups", "How the Base HR model forms groups")
    replace(
        "B splits all of Engineering by years at Qualcomm, then team exits, then level: 22 groups eligible, each with 300+ people",
        "The Base HR model splits Engineering by years at Qualcomm, then team exits, then level: 22 groups eligible, each with 300+ people",
    )
    replace("B used information HR already tracks.", "The Base HR model used information HR already tracks.")

    # Slide 4: por qué ganó Enhanced HR + QVoice.
    replace(
        "CQ combined a stronger HR base with useful QVoice signal",
        "The selected model combines Enhanced HR with QVoice",
    )
    replace(
        "The evidence path from Core HR (B) to the selected C + QVoice model",
        "The evidence path from Base HR to Enhanced HR + QVoice",
    )
    replace('<div class="pipe-num">Stronger HR base</div>', '<div class="pipe-num">Enhanced HR</div>')
    replace("C reduced estimation error while keeping the same groups", "Enhanced HR reduced estimation error while keeping the same groups")
    replace('<div class="pipe-num">Selected CQ</div>', '<div class="pipe-num">Selected model</div>')
    replace("CQ improved C across the headline measures", "Adding QVoice improved Enhanced HR across the headline measures")
    replace(
        "CQ was selected for its stronger overall balance: better ranking, lower loss and lower group estimation error.",
        "Enhanced HR + QVoice was selected for its stronger overall balance: better prioritization and lower estimation error.",
    )
    replace(
        "B→C uses 4 historical periods; C→CQ uses Aug–Dec 2025 and Jan–Feb 2026 · CQ improved capture in 2025 and tied C in Jan–Feb 2026;",
        "Base HR → Enhanced HR uses 4 historical periods; Enhanced HR → Enhanced HR + QVoice uses Aug–Dec 2025 and Jan–Feb 2026 · the selected model improved capture in 2025 and tied Enhanced HR in Jan–Feb 2026;",
    )
    replace("Compared with the Core HR model (B)", "Compared with the Base HR model")
    replace("Employee feedback test", "QVoice test")
    replace("Leading feedback option (Q4)", "Leading QVoice option (Q4)")
    replace("when feedback improved prioritization", "when QVoice improved prioritization")

    # Slide 5: comparación Base HR vs Enhanced HR.
    replace(
        "The expanded HR model kept the group definitions and cut the gap by 11%",
        "The Enhanced HR model kept the group definitions and cut the gap by 11%",
    )
    replace(
        "Core HR (B) vs Expanded HR (C) · same group definitions",
        "Base HR vs Enhanced HR · same group definitions",
    )
    replace(
        "Core HR model B versus expanded HR model C",
        "Base HR model versus Enhanced HR model",
    )
    replace('<th scope="col" class="num">Core HR (B)</th>', '<th scope="col" class="num">Base HR</th>')
    replace('<th scope="col" class="num rec">Expanded HR (C)</th>', '<th scope="col" class="num rec">Enhanced HR</th>')

    # Slide 6: el aporte incremental de QVoice.
    replace(
        "Adding employee feedback found modestly more exits in",
        "Adding QVoice found modestly more exits in",
    )
    replace(
        "Random 30% holds about 30% of exits; expanded HR model C 42.4%; HR plus feedback CQ 43.1%, +0.7 points more",
        "Random 30% holds about 30% of exits; Enhanced HR 42.4%; Enhanced HR plus QVoice 43.1%, +0.7 points more",
    )
    replace('<div class="blabel">Expanded HR (C)</div>', '<div class="blabel">Enhanced HR</div>')
    replace('<div class="blabel">HR + feedback (CQ)</div>', '<div class="blabel">Enhanced HR + QVoice</div>')
    replace(
        "CQ underestimated the overall rate by 0.3 pp.",
        "the selected model underestimated the overall rate by 0.3 pp.",
    )

    # Slide 7: composición del modelo elegido.
    replace("Feedback refines risk estimates within the same familiar groups", "QVoice refines risk estimates within the same familiar groups")
    replace("HR + employee feedback (CQ) · how the pieces fit", "Enhanced HR + QVoice · how the pieces fit")
    replace('<div class="st-head">Employee feedback</div>', '<div class="st-head">QVoice</div>')
    replace("Career goals · overall feedback · wellbeing · confidence", "Career goals · overall sentiment · wellbeing · confidence")
    replace(
        "HR information and employee feedback refine risk estimates for the same group definitions.",
        "HR information and QVoice responses refine risk estimates for the same group definitions.",
    )
    replace("<h3>CQ · Jan–Feb 2026</h3>", "<h3>Selected model · Jan–Feb 2026</h3>")
    replace("Missing feedback is a model state", "Missing QVoice data is a model state")
    replace(
        "Top: final September CQ structure; historical models used separate saved selections · Bottom: historical CQ, 6-month outcomes",
        "Top: final September selected-model structure; historical versions used separate saved selections · Bottom: selected-model historical results, 6-month outcomes",
    )

    # Slide 8: candidatos posteriores descritos por contenido, no por letras.
    replace(
        "C + BU alone does not beat CQ; city and feedback add value",
        "Later work-city tests improved estimates, but did not change the selected model",
    )
    replace(
        "Same tenure × team exits × level groups; BU only adjusts risk · lower log-loss is better",
        "Same group definitions · later tests add BU L3, work city or both · lower log-loss is better",
    )
    row_labels = {
        "C + QVoice (CQ) · selected": ('Selected model <span class="model-status">✓ Selected</span>', "Enhanced HR + QVoice"),
        "C + BU L3 · no QVoice": ("BU-only test", "Enhanced HR + BU L3"),
        "C + BU L3 + QVoice": ("BU + QVoice test", "Enhanced HR + BU L3 + QVoice"),
        "C + city + QVoice": ("Work-city test", "Enhanced HR + work city + QVoice"),
        "C + city + BU L3 + QVoice": ("Combined test", "Enhanced HR + work city + BU L3 + QVoice"),
    }
    for old, (name, composition) in row_labels.items():
        replace(
            f"<td>{old}</td>",
            f'<td class="model-name"><b>{name}</b><small>{composition}</small></td>',
        )
    replace(
        "BU added to C with the same training dates:",
        "BU added to Enhanced HR with the same training dates:",
    )
    replace(
        "Earlier RSF + QVoice tests did not improve CQ’s capture/error balance. Here, CQ retains its August HR fit in January; candidates use the January cutoff. CQ remains selected pending review.",
        "Earlier alternative-method + QVoice tests did not improve the selected model’s capture/error balance. The selected model retains its August HR fit in January; later candidates use the January cutoff. Enhanced HR + QVoice remains selected pending review.",
    )

    # Slide 9 y navegación.
    replace("Choose attention capacity · CQ", "Choose attention capacity · selected model")
    replace("Historical group card · CQ", "Historical group card · selected model")
    replace(">4. Evidence path to CQ<", ">4. Why the selected model won<")
    replace(">5. B vs C<", ">5. Base vs enhanced HR<")
    replace(">6. C vs CQ<", ">6. Enhanced HR + QVoice<")
    replace(">7. How CQ works<", ">7. How the selected model works<")

    css = """
    /* Descriptive model labels for an HR audience */
    #slide-8 td.model-name { min-width: 330px; }
    #slide-8 td.model-name b { display: block; color: var(--text-main); font-size: 15px; line-height: 1.15; }
    #slide-8 td.model-name small { display: block; margin-top: 3px; color: var(--text-muted); font-size: 12px; line-height: 1.2; }
    #slide-8 .model-status { margin-left: 7px; color: #15803d; font-size: 12px; white-space: nowrap; }
    body.theme-dark-royal #slide-8 .model-status,
    body.theme-dark-carbon #slide-8 .model-status { color: #4ade80; }
    """
    assert html.count("</style>") == 1
    html = html.replace("</style>", css + "\n  </style>")

    new = BeautifulSoup(html, "html.parser")
    assert len(new.select(".slide-stage")) == len(new.select(".nav-pill")) == 9
    assert visible_numbers(html) == original_numbers
    visible = visible_content(new)
    forbidden = ["CQ", "FQ", "(B)", "(C)", "B→C", "C→CQ", "Core HR", "Expanded HR"]
    assert not {term: visible.count(term) for term in forbidden if term in visible}
    feedback_hits = re.findall(r".{0,55}feedback.{0,75}", visible, flags=re.IGNORECASE)
    assert visible.lower().count("feedback") == 1, feedback_hits
    assert "QVoice (employee feedback)" in visible
    assert len(new.select("#slide4-checks .check-item")) == 8
    assert len(new.select("#slide4-checks .check-status.pass")) == 7
    assert len(new.select("#slide4-checks .check-status.fail")) == 1
    assert len(new.select("#slide-8 tbody tr")) == 5

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "presentacion-eng.html"
    shutil.copy2(TEMPLATE, target)
    target.write_text(html, encoding="utf-8")
    shutil.copy2(TEMPLATE, OUT / "template-origin.html")
    shutil.copytree(BASE / "historical-evidence", OUT / "historical-evidence", dirs_exist_ok=True)

    evidence = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))
    evidence.update(
        revision_base=str(source.relative_to(ROOT)),
        revision_base_sha256=sha(source),
        deck_sha256=sha(target),
        changes=changes,
        unchanged_slide_count=9,
        numeric_tokens_unchanged=True,
        model_selection_changed=False,
        visible_model_names={
            "B": "Base HR model",
            "C": "Enhanced HR model",
            "CQ": "Enhanced HR + QVoice model (selected)",
            "C_BU": "BU-only test — Enhanced HR + BU L3",
            "C_BU_Q": "BU + QVoice test — Enhanced HR + BU L3 + QVoice",
            "FQ": "Work-city test — Enhanced HR + work city + QVoice",
            "FQ_BU_L3": "Combined test — Enhanced HR + work city + BU L3 + QVoice",
        },
        projected_internal_codes=False,
        qvoice_wording="First mention: QVoice (employee feedback); later references: QVoice.",
        browser_verification=str((OUT / "browser-verification.json").relative_to(ROOT)),
        replaces_deliverable=str(source.relative_to(ROOT)),
    )
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "guion.md").write_text(
        "# Nombres de modelos para una audiencia de RH\n\n"
        "La progresión visible es `Base HR → Enhanced HR → Enhanced HR + QVoice`, "
        "con `Selected` como estado separado. Los códigos B, C, CQ y FQ se conservan "
        "únicamente en la evidencia técnica. Las pruebas posteriores se nombran por "
        "su contenido: BU L3, work city y combinación.\n\n"
        "Se conservaron las nueve diapositivas, cifras, periodos, fuentes, variantes, "
        "orden y decisión vigente. No se hicieron cálculos ni consultas nuevas.\n",
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
