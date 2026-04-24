"""App chrome: CSS and nav separator (pattern aligned with Inventory I/O top bar)."""

import streamlit as st


def inject_order_nav_shell_css() -> None:
    """Space for the main bar + thin rule under the segmented control."""
    st.markdown(
        """
        <style>
        .stApp .stMain .block-container {
            padding-top: 1.5rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            overflow: visible !important;
        }
        .on-nav-sep {
            box-sizing: border-box;
            height: 0;
            margin: 0 0 0.28rem 0;
            border: 0;
            border-top: 1px solid rgba(49, 51, 63, 0.14);
        }
        [data-testid="stMarkdownContainer"]:has(.on-nav-sep) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        [data-testid="stMarkdownContainer"]:has(.on-nav-sep) p {
            margin: 0 !important;
        }
        .on-hero { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; margin: 0 0 0.1rem 0; }
        .on-sub  { color: #94a3b8; font-size: 0.95rem; margin: 0 0 0.75rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_main_nav_separator() -> None:
    st.markdown(
        '<div class="on-nav-sep" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
