"""Section 1 — Orders: parsed from dirty Excel, sortable, column pick, quick search."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from order_navigator.parsing import parse_orders_from_raw


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
        "Source: parsed from a **dirty** Excel export. Here: choose fields, sort, and quick text search. "
        "The parse step is a stub until the backend is wired."
    )

    raw = st.session_state.get("raw_orders_df")
    if raw is None or not isinstance(raw, pd.DataFrame) or raw.empty:
        st.info("Upload an Excel or CSV in the **sidebar** to load orders. Nothing to show yet.")
        return

    if st.session_state.get("orders_parsed_df") is None:
        st.session_state["orders_parsed_df"] = parse_orders_from_raw(raw)
    df = st.session_state["orders_parsed_df"]
    if df is None or df.empty:
        st.warning("Parsed orders are empty after the (stub) parse step.")
        return

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1:
        show_cols = st.multiselect(
            "Visible columns",
            list(df.columns),
            default=list(df.columns),
            help="Show a subset of fields; table stays sortable in the viewer.",
        )
    with c2:
        sort_col = st.selectbox("Sort by", list(df.columns), index=0)
    with c3:
        sort_asc = st.toggle("Ascending", value=True)
    with c4:
        if st.button("Re-run parse (stub)"):
            st.session_state["orders_parsed_df"] = parse_orders_from_raw(raw)
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
