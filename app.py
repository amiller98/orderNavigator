"""
Order Navigator — turn raw tabular uploads into clearer, more actionable views.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Order Navigator",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _load_table(upload: Any) -> pd.DataFrame:
    name = upload.name.lower()
    raw = upload.getvalue()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(raw))
    st.error("Please upload a CSV or Excel file (.csv, .xlsx).")
    st.stop()


def _profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        s = df[col]
        null_pct = 100.0 * s.isna().mean() if len(df) else 0.0
        nunique = s.nunique(dropna=True)
        sample = s.dropna().head(1)
        ex = str(sample.iloc[0]) if len(sample) else "—"
        if len(ex) > 40:
            ex = ex[:37] + "…"
        rows.append(
            {
                "Column": col,
                "Type": str(s.dtype),
                "Non-null": int(s.notna().sum()),
                "Null %": round(null_pct, 1),
                "Unique": int(nunique),
                "Example": ex,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    st.markdown(
        """
        <style>
        .hero { font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.15rem; }
        .sub { color: #94a3b8; font-size: 1.05rem; margin-bottom: 1.5rem; }
        div[data-testid="stMetricValue"] { font-size: 1.6rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero">Order Navigator</p><p class="sub">Load a table. See structure, health, and a clean working view — the start of better decisions from your data.</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Data")
        upload = st.file_uploader(
            "Drop a spreadsheet",
            type=["csv", "xlsx", "xlsm", "xls"],
            help="CSV or Excel. More sources later (e.g. Inventory I/O).",
        )
        st.divider()
        st.caption("v0.1 · local use")

    if upload is None:
        st.info("Upload a **CSV** or **Excel** file in the sidebar to begin.")
        st.stop()

    try:
        df = _load_table(upload)
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        st.stop()

    if df.empty:
        st.warning("That file has no rows.")
        st.stop()

    st.session_state["df"] = df

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    c3.metric("Duplicate rows", f"{int(df.duplicated().sum()):,}")
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    c4.metric("Est. size", f"{mem_mb:.2f} MB")

    st.subheader("Table")
    st.dataframe(
        df,
        use_container_width=True,
        height=360,
    )

    st.subheader("Column map")
    st.caption("Types, nulls, and a sample value per column — quick orientation before you act on the data.")
    st.dataframe(
        _profile(df),
        use_container_width=True,
        height=min(400, 60 + 28 * len(df.columns)),
        hide_index=True,
    )

    st.download_button(
        "Download profile as CSV",
        _profile(df).to_csv(index=False).encode("utf-8"),
        file_name="order_navigator_column_profile.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
