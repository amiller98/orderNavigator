"""
Pick which row in a headerless table is the real column header row.
Targets exports with a title row, section headers, and multiline data cells.
"""

from __future__ import annotations

import re
import warnings

import pandas as pd

_LETTER = re.compile(r"[A-Za-z]")


def _non_empty_texts(row: pd.Series) -> list[str]:
    out: list[str] = []
    for v in row:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        s = str(v).strip()
        if s and s.lower() not in ("nan", "none", "nat"):
            out.append(s)
    return out


def detect_header_row_index(
    raw: pd.DataFrame,
    *,
    max_scan: int = 80,
    min_cols: int = 3,
    max_cell_len: int = 280,
) -> int:
    """
    Return 0-based row index of the header row (first match from the top).

    Heuristic: the header row has several non-empty, short, single-line cells
    (field names), unlike title rows (one cell) or data rows (often a huge
    multiline description in one cell).
    """
    if raw.empty:
        return 0
    hmax = min(max_scan, len(raw))

    def _pass1(r: int) -> bool:
        row = raw.iloc[r]
        cells = _non_empty_texts(row)
        n = len(cells)
        if n < min_cols:
            return False
        if max((len(s) for s in cells), default=0) > max_cell_len:
            return False
        if any(("\n" in s) or ("\r" in s) for s in cells):
            return False
        with_letter = sum(1 for s in cells if _LETTER.search(s))
        if with_letter < max(2, min(3, n - 1)):
            return False
        return True

    for r in range(hmax):
        if _pass1(r):
            return r

    # Looser pass: e.g. thin exports that still have short "header" cells but failed the letter test
    best: tuple[int, int] = (-1, 0)  # score, row
    for r in range(hmax):
        row = raw.iloc[r]
        cells = _non_empty_texts(row)
        n, mx = len(cells), max((len(s) for s in cells), default=0)
        if n < min_cols or mx > max_cell_len * 2:
            continue
        if any(("\n" in s) or ("\r" in s) for s in cells):
            continue
        score = n * 1_000_000 - min(mx, 99_999)
        if score > best[0]:
            best = (score, r)
    if best[0] >= 0:
        return best[1]
    return 0


def _munge_column_names(row: pd.Series) -> list[str]:
    """Turn one header row into string column names, fill blanks, make unique."""
    n = len(row)
    base: list[str] = []
    for i, v in enumerate(row):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            base.append(f"Column {i + 1}")
            continue
        s = str(v).strip().lstrip("\ufeff")
        if not s or s.lower() == "nan":
            base.append(f"Column {i + 1}")
        else:
            base.append(s)

    seen: dict[str, int] = {}
    out: list[str] = []
    for c in base:
        if c not in seen:
            seen[c] = 0
            out.append(c)
        else:
            seen[c] += 1
            out.append(f"{c}.{seen[c]}")
    return out


def dataframe_with_detected_header(raw: pd.DataFrame, header_idx: int) -> pd.DataFrame:
    """
    Use row header_idx for column names; return rows below, with reset index.
    """
    if header_idx < 0 or header_idx >= len(raw):
        return raw.copy()
    col_names = _munge_column_names(raw.iloc[header_idx])
    body = raw.iloc[header_idx + 1 :].copy()
    with warnings.catch_warnings():
        # pandas FutureWarning: columns not matching length — body should have same width
        if len(body.columns) == len(col_names):
            body.columns = col_names
        else:
            m = min(len(body.columns), len(col_names))
            body = body.iloc[:, :m]
            col_names = col_names[:m]
            body.columns = col_names
    return body.reset_index(drop=True)
