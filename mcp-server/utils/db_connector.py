"""
Database Connector Utility
===========================
Manages database connections with a unified interface.
Supports DuckDB (local) and Snowflake (cloud) backends via a factory function.

Usage:
    from mcp_server.utils.db_connector import create_connector

    # Automatically picks DuckDB or Snowflake based on DATABASE_TYPE in .env
    db = create_connector()

    # Or explicitly:
    db = create_connector(db_type="duckdb", db_path="./data/database.duckdb")
    db = create_connector(db_type="snowflake", snowflake_config={...})
"""

import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# Abstract Base Class — shared interface for all backends
# =============================================================================

class BaseDatabaseConnector(ABC):
    """Abstract base class that defines the interface all connectors must implement."""

    @abstractmethod
    def execute_query(self, sql: str, params: list | None = None) -> dict[str, Any]:
        """Execute SQL and return {columns, rows, row_count, execution_time_ms}."""
        ...

    @abstractmethod
    def execute_query_df(self, sql: str) -> pd.DataFrame:
        """Execute SQL and return a pandas DataFrame."""
        ...

    @abstractmethod
    def get_tables(self) -> list[dict]:
        """Return [{name, row_count}, ...]."""
        ...

    @abstractmethod
    def get_schema(self, table_name: str) -> list[dict]:
        """Return [{column, type, nullable}, ...]."""
        ...

    @abstractmethod
    def get_views(self) -> list[str]:
        """Return list of view names."""
        ...

    def get_sample(self, table_name: str, limit: int = 5) -> dict:
        """Get sample rows from a table."""
        return self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")

    def get_backend_name(self) -> str:
        """Return the name of the backend (duckdb / snowflake)."""
        return self.__class__.__name__


# =============================================================================
# DuckDB Connector
# =============================================================================

class DuckDBConnector(BaseDatabaseConnector):
    """DuckDB connection manager for local development."""

    def __init__(self, db_path: str):
        import duckdb  # lazy import
        self._duckdb = duckdb
        self.db_path = db_path
        self._ensure_db_exists()
        logger.info(f"DuckDBConnector initialized: {db_path}")

    def _ensure_db_exists(self) -> None:
        path = Path(self.db_path)
        if not path.exists():
            logger.warning(f"Database not found at {self.db_path}. Run sample_data_generator.py first.")

    @contextmanager
    def connection(self):
        con = self._duckdb.connect(self.db_path, read_only=False)
        try:
            yield con
        finally:
            con.close()

    def execute_query(self, sql: str, params: list | None = None) -> dict[str, Any]:
        start = time.time()
        try:
            with self.connection() as con:
                result = con.execute(sql, params) if params else con.execute(sql)
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
        with self.connection() as con:
            return con.execute(sql).fetchdf()

    def get_tables(self) -> list[dict]:
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
        result = self.execute_query(f"DESCRIBE {table_name}")
        if result.get("error"):
            return []
        return [
            {"column": row[0], "type": row[1], "nullable": row[2] == "YES"}
            for row in result.get("rows", [])
        ]

    def get_views(self) -> list[str]:
        result = self.execute_query(
            "SELECT view_name FROM duckdb_views() WHERE NOT internal"
        )
        return [row[0] for row in result.get("rows", [])]

    def get_backend_name(self) -> str:
        return "DuckDB"


# =============================================================================
# Snowflake Connector
# =============================================================================

class SnowflakeConnector(BaseDatabaseConnector):
    """
    Snowflake connection manager for cloud data warehouse.

    Requires: pip install snowflake-connector-python
    """

    def __init__(self, config: dict):
        """
        Initialize Snowflake connection.

        Args:
            config: Dictionary with keys:
                - account: Snowflake account identifier (e.g. "xy12345.us-east-1")
                - user: Username
                - password: Password
                - warehouse: Warehouse name
                - database: Database name
                - schema: Schema name (default: "PUBLIC")
                - role: Role (optional)
        """
        try:
            import snowflake.connector
            self._sf = snowflake.connector
        except ImportError:
            raise ImportError(
                "Snowflake connector not installed. Run: pip install snowflake-connector-python"
            )

        self._config = config
        self._conn = None
        self._connect()
        logger.info(
            f"SnowflakeConnector initialized: {config.get('account')} / "
            f"{config.get('database')}.{config.get('schema', 'PUBLIC')}"
        )

    def _connect(self) -> None:
        """Establish Snowflake connection."""
        connect_params = {
            "account": self._config["account"],
            "user": self._config["user"],
            "password": self._config["password"],
            "warehouse": self._config.get("warehouse", "COMPUTE_WH"),
            "database": self._config.get("database", "BI_COPILOT"),
            "schema": self._config.get("schema", "PUBLIC"),
        }
        if self._config.get("role"):
            connect_params["role"] = self._config["role"]

        self._conn = self._sf.connect(**connect_params)
        logger.info("Snowflake connection established")

    def _ensure_connected(self) -> None:
        """Reconnect if the connection was lost."""
        try:
            self._conn.cursor().execute("SELECT 1")
        except Exception:
            logger.warning("Snowflake connection lost, reconnecting...")
            self._connect()

    @contextmanager
    def connection(self):
        """Context manager that returns the persistent connection."""
        self._ensure_connected()
        yield self._conn

    def execute_query(self, sql: str, params: list | None = None) -> dict[str, Any]:
        start = time.time()
        try:
            self._ensure_connected()
            cursor = self._conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            elapsed = round((time.time() - start) * 1000, 2)

            logger.info(f"Snowflake query executed in {elapsed}ms, returned {len(rows)} rows")
            return {
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
                "execution_time_ms": elapsed,
            }
        except Exception as e:
            elapsed = round((time.time() - start) * 1000, 2)
            logger.error(f"Snowflake query failed after {elapsed}ms: {e}")
            return {
                "error": str(e),
                "type": type(e).__name__,
                "execution_time_ms": elapsed,
                "suggestion": _get_error_suggestion(str(e)),
            }

    def execute_query_df(self, sql: str) -> pd.DataFrame:
        self._ensure_connected()
        cursor = self._conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)

    def get_tables(self) -> list[dict]:
        result = self.execute_query("SHOW TABLES")
        tables = []
        for row in result.get("rows", []):
            # SHOW TABLES in Snowflake: columns vary, name is typically at index 1
            table_name = row[1] if len(row) > 1 else row[0]
            count = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            tables.append({
                "name": table_name,
                "row_count": count["rows"][0][0] if count.get("rows") else 0,
            })
        return tables

    def get_schema(self, table_name: str) -> list[dict]:
        result = self.execute_query(f"DESCRIBE TABLE {table_name}")
        if result.get("error"):
            return []
        return [
            {
                "column": row[0],
                "type": row[1],
                "nullable": row[3] == "Y" if len(row) > 3 else True,
            }
            for row in result.get("rows", [])
        ]

    def get_views(self) -> list[str]:
        result = self.execute_query("SHOW VIEWS")
        if result.get("error"):
            return []
        return [row[1] if len(row) > 1 else row[0] for row in result.get("rows", [])]

    def get_backend_name(self) -> str:
        return "Snowflake"

    def close(self) -> None:
        """Close the Snowflake connection."""
        if self._conn:
            self._conn.close()
            logger.info("Snowflake connection closed")


# =============================================================================
# Factory Function — creates the right connector based on config
# =============================================================================

def create_connector(
    db_type: str | None = None,
    db_path: str | None = None,
    snowflake_config: dict | None = None,
) -> BaseDatabaseConnector:
    """
    Factory function to create the appropriate database connector.

    If no arguments are provided, reads from Settings (environment variables).

    Args:
        db_type: "duckdb" or "snowflake". Defaults to DATABASE_TYPE env var.
        db_path: Path to DuckDB file. Defaults to DATABASE_PATH env var.
        snowflake_config: Dict with Snowflake connection params.

    Returns:
        A BaseDatabaseConnector instance (DuckDBConnector or SnowflakeConnector).
    """
    if db_type is None:
        from mcp_server.config import settings
        db_type = settings.database_type

    db_type = db_type.lower()

    if db_type == "snowflake":
        if snowflake_config is None:
            from mcp_server.config import settings
            snowflake_config = {
                "account": settings.snowflake_account,
                "user": settings.snowflake_user,
                "password": settings.snowflake_password,
                "warehouse": settings.snowflake_warehouse,
                "database": settings.snowflake_database,
                "schema": settings.snowflake_schema,
            }

        # Validate required fields
        missing = [k for k in ("account", "user", "password") if not snowflake_config.get(k)]
        if missing:
            raise ValueError(
                f"Missing Snowflake config: {missing}. "
                "Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD in .env"
            )

        logger.info("Creating Snowflake connector...")
        return SnowflakeConnector(snowflake_config)

    else:
        if db_path is None:
            from mcp_server.config import settings
            db_path = settings.resolve_database_path()

        logger.info("Creating DuckDB connector...")
        return DuckDBConnector(db_path)


# Keep backward compatibility — old code uses DatabaseConnector directly
DatabaseConnector = DuckDBConnector


# =============================================================================
# Helpers
# =============================================================================

def _get_error_suggestion(error_msg: str) -> str:
    """Return a user-friendly suggestion based on common errors."""
    msg = error_msg.lower()
    if "no such table" in msg or "does not exist" in msg:
        return "Table not found. Run 'python data/sample_data_generator.py' to create tables."
    if "syntax error" in msg:
        return "SQL syntax error. Check your query for typos or missing keywords."
    if "permission" in msg:
        return "Permission denied. Check file permissions or Snowflake role."
    if "could not connect" in msg or "connection refused" in msg:
        return "Connection failed. Check your Snowflake account/credentials in .env."
    if "warehouse" in msg:
        return "Snowflake warehouse issue. Check that your warehouse is running and accessible."
    if "authentication" in msg or "incorrect" in msg:
        return "Authentication failed. Check SNOWFLAKE_USER and SNOWFLAKE_PASSWORD in .env."
    return "An unexpected error occurred. Check the logs for details."
