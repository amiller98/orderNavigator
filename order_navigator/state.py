"""Session state defaults for Order Navigator."""

from __future__ import annotations

import streamlit as st

# Bump when `parse_orders_from_raw` output columns or logic change (invalidates cached parse).
ORDERS_PARSE_VERSION = 2


def init_state() -> None:
    st.session_state.setdefault("raw_upload_name", None)
    st.session_state.setdefault("raw_orders_df", None)
    st.session_state.setdefault("orders_parsed_df", None)
    st.session_state.setdefault("reference_unlocked", False)
    st.session_state.setdefault("materials_weeks_out", 4)
