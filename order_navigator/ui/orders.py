"""Section 1 — Orders: parsed from dirty Excel, sortable, column pick, quick search."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from order_navigator.parsing import parse_orders_from_raw
from order_navigator.state import ORDERS_PARSE_VERSION

# Default column order: keys + structured fields up front, then the rest.
_COLUMN_ORDER_BUMP = [
    "Customer name",
    "Cust#",
    "SO#",
    "WO#",
    "CC",
    "Cost Obj",
    "Item ID",
    "Isotopes",
    "Activity tolerance",
    "Overall dimensions",
    "Active dimensions",
    "Fill Volume",
]


def _default_visible_columns(columns: list[str]) -> list[str]:
    """All columns except the raw multiline `Item description` if we have `Desc L*`; bump useful fields first."""
    cols = list(columns)
    if "Desc L1" in cols and "Item description" in cols:
        cols = [c for c in cols if c != "Item description"]
    first = [c for c in _COLUMN_ORDER_BUMP if c in cols]
    rest = [c for c in cols if c not in first]
    return first + rest


def _apply_text_filters(df: pd.DataFrame, q1: str, q2: str, q3: str) -> pd.DataFrame:
    out = df
    for q in (q1, q2, q3):
        t = (q or "").strip()
        if not t or out.empty:
            continue
        m = pd.Series([False] * len(out), index=out.index, dtype=bool)
        for col in out.columns:
            m = m | out[col].astype(str).str.contains(t, case=False, na=False, regex=False)
        out = out.loc[m]
    return out


def render_orders() -> None:
    st.markdown("#### Orders")
    st.caption(
        "Source: parsed from a **dirty** Excel export. **Item description** is split into **Desc L1, L2, …** by line. "
        "Structured fields are regex-pulled from the full text: **Isotopes** (e.g. Cd-109, Tc-99m), **Activity tolerance**, "
        "**Overall dimensions**, **Active dimensions**, **Fill Volume**."
    )

    raw = st.session_state.get("raw_orders_df")
    if raw is None or not isinstance(raw, pd.DataFrame) or raw.empty:
        st.info("Upload an Excel or CSV in the **sidebar** to load orders. Nothing to show yet.")
        return

    if st.session_state.get("orders_parse_version") != ORDERS_PARSE_VERSION:
        st.session_state["orders_parse_version"] = ORDERS_PARSE_VERSION
        st.session_state["orders_parsed_df"] = None

    if st.session_state.get("orders_parsed_df") is None:
        st.session_state["orders_parsed_df"] = parse_orders_from_raw(raw)
    df = st.session_state["orders_parsed_df"]
    if df is None or df.empty:
        st.warning("Parsed orders are empty after the (stub) parse step.")
        return

    col_sig = "\x1e".join(map(str, df.columns))
    if st.session_state.get("_on_orders_col_sig") != col_sig:
        st.session_state["_on_orders_col_sig"] = col_sig
        st.session_state["on_visible_multiselect"] = _default_visible_columns(list(df.columns))

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        show_cols = st.multiselect(
            "Visible columns",
            list(df.columns),
            key="on_visible_multiselect",
            help="Streamlit may cache this list; it resets when the file / columns change. "
            "Desc L* = lines from Item description. Re-add **Item description** to see the raw multiline cell.",
        )
    with c2:
        sort_col = st.selectbox("Sort by", list(df.columns), index=0)
    with c3:
        sort_asc = st.toggle("Ascending", value=True)
    with c4:
        if st.button("Re-run parse"):
            st.session_state["orders_parsed_df"] = parse_orders_from_raw(raw)
            st.session_state["_on_orders_col_sig"] = None
            st.rerun()

    if not show_cols:
        st.warning("Pick at least one column.")
        return

    view = df[show_cols].copy()
    try:
        view = view.sort_values(by=sort_col, ascending=sort_asc, kind="mergesort")
    except Exception:
        st.caption("Sort could not use that column as a key; showing unsorted.")
    s1, s2, s3 = st.columns(3)
    with s1:
        q1 = st.text_input("Quick search 1", "", placeholder="matches any column…", key="on_q1")
    with s2:
        q2 = st.text_input("Quick search 2", "", placeholder="optional second filter", key="on_q2")
    with s3:
        q3 = st.text_input("Quick search 3", "", placeholder="optional third filter", key="on_q3")

    filtered = _apply_text_filters(view, q1, q2, q3)
    st.caption(f"Showing **{len(filtered):,}** of **{len(view):,}** rows in this view.")
    st.dataframe(
        filtered,
        use_container_width=True,
        height=420,
    )

    with st.expander("Data quality (placeholder)"):
        st.write("Column profile, duplicate detection, and parse diagnostics will land here.")
