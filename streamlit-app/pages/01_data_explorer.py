"""
Page: Data Explorer
=====================
Browse tables, view schemas, preview data, and examine column statistics.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.utils.db_connector import create_connector

st.set_page_config(page_title="Data Explorer | BI Copilot", page_icon="🔍", layout="wide")
st.title("🔍 Data Explorer")

# --- Initialize DB ---
@st.cache_resource
def get_db():
    return create_connector()

try:
    db = get_db()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- Table Selector ---
try:
    tables = db.get_tables()
    views = db.get_views()
except Exception as e:
    st.error(f"Failed to list tables: {e}")
    st.stop()

all_datasets = [t["name"] for t in tables] + views

if not all_datasets:
    st.warning("No tables found. Run `python data/sample_data_generator.py` first.")
    st.stop()

selected = st.selectbox("Select a table or view", all_datasets)

# --- Schema ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Schema")
    try:
        schema = db.get_schema(selected)
        schema_df = pd.DataFrame(schema)
        st.dataframe(schema_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Schema error: {e}")

    # Row count
    try:
        count_result = db.execute_query(f"SELECT COUNT(*) FROM {selected}")
        if count_result.get("rows"):
            st.metric("Row Count", f"{count_result['rows'][0][0]:,}")
    except Exception as e:
        st.error(f"Count error: {e}")

with col2:
    st.subheader("Data Preview")
    limit = st.slider("Preview rows", 5, 100, 10)

    try:
        preview_df = db.execute_query_df(f"SELECT * FROM {selected} LIMIT {limit}")
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Preview error: {e}")

# --- Column Statistics ---
st.divider()
st.subheader("Column Statistics")

try:
    df = db.execute_query_df(f"SELECT * FROM {selected}")
except Exception as e:
    st.error(f"Failed to load data for statistics: {e}")
    st.stop()

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

tab1, tab2, tab3 = st.tabs(["Numeric Stats", "Categorical Stats", "Null Analysis"])

with tab1:
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)
    else:
        st.info("No numeric columns in this table.")

with tab2:
    if categorical_cols:
        col_select = st.selectbox("Select column", categorical_cols)
        value_counts = df[col_select].value_counts().head(20)
        st.bar_chart(value_counts)
    else:
        st.info("No categorical columns in this table.")

with tab3:
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if len(null_counts) > 0:
        null_df = pd.DataFrame({
            "Column": null_counts.index,
            "Null Count": null_counts.values,
            "Null %": (null_counts.values / len(df) * 100).round(2),
        })
        st.dataframe(null_df, use_container_width=True, hide_index=True)
    else:
        st.success("No null values found.")

# --- Export ---
st.divider()
csv = df.to_csv(index=False)
st.download_button("Download as CSV", csv, f"{selected}.csv", "text/csv")
