"""Archive the available historical Attrition distribution deck versions.

Copies the V1-V7 deck artifacts that are present into the V8-adjacent archive
without changing their live source files. Existing archived files are treated
as immutable: a source/hash mismatch stops the run rather than overwriting a
historical backup.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION = ROOT / "output" / "distribution"
JSON_DIRECTORY = DISTRIBUTION / "json"
ARCHIVE_ROOT = DISTRIBUTION / "v8-backups" / "historical-v1-v7"
REGISTRY = ARCHIVE_ROOT / "history.json"
PREFIX = "attrition-43-variable-distributions"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_immutable(source: Path, destination: Path) -> dict[str, str]:
    """Copy once, then verify the historical copy is byte-for-byte unchanged."""
    source_hash = digest(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if digest(destination) != source_hash:
            raise ValueError(f"Historical archive collision: {destination}")
    else:
        shutil.copy2(source, destination)
    return {
        "source": str(source.relative_to(ROOT)).replace("\\", "/"),
        "archived": str(destination.relative_to(ROOT)).replace("\\", "/"),
        "sha256": source_hash,
    }


def archive_version(version: int) -> dict[str, object]:
    source_deck = DISTRIBUTION / f"{PREFIX}-v{version}.html"
    source_manifest = JSON_DIRECTORY / f"{PREFIX}-v{version}-manifest.json"
    evidence = sorted(JSON_DIRECTORY.glob(f"{PREFIX}-v{version}.*.json"))
    source_paths = [path for path in (source_deck, source_manifest) if path.exists()] + evidence
    if not source_paths:
        return {
            "version": version,
            "status": "not_found",
            "reason": "No distribution deck, manifest, or version-scoped aggregate evidence exists in the workspace.",
        }

    destination_root = ARCHIVE_ROOT / f"v{version}"
    files: list[dict[str, str]] = []
    if source_deck.exists():
        files.append(copy_immutable(source_deck, destination_root / source_deck.name))
    if source_manifest.exists():
        files.append(copy_immutable(source_manifest, destination_root / "json" / source_manifest.name))
    for source in evidence:
        files.append(copy_immutable(source, destination_root / "json" / source.name))
    return {
        "version": version,
        "status": "archived",
        "files": files,
        "deck_available": source_deck.exists(),
        "manifest_available": source_manifest.exists(),
        "evidence_file_count": len(evidence),
    }


def main() -> None:
    versions = [archive_version(version) for version in range(1, 8)]
    payload = {
        "schema_version": 1,
        "artifact": "Attrition distribution historical version archive",
        "scope": "V1 through V7; all available deck HTML, manifests, and version-scoped aggregate JSON evidence.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "search_instruction": "Search by version, status, source path, archived path, or sha256. For a slide or metric, open that version's archived HTML and then its archived manifest/evidence files.",
        "immutability_rule": "Archived files are copied once. A future source mismatch raises an error instead of overwriting a historical backup.",
        "versions": versions,
    }
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archived = sum(1 for version in versions if version["status"] == "archived")
    unavailable = [str(version["version"]) for version in versions if version["status"] == "not_found"]
    print(REGISTRY)
    print(f"archived_versions={archived}")
    print(f"not_found_versions={','.join(unavailable) or 'none'}")


if __name__ == "__main__":
    main()
