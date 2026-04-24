"""
Split 'Item description' style blocks (multiline text from ERP exports) into
per-line fields so tabular views stay readable. Formats vary a lot; we lean on
newlines first, light cleanup, optional max width.

Also extracts structured fields via regex: isotopes, activity tolerance, dimensions, fill.
"""

from __future__ import annotations

import re
from typing import List, TypedDict

import pandas as pd

# Trailing mojibake / bullets often seen at end of lines in this export
_GUNK = re.compile(r"[\uFFFD\u00a0\t]+")
_MULTI_NL = re.compile(r"[\r\n]+")

# Element-###+optional suffix, e.g. Co-60, Tc-99m, I-123, H-3
_ISOTOPE_RE = re.compile(r"\b([A-Z][a-z]?-\d+[a-z]?)\b", re.IGNORECASE)
_ACTIVITY_TOLERANCE = re.compile(r"Activity\s*Tolerance:\s*([^\r\n]+)", re.IGNORECASE)
_OVERALL_DIMS = re.compile(r"Overall\s*Dimensions:\s*([^\r\n]+)", re.IGNORECASE)
_ACTIVE_DIMS = re.compile(r"Active\s*Dimensions:\s*([^\r\n]+)", re.IGNORECASE)
_FILL_VOLUME = re.compile(r"Fill\s*Volume:\s*([^\r\n]+)", re.IGNORECASE)


class DescriptionFields(TypedDict):
    isotopes: str
    activity_tolerance: str
    overall_dimensions: str
    active_dimensions: str
    fill_volume: str


def _trim_field(s: str) -> str:
    t = s.strip()
    t = t.rstrip(" \t,;")
    for junk in ("\u00a0", "\u200b", "�"):
        t = t.replace(junk, " ")
    return t.strip()


def _isotopes_ordered(s: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in _ISOTOPE_RE.finditer(s):
        raw = m.group(1)
        k = raw.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(raw)
    return out


def extract_description_fields(text: object) -> DescriptionFields:
    """
    Pull structured substrings from one Item description block.
    Isotopes: Cd-109 / Tc-99m-style tokens across the full text (incl. multiple
    lines), de-duplicated, first-seen order, joined with ", ".
    """
    empty: DescriptionFields = {
        "isotopes": "",
        "activity_tolerance": "",
        "overall_dimensions": "",
        "active_dimensions": "",
        "fill_volume": "",
    }
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return empty
    s_norm = str(text).replace("\r\n", "\n").replace("\r", "\n")
    isos = _isotopes_ordered(s_norm)
    m_tol = _ACTIVITY_TOLERANCE.search(s_norm)
    m_oa = _OVERALL_DIMS.search(s_norm)
    m_ad = _ACTIVE_DIMS.search(s_norm)
    m_fv = _FILL_VOLUME.search(s_norm)
    return {
        "isotopes": ", ".join(isos) if isos else "",
        "activity_tolerance": _trim_field(m_tol.group(1) if m_tol else ""),
        "overall_dimensions": _trim_field(m_oa.group(1) if m_oa else ""),
        "active_dimensions": _trim_field(m_ad.group(1) if m_ad else ""),
        "fill_volume": _trim_field(m_fv.group(1) if m_fv else ""),
    }


def lines_from_description_block(text: object, *, max_lines: int = 16) -> List[str]:
    """
    Turn one cell's text into a list of non-empty display lines.
    Splits on newlines; does not try to infer 'columns' inside a single line
    (that can be a later opt-in for specific patterns).
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return []
    s = str(text).replace("\r\n", "\n").replace("\r", "\n")
    s = _GUNK.sub(" ", s)
    out: list[str] = []
    for part in _MULTI_NL.split(s):
        line = part.strip()
        if not line:
            continue
        line = _GUNK.sub(" ", line).strip()
        if not line or line in ("�", "•"):
            continue
        out.append(line)
        if len(out) >= max_lines:
            break
    return out


def add_description_line_columns(
    df: pd.DataFrame,
    source_col: str = "Item description",
    prefix: str = "Desc L",
    max_lines: int = 12,
) -> pd.DataFrame:
    """
    Append Desc L1..Desc Ln columns (1-based) from `source_col`. Original column kept.
    Missing or empty source yields empty strings in line columns (not NaN) for stable sorting.
    """
    if source_col not in df.columns:
        return df
    n = int(max(1, max_lines))
    names = [f"{prefix}{i}" for i in range(1, n + 1)]
    series = df[source_col]
    new_cols: dict[str, list[str]] = {c: [] for c in names}
    for val in series:
        lines = lines_from_description_block(val, max_lines=n)
        for i, col in enumerate(names):
            new_cols[col].append(lines[i] if i < len(lines) else "")
    out = df.copy()
    for col in names:
        out[col] = new_cols[col]
    return out

# Public column names in the table (match user-facing labels)
COL_ISOTOPES = "Isotopes"
COL_ACTIVITY_TOLERANCE = "Activity tolerance"
COL_OVERALL_DIMS = "Overall dimensions"
COL_ACTIVE_DIMS = "Active dimensions"
COL_FILL_VOLUME = "Fill Volume"


def add_structured_description_columns(
    df: pd.DataFrame,
    source_col: str = "Item description",
) -> pd.DataFrame:
    """Add regex-parsed Isotopes, Activity tolerance, dimension, and fill columns."""
    if source_col not in df.columns:
        return df
    out = df.copy()
    keys = list(zip(
        (COL_ISOTOPES, COL_ACTIVITY_TOLERANCE, COL_OVERALL_DIMS, COL_ACTIVE_DIMS, COL_FILL_VOLUME),
        ("isotopes", "activity_tolerance", "overall_dimensions", "active_dimensions", "fill_volume"),
    ))
    bucket: dict[str, list[str]] = {c: [] for c, _ in keys}
    for val in out[source_col]:
        f = extract_description_fields(val)
        for col_name, fkey in keys:
            bucket[col_name].append(f[fkey])  # type: ignore[literal-required]
    for col_name, _ in keys:
        out[col_name] = bucket[col_name]
    return out
