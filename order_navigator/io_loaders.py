"""Load tabular files into DataFrames (same formats as the early prototype)."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st


def load_uploaded_table(upload: Any) -> pd.DataFrame:
    name = upload.name.lower()
    raw = upload.getvalue()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(raw))
    st.error("Use CSV or Excel (.csv, .xlsx, .xlsm, .xls).")
    st.stop()
