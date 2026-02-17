"""
Real-Time BI Copilot — Streamlit Control Center
==================================================
Multi-page Streamlit dashboard for data exploration, querying,
insights visualization, and system health monitoring.

Usage:
    streamlit run streamlit-app/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Page Config ---
st.set_page_config(
    page_title="BI Copilot Control Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stMetric > div { background-color: #1e1e2e; padding: 1rem; border-radius: 0.5rem; }
    .stMetric label { font-size: 0.85rem !important; color: #a0a0b0 !important; }
    div[data-testid="stSidebarContent"] { background-color: #0e0e1a; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("📊 BI Copilot")
    st.caption("Real-Time Business Intelligence")
    st.divider()

    st.markdown("### Navigation")
    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/01_data_explorer.py", label="Data Explorer", icon="🔍")
    st.page_link("pages/02_query_interface.py", label="Query Interface", icon="💬")
    st.page_link("pages/03_insights_dashboard.py", label="Insights Dashboard", icon="💡")
    st.page_link("pages/04_system_health.py", label="System Health", icon="🩺")

    st.divider()
    st.caption("Powered by MCP + Claude AI")

# --- Home Page ---
st.title("Real-Time BI Copilot")
st.subheader("AI-Powered Business Intelligence Control Center")

st.markdown("""
Welcome to the **BI Copilot Control Center**. This dashboard connects to the MCP server
to provide real-time data analytics powered by Claude AI.

### Getting Started

1. **Data Explorer** — Browse available tables, view schemas, and preview data
2. **Query Interface** — Ask questions in natural language or write SQL directly
3. **Insights Dashboard** — View KPIs, trends, and AI-generated business insights
4. **System Health** — Monitor MCP server, database, and API status

### Architecture

```
VS Code / Claude Desktop
        │
        ▼
   MCP Server (stdio)
    ├── query_database     → SQL or natural language queries
    ├── analyze_data       → Statistical analysis
    ├── generate_insights  → AI-powered business insights
    └── detect_anomalies   → Anomaly detection
        │
        ▼
   DuckDB (local) ←→ Streamlit Dashboard (this app)
```
""")

# Quick status check
col1, col2, col3 = st.columns(3)

try:
    from mcp_server.utils.db_connector import create_connector

    db = create_connector()
    tables = db.get_tables()

    with col1:
        st.metric("Database", "Connected", delta="Online")
    with col2:
        st.metric("Tables", len(tables))
    with col3:
        total_rows = sum(t["row_count"] for t in tables)
        st.metric("Total Records", f"{total_rows:,}")

except Exception as e:
    with col1:
        st.metric("Database", "Offline", delta="Error", delta_color="inverse")
    with col2:
        st.error(f"Cannot connect to database: {e}")
    with col3:
        st.info("Run `python data/sample_data_generator.py` to initialize.")
