"""App entry: top segmented control (Inventory-style) and section dispatch."""

from __future__ import annotations

import streamlit as st

from order_navigator.io_loaders import load_uploaded_table
from order_navigator.shell import inject_order_nav_shell_css, render_main_nav_separator
from order_navigator.state import init_state
from order_navigator.ui.materials import render_materials
from order_navigator.ui.orders import render_orders
from order_navigator.ui.reference import render_reference

_SECTIONS = ["Orders", "Required materials", "Reference"]


def run() -> None:
    st.set_page_config(
        page_title="Order Navigator",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    inject_order_nav_shell_css()

    st.markdown(
        """
        <p class="on-hero">Order Navigator</p>
        <p class="on-sub">Parse messy order exports, roll up isotope demand, and keep reference rules in one place.</p>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Data source")
        upload = st.file_uploader(
            "Orders file (dirty Excel or CSV)",
            type=["csv", "xlsx", "xlsm", "xls"],
            help="Used for the Orders section and (later) materials from the same dataset.",
        )
        st.divider()
        st.caption("v0.2 · scaffold")

    if upload is not None:
        try:
            key = f"{upload.name}:{len(upload.getvalue())}"
            if st.session_state.get("_orders_upload_key") != key:
                st.session_state["_orders_upload_key"] = key
                st.session_state["raw_orders_df"] = load_uploaded_table(upload)
                st.session_state["orders_parsed_df"] = None
        except Exception as e:
            st.error(f"Could not read the file: {e}")
            st.session_state["raw_orders_df"] = None
            st.session_state["orders_parsed_df"] = None
    else:
        st.session_state["raw_orders_df"] = None
        st.session_state["orders_parsed_df"] = None
        st.session_state.pop("_orders_upload_key", None)

    active = st.segmented_control(
        "App section",
        _SECTIONS,
        default=_SECTIONS[0],
        key="on_main_section",
        label_visibility="visible",
        width="stretch",
    )
    if not active:
        active = _SECTIONS[0]
    render_main_nav_separator()

    if active == "Orders":
        render_orders()
    elif active == "Required materials":
        render_materials()
    else:
        render_reference()
