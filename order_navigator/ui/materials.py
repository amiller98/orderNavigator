"""Section 2 — Required materials: weeks-out horizon, roll-up, then isotope → orders detail."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _placeholder_summary(weeks: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "isotope": ["(example) F-18", "(example) I-123"],
            f"total_needed_next_{weeks}w": [0.0, 0.0],
            "unit": ["GBq", "MBq"],
        }
    )


def _placeholder_isotope_orders(isotope: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [f"ORD-{i}" for i in (101, 102)],
            "need_by": ["TBD", "TBD"],
            "quantity": [0.0, 0.0],
            "unit": ["—", "—"],
        }
    )


def render_materials() -> None:
    st.markdown("#### Required materials")
    st.caption(
        "Summary of isotope **needs** for the next **N** weeks, derived from orders. "
        "Beneath the roll-up, open an isotope to see which orders drive the demand. "
        "Backend roll-up and date logic are **not** implemented yet."
    )

    wk = st.number_input(
        "Weeks out (horizon)",
        min_value=1,
        max_value=52,
        value=int(st.session_state.get("materials_weeks_out", 4)),
        key="on_weeks_out",
    )
    st.session_state["materials_weeks_out"] = wk

    st.subheader("Summary by isotope")
    summary = _placeholder_summary(wk)
    st.dataframe(summary, use_container_width=True, hide_index=True, height=120)

    st.subheader("Details: by isotope")
    st.caption("Tree-style layout TBD; expanders are a stand-in for per-isotope drilldown.")

    for iso in summary["isotope"].tolist():
        with st.expander(f"{iso} — orders that need this isotope", expanded=False):
            st.dataframe(
                _placeholder_isotope_orders(iso),
                use_container_width=True,
                hide_index=True,
            )
