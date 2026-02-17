"""
Unit Tests for Database Connector
====================================
Tests database connectivity, query execution, and schema inspection.
"""

import sys
from pathlib import Path

import pytest
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.utils.db_connector import DatabaseConnector


@pytest.fixture
def test_db(tmp_path):
    """Create a minimal test database."""
    db_path = str(tmp_path / "test.duckdb")
    con = duckdb.connect(db_path)
    con.execute("CREATE TABLE test_table (id INTEGER, name VARCHAR, value DOUBLE)")
    con.execute("INSERT INTO test_table VALUES (1, 'Alice', 100.5), (2, 'Bob', 200.3), (3, NULL, 300.1)")
    con.execute("CREATE VIEW test_view AS SELECT id, value FROM test_table WHERE value > 150")
    con.close()
    return DatabaseConnector(db_path)


class TestDatabaseConnector:
    def test_execute_query(self, test_db):
        result = test_db.execute_query("SELECT * FROM test_table")
        assert result["row_count"] == 3
        assert len(result["columns"]) == 3
        assert result["execution_time_ms"] > 0

    def test_execute_query_with_error(self, test_db):
        result = test_db.execute_query("SELECT * FROM nonexistent")
        assert "error" in result
        assert "suggestion" in result

    def test_get_tables(self, test_db):
        tables = test_db.get_tables()
        table_names = [t["name"] for t in tables]
        assert "test_table" in table_names
        test_table = next(t for t in tables if t["name"] == "test_table")
        assert test_table["row_count"] == 3

    def test_get_schema(self, test_db):
        schema = test_db.get_schema("test_table")
        assert len(schema) == 3
        col_names = [c["column"] for c in schema]
        assert "id" in col_names
        assert "name" in col_names
        assert "value" in col_names

    def test_get_sample(self, test_db):
        sample = test_db.get_sample("test_table", limit=2)
        assert sample["row_count"] == 2

    def test_get_views(self, test_db):
        views = test_db.get_views()
        assert "test_view" in views

    def test_execute_query_df(self, test_db):
        df = test_db.execute_query_df("SELECT * FROM test_table")
        assert len(df) == 3
        assert list(df.columns) == ["id", "name", "value"]

    def test_schema_nonexistent_table(self, test_db):
        schema = test_db.get_schema("nonexistent")
        assert schema == []
