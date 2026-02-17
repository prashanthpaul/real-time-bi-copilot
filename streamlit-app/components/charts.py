"""
Reusable Chart Components
===========================
Plotly chart builders for the Streamlit dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def revenue_trend_chart(df: pd.DataFrame, date_col: str = "month", value_col: str = "total_revenue") -> go.Figure:
    """Line chart showing revenue over time."""
    fig = px.line(
        df, x=date_col, y=value_col,
        title="Revenue Trend",
        labels={date_col: "Period", value_col: "Revenue ($)"},
        template="plotly_dark",
    )
    fig.update_layout(hovermode="x unified", height=400)
    return fig


def category_breakdown_chart(df: pd.DataFrame, names_col: str = "category", values_col: str = "total_revenue") -> go.Figure:
    """Donut chart for category breakdown."""
    fig = px.pie(
        df, names=names_col, values=values_col,
        title="Revenue by Category",
        hole=0.4,
        template="plotly_dark",
    )
    fig.update_layout(height=400)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str | None = None) -> go.Figure:
    """Horizontal bar chart."""
    fig = px.bar(
        df, x=y, y=x, orientation="h",
        title=title, color=color,
        template="plotly_dark",
    )
    fig.update_layout(height=max(300, len(df) * 30), yaxis={"categoryorder": "total ascending"})
    return fig


def scatter_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> go.Figure:
    """Scatter plot for correlation analysis."""
    fig = px.scatter(
        df, x=x, y=y, color=color,
        title=title, template="plotly_dark",
        opacity=0.6,
    )
    fig.update_layout(height=400)
    return fig


def time_series_with_anomalies(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    anomaly_dates: list | None = None,
    title: str = "Time Series with Anomalies",
) -> go.Figure:
    """Time series chart with anomaly points highlighted."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[value_col],
        mode="lines", name="Values",
        line=dict(color="#636EFA"),
    ))

    if anomaly_dates:
        anomaly_df = df[df[date_col].isin(anomaly_dates)]
        fig.add_trace(go.Scatter(
            x=anomaly_df[date_col], y=anomaly_df[value_col],
            mode="markers", name="Anomalies",
            marker=dict(color="red", size=10, symbol="x"),
        ))

    fig.update_layout(title=title, template="plotly_dark", height=400, hovermode="x unified")
    return fig


def kpi_gauge(value: float, title: str, max_val: float | None = None, suffix: str = "") -> go.Figure:
    """Gauge chart for KPI display."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title},
        number={"suffix": suffix},
        gauge={
            "axis": {"range": [0, max_val or value * 1.5]},
            "bar": {"color": "#636EFA"},
            "steps": [
                {"range": [0, (max_val or value * 1.5) * 0.5], "color": "#1f1f2e"},
                {"range": [(max_val or value * 1.5) * 0.5, max_val or value * 1.5], "color": "#2d2d44"},
            ],
        },
    ))
    fig.update_layout(height=250, template="plotly_dark")
    return fig
