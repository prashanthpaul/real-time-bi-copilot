# Demo Script (5 Minutes)

## Introduction (30 seconds)

> "This is a Real-Time BI Copilot — an AI-powered business intelligence system built on the Model Context Protocol. It lets you query data in natural language, get AI-generated insights, and detect anomalies automatically. Let me show you how it works."

## Demo Flow

### Part 1: MCP Server & Tools (2 minutes)

1. **Start the smoke test**:
```bash
python scripts/test_mcp_server.py
```
> "Here you can see the MCP server initializing. It registers 4 tools, 2 resources, and 5 workflow prompts. All tests pass."

2. **Run the interactive demo**:
```bash
python scripts/demo.py
```
> "Watch the query tool execute SQL against our 10,000-row sales database. Results come back in milliseconds."

> "Now the analysis tool detects a revenue trend and reports data quality metrics."

> "The anomaly detector finds unusual transactions using Z-score analysis and classifies them by severity."

### Part 2: Streamlit Dashboard (2 minutes)

3. **Open the dashboard**:
```bash
streamlit run streamlit-app/app.py
```

4. **Navigate through pages**:
   - **Home**: Show the system status — database connected, tables loaded
   - **Data Explorer**: Browse the sales table schema, preview data, column stats
   - **Query Interface**: Type a natural language question, show SQL generation
   - **Insights Dashboard**: KPI cards, revenue trends, category breakdown, anomaly alerts
   - **System Health**: API status, query performance stats

### Part 3: VS Code Integration (30 seconds)

5. **Show the MCP config**:
> "In VS Code, the MCP server connects via stdio. When you use agent mode, Claude can call these tools directly from your editor — querying data, running analysis, detecting anomalies — all through natural language."

## Technical Discussion Points

- **MCP Protocol**: Explain tools vs resources vs prompts
- **AI Integration**: NL→SQL pipeline, structured insight generation
- **Scalability**: DuckDB → Snowflake migration path
- **Production Readiness**: Docker, health checks, logging, error handling
- **Data Quality**: Built-in null detection, duplicate detection, outlier detection

## Wrap Up (30 seconds)

> "The system is containerized with Docker, tested with pytest, and documented with migration guides for Snowflake and Power BI. It's designed to be production-ready while being easy to demo and extend."
