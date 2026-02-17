"""
MCP Server Smoke Test
========================
Verifies the MCP server can initialize and all tools/resources work.

Usage:
    python scripts/test_mcp_server.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.config import settings
from mcp_server.tools.query_database import query_database
from mcp_server.tools.analyze_data import analyze_data
from mcp_server.tools.detect_anomalies import detect_anomalies
from mcp_server.resources.datasets import list_datasets, get_dataset
from mcp_server.prompts.analytics_workflows import list_prompts


def print_result(name: str, result: dict, success: bool):
    status = "✅" if success else "❌"
    print(f"  {status} {name}")
    if not success and "error" in result:
        print(f"     Error: {result['error']}")


async def main():
    print("=" * 50)
    print(" MCP Server Smoke Test")
    print("=" * 50)

    db_path = settings.resolve_database_path()
    print(f"\nDatabase: {db_path}")

    db = DatabaseConnector(db_path)
    passed = 0
    failed = 0

    # Test 1: Database connectivity
    print("\n--- Database ---")
    tables = db.get_tables()
    if tables:
        print_result("Database connection", {}, True)
        print_result(f"Found {len(tables)} tables", {}, True)
        passed += 2
    else:
        print_result("Database connection", {"error": "No tables found"}, False)
        failed += 1
        print("\n⚠️  Run 'python data/sample_data_generator.py' first.")
        return

    # Test 2: query_database tool
    print("\n--- Tools ---")
    result = await query_database(query="SELECT COUNT(*) as total FROM sales", query_type="sql", db=db)
    ok = "error" not in result
    print_result("query_database (SQL)", result, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # Test 3: analyze_data tool
    result = await analyze_data(table_name="sales", db=db)
    ok = "error" not in result
    print_result("analyze_data", result, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # Test 4: detect_anomalies tool
    result = await detect_anomalies(table_name="sales", metric_column="revenue", db=db)
    ok = "error" not in result
    print_result("detect_anomalies", result, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # Test 5: Resources
    print("\n--- Resources ---")
    datasets = await list_datasets(db)
    ok = len(datasets) > 0
    print_result(f"list_datasets ({len(datasets)} found)", {}, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    dataset = await get_dataset("sales", db)
    ok = "error" not in dataset
    print_result("get_dataset (sales)", dataset, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # Test 6: Prompts
    print("\n--- Prompts ---")
    prompts = list_prompts()
    ok = len(prompts) > 0
    print_result(f"list_prompts ({len(prompts)} found)", {}, ok)
    passed += 1 if ok else 0
    failed += 0 if ok else 1

    # Summary
    print("\n" + "=" * 50)
    total = passed + failed
    print(f" Results: {passed}/{total} passed")
    if failed == 0:
        print(" Status: All tests passed! ✅")
    else:
        print(f" Status: {failed} test(s) failed ❌")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
