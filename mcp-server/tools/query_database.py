"""
MCP Tool: query_database
==========================
Executes SQL or natural language queries against the data warehouse.
Supports both raw SQL and natural-language-to-SQL conversion via Claude.
"""

import json
import logging
from typing import Any

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.utils.ai_client import AIClient

logger = logging.getLogger(__name__)


async def query_database(
    query: str,
    query_type: str = "auto",
    limit: int = 100,
    db: DatabaseConnector = None,
    ai: AIClient = None,
) -> dict[str, Any]:
    """
    Execute a query against the database.

    Args:
        query: SQL query string or natural language question.
        query_type: "sql", "natural_language", or "auto" (detect automatically).
        limit: Maximum rows to return (default 100).
        db: DatabaseConnector instance.
        ai: AIClient instance (required for natural language queries).

    Returns:
        Dictionary with columns, rows, row_count, execution_time, and optionally
        the generated SQL if the input was natural language.
    """
    if db is None:
        return {"error": "Database connector not initialized"}

    # Detect query type
    if query_type == "auto":
        query_type = _detect_query_type(query)
        logger.info(f"Auto-detected query type: {query_type}")

    sql = query
    generated_sql = None

    # Convert natural language to SQL
    if query_type == "natural_language":
        if ai is None:
            return {"error": "AI client required for natural language queries. Set ANTHROPIC_API_KEY."}

        schema_info = _get_schema_info(db)
        result = ai.generate_sql(query, schema_info)

        if "error" in result:
            return {"error": f"SQL generation failed: {result['error']}"}

        sql = result["sql"]
        generated_sql = sql
        logger.info(f"Generated SQL: {sql}")

    # Apply limit if not already present
    sql_upper = sql.strip().upper()
    if "LIMIT" not in sql_upper and sql_upper.startswith("SELECT"):
        sql = f"{sql.rstrip(';')} LIMIT {limit}"

    # Execute
    result = db.execute_query(sql)

    if "error" in result:
        return result

    response = {
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
        "execution_time_ms": result["execution_time_ms"],
    }

    if generated_sql:
        response["generated_sql"] = generated_sql
        response["original_question"] = query

    return response


def _detect_query_type(query: str) -> str:
    """Heuristic to detect if input is SQL or natural language."""
    sql_keywords = {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "WITH", "SHOW", "DESCRIBE"}
    first_word = query.strip().split()[0].upper() if query.strip() else ""
    if first_word in sql_keywords:
        return "sql"
    return "natural_language"


def _get_schema_info(db: DatabaseConnector) -> str:
    """Build a schema description string for the AI."""
    tables = db.get_tables()
    views = db.get_views()
    lines = ["Available tables and views:\n"]

    for table in tables:
        schema = db.get_schema(table["name"])
        cols = ", ".join([f'{c["column"]} ({c["type"]})' for c in schema])
        lines.append(f"TABLE {table['name']} ({table['row_count']} rows): {cols}")

    for view_name in views:
        schema = db.get_schema(view_name)
        cols = ", ".join([f'{c["column"]} ({c["type"]})' for c in schema])
        lines.append(f"VIEW {view_name}: {cols}")

    return "\n".join(lines)


# Tool metadata for MCP registration
TOOL_DEFINITION = {
    "name": "query_database",
    "description": (
        "Execute a SQL query or natural language question against the data warehouse. "
        "Supports DuckDB SQL syntax. Natural language questions are automatically "
        "converted to SQL using AI."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL query or natural language question",
            },
            "query_type": {
                "type": "string",
                "enum": ["sql", "natural_language", "auto"],
                "description": "Query type: sql, natural_language, or auto (default: auto)",
                "default": "auto",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum rows to return (default: 100)",
                "default": 100,
            },
        },
        "required": ["query"],
    },
}
