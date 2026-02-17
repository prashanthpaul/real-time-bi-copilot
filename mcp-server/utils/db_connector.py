"""
Database Connector Utility
===========================
Manages DuckDB connections with query execution, error handling,
and a documented migration path to Snowflake.
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """DuckDB connection manager with query execution utilities."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_exists()
        logger.info(f"DatabaseConnector initialized: {db_path}")

    def _ensure_db_exists(self) -> None:
        """Verify the database file exists."""
        path = Path(self.db_path)
        if not path.exists():
            logger.warning(f"Database not found at {self.db_path}. Run sample_data_generator.py first.")

    @contextmanager
    def connection(self):
        """Context manager for DuckDB connections."""
        con = duckdb.connect(self.db_path, read_only=False)
        try:
            yield con
        finally:
            con.close()

    def execute_query(self, sql: str, params: list | None = None) -> dict[str, Any]:
        """
        Execute a SQL query and return results as a dictionary.

        Returns:
            {
                "columns": [...],
                "rows": [[...], ...],
                "row_count": int,
                "execution_time_ms": float
            }
        """
        start = time.time()
        try:
            with self.connection() as con:
                if params:
                    result = con.execute(sql, params)
                else:
                    result = con.execute(sql)

                columns = [desc[0] for desc in result.description] if result.description else []
                rows = result.fetchall()
                elapsed = round((time.time() - start) * 1000, 2)

                logger.info(f"Query executed in {elapsed}ms, returned {len(rows)} rows")
                return {
                    "columns": columns,
                    "rows": [list(row) for row in rows],
                    "row_count": len(rows),
                    "execution_time_ms": elapsed,
                }
        except Exception as e:
            elapsed = round((time.time() - start) * 1000, 2)
            logger.error(f"Query failed after {elapsed}ms: {e}")
            return {
                "error": str(e),
                "type": type(e).__name__,
                "execution_time_ms": elapsed,
                "suggestion": _get_error_suggestion(str(e)),
            }

    def execute_query_df(self, sql: str) -> pd.DataFrame:
        """Execute a query and return results as a pandas DataFrame."""
        with self.connection() as con:
            return con.execute(sql).fetchdf()

    def get_tables(self) -> list[dict]:
        """List all tables with row counts."""
        result = self.execute_query("SHOW TABLES")
        tables = []
        for row in result.get("rows", []):
            table_name = row[0]
            count = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            tables.append({
                "name": table_name,
                "row_count": count["rows"][0][0] if count.get("rows") else 0,
            })
        return tables

    def get_schema(self, table_name: str) -> list[dict]:
        """Get column schema for a table."""
        result = self.execute_query(f"DESCRIBE {table_name}")
        if result.get("error"):
            return []
        return [
            {"column": row[0], "type": row[1], "nullable": row[2] == "YES"}
            for row in result.get("rows", [])
        ]

    def get_sample(self, table_name: str, limit: int = 5) -> dict:
        """Get sample rows from a table."""
        return self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")

    def get_views(self) -> list[str]:
        """List all user-created views."""
        result = self.execute_query(
            "SELECT view_name FROM duckdb_views() WHERE NOT internal"
        )
        return [row[0] for row in result.get("rows", [])]


# TODO: Snowflake connector — see docs/SNOWFLAKE_MIGRATION.md
# class SnowflakeConnector:
#     """Snowflake connection manager (future implementation)."""
#     pass


def _get_error_suggestion(error_msg: str) -> str:
    """Return a user-friendly suggestion based on common errors."""
    msg = error_msg.lower()
    if "no such table" in msg or "does not exist" in msg:
        return "Table not found. Run 'python data/sample_data_generator.py' to create tables."
    if "syntax error" in msg:
        return "SQL syntax error. Check your query for typos or missing keywords."
    if "permission" in msg:
        return "Permission denied. Check file permissions on the database file."
    return "An unexpected error occurred. Check the logs for details."
