"""Planned: normalize dirty export sheets into canonical order rows."""

from __future__ import annotations

import pandas as pd

from order_navigator.description_parse import add_description_line_columns


def filter_rows_requiring_leading_keys(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Keep only rows where the first `n` columns are all non-empty.
    Drops section headers (e.g. month backorder banners), blank spacer rows, and
    other garbage that does not have customer + key fields populated.
    """
    if df.empty or len(df.columns) < n:
        return df.copy()
    cols = [df.columns[i] for i in range(n)]

    def row_ok(row: pd.Series) -> bool:
        for c in cols:
            v = row[c]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return False
            s = str(v).strip()
            if not s or s.lower() in ("nan", "none", "nat"):
                return False
        return True

    out = df[df.apply(row_ok, axis=1)].copy()
    return out.reset_index(drop=True)


def parse_orders_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Drop non-data rows, then split multiline `Item description` into `Desc L1`..`Desc Ln`.
    """
    out = filter_rows_requiring_leading_keys(raw, n=3)
    if "Item description" in out.columns:
        out = add_description_line_columns(
            out, source_col="Item description", prefix="Desc L", max_lines=12
        )
    return out
