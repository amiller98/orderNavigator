"""Planned: normalize dirty export sheets into canonical order rows."""

from __future__ import annotations

import pandas as pd

from order_navigator.description_parse import add_description_line_columns


def parse_orders_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Scaffolding hook: will map messy headers, drop junk rows, and coerce types.
    Splits multiline `Item description` into `Desc L1`..`Desc Ln` for grid display.
    """
    out = raw.copy()
    out = add_description_line_columns(out, source_col="Item description", prefix="Desc L", max_lines=12)
    return out
