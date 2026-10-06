"""Comprueba la lámina 8 con períodos parciales en los cuatro temas."""
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import audit_acquisition_internal_slide as previous
import build_distribution_html_v10 as builder

OUTPUT = builder.PREVIEW.parent

EXTRA_JS = """(() => {
 const s=document.getElementById('slide-acquisition');
 const details=s.querySelector('.v8-acquisition-details');
 const last=s.querySelector('tbody tr:last-child').getBoundingClientRect();
 const legend=s.querySelector('.v8-acquisition-legend').getBoundingClientRect();
 return {
   rows:[...s.querySelectorAll('tbody tr')].map(r=>({
     label:r.dataset.acquisitionLabel, kind:r.dataset.windowKind, start:r.dataset.startDate,
     rate:r.querySelector('.v8-acquisition-rate').textContent.trim(),
     counts:r.querySelector('.v9-rate-counts')?.textContent.trim()||null,
     months:r.querySelector('.v10-period > span').textContent.trim(),
     date:r.querySelector('.v10-period small').textContent.trim(),
     neutral:r.querySelector('.v8-acquisition-rate').classList.contains('v8-reference-unavailable'),
     tooltip:r.querySelector('.v8-acquisition-rate').title,
     cells:r.children.length
   })),
   row_ends_before_legend:last.bottom<=legend.top+1,
   legend_inside_panel:legend.bottom<=details.getBoundingClientRect().bottom-4,
   legend:s.querySelector('.v8-acquisition-legend').textContent,
   reference:s.querySelector('.v9-internal-source p').textContent,
   errors:window.__auditErrors||[],
   english_tooltips:[...s.querySelectorAll('[title],[aria-label]')].map(e=>(e.title||'')+' '+(e.getAttribute('aria-label')||'')).filter(t=>/\\b(?:voluntary exits|employees at|Suppressed)\\b/.test(t))
 };
})()"""


def main() -> None:
    evidence = builder.read_json(builder.EVIDENCE)
    expected = {r["category_label"]: r for r in evidence["periods"]}
    annual = builder.read_json(builder.v9.EVIDENCE)
    expected_annual = [builder.rate_text(r["annual_attrition_rate_percent"]) for r in annual["overall_distribution"]]
    expected_annual += [builder.rate_text(r["annual_attrition"]["annual_attrition_rate_percent"]) for r in annual["top_acquisitions"] if r["annual_attrition"]["annual_attrition_rate_percent"] is not None]
    cases = []
    with tempfile.TemporaryDirectory(prefix="browser-audit-", dir=OUTPUT) as profile:
        profile_path = Path(profile).resolve()
        if not profile_path.is_relative_to(OUTPUT.resolve()):
            raise ValueError("El perfil debe permanecer en la carpeta de revisión.")
        process = subprocess.Popen([
            str(previous.BROWSER), "--headless=new", "--disable-gpu", "--no-first-run",
            "--remote-debugging-port=0", f"--user-data-dir={profile_path}", builder.OUTPUT.as_uri(),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        client = None
        try:
            client = previous.DevToolsSocket(previous.browser_target(previous.wait_for_port(profile_path)))
            client.command("Page.addScriptToEvaluateOnNewDocument", {"source": "window.__auditErrors=[]; window.addEventListener('error', e=>{if(e.message) window.__auditErrors.push(e.message)});"})
            client.command("Page.navigate", {"url": builder.OUTPUT.as_uri()})
            previous.wait_for_page_ready(client)
            navigation = previous.evaluate(client, """(() => {
              const stages=[...document.querySelectorAll('.slide-stage')];
              return [...document.querySelectorAll('#slide-nav .nav-pill')].map((b,i)=>{
                b.click(); return stages.filter(s=>getComputedStyle(s).display!=='none').length===1 && getComputedStyle(stages[i]).display!=='none';
              });
            })()""")
            for width, height in ((1440, 810), (1280, 720), (1920, 1080)):
                client.command("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
                for theme in previous.THEMES:
                    previous.evaluate(client, f"""(async () => {{
                      document.querySelector('#theme-selector [data-theme="{theme}"]').click();
                      document.querySelector('#slide-nav [data-slide="7"]').click();
                      await document.fonts.ready;
                      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                    }})()""")
                    observed = previous.evaluate(client, previous.AUDIT_JS)
                    extra = previous.evaluate(client, EXTRA_JS)
                    partials = [r for r in extra["rows"] if r["label"] in expected]
                    checks = {
                        "navegacion_completa": len(navigation) == 44 and all(navigation),
                        "tasas_anuales_conservadas": [r["value"] for r in observed["rates"]] == expected_annual,
                        "tasas_parciales_y_periodos": len(partials) == 5 and all(r["rate"] == expected[r["label"]]["display_rate"] and r["months"] == expected[r["label"]]["display_months"] and r["start"] == expected[r["label"]]["start_snapshot_date"] and r["date"] == builder.short_date(r["start"]) for r in partials),
                        "conteos_parciales": all(r["counts"] == f'{expected[r["label"]]["voluntary_exit_count"]:,} / {expected[r["label"]]["baseline_employee_count"]:,}' for r in partials if r["kind"] == "partial_period"),
                        "periodos_no_comparables_en_gris": all(r["neutral"] for r in partials),
                        "cohorte_naps_explicita": "cohorte inicial de 4 empleados" in extra["legend"],
                        "sin_cero_ficticio": sum(r["kind"] == "no_followup" and r["rate"] == "—" and r["counts"] is None for r in partials) == 1,
                        "sin_recortes": not observed["text_outside_stage"] and not observed["overflowing_cells"],
                        "sin_superposicion": extra["row_ends_before_legend"] and extra["legend_inside_panel"],
                        "colores_anuales": all(r["semantic_style_applied"] for r in observed["rates"]),
                        "referencias_visibles": "5.5%" in extra["reference"] and "3.1%" in extra["reference"] and "0.5 puntos" in extra["reference"],
                        "columnas_y_idioma": all(r["cells"] == 6 for r in extra["rows"]) and observed["stage_language"] == "es" and not extra["english_tooltips"],
                        "etiquetas_legibles": observed["minimum_body_font_px"] >= 12,
                        "distribucion_actual_conservada": observed["current_shares"] == ["15.4%", "84.6%"] and sum(r["employees"] for r in observed["table_rows"]) == 7711,
                        "sin_errores_javascript": not extra["errors"],
                    }
                    record = {"theme": theme, "viewport": [width, height], "checks": checks,
                              "observed": observed, "period_details": extra,
                              "outcome": "pass" if all(checks.values()) else "fail"}
                    if width == 1440:
                        screenshot = OUTPUT / f"slide-8-{theme}.png"
                        screenshot.write_bytes(base64.b64decode(client.command("Page.captureScreenshot", {"format": "png"})["data"]))
                        record["screenshot"] = builder.relative(screenshot)
                    cases.append(record)
        finally:
            if client:
                client.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    report = {"artifact_classification": "internal_analysis", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "deck": builder.relative(builder.OUTPUT), "deck_sha256": builder.digest(builder.OUTPUT),
              "authorization": evidence["authorization"], "cases": cases,
              "outcome": "pass" if all(c["outcome"] == "pass" for c in cases) else "fail"}
    path = OUTPUT / "visual-validation.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    print(json.dumps({"report": builder.relative(path), "outcome": report["outcome"],
                      "failed": [{"theme": c["theme"], "viewport": c["viewport"], "checks": [k for k,v in c["checks"].items() if not v]} for c in cases if c["outcome"] != "pass"]}, ensure_ascii=True))
    if report["outcome"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
