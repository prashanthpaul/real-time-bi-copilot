"""
Configuration Management for MCP Server
=========================================
Loads settings from environment variables with sensible defaults.
Uses pydantic-settings for validation and type safety.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Paths ---
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent,
        description="Root directory of the project",
    )
    database_path: str = Field(
        default="./data/database.duckdb",
        description="Path to DuckDB database file",
    )

    # --- Database ---
    database_type: str = Field(default="duckdb", description="Database backend: duckdb or snowflake")

    # --- Snowflake (future) ---
    snowflake_account: str = Field(default="", description="Snowflake account identifier")
    snowflake_user: str = Field(default="", description="Snowflake username")
    snowflake_password: str = Field(default="", description="Snowflake password")
    snowflake_warehouse: str = Field(default="COMPUTE_WH", description="Snowflake warehouse")
    snowflake_database: str = Field(default="BI_COPILOT", description="Snowflake database")
    snowflake_schema: str = Field(default="PUBLIC", description="Snowflake schema")

    # --- Claude AI ---
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    claude_model: str = Field(default="claude-sonnet-4-5-20250929", description="Claude model to use")

    # --- MCP Server ---
    mcp_server_host: str = Field(default="localhost", description="MCP server host")
    mcp_server_port: int = Field(default=8080, description="MCP server port")
    mcp_transport: str = Field(default="stdio", description="MCP transport: stdio or sse")

    # --- Features ---
    enable_ai_insights: bool = Field(default=True, description="Enable AI-powered insights")
    enable_anomaly_detection: bool = Field(default=True, description="Enable anomaly detection")
    enable_query_cache: bool = Field(default=True, description="Enable query result caching")
    cache_ttl_seconds: int = Field(default=300, description="Cache time-to-live in seconds")

    # --- Logging ---
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format: json or text")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def resolve_database_path(self) -> str:
        """Resolve database path relative to project root."""
        db_path = Path(self.database_path)
        if not db_path.is_absolute():
            db_path = self.project_root / db_path
        return str(db_path)


# Singleton instance
settings = Settings()
