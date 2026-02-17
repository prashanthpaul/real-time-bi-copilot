"""
MCP Tool: generate_insights
==============================
AI-powered business insight generation. Queries data, sends it to Claude
for analysis, and returns structured business insights with recommendations.
"""

import json
import logging
from typing import Any

import pandas as pd

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.utils.ai_client import AIClient

logger = logging.getLogger(__name__)


async def generate_insights(
    question: str,
    table_name: str = "sales",
    time_period: str | None = None,
    db: DatabaseConnector = None,
    ai: AIClient = None,
) -> dict[str, Any]:
    """
    Generate AI-powered business insights from data.

    Args:
        question: Business question to answer.
        table_name: Table to analyze (default: sales).
        time_period: Optional filter like "last_30_days", "last_quarter", "2024".
        db: DatabaseConnector instance.
        ai: AIClient instance.

    Returns:
        Dictionary with AI-generated insights, key findings, and recommendations.
    """
    if db is None:
        return {"error": "Database connector not initialized"}
    if ai is None:
        return {"error": "AI client not initialized. Set ANTHROPIC_API_KEY."}

    # Build query with optional time filter
    where_clause = _build_time_filter(time_period)
    sql = f"SELECT * FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"

    try:
        df = db.execute_query_df(sql)
    except Exception as e:
        return {"error": f"Failed to query '{table_name}': {e}"}

    if df.empty:
        return {"error": "No data found for the specified criteria"}

    # Build data summary for AI
    data_summary = _build_data_summary(df, table_name)

    # Get AI insights
    result = ai.generate_insights(data_summary, question)

    if "error" in result:
        return result

    return {
        "question": question,
        "table": table_name,
        "time_period": time_period or "all",
        "rows_analyzed": len(df),
        "ai_response": result.get("response", ""),
        "insights": result.get("insights"),
        "tokens_used": {
            "input": result.get("input_tokens", 0),
            "output": result.get("output_tokens", 0),
        },
        "latency_ms": result.get("latency_ms", 0),
    }


def _build_time_filter(time_period: str | None) -> str:
    """Build a SQL WHERE clause for time filtering."""
    if not time_period:
        return ""

    filters = {
        "last_7_days": "transaction_date >= CURRENT_DATE - INTERVAL '7 days'",
        "last_30_days": "transaction_date >= CURRENT_DATE - INTERVAL '30 days'",
        "last_90_days": "transaction_date >= CURRENT_DATE - INTERVAL '90 days'",
        "last_quarter": "transaction_date >= DATE_TRUNC('quarter', CURRENT_DATE) - INTERVAL '3 months'",
        "this_year": "YEAR(CAST(transaction_date AS DATE)) = YEAR(CURRENT_DATE)",
        "2023": "YEAR(CAST(transaction_date AS DATE)) = 2023",
        "2024": "YEAR(CAST(transaction_date AS DATE)) = 2024",
        "2025": "YEAR(CAST(transaction_date AS DATE)) = 2025",
    }
    return filters.get(time_period, "")


def _build_data_summary(df: pd.DataFrame, table_name: str) -> str:
    """Build a concise data summary for the AI prompt."""
    lines = [
        f"Dataset: {table_name}",
        f"Total records: {len(df)}",
        f"Columns: {', '.join(df.columns.tolist())}",
        "",
    ]

    # Numeric summaries
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        lines.append("Numeric Summary:")
        for col in numeric_cols[:8]:
            lines.append(
                f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, "
                f"mean={df[col].mean():.2f}, median={df[col].median():.2f}"
            )

    # Categorical breakdowns
    cat_cols = df.select_dtypes(include=["object"]).columns
    for col in cat_cols[:5]:
        top = df[col].value_counts().head(5).to_dict()
        lines.append(f"\n{col} distribution: {top}")

    # Date range
    date_cols = [c for c in df.columns if "date" in c.lower()]
    if date_cols:
        col = date_cols[0]
        try:
            dates = pd.to_datetime(df[col])
            lines.append(f"\nDate range: {dates.min()} to {dates.max()}")
        except Exception:
            pass

    # Revenue/profit totals if available
    if "revenue" in df.columns:
        lines.append(f"\nTotal Revenue: ${df['revenue'].sum():,.2f}")
    if "profit" in df.columns:
        lines.append(f"Total Profit: ${df['profit'].sum():,.2f}")
        margin = (df["profit"].sum() / df["revenue"].sum() * 100) if df["revenue"].sum() > 0 else 0
        lines.append(f"Profit Margin: {margin:.1f}%")

    return "\n".join(lines)


TOOL_DEFINITION = {
    "name": "generate_insights",
    "description": (
        "Generate AI-powered business insights by analyzing data and using Claude "
        "to identify trends, patterns, and actionable recommendations. "
        "Answers specific business questions using real data."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Business question to answer (e.g., 'What are our top-performing products?')",
            },
            "table_name": {
                "type": "string",
                "description": "Table to analyze (default: sales)",
                "default": "sales",
            },
            "time_period": {
                "type": "string",
                "enum": ["last_7_days", "last_30_days", "last_90_days", "last_quarter", "this_year", "2023", "2024", "2025"],
                "description": "Time period filter",
            },
        },
        "required": ["question"],
    },
}
