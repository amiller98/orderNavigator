"""Load tabular files into DataFrames (same formats as the early prototype)."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

from order_navigator.header_detect import dataframe_with_detected_header, detect_header_row_index


def _read_csv_all_rows_headerless(b: io.BytesIO) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            b.seek(0)
            return pd.read_csv(
                b,
                header=None,
                encoding=enc,
                on_bad_lines="skip",
            )
        except (UnicodeDecodeError, pd.errors.EmptyDataError, UnicodeError):
            continue
    b.seek(0)
    return pd.read_csv(
        b,
        header=None,
        encoding="latin-1",
        on_bad_lines="skip",
    )


def load_uploaded_table(upload: Any) -> pd.DataFrame:
    name = upload.name.lower()
    data = upload.getvalue()
    buf = io.BytesIO(data)

    if name.endswith(".csv"):
        frame = _read_csv_all_rows_headerless(buf)
    elif name.endswith((".xlsx", ".xlsm")):
        frame = pd.read_excel(buf, engine="openpyxl", header=None, sheet_name=0)
    elif name.endswith(".xls"):
        frame = pd.read_excel(buf, header=None, sheet_name=0)
    else:
        st.error("Use CSV or Excel (.csv, .xlsx, .xlsm, .xls).")
        st.stop()

    h = detect_header_row_index(frame)
    return dataframe_with_detected_header(frame, h)
