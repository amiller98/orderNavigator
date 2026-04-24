"""
Split 'Item description' style blocks (multiline text from ERP exports) into
per-line fields so tabular views stay readable. Formats vary a lot; we lean on
newlines first, light cleanup, optional max width.
"""

from __future__ import annotations

import re
from typing import List

import pandas as pd

# Trailing mojibake / bullets often seen at end of lines in this export
_GUNK = re.compile(r"[\uFFFD\u00a0\t]+")
_MULTI_NL = re.compile(r"[\r\n]+")


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
