"""Load tabular files into DataFrames (same formats as the early prototype)."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

# Open Order / ERP-style exports: title in row 1, real headers in row 2 (Excel line 2 → pandas header=1).
_EXCEL_HEADER_ROW = 1


def load_uploaded_table(upload: Any) -> pd.DataFrame:
    name = upload.name.lower()
    raw = upload.getvalue()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(
            io.BytesIO(raw),
            engine="openpyxl",
            header=_EXCEL_HEADER_ROW,
            sheet_name=0,
        )
    if name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(raw), header=_EXCEL_HEADER_ROW, sheet_name=0)
    st.error("Use CSV or Excel (.csv, .xlsx, .xlsm, .xls).")
    st.stop()
