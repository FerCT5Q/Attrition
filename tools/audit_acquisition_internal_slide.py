"""Valida tasas y geometría de la lámina interna en Edge sin consultas de datos."""
from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import build_distribution_html_v9 as builder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/.tmp"))
from render_html_themes import DevToolsSocket, THEMES, browser_target, wait_for_page_ready, wait_for_port
from audit_acquisition_visual import AUDIT_JS, evaluate

OUTPUT = ROOT / "output/preview/acquisition-internal-20261005"
BROWSER = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence = builder.acquisition.load_json(builder.EVIDENCE)
    expected_rates = [builder.rate_text(row["annual_attrition_rate_percent"]) for row in evidence["overall_distribution"]]
    expected_rates += [builder.rate_text(row["annual_attrition"]["annual_attrition_rate_percent"])
                       for row in evidence["top_acquisitions"] if row["annual_attrition"]["annual_attrition_rate_percent"] is not None]
    results = []
    with tempfile.TemporaryDirectory(prefix="browser-audit-", dir=OUTPUT) as profile:
        profile_path = Path(profile).resolve()
        if not profile_path.is_relative_to(OUTPUT.resolve()):
            raise ValueError("El perfil temporal debe permanecer dentro de la carpeta de revisión.")
        process = subprocess.Popen([
            str(BROWSER), "--headless=new", "--disable-gpu", "--no-first-run",
            "--remote-debugging-port=0", f"--user-data-dir={profile_path}", builder.OUTPUT.as_uri(),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        client = None
        try:
            client = DevToolsSocket(browser_target(wait_for_port(profile_path)))
            client.command("Page.addScriptToEvaluateOnNewDocument", {"source": "window.__auditErrors=[]; window.addEventListener('error', e=>{if(e.message) window.__auditErrors.push(e.message)});"})
            client.command("Page.navigate", {"url": builder.OUTPUT.as_uri()})
            wait_for_page_ready(client)
            navigation = evaluate(client, """(() => {
              const stages = [...document.querySelectorAll('.slide-stage')];
              return [...document.querySelectorAll('#slide-nav .nav-pill')].map((b,i) => {
                b.click(); return stages.filter(s => getComputedStyle(s).display !== 'none').length === 1 &&
                getComputedStyle(stages[i]).display !== 'none';
              });
            })()""")
            for width, height in ((1440, 810), (1280, 720), (1920, 1080)):
                client.command("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
                for theme in THEMES:
                    evaluate(client, f"""(async () => {{
                      document.querySelector('#theme-selector [data-theme="{theme}"]').click();
                      document.querySelector('#slide-nav [data-slide="7"]').click();
                      await document.fonts.ready;
                      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                    }})()""")
                    observed = evaluate(client, AUDIT_JS)
                    extra = evaluate(client, """(() => {
                      const s=document.getElementById('slide-acquisition');
                      const details=s.querySelector('.v8-acquisition-details');
                      const last=s.querySelector('tbody tr:last-child').getBoundingClientRect();
                      const legend=s.querySelector('.v8-acquisition-legend').getBoundingClientRect();
                      return {
                        no_cohort:[...s.querySelectorAll('.v8-reference-unavailable')].filter(e=>e.textContent.trim()==='Sin cohorte').length,
                        counts:[...s.querySelectorAll('.v9-rate-counts')].map(e=>e.textContent.trim()),
                        row_ends_before_legend:last.bottom<=legend.top+1,
                        legend_inside_panel:legend.bottom<=details.getBoundingClientRect().bottom-4,
                        errors:window.__auditErrors||[],
                        english_tooltips:[...s.querySelectorAll('[title],[aria-label]')].map(e=>(e.title||'')+' '+(e.getAttribute('aria-label')||'')).filter(t=>/\b(?:voluntary exits|employees at|for Acquisition|Suppressed)\b/.test(t))
                      };
                    })()""")
                    checks = {
                        "navegacion_completa": len(navigation) == 44 and all(navigation),
                        "tasas_correctas": [r["value"] for r in observed["rates"]] == expected_rates,
                        "conteos_visibles": extra["counts"] == [f'{r["annual_attrition"]["voluntary_exit_count"]:,} / {r["annual_attrition"]["baseline_employee_count"]:,}' for r in evidence["top_acquisitions"] if r["annual_attrition"]["baseline_employee_count"]],
                        "sin_cohortes_inventadas": extra["no_cohort"] == 5 and observed["suppressed_count"] == 0,
                        "sin_recortes": not observed["text_outside_stage"] and not observed["overflowing_cells"],
                        "sin_superposicion": extra["row_ends_before_legend"] and extra["legend_inside_panel"],
                        "colores_por_referencia": all(r["semantic_style_applied"] for r in observed["rates"]),
                        "idioma_de_la_lamina": observed["stage_language"] == "es" and not extra["english_tooltips"],
                        "etiquetas_legibles": observed["minimum_body_font_px"] >= 12,
                        "proporciones_originales": observed["current_shares"] == ["15.4%", "84.6%"],
                        "sin_errores_javascript": not extra["errors"],
                    }
                    record = {"theme": theme, "viewport": [width, height], "checks": checks,
                              "observed": observed, "additional_observations": extra,
                              "outcome": "pass" if all(checks.values()) else "fail"}
                    if width == 1440:
                        screenshot = OUTPUT / f"slide-8-{theme}.png"
                        png = client.command("Page.captureScreenshot", {"format": "png"})
                        screenshot.write_bytes(base64.b64decode(png["data"]))
                        record["screenshot"] = builder.acquisition.relative_path(screenshot)
                    results.append(record)
        finally:
            if client:
                client.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    helper_path = ROOT / ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py"
    spec = importlib.util.spec_from_file_location("redshift_readonly_guard", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    readonly_ok = bool(helper.validate_readonly(builder.acquisition.SOURCE_SQL.read_text(encoding="utf-8")))
    validation = {
        "artifact_classification": "internal_analysis", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "deck": builder.acquisition.relative_path(builder.OUTPUT), "deck_sha256": builder.v8.digest(builder.OUTPUT),
        "authorization": evidence["authorization"], "redshift_readonly_guard": "pass" if readonly_ok else "fail",
        "cases": results, "outcome": "pass" if readonly_ok and all(r["outcome"] == "pass" for r in results) else "fail",
    }
    path = OUTPUT / "visual-validation.json"
    path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": builder.acquisition.relative_path(path), "outcome": validation["outcome"],
                      "failed": [{"theme": r["theme"], "viewport": r["viewport"], "checks": [k for k,v in r["checks"].items() if not v]} for r in results if r["outcome"] != "pass"]}, ensure_ascii=False))
    if validation["outcome"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
