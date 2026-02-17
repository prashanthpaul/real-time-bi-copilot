"""
Page: Insights Dashboard
===========================
Real-time KPIs, interactive charts, AI-generated insights, and anomaly alerts.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.utils.db_connector import create_connector
from streamlit_app.components.metrics import display_kpi_row, format_currency, format_number

st.set_page_config(page_title="Insights Dashboard | BI Copilot", page_icon="💡", layout="wide")
st.title("💡 Insights Dashboard")

# --- Initialize ---
@st.cache_resource
def get_db():
    return create_connector()

try:
    db = get_db()
except Exception as e:
    st.error(f"Database not available: {e}")
    st.stop()

# --- Load Data ---
@st.cache_data(ttl=60)
def load_sales(_db):
    return _db.execute_query_df("SELECT * FROM sales")

@st.cache_data(ttl=60)
def load_monthly(_db):
    return _db.execute_query_df("SELECT * FROM monthly_revenue ORDER BY month")

@st.cache_data(ttl=60)
def load_daily(_db):
    return _db.execute_query_df("SELECT * FROM daily_kpis ORDER BY date")

sales = load_sales(db)
monthly = load_monthly(db)
daily = load_daily(db)

# --- KPI Row ---
total_revenue = sales["revenue"].sum()
total_profit = sales["profit"].sum()
total_txns = len(sales)
avg_order = sales["revenue"].mean()
margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

display_kpi_row([
    {"label": "Total Revenue", "value": format_currency(total_revenue)},
    {"label": "Total Profit", "value": format_currency(total_profit)},
    {"label": "Transactions", "value": format_number(total_txns)},
    {"label": "Avg Order Value", "value": format_currency(avg_order)},
    {"label": "Profit Margin", "value": f"{margin:.1f}%"},
])

st.divider()

# --- Charts Row 1 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue Trend")
    if not monthly.empty:
        monthly["month"] = pd.to_datetime(monthly["month"].astype(str))
        monthly_agg = monthly.groupby("month")["total_revenue"].sum().reset_index()
        fig = px.line(
            monthly_agg, x="month", y="total_revenue",
            template="plotly_dark",
            labels={"month": "Month", "total_revenue": "Revenue ($)"},
        )
        fig.update_layout(height=350, hovermode="x unified")
        st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Revenue by Category")
    cat_revenue = sales.groupby("category")["revenue"].sum().reset_index()
    fig = px.pie(
        cat_revenue, names="category", values="revenue",
        hole=0.4, template="plotly_dark",
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, width="stretch")

# --- Charts Row 2 ---
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 10 Products")
    top_products = (
        sales.groupby("product_name")["revenue"]
        .sum()
        .sort_values(ascending=True)
        .tail(10)
        .reset_index()
    )
    fig = px.bar(
        top_products, x="revenue", y="product_name",
        orientation="h", template="plotly_dark",
        labels={"revenue": "Revenue ($)", "product_name": "Product"},
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, width="stretch")

with col4:
    st.subheader("Revenue by Region")
    region_revenue = sales.groupby("region")["revenue"].sum().reset_index()
    fig = px.bar(
        region_revenue, x="region", y="revenue",
        template="plotly_dark", color="region",
        labels={"revenue": "Revenue ($)", "region": "Region"},
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, width="stretch")

# --- Daily Trends ---
st.divider()
st.subheader("Daily Transaction Volume")
if not daily.empty:
    daily["date"] = pd.to_datetime(daily["date"])
    fig = px.area(
        daily, x="date", y="transactions",
        template="plotly_dark",
        labels={"date": "Date", "transactions": "Transactions"},
    )
    fig.update_layout(height=300, hovermode="x unified")
    st.plotly_chart(fig, width="stretch")

# --- Channel & Segment Breakdown ---
col5, col6 = st.columns(2)

with col5:
    st.subheader("Sales Channel Mix")
    channel = sales.groupby("sales_channel")["revenue"].sum().reset_index()
    fig = px.pie(channel, names="sales_channel", values="revenue", hole=0.4, template="plotly_dark")
    fig.update_layout(height=300)
    st.plotly_chart(fig, width="stretch")

with col6:
    st.subheader("Customer Segment Mix")
    segment = sales.groupby("customer_segment")["revenue"].sum().reset_index()
    fig = px.pie(segment, names="customer_segment", values="revenue", hole=0.4, template="plotly_dark")
    fig.update_layout(height=300)
    st.plotly_chart(fig, width="stretch")
