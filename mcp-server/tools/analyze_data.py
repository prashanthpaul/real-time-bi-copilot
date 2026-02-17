"""
MCP Tool: analyze_data
========================
Performs statistical analysis on a table or query result,
generating summary statistics, distributions, and trend information.
"""

import json
import logging
from typing import Any

import numpy as np
import pandas as pd

from mcp_server.utils.db_connector import DatabaseConnector

logger = logging.getLogger(__name__)


async def analyze_data(
    table_name: str,
    columns: list[str] | None = None,
    group_by: str | None = None,
    db: DatabaseConnector = None,
) -> dict[str, Any]:
    """
    Perform statistical analysis on a database table.

    Args:
        table_name: Name of the table or view to analyze.
        columns: Specific columns to analyze (default: all numeric columns).
        group_by: Optional column to group analysis by.
        db: DatabaseConnector instance.

    Returns:
        Dictionary with summary statistics, distributions, and data quality metrics.
    """
    if db is None:
        return {"error": "Database connector not initialized"}

    try:
        df = db.execute_query_df(f"SELECT * FROM {table_name}")
    except Exception as e:
        return {"error": f"Failed to load table '{table_name}': {e}"}

    if df.empty:
        return {"error": f"Table '{table_name}' is empty"}

    # Select columns to analyze
    if columns:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return {"error": f"Columns not found: {missing}"}
        df_analyze = df[columns]
    else:
        df_analyze = df

    numeric_cols = df_analyze.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_analyze.select_dtypes(include=["object", "category"]).columns.tolist()

    result = {
        "table": table_name,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns_analyzed": numeric_cols + categorical_cols,
    }

    # Summary statistics for numeric columns
    if numeric_cols:
        stats = df[numeric_cols].describe().round(2).to_dict()
        result["numeric_summary"] = stats

        # Correlation matrix (top correlations)
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().round(3)
            top_corr = []
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    val = corr.iloc[i, j]
                    if abs(val) > 0.3:
                        top_corr.append({
                            "col_a": corr.columns[i],
                            "col_b": corr.columns[j],
                            "correlation": float(val),
                        })
            top_corr.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            result["top_correlations"] = top_corr[:10]

    # Categorical column summaries
    if categorical_cols:
        cat_summary = {}
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(10).to_dict()
            cat_summary[col] = {
                "unique_values": int(df[col].nunique()),
                "top_values": {str(k): int(v) for k, v in value_counts.items()},
                "null_count": int(df[col].isnull().sum()),
            }
        result["categorical_summary"] = cat_summary

    # Data quality metrics
    result["data_quality"] = {
        "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns if df[col].isnull().sum() > 0},
        "null_percentage": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    # Group-by analysis
    if group_by and group_by in df.columns and numeric_cols:
        target_cols = [c for c in numeric_cols if c != group_by][:3]
        if target_cols:
            grouped = df.groupby(group_by)[target_cols].agg(["mean", "sum", "count"]).round(2)
            grouped.columns = ["_".join(col) for col in grouped.columns]
            result["grouped_analysis"] = {
                "group_by": group_by,
                "groups": grouped.head(20).to_dict(orient="index"),
            }

    # Trend detection for date columns
    date_cols = [c for c in df.columns if "date" in c.lower()]
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        metric_col = numeric_cols[0]
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            monthly = df.groupby(df[date_col].dt.to_period("M"))[metric_col].sum()
            if len(monthly) > 1:
                values = monthly.values.astype(float)
                trend = "increasing" if values[-1] > values[0] else "decreasing"
                pct_change = round(((values[-1] - values[0]) / values[0]) * 100, 1) if values[0] != 0 else 0
                result["trend"] = {
                    "date_column": date_col,
                    "metric": metric_col,
                    "direction": trend,
                    "overall_change_pct": pct_change,
                    "periods": len(monthly),
                }
        except Exception:
            pass

    logger.info(f"Analysis complete for '{table_name}': {len(df)} rows, {len(numeric_cols)} numeric cols")
    return result


TOOL_DEFINITION = {
    "name": "analyze_data",
    "description": (
        "Perform statistical analysis on a database table or view. "
        "Returns summary statistics, correlations, data quality metrics, "
        "categorical breakdowns, and trend detection."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table or view to analyze",
            },
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific columns to analyze (default: all)",
            },
            "group_by": {
                "type": "string",
                "description": "Column to group the analysis by",
            },
        },
        "required": ["table_name"],
    },
}
