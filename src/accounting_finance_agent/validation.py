"""Bounded structural checks only; no execution of generated code or documents."""

import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def validate_artifact(path: Path) -> dict:
    result = {"file": path.name, "scope": "file structure only", "errors": [], "warnings": []}
    suffix = path.suffix.lower()
    try:
        if suffix in {".xlsx", ".docx", ".pptx"}:
            required = {".xlsx": "xl/workbook.xml", ".docx": "word/document.xml", ".pptx": "ppt/presentation.xml"}[suffix]
            with ZipFile(path) as archive:
                if sum(info.file_size for info in archive.infolist()) > 200 * 1024**2:
                    result["warnings"].append("Archive exceeds the 200 MiB inspection limit; contents not checked.")
                    return result
                if required not in archive.namelist():
                    raise ValueError(f"Missing required part: {required}")
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"Corrupt ZIP member: {bad}")
                formulas = missing_cache = 0
                for name in archive.namelist():
                    if name.endswith(".xml"):
                        root = ET.fromstring(archive.read(name))
                        if name.startswith("xl/worksheets/"):
                            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                            for cell in root.findall(".//s:c", ns):
                                if cell.find("s:f", ns) is not None:
                                    formulas += 1
                                    value = cell.find("s:v", ns)
                                    missing_cache += value is None or not value.text
                if formulas:
                    result["warnings"].append(f"{formulas} formulas; {missing_cache} without cached values. No recalculation performed.")
            result["warnings"].append("Numerical accuracy and visual layout not checked.")
        elif suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader, None)
                if not header:
                    raise ValueError("CSV is empty or lacks a header.")
                count = 0
                for count, row in enumerate(reader, start=1):
                    if len(row) != len(header):
                        raise ValueError(f"CSV row {count + 1} has {len(row)} fields; expected {len(header)}.")
            result["rows"] = count
        elif suffix == ".json":
            with path.open(encoding="utf-8-sig") as stream:
                json.load(stream)
        else:
            result["warnings"].append("No structural checker for this file type.")
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    return result
