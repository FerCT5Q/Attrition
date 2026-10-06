"""Consulta fuentes bibliográficas públicas y guarda trazabilidad de lectura.

Sólo GET HTTPS. Los PDF se analizan en memoria; no se guardan sus bytes ni
su texto completo. No consulta datos internos ni usa credenciales.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/research/attrition-literature/20260929-pending-review"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", choices=["P14", "P15", "P16", "P17", "P31", "P38", "P39", "P43"])
    parser.add_argument("kind", choices=["crossref", "openalex", "json", "html", "pdf"])
    parser.add_argument("target", help="DOI para Crossref/OpenAlex; URL HTTPS en otros casos")
    parser.add_argument("--pages", default="", help="Páginas PDF, por ejemplo 1-4,8")
    parser.add_argument("--limit", type=int, default=20000)
    parser.add_argument("--start", type=int, default=0, help="Desplazamiento para completar lecturas largas de HTML")
    args = parser.parse_args()
    url = args.target
    if args.kind == "crossref":
        url = "https://api.crossref.org/works/" + urllib.parse.quote(args.target, safe="")
    elif args.kind == "openalex":
        url = "https://api.openalex.org/works/https://doi.org/" + args.target
    if urllib.parse.urlsplit(url).scheme != "https":
        parser.error("Sólo se permiten fuentes HTTPS públicas.")
    fetched = datetime.now(timezone.utc)
    record = {
        "paper_id": args.paper,
        "classification": "presentation",
        "requested_url": url,
        "retrieved_at_utc": fetched.isoformat(),
        "source_kind": args.kind,
        "note": "Lectura bibliográfica pública; no contiene datos internos de empleados.",
    }
    body = b""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AttritionLiteratureReview/1.0 (public academic research)"})
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read(30 * 1024 * 1024 + 1)
            if len(body) > 30 * 1024 * 1024:
                raise ValueError("La respuesta excede el límite de 30 MB.")
            record.update(status=response.status, final_url=response.url,
                          content_type=response.headers.get("Content-Type"))
        record["sha256"] = hashlib.sha256(body).hexdigest()
        record["bytes"] = len(body)
        if args.kind in {"crossref", "openalex", "json"}:
            data = json.loads(body)
            if args.kind == "crossref":
                data = data["message"]
                keys = ["DOI", "title", "author", "published", "published-print", "published-online", "container-title", "volume", "issue", "page", "abstract", "link", "license", "relation", "update-to", "type", "publisher", "URL"]
                data = {key: data[key] for key in keys if key in data}
            elif args.kind == "openalex":
                index = data.get("abstract_inverted_index") or {}
                tokens = {position: word for word, positions in index.items() for position in positions}
                abstract = " ".join(tokens[p] for p in sorted(tokens))
                keys = ["id", "doi", "display_name", "publication_year", "publication_date", "type", "is_retracted", "open_access", "primary_location", "best_oa_location", "locations", "biblio", "authorships"]
                data = {key: data[key] for key in keys if key in data}
                data["abstract"] = abstract
            record["public_metadata"] = data
            output = json.dumps(data, ensure_ascii=False, indent=2)
        elif args.kind == "html":
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(body, "html.parser")
            record["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            record["citation_meta"] = [dict(tag.attrs) for tag in soup.find_all("meta") if "citation" in str(tag.attrs) or "dc." in str(tag.attrs).lower()]
            record["links"] = [{"text": a.get_text(" ", strip=True), "url": urllib.parse.urljoin(record["final_url"], a.get("href", ""))} for a in soup.find_all("a", href=True)]
            for node in soup(["script", "style", "nav", "footer", "header"]):
                node.decompose()
            output = soup.get_text("\n", strip=True)
            record["content_note"] = "HTML leído; texto completo no persistido. El análisis propio se guarda en la ficha del paper."
        else:
            if not body.lstrip().startswith(b"%PDF"):
                raise ValueError("La respuesta no es un PDF; puede ser una barrera editorial.")
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(body))
                page_count = len(reader.pages)
                extract_page = lambda n: reader.pages[n].extract_text()
            except ImportError:
                import fitz
                reader = fitz.open(stream=body, filetype="pdf")
                page_count = len(reader)
                extract_page = lambda n: reader[n].get_text()
            record["page_count"] = page_count
            selected = set()
            for item in filter(None, args.pages.split(",")):
                parts = item.split("-")
                start = int(parts[0])
                end = int(parts[-1])
                selected.update(range(start, end + 1))
            if not selected:
                selected.update(range(1, page_count + 1))
            selected = sorted(p for p in selected if 1 <= p <= page_count)
            record["pages_read"] = selected
            record["content_note"] = "PDF leído en memoria desde la URL pública. No se guardan PDF ni transcripción; consultar la síntesis propia y sus localizadores."
            output = "\n\n".join(f"[PÁGINA PDF {p}]\n{extract_page(p-1)}" for p in selected)
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, urllib.error.HTTPError):
            record["status"] = exc.code
        output = record["error"]
    folder = OUT / args.paper / "sources"
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", urllib.parse.urlsplit(url).netloc).strip("-")
    path = folder / f"{fetched.strftime('%Y%m%dT%H%M%S%fZ')}-{args.kind}-{slug}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in {"public_metadata", "links"}}, ensure_ascii=True))
    print("Registro: " + path.relative_to(ROOT).as_posix())
    print(output[args.start:args.start + args.limit].encode("ascii", "backslashreplace").decode("ascii"))
    if len(output) > args.start + args.limit:
        print(f"[Salida parcial: intervalo {args.start}-{args.start + args.limit} de {len(output)} caracteres; seleccionar páginas o --start para completar la lectura.]")


if __name__ == "__main__":
    main()
