"""
Unit Tests for MCP Tools
===========================
Tests each MCP tool independently with a test database.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.tools.query_database import query_database
from mcp_server.tools.analyze_data import analyze_data
from mcp_server.tools.detect_anomalies import detect_anomalies


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database with sample data."""
    db_path = str(tmp_path / "test.duckdb")
    con = duckdb.connect(db_path)

    # Create test sales table
    np.random.seed(42)
    n = 200
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    data = {
        "transaction_id": [f"TXN-{i:04d}" for i in range(n)],
        "transaction_date": dates.strftime("%Y-%m-%d").tolist(),
        "product_name": np.random.choice(["Widget A", "Widget B", "Gadget C"], n).tolist(),
        "category": np.random.choice(["Electronics", "Software"], n).tolist(),
        "region": np.random.choice(["North", "South", "East", "West"], n).tolist(),
        "revenue": np.random.uniform(50, 5000, n).round(2).tolist(),
        "profit": np.random.uniform(10, 2000, n).round(2).tolist(),
        "quantity": np.random.randint(1, 20, n).tolist(),
        "customer_id": [f"CUST-{np.random.randint(1, 50):03d}" for _ in range(n)],
    }
    # Add a few outliers
    data["revenue"][5] = 50000.0
    data["revenue"][10] = 75000.0

    df = pd.DataFrame(data)
    con.execute("CREATE TABLE sales AS SELECT * FROM df")
    con.close()

    return DatabaseConnector(db_path)


class TestQueryDatabase:
    @pytest.mark.asyncio
    async def test_sql_query(self, test_db):
        result = await query_database(query="SELECT COUNT(*) FROM sales", query_type="sql", db=test_db)
        assert "error" not in result
        assert result["row_count"] == 1
        assert result["rows"][0][0] == 200

    @pytest.mark.asyncio
    async def test_sql_with_limit(self, test_db):
        result = await query_database(query="SELECT * FROM sales", query_type="sql", limit=5, db=test_db)
        assert "error" not in result
        assert result["row_count"] == 5

    @pytest.mark.asyncio
    async def test_invalid_sql(self, test_db):
        result = await query_database(query="SELECT * FROM nonexistent_table", query_type="sql", db=test_db)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_no_db_connector(self):
        result = await query_database(query="SELECT 1", db=None)
        assert "error" in result


class TestAnalyzeData:
    @pytest.mark.asyncio
    async def test_basic_analysis(self, test_db):
        result = await analyze_data(table_name="sales", db=test_db)
        assert "error" not in result
        assert result["total_rows"] == 200
        assert "numeric_summary" in result
        assert "data_quality" in result

    @pytest.mark.asyncio
    async def test_specific_columns(self, test_db):
        result = await analyze_data(table_name="sales", columns=["revenue", "profit"], db=test_db)
        assert "error" not in result
        assert "revenue" in result.get("numeric_summary", {})

    @pytest.mark.asyncio
    async def test_group_by(self, test_db):
        result = await analyze_data(table_name="sales", group_by="category", db=test_db)
        assert "error" not in result
        assert "grouped_analysis" in result

    @pytest.mark.asyncio
    async def test_nonexistent_table(self, test_db):
        result = await analyze_data(table_name="fake_table", db=test_db)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_missing_columns(self, test_db):
        result = await analyze_data(table_name="sales", columns=["nonexistent"], db=test_db)
        assert "error" in result


class TestDetectAnomalies:
    @pytest.mark.asyncio
    async def test_zscore_detection(self, test_db):
        result = await detect_anomalies(
            table_name="sales", metric_column="revenue", method="zscore", threshold=3.0, db=test_db
        )
        assert "error" not in result
        assert result["anomalies_found"] >= 0
        assert "baseline" in result

    @pytest.mark.asyncio
    async def test_iqr_detection(self, test_db):
        result = await detect_anomalies(
            table_name="sales", metric_column="revenue", method="iqr", threshold=1.5, db=test_db
        )
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_detects_outliers(self, test_db):
        result = await detect_anomalies(
            table_name="sales", metric_column="revenue", method="zscore", threshold=2.5, db=test_db
        )
        assert result["anomalies_found"] > 0

    @pytest.mark.asyncio
    async def test_invalid_column(self, test_db):
        result = await detect_anomalies(
            table_name="sales", metric_column="nonexistent", db=test_db
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_method(self, test_db):
        result = await detect_anomalies(
            table_name="sales", metric_column="revenue", method="invalid", db=test_db
        )
        assert "error" in result
