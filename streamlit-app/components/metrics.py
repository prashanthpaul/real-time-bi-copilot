"""
Reusable Metric Components
=============================
Helper functions for displaying KPI metrics in Streamlit.
"""

import streamlit as st


def display_kpi_row(metrics: list[dict]) -> None:
    """
    Display a row of KPI metric cards.

    Args:
        metrics: List of dicts with keys: label, value, delta (optional), delta_color (optional)
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            kwargs = {"label": m["label"], "value": m["value"]}
            if "delta" in m:
                kwargs["delta"] = m["delta"]
            if "delta_color" in m:
                kwargs["delta_color"] = m["delta_color"]
            st.metric(**kwargs)


def format_currency(value: float) -> str:
    """Format a number as currency."""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.2f}"


def format_number(value: float) -> str:
    """Format a large number with abbreviations."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def format_percentage(value: float) -> str:
    """Format a number as percentage."""
    return f"{value:+.1f}%"
