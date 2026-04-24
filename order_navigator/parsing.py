"""Planned: normalize dirty export sheets into canonical order rows."""

from __future__ import annotations

import pandas as pd


def parse_orders_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Scaffolding hook: will map messy headers, drop junk rows, and coerce types.
    For now, returns a copy of the input so the UI can be built first.
    """
    return raw.copy()
