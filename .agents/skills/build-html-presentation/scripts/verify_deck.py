"""Comprobaciones estáticas de un deck HTML del proyecto Attrition.

No sustituye la revisión en navegador: verifica estructura de la plantilla
html-slide-generator, idioma, clasificación del entregable, dependencias y
señales de contenido pendiente o de privacidad.

Uso:
    python verify_deck.py <deck.html> [--mode presentation|internal_analysis]
Sale con código 1 si hay errores.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

THEMES = ("theme-light-classic", "theme-light-soft", "theme-dark-royal", "theme-dark-carbon")
PLACEHOLDERS = ("[Slide Title]", "[Subtitle", "[First Slide Title]", "[content here]", "Lorem ipsum")
ALLOWED_SCRIPT_HOSTS = ("cdn.plot.ly",)
SENSITIVE_KEYS = re.compile(
    r"""["']?(employee_id|emp_id|worker_id|employee_name|full_name|email|e_mail|"""
    r"""home_address|street_address|birth_date|date_of_birth|base_pay|salary)["']?\s*:""",
    re.IGNORECASE,
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def check(html: str, mode: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    # Los comentarios de la plantilla contienen ejemplos de marcado; no cuentan.
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

    stages = re.findall(r'<div[^>]*class="[^"]*\bslide-stage\b[^"]*"[^>]*>', html)
    stage_ids = [re.search(r'id="([^"]+)"', s).group(1) for s in stages if re.search(r'id="([^"]+)"', s)]
    pills = [int(v) for v in re.findall(r'class="[^"]*\bnav-pill\b[^"]*"[^>]*data-slide="(\d+)"', html)]
    pills += [int(v) for v in re.findall(r'data-slide="(\d+)"[^>]*class="[^"]*\bnav-pill\b', html)]

    if not stages:
        errors.append("No hay elementos .slide-stage.")
    if len(stage_ids) != len(stages):
        errors.append("Algún .slide-stage no tiene id.")
    if len(set(stage_ids)) != len(stage_ids):
        errors.append("Hay ids de .slide-stage duplicados.")
    if sorted(pills) != list(range(len(stages))):
        errors.append(
            f"nav-pill data-slide {sorted(pills)} no coincide con {len(stages)} diapositivas (0..{len(stages) - 1})."
        )
    if len(stages) >= 4 and not re.search(r"agenda|contenido|índice", html, re.IGNORECASE):
        warnings.append("Deck de 4+ diapositivas sin agenda aparente (válido sólo si se acordó omitirla).")

    for theme in THEMES:
        if f'data-theme="{theme}"' not in html:
            errors.append(f"Falta el botón de tema {theme}.")
    if "slide-studio-theme" not in html:
        errors.append("Falta la clave localStorage 'slide-studio-theme' (bloque JS base modificado).")
    if "function fitSlide" not in html or "showSlide(0)" not in html:
        errors.append("Falta fitSlide/showSlide(0) del bloque JS base.")
    if "app-header" in html:
        errors.append("Contiene .app-header; la plantilla no usa navbar.")
    if re.search(r"\.slide-stage\s*\{[^}]*overflow\s*:\s*visible", html):
        errors.append(".slide-stage con overflow: visible.")

    lang = re.search(r"<html[^>]*\blang=\"([^\"]+)\"", html)
    if not lang or not lang.group(1).lower().startswith("es"):
        errors.append('El elemento <html> debe declarar lang="es".')

    meta = re.search(r'<meta\s+name="deliverable-classification"\s+content="([^"]+)"', html)
    if not meta:
        errors.append('Falta <meta name="deliverable-classification" content="presentation|internal_analysis">.')
    else:
        declared = meta.group(1)
        if declared not in ("presentation", "internal_analysis"):
            errors.append(f"Clasificación desconocida: {declared}.")
        if mode and declared != mode:
            errors.append(f"Clasificación declarada {declared} distinta de la esperada {mode}.")
        if declared == "internal_analysis" and not re.search(r"an[áa]lisis interno", html, re.IGNORECASE):
            errors.append("Entregable internal_analysis sin marca visible de «análisis interno».")

    for src in re.findall(r"<script[^>]*\bsrc=\"([^\"]+)\"", html):
        if src.startswith(("http://", "https://", "//")) and not any(h in src for h in ALLOWED_SCRIPT_HOSTS):
            errors.append(f"Script externo no permitido: {src}")
    for href in re.findall(r"<link[^>]*\bhref=\"(https?://[^\"]+)\"", html):
        errors.append(f"Recurso externo no permitido: {href}")
    if "cdn.plot.ly" in html:
        warnings.append("Usa Plotly por CDN: requiere internet; decláralo en la entrega.")
        if "connectgaps: true" in html.replace("'", "").replace('"', ""):
            errors.append("Plotly con connectgaps: true oculta periodos faltantes.")
    for src in re.findall(r"<img[^>]*\bsrc=\"([^\"]+)\"", html):
        if not src.startswith("data:"):
            errors.append(f"Imagen no embebida (rompe el archivo único): {src}")

    for token in PLACEHOLDERS:
        if token in html:
            errors.append(f"Queda contenido de ejemplo: {token}")
    for label in (">Theme<", ">Slides<", ">Navigation<"):
        if label in html:
            warnings.append(f"Etiqueta visible en inglés: {label.strip('><')}")

    if SENSITIVE_KEYS.search(html):
        errors.append("Aparece una clave de dato sensible a nivel persona en el HTML o su JavaScript.")
    emails = {e for e in EMAIL.findall(html) if not e.endswith((".png", ".svg"))}
    if emails:
        errors.append(f"Aparecen {len(emails)} direcciones de correo en el HTML.")

    visible = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    visible = re.sub(r"<[^>]+>", " ", visible)
    # es-MX usa punto decimal y coma de miles: 2,484 es un entero válido.
    long_decimals = re.findall(r"(?<![\w.#-])\d+\.\d{2,}(?![\d.])\s*%?", visible)
    if long_decimals:
        warnings.append(
            f"{len(long_decimals)} cifras visibles con 2+ decimales (p. ej. {long_decimals[0].strip()})."
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("deck", type=Path)
    parser.add_argument("--mode", choices=("presentation", "internal_analysis"))
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    errors, warnings = check(args.deck.read_text(encoding="utf-8"), args.mode)
    for w in warnings:
        print(f"AVISO: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} errores, {len(warnings)} avisos.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
