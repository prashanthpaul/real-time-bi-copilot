"""
MCP Resource: datasets
========================
Exposes available database tables and views as MCP resources,
including schema information, row counts, and sample data.
"""

import logging
from typing import Any

from mcp_server.utils.db_connector import DatabaseConnector

logger = logging.getLogger(__name__)


async def list_datasets(db: DatabaseConnector) -> list[dict[str, Any]]:
    """List all available datasets (tables and views)."""
    tables = db.get_tables()
    views = db.get_views()

    datasets = []
    for table in tables:
        schema = db.get_schema(table["name"])
        datasets.append({
            "uri": f"bi-copilot://datasets/{table['name']}",
            "name": table["name"],
            "type": "table",
            "row_count": table["row_count"],
            "columns": schema,
            "description": _get_table_description(table["name"]),
        })

    for view_name in views:
        schema = db.get_schema(view_name)
        datasets.append({
            "uri": f"bi-copilot://datasets/{view_name}",
            "name": view_name,
            "type": "view",
            "columns": schema,
            "description": _get_table_description(view_name),
        })

    return datasets


async def get_dataset(name: str, db: DatabaseConnector) -> dict[str, Any]:
    """Get detailed information about a specific dataset."""
    schema = db.get_schema(name)
    if not schema:
        return {"error": f"Dataset '{name}' not found"}

    sample = db.get_sample(name, limit=5)
    count_result = db.execute_query(f"SELECT COUNT(*) FROM {name}")
    row_count = count_result["rows"][0][0] if count_result.get("rows") else 0

    return {
        "uri": f"bi-copilot://datasets/{name}",
        "name": name,
        "row_count": row_count,
        "columns": schema,
        "sample_data": {
            "columns": sample.get("columns", []),
            "rows": sample.get("rows", []),
        },
        "description": _get_table_description(name),
    }


def _get_table_description(name: str) -> str:
    """Return a human-readable description for known tables/views."""
    descriptions = {
        "sales": "Transaction-level sales data with revenue, product, customer, and region details",
        "customers": "Customer master data with company name, segment, region, and status",
        "products": "Product catalog with pricing, categories, and subcategories",
        "monthly_revenue": "Aggregated monthly revenue by category and region",
        "top_products": "Product performance ranking by total revenue",
        "customer_summary": "Customer lifetime value and order history summary",
        "daily_kpis": "Daily key performance indicators (revenue, transactions, unique customers)",
    }
    return descriptions.get(name, f"Dataset: {name}")


RESOURCE_DEFINITIONS = [
    {
        "uri": "bi-copilot://datasets",
        "name": "Available Datasets",
        "description": "List all tables and views available for analysis",
        "mimeType": "application/json",
    }
]
