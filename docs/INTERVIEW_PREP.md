# Interview Preparation Guide

## 30-Second Pitch

> "I built a Real-Time Business Intelligence Copilot that uses the Model Context Protocol to enable AI-powered data analytics. It connects Claude AI to a data warehouse, allowing users to query data in natural language, get AI-generated business insights, and detect anomalies automatically — all from VS Code or a Streamlit dashboard. The system is production-ready with Docker deployment and designed for easy migration from local DuckDB to Snowflake."

## 5-Minute Demo Script

See `DEMO_SCRIPT.md` for the full walkthrough.

## Technical Q&A

### Architecture & Design (15 questions)

**Q1: Why did you choose MCP over a custom API?**
MCP is an open standard that provides a unified interface for AI-tool interaction. It works natively with VS Code and Claude Desktop, reducing integration effort. It also separates concerns — the server exposes capabilities, and any MCP-compatible client can consume them.

**Q2: Why DuckDB instead of PostgreSQL or SQLite?**
DuckDB is optimized for analytical queries (columnar storage, vectorized execution) and its SQL dialect is compatible with Snowflake, making migration straightforward. SQLite is row-oriented and slower for analytics. PostgreSQL adds infrastructure overhead for a demo project.

**Q3: How does the natural language to SQL conversion work?**
The `query_database` tool auto-detects if input is SQL or natural language. For NL, it sends the schema information and question to Claude, which generates DuckDB-compatible SQL. The generated SQL is then executed directly on the database.

**Q4: How do you handle SQL injection in generated queries?**
DuckDB queries run on local data with no network exposure. For production, we'd add query parameterization, input sanitization, and a SQL allowlist (SELECT only, no DDL/DML).

**Q5: Why Streamlit instead of React/Next.js?**
Streamlit enables rapid prototyping in Python with built-in real-time updates, session state, and caching. For a production enterprise app, I'd consider React + a Python API backend for better customization.

**Q6: How would you scale this for millions of rows?**
Migrate to Snowflake (designed for petabyte scale), add query result caching, implement materialized views for common aggregations, and use Snowflake's auto-scaling warehouses.

**Q7: What's the difference between Tools, Resources, and Prompts in MCP?**
Tools are actions the AI can execute (like functions). Resources are data the AI can read (like files). Prompts are templates that guide the AI through multi-step workflows.

**Q8: How do you ensure data freshness in the dashboard?**
Streamlit's `@st.cache_data(ttl=60)` decorator refreshes data every 60 seconds. For true real-time, we'd use Snowpipe Streaming or database change notifications.

**Q9: What error handling patterns do you use?**
Every tool returns structured errors with type, message, and a user-friendly suggestion. The AI client handles rate limits with automatic retry. Database errors include actionable fix suggestions.

**Q10: How do you handle Claude API costs?**
Token usage tracking in the AIClient class, query caching to avoid repeat calls, concise prompts that minimize input tokens, and configurable feature flags to disable AI features when not needed.

**Q11: What's your testing strategy?**
Unit tests for each MCP tool with mock databases, integration tests for end-to-end workflows, and a smoke test script for deployment verification. Tests use temporary DuckDB databases with controlled data.

**Q12: How would you add authentication?**
For the Streamlit app: Streamlit's built-in authentication or Azure AD SSO. For the MCP server: OAuth 2.0 bearer tokens in the SSE transport. For Snowflake: service account with role-based access control.

**Q13: How does anomaly detection work?**
Two methods: Z-score (measures standard deviations from mean) and IQR (measures distance from interquartile range). Anomalies are classified by severity (low/medium/high/critical) and optionally explained by Claude.

**Q14: What monitoring would you add in production?**
Prometheus metrics for query latency and error rates, structured JSON logging for ELK/Splunk, health check endpoints, and PagerDuty alerts for critical anomalies.

**Q15: How do Tools and Resources differ in your MCP implementation?**
Tools execute logic (query, analyze, detect). Resources provide data (dataset catalog, query history). Resources are cheaper — they return cached data without computation.

### Data & Analytics (10 questions)

**Q16: How do you handle data quality issues?**
The `analyze_data` tool reports null counts, duplicate rows, and null percentages. The sample data intentionally includes 2-3% nulls and 0.5% duplicates to demonstrate handling.

**Q17: What statistical methods do you use for anomaly detection?**
Z-score (parametric, assumes normal distribution) and IQR (non-parametric, robust to outliers). Both are configurable with sensitivity thresholds.

**Q18: How would you add forecasting?**
Integrate Facebook Prophet or statsmodels ARIMA. Create a `forecast_revenue` MCP tool that fits a model on historical data and returns projections with confidence intervals.

**Q19: How do you handle missing values in analysis?**
Pandas `dropna()` for numeric calculations, explicit null counting in data quality reports, and `NaN`-safe aggregation functions throughout.

**Q20: What's your approach to data modeling?**
Star schema: fact table (sales) with dimension tables (customers, products). Pre-aggregated views (monthly_revenue, daily_kpis) for common queries.

**Q21-Q25: (Additional data questions about partitioning, indexing, ETL, data lineage, and data governance — prepared but brief.)**

### MCP & AI Integration (10 questions)

**Q26: How does stdio transport work?**
The MCP server reads JSON-RPC messages from stdin and writes responses to stdout. stderr is used for logging. VS Code spawns the server as a child process and communicates over these pipes.

**Q27: Can multiple clients connect simultaneously?**
With stdio: one client per server process. With SSE: multiple clients via HTTP. For production multi-tenancy, use SSE transport with session management.

**Q28: How do you handle Claude API rate limits?**
The AIClient catches `RateLimitError` and retries after 60 seconds. For production, implement exponential backoff and a request queue.

**Q29: How do you parse Claude's JSON responses?**
Try `json.loads()` first. If that fails, extract JSON from markdown code fences. If that fails, log a warning and return the raw text.

**Q30: What if Claude generates invalid SQL?**
The database connector catches execution errors and returns them to the AI with the error message. The AI can then self-correct and try again.

### Production & DevOps (10 questions)

**Q31-Q40: (Questions about Docker multi-stage builds, CI/CD pipelines, blue-green deployment, secrets management, performance profiling, load testing, database migrations, backup strategy, disaster recovery, and cost optimization.)**

### Behavioral & Situational (5 questions)

**Q41: What was the hardest part of building this?**
Designing the MCP tool schemas to be both AI-friendly (clear descriptions, structured output) and developer-friendly (type-safe, well-documented). The AI needs enough context to use tools effectively without overwhelming the context window.

**Q42: What would you do differently?**
Start with SSE transport from the beginning (more flexible than stdio), add WebSocket support for real-time Streamlit updates, and use a proper task queue (Celery) for long-running analyses.

**Q43: How did you test the AI integration?**
Mock the Anthropic client in unit tests, use real API calls in integration tests with a test budget cap, and manual verification of generated SQL accuracy against known queries.

**Q44: What's your favorite feature?**
The natural language → SQL → results pipeline. It democratizes data access — anyone can ask questions without knowing SQL.

**Q45: Where would you take this project next?**
Add Snowflake integration, Power BI embedding, real-time data ingestion with Kafka, and a fine-tuned SQL generation model to reduce Claude API costs.
