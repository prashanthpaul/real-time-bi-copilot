"""
Page: System Health
======================
Monitor MCP server, database, and API status.
"""

import sys
import os
from pathlib import Path

import streamlit as st

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.config import settings
from mcp_server.resources.query_history import query_history

st.set_page_config(page_title="System Health | BI Copilot", page_icon="🩺", layout="wide")
st.title("🩺 System Health")

# --- Database Status ---
st.subheader("Database")
col1, col2, col3 = st.columns(3)

try:
    db = DatabaseConnector(settings.resolve_database_path())
    tables = db.get_tables()
    views = db.get_views()
    total_rows = sum(t["row_count"] for t in tables)

    with col1:
        st.metric("Status", "Connected")
        st.success(f"Path: {settings.resolve_database_path()}")
    with col2:
        st.metric("Tables", len(tables))
        st.metric("Views", len(views))
    with col3:
        st.metric("Total Rows", f"{total_rows:,}")
        st.metric("Type", settings.database_type.upper())

    # Table details
    with st.expander("Table Details"):
        for t in tables:
            schema = db.get_schema(t["name"])
            cols = ", ".join([f'{c["column"]}({c["type"]})' for c in schema])
            st.text(f"📋 {t['name']}: {t['row_count']:,} rows — [{cols}]")

except Exception as e:
    with col1:
        st.metric("Status", "Offline")
        st.error(str(e))

# --- API Status ---
st.divider()
st.subheader("Claude AI API")

col4, col5 = st.columns(2)
with col4:
    if settings.anthropic_api_key:
        st.metric("API Key", "Configured")
        st.success(f"Model: {settings.claude_model}")
    else:
        st.metric("API Key", "Not Set")
        st.warning("Set ANTHROPIC_API_KEY in .env to enable AI features.")

with col5:
    st.metric("AI Insights", "Enabled" if settings.enable_ai_insights else "Disabled")
    st.metric("Anomaly Detection", "Enabled" if settings.enable_anomaly_detection else "Disabled")

# --- Query Performance ---
st.divider()
st.subheader("Query Performance")

stats = query_history.get_stats()
if stats.get("total_queries", 0) > 0:
    col6, col7, col8, col9 = st.columns(4)
    with col6:
        st.metric("Total Queries", stats["total_queries"])
    with col7:
        st.metric("Successful", stats["successful"])
    with col8:
        st.metric("Failed", stats["failed"])
    with col9:
        st.metric("Avg Latency", f"{stats['avg_execution_ms']}ms")
else:
    st.info("No queries executed yet in this session.")

# --- MCP Server Config ---
st.divider()
st.subheader("MCP Server Configuration")

config_data = {
    "Transport": settings.mcp_transport,
    "Host": settings.mcp_server_host,
    "Port": settings.mcp_server_port,
    "Query Cache": "Enabled" if settings.enable_query_cache else "Disabled",
    "Cache TTL": f"{settings.cache_ttl_seconds}s",
    "Log Level": settings.log_level,
}

for key, value in config_data.items():
    st.text(f"{key}: {value}")

# --- Environment ---
st.divider()
st.subheader("Environment")
env_info = {
    "Python": sys.version.split()[0],
    "Platform": sys.platform,
    "Project Root": str(settings.project_root),
    "Database Path": settings.resolve_database_path(),
}
for key, value in env_info.items():
    st.text(f"{key}: {value}")
