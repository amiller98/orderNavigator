"""Section 3 — Reference data: pin-gated, multi-tab tables (editable in session for now)."""

from __future__ import annotations

import os

import streamlit as st

from order_navigator.reference_data import default_isotope_catalog, default_solution_mass_by_category

# Default PIN for local dev; override with env ORDER_NAV_REFERENCE_PIN. Production: use secrets.
def _expected_pin() -> str:
    return (os.environ.get("ORDER_NAV_REFERENCE_PIN") or "0000").strip()


def render_reference() -> None:
    st.markdown("#### Reference information")
    st.caption(
        "Tables that drive orders parsing and material math (mass ranges, catalogs, etc.). "
        "Edits apply for **this session** until persistence is added. **Unlock** with a PIN."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.session_state.get("reference_unlocked"):
            if st.button("Lock reference"):
                st.session_state["reference_unlocked"] = False
                st.rerun()
        else:
            pin = st.text_input("PIN", type="password", key="on_ref_pin")
            if st.button("Unlock"):
                if pin == _expected_pin():
                    st.session_state["reference_unlocked"] = True
                    st.rerun()
                else:
                    st.error("Incorrect PIN.")
    with col2:
        st.caption("Set a PIN via the `ORDER_NAV_REFERENCE_PIN` environment variable. Default in dev: `0000` if unset.")

    if not st.session_state.get("reference_unlocked"):
        st.info("Reference tables are **locked**. Enter the PIN to edit.")
        return

    t1, t2 = st.tabs(["Solution mass by category", "Isotope catalog"])

    st.session_state.setdefault("ref_solution_mass", default_solution_mass_by_category())
    st.session_state.setdefault("ref_isotope_catalog", default_isotope_catalog())

    with t1:
        st.caption("Example: allowed solution mass (mg) bounds per product category. Extend with more columns as needed.")
        ed = st.data_editor(
            st.session_state["ref_solution_mass"],
            use_container_width=True,
            num_rows="dynamic",
            key="on_editor_solution_mass",
        )
        st.session_state["ref_solution_mass"] = ed

    with t2:
        st.caption("List of isotopes and default units. Wire into materials roll-up later.")
        ed2 = st.data_editor(
            st.session_state["ref_isotope_catalog"],
            use_container_width=True,
            num_rows="dynamic",
            key="on_editor_isotope",
        )
        st.session_state["ref_isotope_catalog"] = ed2
