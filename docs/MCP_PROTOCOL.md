# MCP Protocol Implementation

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI models to interact with external tools, data sources, and services through a unified interface. It defines three primitives:

- **Tools** — Functions the AI can call (like API endpoints)
- **Resources** — Data the AI can read (like files or databases)
- **Prompts** — Pre-configured templates that guide AI behavior

## Our MCP Implementation

### Tools

#### `query_database`
Execute SQL or natural language queries against the data warehouse.

```json
{
  "name": "query_database",
  "arguments": {
    "query": "What are the top 5 products by revenue?",
    "query_type": "auto",
    "limit": 100
  }
}
```

**Flow**: Input → detect type → (NL? → Claude → SQL) → execute on DuckDB → return results

#### `analyze_data`
Statistical analysis of a database table.

```json
{
  "name": "analyze_data",
  "arguments": {
    "table_name": "sales",
    "columns": ["revenue", "profit"],
    "group_by": "category"
  }
}
```

**Returns**: Summary statistics, correlations, data quality metrics, trend detection.

#### `generate_insights`
AI-powered business insight generation.

```json
{
  "name": "generate_insights",
  "arguments": {
    "question": "Why did Q4 revenue spike?",
    "table_name": "sales",
    "time_period": "2024"
  }
}
```

**Flow**: Query data → build summary → send to Claude → parse structured insights.

#### `detect_anomalies`
Statistical anomaly detection with optional AI explanation.

```json
{
  "name": "detect_anomalies",
  "arguments": {
    "table_name": "sales",
    "metric_column": "revenue",
    "method": "zscore",
    "threshold": 3.0,
    "explain": true
  }
}
```

**Methods**: Z-score (default), IQR. Severity: low/medium/high/critical.

### Resources

| URI | Description |
|-----|-------------|
| `bi-copilot://datasets` | List all tables and views |
| `bi-copilot://datasets/{name}` | Schema + sample for a specific table |
| `bi-copilot://query-history` | Recent queries with performance stats |

### Prompts

| Prompt | Description |
|--------|-------------|
| `sales_analysis` | End-to-end sales performance workflow |
| `customer_segmentation` | Customer LTV and segment analysis |
| `revenue_forecast` | Trend analysis and projection |
| `performance_dashboard` | KPI dashboard data package |
| `custom_analysis` | Build your own workflow |

## Transport

- **stdio** (default): For VS Code agent mode and Claude Desktop
- **SSE**: For web-based clients (future)

## VS Code Integration

Copy `vscode-config/mcp.json` to your workspace `.vscode/mcp.json`. The server starts automatically when VS Code's agent mode connects.

## Debugging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python -m mcp_server.server
```

Logs go to stderr (stdio transport keeps stdout clean for MCP messages).
