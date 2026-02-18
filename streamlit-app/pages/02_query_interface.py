"""
Page: Query Interface
========================
Natural language and SQL query interface with results display,
visualization suggestions, and query history.
"""

import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.utils.db_connector import create_connector
from mcp_server.utils.ai_client import AIClient
from mcp_server.config import settings
from mcp_server.resources.query_history import query_history

st.set_page_config(page_title="Query Interface | BI Copilot", page_icon="💬", layout="wide")
st.title("💬 Query Interface")

# --- Initialize ---
@st.cache_resource
def get_db():
    return create_connector()

@st.cache_resource
def get_ai():
    if settings.anthropic_api_key:
        return AIClient(api_key=settings.anthropic_api_key, model=settings.claude_model)
    return None

db = get_db()
ai = get_ai()

# --- Query History State ---
if "query_results" not in st.session_state:
    st.session_state.query_results = []

# --- Input Mode ---
mode = st.radio("Query Mode", ["Natural Language", "SQL"], horizontal=True)

if mode == "Natural Language":
    st.info("Ask a question in plain English. AI will convert it to SQL." if ai else
            "Set ANTHROPIC_API_KEY in .env to enable natural language queries.")
    query = st.text_area(
        "Ask a question",
        placeholder="e.g., What are the top 5 products by revenue in 2024?",
        height=100,
    )
else:
    query = st.text_area(
        "SQL Query",
        placeholder="SELECT * FROM sales LIMIT 10",
        height=150,
    )

col1, col2 = st.columns([1, 4])
with col1:
    run = st.button("Run Query", type="primary", use_container_width=True)
with col2:
    limit = st.number_input("Max rows", min_value=1, max_value=10000, value=100)

# --- Execute Query ---
if run and query.strip():
    with st.spinner("Executing query..."):
        if mode == "Natural Language" and ai:
            schema_info = _build_schema_info(db)
            ai_result = ai.generate_sql(query, schema_info)
            if "error" in ai_result:
                st.error(f"SQL generation failed: {ai_result['error']}")
                st.stop()
            sql = ai_result["sql"]
            st.code(sql, language="sql")
        else:
            sql = query

        # Apply limit
        sql_upper = sql.strip().upper()
        if "LIMIT" not in sql_upper and sql_upper.startswith("SELECT"):
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        result = db.execute_query(sql)

    if "error" in result:
        st.error(f"Query Error: {result['error']}")
        if "suggestion" in result:
            st.info(result["suggestion"])
    else:
        # Record history
        query_history.record(
            query=query,
            query_type="natural_language" if mode == "Natural Language" else "sql",
            result_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
            generated_sql=sql if mode == "Natural Language" else None,
        )

        # Display results
        st.success(f"Returned {result['row_count']} rows in {result['execution_time_ms']}ms")

        df = pd.DataFrame(result["rows"], columns=result["columns"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Quick visualization
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols and len(df) > 1:
            st.subheader("Quick Visualization")
            chart_type = st.selectbox("Chart type", ["Bar", "Line", "Scatter"])
            x_col = st.selectbox("X axis", df.columns.tolist())
            y_col = st.selectbox("Y axis", numeric_cols)

            if chart_type == "Bar":
                st.bar_chart(df.set_index(x_col)[y_col])
            elif chart_type == "Line":
                st.line_chart(df.set_index(x_col)[y_col])
            elif chart_type == "Scatter":
                import plotly.express as px
                fig = px.scatter(df, x=x_col, y=y_col, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        # Download
        csv = df.to_csv(index=False)
        st.download_button("Download Results", csv, "query_results.csv", "text/csv")

# --- Query History ---
st.divider()
st.subheader("Query History")
history = query_history.get_history(limit=10)
if history:
    for entry in history:
        status = "✅" if entry["success"] else "❌"
        with st.expander(f"{status} {entry['timestamp']} — {entry['query'][:80]}..."):
            st.json(entry)
else:
    st.caption("No queries executed yet.")


def _build_schema_info(db) -> str:
    """Build schema info string for AI."""
    tables = db.get_tables()
    views = db.get_views()
    lines = []
    for table in tables:
        schema = db.get_schema(table["name"])
        cols = ", ".join([f'{c["column"]} ({c["type"]})' for c in schema])
        lines.append(f"TABLE {table['name']} ({table['row_count']} rows): {cols}")
    for view_name in views:
        schema = db.get_schema(view_name)
        cols = ", ".join([f'{c["column"]} ({c["type"]})' for c in schema])
        lines.append(f"VIEW {view_name}: {cols}")
    return "\n".join(lines)
