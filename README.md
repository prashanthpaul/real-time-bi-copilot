# Real-Time Business Intelligence Copilot with MCP Integration

A production-ready AI-powered Business Intelligence system built on the **Model Context Protocol (MCP)**, enabling natural language data analytics, real-time insights, and anomaly detection — all controllable from VS Code or a Streamlit dashboard.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Real-Time BI Copilot                         │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────────┐    │
│  │ VS Code  │◄──►│  MCP Server  │◄──►│  DuckDB / Snowflake│    │
│  │ (Agent)  │    │  (Python)    │    │  (Data Warehouse)  │    │
│  └──────────┘    └──────┬───────┘    └────────────────────┘    │
│                         │                                       │
│                         ▼                                       │
│                  ┌──────────────┐                               │
│                  │  Claude AI   │                               │
│                  │  (Analysis)  │                               │
│                  └──────────────┘                               │
│                         │                                       │
│                         ▼                                       │
│                  ┌──────────────┐                               │
│                  │  Streamlit   │                               │
│                  │  Dashboard   │                               │
│                  └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/real-time-bi-copilot.git
cd real-time-bi-copilot
chmod +x scripts/setup.sh && ./scripts/setup.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 3. Generate sample data and start
python scripts/generate_data.py
streamlit run streamlit-app/app.py
```

## Features

### MCP Server Tools
| Tool | Description |
|------|-------------|
| `query_database` | Execute SQL or natural language queries against the data warehouse |
| `analyze_data` | Perform statistical analysis and generate summary statistics |
| `generate_insights` | AI-powered business insight generation using Claude |
| `detect_anomalies` | Automated anomaly detection with severity classification |

### Streamlit Control Center
- **Data Explorer** — Browse tables, view schemas, preview data
- **Query Interface** — Natural language to SQL with instant results
- **Insights Dashboard** — Real-time KPIs, charts, and AI-generated insights
- **System Health** — Monitor MCP server, database, and API status

### VS Code Integration
- Use Claude in VS Code agent mode to query data directly
- MCP tools available as agent actions
- Natural language data analysis from your editor

## Tech Stack

| Component | Technology |
|-----------|------------|
| MCP Server | Python + Official MCP SDK |
| Database | DuckDB (local) / Snowflake (cloud) |
| AI Engine | Claude (Anthropic API) |
| Dashboard | Streamlit + Plotly |
| Deployment | Docker + Docker Compose |

## Project Structure

```
real-time-bi-copilot/
├── mcp-server/          # MCP server with tools, resources, prompts
├── streamlit-app/       # Multi-page Streamlit dashboard
├── data/                # Sample data and database
├── vscode-config/       # VS Code MCP configuration
├── scripts/             # Setup, test, and demo scripts
├── docs/                # Architecture, API, migration guides
├── tests/               # Unit and integration tests
└── deployment/          # Docker and Kubernetes configs
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and data flow
- [MCP Protocol](docs/MCP_PROTOCOL.md) — MCP implementation details
- [API Reference](docs/API_REFERENCE.md) — Tool, resource, and prompt specs
- [Snowflake Migration](docs/SNOWFLAKE_MIGRATION.md) — Moving to cloud data warehouse
- [Power BI Integration](docs/POWERBI_INTEGRATION.md) — Enterprise BI connectivity
- [Setup Guide](SETUP.md) — Detailed installation instructions

## Requirements

- Python 3.11+
- Anthropic API key
- Docker (optional, for containerized deployment)
- VS Code (optional, for agent mode integration)

## License

MIT
