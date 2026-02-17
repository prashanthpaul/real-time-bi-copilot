# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                    │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  VS Code      │    │  Claude      │    │  Streamlit           │  │
│  │  Agent Mode   │    │  Desktop     │    │  Dashboard           │  │
│  │  (MCP Client) │    │  (MCP Client)│    │  (Direct DB Access)  │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
│         │                   │                        │              │
└─────────┼───────────────────┼────────────────────────┼──────────────┘
          │ stdio             │ stdio                  │ DuckDB
          ▼                   ▼                        │
┌─────────────────────────────────────────────┐        │
│              MCP SERVER                     │        │
│                                             │        │
│  ┌─────────────────────────────────────┐    │        │
│  │            TOOLS                     │    │        │
│  │  ┌─────────────┐ ┌───────────────┐  │    │        │
│  │  │ query_      │ │ analyze_      │  │    │        │
│  │  │ database    │ │ data          │  │    │        │
│  │  └─────────────┘ └───────────────┘  │    │        │
│  │  ┌─────────────┐ ┌───────────────┐  │    │        │
│  │  │ generate_   │ │ detect_       │  │    │        │
│  │  │ insights    │ │ anomalies     │  │    │        │
│  │  └─────────────┘ └───────────────┘  │    │        │
│  └─────────────────────────────────────┘    │        │
│                                             │        │
│  ┌──────────────┐  ┌────────────────────┐   │        │
│  │  RESOURCES   │  │  PROMPTS           │   │        │
│  │  - datasets  │  │  - sales_analysis  │   │        │
│  │  - history   │  │  - segmentation    │   │        │
│  └──────────────┘  │  - forecasting     │   │        │
│                    │  - dashboard        │   │        │
│                    │  - custom           │   │        │
│                    └────────────────────┘   │        │
└──────────┬──────────────────┬───────────────┘        │
           │                  │                         │
           ▼                  ▼                         ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────────┐
│   Claude AI    │   │    DuckDB      │   │    DuckDB          │
│   (Anthropic)  │   │    (Local)     │◄──│    (Shared File)   │
│                │   │                │   │                    │
│  - NL → SQL    │   │  - sales       │   └────────────────────┘
│  - Insights    │   │  - customers   │
│  - Anomaly     │   │  - products    │
│    explanation  │   │  - views       │
└────────────────┘   └────────────────┘
```

## Component Details

### MCP Server (`mcp-server/`)
- **Transport**: stdio (VS Code/Claude Desktop) or SSE (web clients)
- **Tools**: 4 tools for querying, analysis, insights, and anomaly detection
- **Resources**: Dataset catalog and query history
- **Prompts**: 5 pre-configured analysis workflows

### Streamlit Dashboard (`streamlit-app/`)
- **Direct database access** (not through MCP) for low-latency visualization
- Multi-page app with data explorer, query interface, insights, and health monitoring
- Plotly charts for interactive visualization

### Data Layer (`data/`)
- **DuckDB** for local development (Snowflake-compatible SQL)
- Sample data generator creates realistic sales data with patterns and anomalies
- Pre-built views for common analytics queries

## Data Flow

1. **Query Flow**: User question → MCP tool → (Claude for NL→SQL) → DuckDB → formatted results
2. **Insight Flow**: User question → data extraction → Claude analysis → structured insights
3. **Anomaly Flow**: Table scan → statistical detection (z-score/IQR) → optional Claude explanation
4. **Dashboard Flow**: Streamlit → DuckDB (direct) → Plotly charts

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Local DB | DuckDB | Snowflake-compatible SQL, zero config, fast analytics |
| AI | Claude API | Best reasoning for data analysis, structured output |
| Protocol | MCP | Standard protocol, VS Code native support |
| Dashboard | Streamlit | Rapid prototyping, Python-native, real-time updates |
| Charts | Plotly | Interactive, dark mode, export-ready |

## Future: Snowflake Migration

The codebase is designed for easy migration:
1. `DatabaseConnector` has a documented `SnowflakeConnector` stub
2. All SQL is DuckDB-compatible (subset of Snowflake SQL)
3. Connection string swap in `.env` is the primary change
4. See `docs/SNOWFLAKE_MIGRATION.md` for step-by-step guide
