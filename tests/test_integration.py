"""
Integration Tests
====================
Tests complete workflows: data generation → database → tool execution.
"""

import asyncio
import sys
from pathlib import Path

import pytest
import duckdb
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.tools.query_database import query_database
from mcp_server.tools.analyze_data import analyze_data
from mcp_server.tools.detect_anomalies import detect_anomalies
from mcp_server.resources.datasets import list_datasets, get_dataset
from mcp_server.resources.query_history import QueryHistory
from mcp_server.prompts.analytics_workflows import list_prompts, get_prompt


@pytest.fixture
def full_db(tmp_path):
    """Create a database mimicking the real data generator output."""
    db_path = str(tmp_path / "integration.duckdb")
    con = duckdb.connect(db_path)

    np.random.seed(42)
    n = 500
    dates = pd.date_range("2024-01-01", periods=365, freq="D")

    sales_data = {
        "transaction_id": [f"TXN-{i:06d}" for i in range(n)],
        "transaction_date": np.random.choice(dates, n).astype(str).tolist(),
        "customer_id": [f"CUST-{np.random.randint(1, 100):05d}" for _ in range(n)],
        "product_id": [f"PROD-{np.random.randint(1, 50):04d}" for _ in range(n)],
        "product_name": np.random.choice(["Laptop Pro", "Cloud Suite", "Server Rack", "API Service"], n).tolist(),
        "category": np.random.choice(["Electronics", "Software", "Hardware", "Services"], n).tolist(),
        "subcategory": np.random.choice(["Premium", "Standard", "Basic"], n).tolist(),
        "region": np.random.choice(["North America", "Europe", "Asia Pacific"], n).tolist(),
        "quantity": np.random.randint(1, 10, n).tolist(),
        "unit_price": np.random.uniform(100, 5000, n).round(2).tolist(),
        "discount_pct": np.random.choice([0, 5, 10, 15, 20], n).tolist(),
        "revenue": np.random.uniform(100, 50000, n).round(2).tolist(),
        "cost": np.random.uniform(50, 25000, n).round(2).tolist(),
        "profit": np.random.uniform(-5000, 25000, n).round(2).tolist(),
        "sales_channel": np.random.choice(["Direct", "Partner", "Online"], n).tolist(),
        "payment_method": np.random.choice(["Credit Card", "Wire", "PO"], n).tolist(),
        "customer_segment": np.random.choice(["Enterprise", "SMB", "Startup"], n).tolist(),
    }

    df = pd.DataFrame(sales_data)
    con.execute("CREATE TABLE sales AS SELECT * FROM df")

    con.execute("""
        CREATE VIEW daily_kpis AS
        SELECT CAST(transaction_date AS DATE) AS date, COUNT(*) AS transactions,
               SUM(revenue) AS revenue, SUM(profit) AS profit
        FROM sales GROUP BY 1 ORDER BY 1
    """)

    con.close()
    return DatabaseConnector(db_path)


class TestEndToEndWorkflow:
    @pytest.mark.asyncio
    async def test_query_then_analyze(self, full_db):
        """Test querying data then analyzing it."""
        query_result = await query_database(
            query="SELECT category, SUM(revenue) as rev FROM sales GROUP BY 1",
            query_type="sql", db=full_db
        )
        assert "error" not in query_result
        assert query_result["row_count"] > 0

        analysis = await analyze_data(table_name="sales", db=full_db)
        assert "error" not in analysis
        assert analysis["total_rows"] == 500

    @pytest.mark.asyncio
    async def test_analyze_then_detect_anomalies(self, full_db):
        """Test analysis followed by anomaly detection."""
        analysis = await analyze_data(table_name="sales", db=full_db)
        assert "error" not in analysis

        anomalies = await detect_anomalies(
            table_name="sales", metric_column="revenue", db=full_db
        )
        assert "error" not in anomalies
        assert "anomalies_found" in anomalies or "baseline" in anomalies

    @pytest.mark.asyncio
    async def test_resources_list_and_get(self, full_db):
        """Test listing datasets then getting details."""
        datasets = await list_datasets(full_db)
        assert len(datasets) > 0

        sales_ds = await get_dataset("sales", full_db)
        assert "error" not in sales_ds
        assert sales_ds["row_count"] == 500
        assert len(sales_ds["columns"]) > 0
        assert len(sales_ds["sample_data"]["rows"]) == 5


class TestQueryHistory:
    def test_record_and_retrieve(self):
        qh = QueryHistory()
        qh.record("SELECT 1", "sql", 1, 5.0)
        qh.record("SELECT 2", "sql", 2, 10.0, success=False, error="fail")

        history = qh.get_history(limit=10)
        assert len(history) == 2
        assert history[0]["success"] is False

    def test_stats(self):
        qh = QueryHistory()
        qh.record("q1", "sql", 10, 50.0)
        qh.record("q2", "sql", 20, 100.0)
        qh.record("q3", "sql", 0, 5.0, success=False, error="err")

        stats = qh.get_stats()
        assert stats["total_queries"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1

    def test_clear(self):
        qh = QueryHistory()
        qh.record("q1", "sql", 1, 1.0)
        qh.clear()
        assert len(qh.get_history()) == 0


class TestPrompts:
    def test_list_prompts(self):
        prompts = list_prompts()
        assert len(prompts) >= 5
        names = [p["name"] for p in prompts]
        assert "sales_analysis" in names
        assert "custom_analysis" in names

    def test_get_prompt(self):
        result = get_prompt("sales_analysis", {"time_period": "2024"})
        assert "error" not in result
        assert len(result["messages"]) > 0
        assert "2024" in result["messages"][0]["content"]["text"]

    def test_unknown_prompt(self):
        result = get_prompt("nonexistent")
        assert "error" in result
