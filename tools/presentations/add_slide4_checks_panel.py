"""Añade al slide 4 un panel desplegable con las ocho comprobaciones QVoice."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output/presentations/20261013-0850_cq-mejoras-slide4"
OUT = ROOT / "output/presentations/20261013-0920_checks-panel-hr-language"
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

    s05_path = (
        ROOT
        / "output/analysis/engineering/20261008/"
        "qvoice-model-b-annual-lag-v2/comparison-results.json"
    )
    s05 = json.loads(s05_path.read_text(encoding="utf-8"))
    q4 = next(v for v in s05["variants"] if v["id"] == "intent_q4")
    checks = q4["decision"]["checks"]
    assert sum(checks.values()) == 7
    assert checks == {
        "ranking_vs_control": True,
        "brier_score_vs_control": True,
        "calibration_error_pp_vs_control": False,
        "top_quintile_calibration_error_pp_vs_control": True,
        "ranking_vs_availability": True,
        "brier_score_vs_availability": True,
        "calibration_error_pp_vs_availability": True,
        "top_quintile_calibration_error_pp_vs_availability": True,
    }

    changes: list[dict[str, str]] = []

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
        "#slide-4 .st4:first-child .st4-row:nth-child(3) span:last-child",
        "All 9 options improved prioritization and kept overall estimates at least as accurate",
    )
    replace(
        "#slide-4 .st4:first-child .st4-row:nth-child(4) span:last-child",
        "Only exception: the average risk estimate was slightly farther from what happened",
    )

    first_source = """
      <div class="check-actions">
        <button class="check-toggle" type="button" data-checks-open
          aria-controls="slide4-checks" aria-expanded="false">See the 8 checks</button>
        <span>S05</span>
      </div>
    """
    replace("#slide-4 .st4:first-child .st4-src", first_source)

    panel = """
      <div class="check-overlay" id="slide4-checks" hidden role="dialog"
        aria-modal="true" aria-labelledby="slide4-checks-title">
        <article class="check-panel">
          <div class="check-head">
            <div>
              <div class="pipe-num">Employee feedback test</div>
              <h3 id="slide4-checks-title">What the 8 checks asked</h3>
              <p>Leading feedback option (Q4) · Aug–Dec 2025 and Jan–Feb 2026</p>
            </div>
            <button class="check-close" type="button" data-checks-close
              aria-label="Close the eight checks panel">Close ×</button>
          </div>
          <div class="check-grid">
            <section class="check-col" aria-labelledby="checks-vs-b">
              <h4 id="checks-vs-b">Compared with the Core HR model (B)</h4>
              <div class="check-item">
                <span class="check-num">1</span><span class="check-status pass">✓</span>
                <div><b>Quality of the priority list</b><span>It prioritized more people who later left, in both periods.</span></div>
              </div>
              <div class="check-item">
                <span class="check-num">2</span><span class="check-status pass">✓</span>
                <div><b>Overall estimate accuracy</b><span>Its overall estimates were at least as close to what happened.</span></div>
              </div>
              <div class="check-item check-fail">
                <span class="check-num">3</span><span class="check-status fail">✕</span>
                <div><b>Average risk estimate</b><span>Its average estimate was slightly farther from what happened.</span></div>
              </div>
              <div class="check-item">
                <span class="check-num">4</span><span class="check-status pass">✓</span>
                <div><b>Highest-priority group</b><span>Its estimates for this group were at least as close to what happened.</span></div>
              </div>
            </section>
            <section class="check-col" aria-labelledby="checks-vs-availability">
              <h4 id="checks-vs-availability">Compared with knowing only whether survey data existed</h4>
              <div class="check-item">
                <span class="check-num">5</span><span class="check-status pass">✓</span>
                <div><b>Quality of the priority list</b><span>It prioritized more people who later left, in both periods.</span></div>
              </div>
              <div class="check-item">
                <span class="check-num">6</span><span class="check-status pass">✓</span>
                <div><b>Overall estimate accuracy</b><span>Its overall estimates were at least as close to what happened.</span></div>
              </div>
              <div class="check-item">
                <span class="check-num">7</span><span class="check-status pass">✓</span>
                <div><b>Average risk estimate</b><span>Its average estimate stayed at least as close to what happened.</span></div>
              </div>
              <div class="check-item">
                <span class="check-num">8</span><span class="check-status pass">✓</span>
                <div><b>Highest-priority group</b><span>Its estimates for this group were at least as close to what happened.</span></div>
              </div>
            </section>
          </div>
          <p class="check-note"><b>Second comparison:</b> the same HR model knew whether survey data existed, but did not use employees' answers. A check passed when feedback improved prioritization in both periods or kept estimates at least as close to what happened. · S05</p>
        </article>
      </div>
    """
    current = BeautifulSoup(html, "html.parser")
    slide4 = current.select_one("#slide-4")
    assert slide4 is not None
    before_slide = str(slide4)
    revised_slide = BeautifulSoup(before_slide, "html.parser").find()
    revised_slide.append(BeautifulSoup(panel, "html.parser"))
    assert html.count(before_slide) == 1
    html = html.replace(before_slide, str(revised_slide))
    changes.append({"selector": "#slide-4", "after": "Added the eight-check overlay."})

    css = """
    /* Slide 4: eight-check disclosure panel */
    .check-actions { margin-top: auto; display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .check-actions > span { font-size: 13px; color: var(--text-muted); }
    .check-toggle, .check-close {
      appearance: none; border: 1px solid color-mix(in oklab, var(--accent) 45%, var(--border-subtle));
      background: color-mix(in oklab, var(--accent) 11%, var(--bg-surface)); color: var(--accent);
      border-radius: var(--radius-pill); padding: 7px 12px; font: 700 14px var(--font-main); cursor: pointer;
    }
    .check-toggle:hover, .check-toggle:focus-visible, .check-close:hover, .check-close:focus-visible {
      background: color-mix(in oklab, var(--accent) 20%, var(--bg-surface)); outline: 2px solid var(--accent); outline-offset: 2px;
    }
    .check-overlay {
      position: absolute; inset: 0; z-index: 80; display: grid; place-items: center; padding: 70px 54px 38px;
      background: color-mix(in oklab, #000 38%, transparent);
    }
    .check-overlay[hidden] { display: none; }
    .check-panel {
      width: 100%; max-width: 1260px; background: var(--bg-surface); color: var(--text-main);
      border: 1px solid var(--border-strong); border-radius: 18px; padding: 22px 26px 18px;
      box-shadow: 0 20px 60px rgba(0,0,0,.28); display: flex; flex-direction: column; gap: 15px;
    }
    .check-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
    .check-head h3 { margin: 3px 0 2px; font-size: 27px; line-height: 1.15; }
    .check-head p { margin: 0; color: var(--text-muted); font-size: 15px; }
    .check-close { flex-shrink: 0; }
    .check-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .check-col { border: 1px solid var(--border-subtle); border-radius: 13px; padding: 14px; background: var(--bg-surface-2); }
    .check-col h4 { margin: 0 0 10px; font-size: 18px; color: var(--accent); }
    .check-item { display: grid; grid-template-columns: 27px 28px 1fr; gap: 7px; align-items: start; padding: 8px 7px; border-top: 1px solid var(--border-subtle); }
    .check-col .check-item:nth-of-type(1) { border-top: none; }
    .check-num { width: 25px; height: 25px; border-radius: 50%; display: grid; place-items: center; background: var(--accent-soft); color: var(--accent); font-size: 13px; font-weight: 800; }
    .check-status { font-size: 19px; line-height: 1.2; font-weight: 800; }
    .check-status.pass { color: #16a34a; }
    .check-status.fail { color: #d97706; }
    .check-item b { display: block; font-size: 16px; line-height: 1.2; }
    .check-item div span { display: block; margin-top: 2px; color: var(--text-muted); font-size: 14px; line-height: 1.3; }
    .check-item.check-fail { background: color-mix(in oklab, #d97706 9%, var(--bg-surface)); border-radius: 8px; }
    .check-note { margin: 0; color: var(--text-muted); font-size: 13px; line-height: 1.35; }
    .check-note b { color: var(--text-main); }
    """
    assert html.count("</style>") == 1
    html = html.replace("</style>", css + "\n  </style>")

    script = """
  <script>
    (function () {
      var openButton = document.querySelector('[data-checks-open]');
      var overlay = document.getElementById('slide4-checks');
      var closeButton = overlay && overlay.querySelector('[data-checks-close]');
      if (!openButton || !overlay || !closeButton) return;
      function setOpen(open, restoreFocus) {
        overlay.hidden = !open;
        openButton.setAttribute('aria-expanded', String(open));
        if (open) closeButton.focus();
        else if (restoreFocus !== false) openButton.focus();
      }
      openButton.addEventListener('click', function () { setOpen(true); });
      closeButton.addEventListener('click', function () { setOpen(false); });
      overlay.addEventListener('click', function (event) {
        if (event.target === overlay) setOpen(false);
      });
      document.addEventListener('keydown', function (event) {
        if (overlay.hidden) return;
        if (event.key === 'Escape') {
          event.preventDefault(); event.stopImmediatePropagation(); setOpen(false); return;
        }
        if (['ArrowRight','ArrowDown','ArrowLeft','ArrowUp','Home','End'].includes(event.key)) {
          event.preventDefault(); event.stopImmediatePropagation();
        }
      }, true);
      document.querySelectorAll('#slide-nav [data-slide]').forEach(function (button) {
        button.addEventListener('click', function () {
          if (!overlay.hidden) setOpen(false, false);
        }, true);
      });
    })();
  </script>
    """
    assert html.count("</body>") == 1
    html = html.replace("</body>", script + "\n</body>")

    new = BeautifulSoup(html, "html.parser")
    assert len(new.select(".slide-stage")) == len(new.select(".nav-pill")) == 9
    assert len(new.select("#slide4-checks .check-item")) == 8
    assert len(new.select("#slide4-checks .check-status.pass")) == 7
    assert len(new.select("#slide4-checks .check-status.fail")) == 1
    for number in [1, 2, 3, 5, 6, 7, 8, 9]:
        assert str(old.select_one(f"#slide-{number}")) == str(new.select_one(f"#slide-{number}"))

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
        unchanged_slides=[1, 2, 3, 5, 6, 7, 8, 9],
        slide4_checks_panel={
            "trigger": "See the 8 checks",
            "checks": checks,
            "passed": sum(checks.values()),
            "failed": len(checks) - sum(checks.values()),
            "source": str(s05_path.relative_to(ROOT)),
            "interaction": ["click trigger", "close button", "backdrop click", "Escape"],
        },
        browser_verification=str(
            (OUT / "browser-verification.json").relative_to(ROOT)
        ),
        replaces_deliverable=str(source.relative_to(ROOT)),
    )
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "guion.md").write_text(
        "# Panel desplegable de las ocho comprobaciones\n\n"
        "Modo `presentation`. El slide 4 conserva su lectura principal y añade un botón "
        "`See the 8 checks`. El panel muestra cuatro comprobaciones contra B y cuatro "
        "contra el control que sólo conoce disponibilidad QVoice. Siete cumplen y una "
        "no cumple: la estimación media quedó ligeramente más lejos de la tasa observada "
        "frente a B. El texto proyectado evita jerga estadística para una audiencia de RH.\n\n"
        "El panel se cierra con su botón, haciendo clic fuera o con Escape. No se hicieron "
        "nuevos cálculos ni consultas; la fuente es S05.\n",
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
