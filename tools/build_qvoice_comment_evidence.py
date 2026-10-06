"""Build aggregate-only QVoice open-text topic evidence.

The workbooks are read in memory and only aggregate diagnostics are persisted.
No identifiers, response text, or employee-level rows are written to disk.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

from lxml import etree
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
QVOICE_ROOT = ROOT / "data" / "QVoice"
DEFAULT_OUTPUT = ROOT / "output" / "distribution" / f"qvoice-comment-evidence-{date.today().isoformat()}.json"
MINIMUM_COHORT = 30


WAVES = [
    {
        "wave": "Mar-2023",
        "file": "March 2023 Pulse_raw data.xlsx",
        "key_column": "EmployeeID",
        "prompt_candidates": {
            "doing_well": ["What is one thing Qualcomm is doing really well? Please describe something that you would like Qualcomm to continue doing."],
            "can_improve": ["What is one thing Qualcomm can do to improve? Please describe something that you would like Qualcomm to do to improve your experience."],
            "processes_to_improve": [],
        },
        "en_diagnostic": False,
    },
    {
        "wave": "Jan-2024",
        "file": "Jan 2024 Qvoice raw data.xlsx",
        "key_column": "Participant's Unique Identifier",
        "prompt_candidates": {
            "doing_well": ["What is one thing Qualcomm is doing really well? Please describe something that you would like Qualcomm to continue doing."],
            "can_improve": ["What is one thing Qualcomm can do to improve? Please describe something that you would like Qualcomm to do to improve your experience."],
            "processes_to_improve": [],
        },
        "en_diagnostic": False,
    },
    {
        "wave": "Jan-2025",
        "file": "Jan 2025_Qvoice_raw data.xlsx",
        "key_column": "EmpID",
        "prompt_candidates": {
            "doing_well": ["What is one thing Qualcomm is doing really well? Please describe something that you would like Qualcomm to continue doing."],
            "can_improve": ["What is one thing Qualcomm can do to improve? Please describe something that you would like Qualcomm to do to improve your experience."],
            "processes_to_improve": ["If desired, please describe 1-2 work processes that you would like to see improved or made more efficient."],
        },
        "en_diagnostic": False,
    },
    {
        "wave": "Jan-2026",
        "file": "Jan 2026 Qvoice_raw data.xlsx",
        "key_column": "Emp ID",
        "prompt_candidates": {
            "doing_well": ["What is one thing Qualcomm is doing really well? Please describe something that you would like Qualcomm to continue doing."],
            "can_improve": ["What is one thing Qualcomm can do to improve? Please describe something that you would like Qualcomm to do to improve your experience."],
            "processes_to_improve": ["If desired, please describe 1-2 work processes that you would like to see improved or made more efficient."],
        },
        "en_diagnostic": True,
    },
]


TAXONOMY = {
    "Remote / WFH": {
        "description": "Remote work or working from home mentions.",
        "patterns": [
            "remote work", "remote-working", "working remotely", "work remotely", "work from home", "working from home",
            "wfh", "telework", "telecommute", "home office", "remote work", "trabajo remoto", "trabajo a distancia",
            "trabajar desde casa", "trabajo desde casa", "desde casa", "teletrabajo", "modalidad remota", "modalidad remoto",
        ],
    },
    "Hybrid": {
        "description": "Hybrid-work mentions and variants.",
        "patterns": [
            "hybrid work", "hybrid-working", "hybrid", "trabajo híbrido", "trabajo hibrido", "modelo híbrido", "modelo hibrido",
            "esquema híbrido", "esquema hibrido", "modalidad híbrida", "modalidad hibrida", "híbrido", "hibrido",
        ],
    },
    "RTO / office attendance": {
        "description": "Return-to-office or office-attendance mentions; home office is excluded from this theme.",
        "patterns": [
            "rto", "return to office", "return to the office", "return back to office", "back to office", "go back to office",
            "in office", "in-office", "in the office", "onsite", "on-site", "office days", "days in office", "office attendance",
            "presencial", "trabajo presencial", "volver a la oficina", "regreso a la oficina", "regresar a la oficina",
            "ir a la oficina", "días de oficina", "dias de oficina", "asistir a la oficina", "presencialidad",
        ],
    },
}


FRICTION_PATTERNS = [
    "mandatory", "mandated", "require", "required", "requirement", "must", "expected", "policy", "política", "politica",
    "obligatorio", "obligada", "obligación", "obligacion", "forced", "forzado", "commute", "commuting", "commute time",
    "parking", "inconvenient", "inconvenience", "difficult", "difficulty", "burden", "flexibility", "flexible", "flexibilidad",
    "not flexible", "days per week", "días por semana", "dias por semana", "prefer", "prefiero", "no quiero", "should not",
]


def _norm_header(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip()


def _norm_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _is_nonempty(value: object) -> bool:
    return bool(_norm_text(value))


def _has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(pattern.casefold()) + r"(?!\w)", text) for pattern in patterns)


def _classify_theme(text: str, theme: str) -> bool:
    if not text:
        return False
    if theme == "RTO / office attendance":
        # "home office" is a remote-work phrase, not office attendance.
        text = re.sub(r"\bhome\s+office\b", " ", text)
    return _has_any(text, TAXONOMY[theme]["patterns"])


def _find_column(headers: list[str], candidates: list[str]) -> str | None:
    normalized = {_norm_header(header): header for header in headers}
    for candidate in candidates:
        if _norm_header(candidate) in normalized:
            return normalized[_norm_header(candidate)]
    # 2026 appends a long opt-out note to the original prompt header.  The
    # prefix match is restricted to the documented prompt candidates and is
    # resolved before any response values are processed.
    for candidate in candidates:
        candidate_norm = _norm_header(candidate).casefold()
        matches = [header for header in headers if _norm_header(header).casefold().startswith(candidate_norm)]
        if len(matches) == 1:
            return matches[0]
    return None


def _find_2026_en_columns(headers: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for header in headers:
        value = _norm_header(header).casefold()
        if " en" not in value and not value.endswith("en"):
            continue
        if "doing really well" in value:
            result["doing_well"] = header
        elif "can do to improve" in value:
            result["can_improve"] = header
        elif "work processes" in value or "processes" in value:
            result["processes_to_improve"] = header
    return result


def _pairwise_counts(theme_sets: dict[str, set[str]]) -> dict[str, int]:
    names = list(TAXONOMY)
    return {
        " + ".join((names[i], names[j])): len(theme_sets[names[i]] & theme_sets[names[j]])
        for i in range(len(names)) for j in range(i + 1, len(names))
    }


def _column_number(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref.upper())
    if not letters:
        raise ValueError(f"Invalid XLSX cell reference: {cell_ref}")
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def _xml_tag(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def _workbook_sheet_path(archive: ZipFile, sheet_name: str) -> str:
    workbook_root = etree.fromstring(archive.read("xl/workbook.xml"))
    sheet_rid = None
    for element in workbook_root.iter():
        if _xml_tag(element.tag) == "sheet" and element.attrib.get("name") == sheet_name:
            sheet_rid = element.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            break
    if not sheet_rid:
        raise ValueError(f"Sheet not found: {sheet_name}")
    rel_root = etree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for element in rel_root.iter():
        if _xml_tag(element.tag) == "Relationship" and element.attrib.get("Id") == sheet_rid:
            target = element.attrib["Target"].lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise ValueError(f"Worksheet relationship not found: {sheet_name}")


def _shared_strings(archive: ZipFile) -> list[str]:
    try:
        stream = archive.open("xl/sharedStrings.xml")
    except KeyError:
        return []
    result: list[str] = []
    for _, element in etree.iterparse(stream, events=("end",), tag="{*}si", recover=True):
        result.append("".join(node.text or "" for node in element.iter() if _xml_tag(node.tag) == "t"))
        element.clear()
    stream.close()
    return result


def _cell_value(cell, shared: list[str]) -> object:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter() if _xml_tag(node.tag) == "t")
    value_node = next((node for node in cell if _xml_tag(node.tag) == "v"), None)
    if value_node is None or value_node.text is None:
        return None
    value = value_node.text
    if kind == "s":
        return shared[int(value)]
    return value


def _iter_selected_rows(path: Path, sheet_name: str, required_columns: set[str]):
    """Yield (header_map, selected_values) without materializing the sheet."""
    with ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheet_path = _workbook_sheet_path(archive, sheet_name)
        stream = archive.open(sheet_path)
        header_map: dict[str, int] | None = None
        selected_indices: set[int] | None = None
        for _, element in etree.iterparse(stream, events=("end",), tag="{*}row", recover=True):
            values: dict[int, object] = {}
            for cell in element:
                if _xml_tag(cell.tag) != "c" or "r" not in cell.attrib:
                    continue
                column = _column_number(cell.attrib["r"])
                if header_map is None or (selected_indices is not None and column in selected_indices):
                    values[column] = _cell_value(cell, shared)
            if header_map is None:
                header_map = {}
                for index, value in values.items():
                    # Raw workbooks can repeat a technical header such as
                    # EmployeeID later in the sheet. Preserve the first
                    # occurrence, which is the response key declared for
                    # the wave.
                    header_map.setdefault(_norm_header(value), index)
                missing = required_columns - set(header_map)
                if missing:
                    raise ValueError(f"Required columns not found in {path.name}: {sorted(missing)}")
                selected_indices = {header_map[column] for column in required_columns}
            else:
                yield header_map, values
            element.clear()
        stream.close()


def _theme_counts(theme_sets: dict[str, set[str]]) -> dict[str, int]:
    return {theme: len(keys) for theme, keys in theme_sets.items()}


def _scan_wave(config: dict[str, object]) -> dict[str, object]:
    path = QVOICE_ROOT / str(config["file"])
    # Read only the header with openpyxl. The data pass below uses the faster
    # XML reader and never materializes the complete worksheet.
    workbook = load_workbook(path, read_only=True, data_only=True)
    if "Raw data" not in workbook.sheetnames:
        workbook.close()
        raise ValueError(f"Missing Raw data sheet: {path.name}")
    worksheet = workbook["Raw data"]
    headers = [_norm_header(value) for value in next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    workbook.close()
    key_column = _find_column(headers, [str(config["key_column"])])
    if not key_column:
        raise ValueError(f"Expected participant key not found in {path.name}: {config['key_column']}")

    prompt_columns: dict[str, str | None] = {}
    for role, candidates in dict(config["prompt_candidates"]).items():
        prompt_columns[role] = _find_column(headers, list(candidates))
    if not prompt_columns.get("doing_well") or not prompt_columns.get("can_improve"):
        raise ValueError(f"Required open-text prompts not found in {path.name}")

    # The streaming reader needs the EN columns in the required set before it
    # starts the data pass; 2026 EN headers are discovered from a lightweight
    # header scan and are never written with their contents.
    en_columns = _find_2026_en_columns(headers) if bool(config.get("en_diagnostic")) else {}
    selected_headers = {key_column} | {column for column in prompt_columns.values() if column} | set(en_columns.values())
    row_count = 0
    keys: Counter[str] = Counter()
    comments_without_key = 0
    rows_with_any_comment = 0
    field_nonempty: Counter[str] = Counter()
    comment_keys: set[str] = set()
    theme_sets: dict[str, set[str]] = {theme: set() for theme in TAXONOMY}
    improvement_rto_keys: set[str] = set()
    friction_context_keys: set[str] = set()
    en_nonempty: Counter[str] = Counter()
    en_theme_sets: dict[str, set[str]] = {theme: set() for theme in TAXONOMY}
    en_keyed_rows: dict[str, set[str]] = defaultdict(set)

    prompt_roles = [role for role, column in prompt_columns.items() if column]
    # One XML pass with only the selected columns retained.
    for header_map, row in _iter_selected_rows(path, "Raw data", selected_headers):
        row_count += 1
        key_value = row.get(header_map[key_column])
        key = _norm_text(key_value)
        comment_values = {
            role: row.get(header_map[column]) if column else None
            for role, column in prompt_columns.items()
        }
        nonempty_roles = [role for role in prompt_roles if _is_nonempty(comment_values[role])]
        if key:
            keys[key] += 1
        if nonempty_roles:
            rows_with_any_comment += 1
            for role in nonempty_roles:
                field_nonempty[role] += 1
            if not key:
                comments_without_key += 1
            else:
                comment_keys.add(key)

        all_text = " ".join(_norm_text(comment_values[role]) for role in nonempty_roles)
        improvement_text = " ".join(
            _norm_text(comment_values[role])
            for role in ("can_improve", "processes_to_improve")
            if role in comment_values and _is_nonempty(comment_values[role])
        )
        if key:
            for theme in TAXONOMY:
                if _classify_theme(all_text, theme):
                    theme_sets[theme].add(key)
            if _classify_theme(improvement_text, "RTO / office attendance"):
                improvement_rto_keys.add(key)
            if _classify_theme(improvement_text, "RTO / office attendance") and _has_any(improvement_text, FRICTION_PATTERNS):
                friction_context_keys.add(key)

        if en_columns:
            for role, column in en_columns.items():
                value = row.get(header_map[column])
                if _is_nonempty(value):
                    en_nonempty[role] += 1
                if key and _is_nonempty(value):
                    en_keyed_rows[role].add(key)
                    text = _norm_text(value)
                    for theme in TAXONOMY:
                        if _classify_theme(text, theme):
                            en_theme_sets[theme].add(key)

    duplicate_keys = {key: count for key, count in keys.items() if count > 1}
    published_themes = {
        theme: (count if count >= MINIMUM_COHORT else None)
        for theme, count in _theme_counts(theme_sets).items()
    }
    diagnostics = {
        "improvement_rto_mentions": len(improvement_rto_keys),
        "requirement_friction_context": len(friction_context_keys),
        "minimum_cohort": MINIMUM_COHORT,
        "improvement_rto_publishable": len(improvement_rto_keys) >= MINIMUM_COHORT,
        "requirement_friction_publishable": len(friction_context_keys) >= MINIMUM_COHORT,
    }
    en_diagnostic = None
    if en_columns:
        en_diagnostic = {
            "columns_available": en_columns,
            "field_nonempty_rows": dict(en_nonempty),
            "distinct_keyed_respondents": {role: len(keys_set) for role, keys_set in en_keyed_rows.items()},
            "theme_counts": _theme_counts(en_theme_sets),
            "note": "Aggregate quality diagnostic only; EN columns are excluded from the primary trend.",
        }

    return {
        "wave": config["wave"],
        "source_file": config["file"],
        "sheet": "Raw data",
        "key_column": key_column,
        "prompt_columns": prompt_columns,
        "en_diagnostic": en_diagnostic,
        "row_count": row_count,
        "distinct_usable_participant_keys": len(keys),
        "respondent_wave_count": len(comment_keys),
        "field_nonempty_rows": dict(field_nonempty),
        "rows_with_any_comment": rows_with_any_comment,
        "duplicate_participant_keys": len(duplicate_keys),
        "duplicate_participant_rows": sum(count - 1 for count in duplicate_keys.values()),
        "comments_without_key": comments_without_key,
        "theme_counts": _theme_counts(theme_sets),
        "published_theme_counts": published_themes,
        "overlap_counts": _pairwise_counts(theme_sets),
        "diagnostics": diagnostics,
        "suppression_status": {
            theme: "published" if count is not None else "suppressed_below_n_30"
            for theme, count in published_themes.items()
        },
    }


def build_evidence(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    waves = [_scan_wave(config) for config in WAVES]
    for wave in waves:
        if wave["duplicate_participant_rows"] != 0:
            raise ValueError(f"Duplicate participant rows found in {wave['wave']}")
        if wave["comments_without_key"] != 0:
            raise ValueError(f"Comments without a usable participant key found in {wave['wave']}")
        if any(value is not None and value < MINIMUM_COHORT for value in wave["published_theme_counts"].values()):
            raise ValueError(f"Published theme below minimum cohort in {wave['wave']}")

    result = {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice raw open-text topic mentions",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "minimum_cohort": MINIMUM_COHORT,
        "primary_source_rule": "Original open-ended fields only; 2026 EN columns are diagnostics and are not used in the trend.",
        "grain": "distinct participant-wave case per theme",
        "deduplication_rule": "Each participant contributes at most once per wave and theme, across all selected prompts.",
        "comment_text_persisted": False,
        "identifiers_persisted": False,
        "keyword_taxonomy": TAXONOMY,
        "requirement_friction_rule": "Flag requirement/friction context only when a requirement/friction term co-occurs with an RTO / office attendance mention in an improvement-oriented prompt; this is context, not a complaint label.",
        "friction_patterns": FRICTION_PATTERNS,
        "waves": waves,
        "acceptance_rule": {
            "expected_waves": [config["wave"] for config in WAVES],
            "required_prompt_roles": ["doing_well", "can_improve"],
            "zero_duplicate_participant_rows": True,
            "zero_comments_without_key": True,
            "published_counts_minimum_n": MINIMUM_COHORT,
            "no_identifiers_or_free_text": True,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build aggregate-only QVoice comment evidence.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    evidence = build_evidence(args.output)
    print(json.dumps({"output": str(args.output), "waves": [wave["wave"] for wave in evidence["waves"]], "outcome": evidence["outcome"]}, ensure_ascii=False))
