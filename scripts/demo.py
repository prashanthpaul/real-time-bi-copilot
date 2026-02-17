"""
Demo Automation Script
========================
Runs through key BI Copilot features for a live demo.

Usage:
    python scripts/demo.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from mcp_server.utils.db_connector import DatabaseConnector
from mcp_server.config import settings
from mcp_server.tools.query_database import query_database
from mcp_server.tools.analyze_data import analyze_data
from mcp_server.tools.detect_anomalies import detect_anomalies

console = Console()


def pause(msg: str = "Press Enter to continue..."):
    console.print(f"\n[dim]{msg}[/dim]")
    input()


async def main():
    console.print(Panel.fit(
        "[bold cyan]Real-Time BI Copilot — Live Demo[/bold cyan]\n"
        "AI-Powered Business Intelligence with MCP Integration",
        border_style="cyan",
    ))

    db = DatabaseConnector(settings.resolve_database_path())

    # --- Demo 1: SQL Query ---
    pause("Demo 1: SQL Query Execution")
    console.print("\n[bold yellow]1. Querying top 5 products by revenue...[/bold yellow]")
    sql = "SELECT product_name, category, SUM(revenue) as total_revenue FROM sales GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5"
    console.print(Syntax(sql, "sql", theme="monokai"))

    result = await query_database(query=sql, query_type="sql", db=db)

    table = Table(title="Top 5 Products by Revenue")
    for col in result["columns"]:
        table.add_column(col)
    for row in result["rows"]:
        table.add_row(*[str(v) for v in row])
    console.print(table)
    console.print(f"[dim]Executed in {result['execution_time_ms']}ms[/dim]")

    # --- Demo 2: Data Analysis ---
    pause("Demo 2: Statistical Analysis")
    console.print("\n[bold yellow]2. Running statistical analysis on sales data...[/bold yellow]")

    result = await analyze_data(table_name="sales", db=db)
    console.print(f"[green]Analyzed {result['total_rows']:,} rows across {result['total_columns']} columns[/green]")

    if "trend" in result:
        t = result["trend"]
        console.print(f"\n[bold]Trend Detected:[/bold] Revenue is [{'green' if t['direction'] == 'increasing' else 'red'}]{t['direction']}[/] ({t['overall_change_pct']:+.1f}% over {t['periods']} periods)")

    if "data_quality" in result:
        dq = result["data_quality"]
        console.print(f"[bold]Data Quality:[/bold] {dq['null_percentage']}% nulls, {dq['duplicate_rows']} duplicates")

    # --- Demo 3: Anomaly Detection ---
    pause("Demo 3: Anomaly Detection")
    console.print("\n[bold yellow]3. Detecting anomalies in revenue...[/bold yellow]")

    result = await detect_anomalies(table_name="sales", metric_column="revenue", method="zscore", threshold=3.0, db=db)
    console.print(f"[green]Found {result['anomalies_found']} anomalies ({result['anomaly_rate_pct']}% of data)[/green]")

    if result.get("severity_breakdown"):
        console.print(f"[bold]Severity:[/bold] {result['severity_breakdown']}")

    if result.get("anomalies"):
        table = Table(title="Sample Anomalies")
        table.add_column("Date")
        table.add_column("Value")
        table.add_column("Severity")
        table.add_column("Deviation (σ)")
        for a in result["anomalies"][:5]:
            color = {"critical": "red", "high": "yellow", "medium": "cyan"}.get(a["severity"], "white")
            table.add_row(a["date"], f"${a['value']:,.2f}", f"[{color}]{a['severity']}[/{color}]", str(a["deviation"]))
        console.print(table)

    # --- Done ---
    console.print(Panel.fit(
        "[bold green]Demo Complete![/bold green]\n\n"
        "Key Takeaways:\n"
        "  • Natural language → SQL conversion via Claude AI\n"
        "  • Statistical analysis with trend detection\n"
        "  • Automated anomaly detection with severity classification\n"
        "  • MCP protocol for VS Code agent integration\n"
        "  • Production-ready with Docker deployment",
        border_style="green",
    ))


if __name__ == "__main__":
    asyncio.run(main())
