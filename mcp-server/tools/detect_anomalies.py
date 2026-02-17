"""
MCP Tool: detect_anomalies
=============================
Anomaly detection using statistical methods (Z-score, IQR) on time-series
and categorical data. Optionally uses Claude for contextual explanation.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.utils.ai_client import AIClient

logger = logging.getLogger(__name__)


async def detect_anomalies(
    table_name: str = "sales",
    metric_column: str = "revenue",
    date_column: str = "transaction_date",
    method: str = "zscore",
    threshold: float = 3.0,
    explain: bool = False,
    db: DatabaseConnector = None,
    ai: AIClient = None,
) -> dict[str, Any]:
    """
    Detect anomalies in time-series data.

    Args:
        table_name: Table to analyze.
        metric_column: Numeric column to check for anomalies.
        date_column: Date column for time-series ordering.
        method: Detection method — "zscore" or "iqr".
        threshold: Sensitivity threshold (default 3.0 for z-score, 1.5 for IQR).
        explain: Whether to use AI to explain anomalies.
        db: DatabaseConnector instance.
        ai: AIClient instance (required if explain=True).

    Returns:
        Dictionary with detected anomalies, severity levels, and optional AI explanations.
    """
    if db is None:
        return {"error": "Database connector not initialized"}

    try:
        df = db.execute_query_df(
            f"SELECT * FROM {table_name} ORDER BY {date_column}"
        )
    except Exception as e:
        return {"error": f"Failed to load data: {e}"}

    if metric_column not in df.columns:
        return {"error": f"Column '{metric_column}' not found in '{table_name}'"}

    # Convert date column
    try:
        df[date_column] = pd.to_datetime(df[date_column])
    except Exception:
        pass

    metric = df[metric_column].dropna()

    # Detect anomalies
    if method == "zscore":
        anomaly_mask = _zscore_detect(metric, threshold)
    elif method == "iqr":
        anomaly_mask = _iqr_detect(metric, threshold)
    else:
        return {"error": f"Unknown method '{method}'. Use 'zscore' or 'iqr'."}

    anomaly_df = df[anomaly_mask].copy()

    if anomaly_df.empty:
        return {
            "table": table_name,
            "metric": metric_column,
            "method": method,
            "threshold": threshold,
            "anomalies_found": 0,
            "message": "No anomalies detected with the current threshold.",
        }

    # Classify severity
    anomaly_df["severity"] = anomaly_df[metric_column].apply(
        lambda x: _classify_severity(x, metric.mean(), metric.std())
    )

    # Build anomaly records
    anomalies = []
    for _, row in anomaly_df.head(50).iterrows():
        record = {
            "date": str(row.get(date_column, "N/A")),
            "value": float(row[metric_column]),
            "severity": row["severity"],
            "deviation": round(
                abs(row[metric_column] - metric.mean()) / metric.std(), 2
            ) if metric.std() > 0 else 0,
        }
        # Include identifying columns
        for col in ["transaction_id", "product_name", "category", "region", "customer_id"]:
            if col in row.index:
                record[col] = str(row[col])
        anomalies.append(record)

    result = {
        "table": table_name,
        "metric": metric_column,
        "method": method,
        "threshold": threshold,
        "total_records": len(df),
        "anomalies_found": len(anomaly_df),
        "anomaly_rate_pct": round(len(anomaly_df) / len(df) * 100, 2),
        "baseline": {
            "mean": round(float(metric.mean()), 2),
            "std": round(float(metric.std()), 2),
            "median": round(float(metric.median()), 2),
        },
        "severity_breakdown": anomaly_df["severity"].value_counts().to_dict(),
        "anomalies": anomalies,
    }

    # AI explanation
    if explain and ai is not None and anomalies:
        anomaly_summary = (
            f"Detected {len(anomaly_df)} anomalies in {metric_column} "
            f"(mean={metric.mean():.2f}, std={metric.std():.2f}).\n"
            f"Severity breakdown: {result['severity_breakdown']}\n"
            f"Sample anomalies: {anomalies[:5]}"
        )
        ai_result = ai.explain_anomaly(anomaly_summary)
        if "analysis" in ai_result:
            result["ai_explanation"] = ai_result["analysis"]

    logger.info(
        f"Anomaly detection on '{table_name}.{metric_column}': "
        f"{len(anomaly_df)} anomalies found ({result['anomaly_rate_pct']}%)"
    )
    return result


def _zscore_detect(series: pd.Series, threshold: float) -> pd.Series:
    """Detect anomalies using Z-score method."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series([False] * len(series), index=series.index)
    z_scores = (series - mean).abs() / std
    return z_scores > threshold


def _iqr_detect(series: pd.Series, threshold: float) -> pd.Series:
    """Detect anomalies using IQR (Interquartile Range) method."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - threshold * iqr
    upper = q3 + threshold * iqr
    return (series < lower) | (series > upper)


def _classify_severity(value: float, mean: float, std: float) -> str:
    """Classify anomaly severity based on deviation from mean."""
    if std == 0:
        return "low"
    deviation = abs(value - mean) / std
    if deviation > 5:
        return "critical"
    if deviation > 4:
        return "high"
    if deviation > 3:
        return "medium"
    return "low"


TOOL_DEFINITION = {
    "name": "detect_anomalies",
    "description": (
        "Detect anomalies in time-series data using statistical methods (Z-score, IQR). "
        "Returns anomalies with severity levels and optional AI-powered explanations."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Table to analyze (default: sales)",
                "default": "sales",
            },
            "metric_column": {
                "type": "string",
                "description": "Numeric column to check for anomalies (default: revenue)",
                "default": "revenue",
            },
            "date_column": {
                "type": "string",
                "description": "Date column for ordering (default: transaction_date)",
                "default": "transaction_date",
            },
            "method": {
                "type": "string",
                "enum": ["zscore", "iqr"],
                "description": "Detection method (default: zscore)",
                "default": "zscore",
            },
            "threshold": {
                "type": "number",
                "description": "Sensitivity threshold (default: 3.0)",
                "default": 3.0,
            },
            "explain": {
                "type": "boolean",
                "description": "Use AI to explain anomalies (default: false)",
                "default": False,
            },
        },
        "required": [],
    },
}
