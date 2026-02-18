# Real-Time BI Copilot — Project Overview

A simple, beginner-friendly explanation of what this project is, why it exists, and how everything works together.

---

## 1. What Is This Project?

This is an **AI-powered Business Intelligence tool** that lets you ask questions about your business data in plain English and get instant answers.

Instead of writing complex SQL queries manually, you just ask:
> "What were the top 5 products by revenue last quarter?"

And the system:
1. Understands your question (using AI)
2. Converts it to SQL automatically
3. Runs it on your cloud database (Snowflake)
4. Returns the results with analysis

---

## 2. Why Did We Build This? (Problem Statement)

### The Problem

In most companies, getting answers from data is slow and painful:

- **Business users** (managers, executives) have questions about sales, revenue, customers
- **But they can't write SQL** — they depend on data analysts
- **Data analysts** are busy — requests sit in a queue for days
- **Dashboards** show fixed charts — they can't answer new questions on the fly

### The Solution

Build an **AI Copilot** that:
- Understands plain English questions
- Queries the database automatically
- Returns answers in seconds
- Also provides a visual dashboard for common metrics
- Works inside VS Code (where developers already work)

---

## 3. Tools Used and Why

### Core Tools

| Tool | What It Is | Why We Used It |
|------|-----------|----------------|
| **Python** | Programming language | The backbone — everything is written in Python |
| **Snowflake** | Cloud data warehouse | Stores all business data (sales, customers, products) in the cloud. Used by most large companies. |
| **DuckDB** | Local database | For offline development/testing — works without internet |
| **Claude AI (Anthropic)** | Large Language Model (like ChatGPT) | Converts English questions to SQL, generates business insights, explains anomalies |
| **Streamlit** | Python web framework | Builds the interactive dashboard (charts, tables, KPIs) — no HTML/CSS needed |
| **Plotly** | Charting library | Creates the interactive charts inside Streamlit |

### Infrastructure Tools

| Tool | What It Is | Why We Used It |
|------|-----------|----------------|
| **MCP (Model Context Protocol)** | AI communication protocol | Lets Claude talk to our database (explained in detail below) |
| **Docker** | Container platform | Packages the entire app so anyone can run it with one command |
| **Git / GitHub** | Version control | Tracks code changes, hosts the project publicly |
| **AWS EC2** | Cloud server | Runs the app on the internet so anyone can access it |
| **pytest** | Testing framework | Makes sure the code works correctly (31 tests) |

---

## 4. What Is MCP? (The Key Innovation)

### The Simple Explanation

**MCP = Model Context Protocol**

Think of it like a **universal translator between AI and your tools**.

Without MCP:
```
You ask Claude: "What are the top products?"
Claude says: "I don't have access to your database. Please provide the data."
(Claude is stuck — it can't reach your data)
```

With MCP:
```
You ask Claude: "What are the top products?"
Claude thinks: "I have a tool called query_database. Let me use it."
Claude calls: query_database("top products by revenue")
MCP Server: Converts to SQL → Runs on Snowflake → Returns results
Claude says: "ThinkPad X1 leads at $7M, followed by..."
(Claude can now access your data through the MCP server)
```

### How MCP Works (Step by Step)

```
Step 1: You ask a question in VS Code
        ↓
Step 2: Claude (AI) receives your question
        ↓
Step 3: Claude sees it has MCP tools available:
        - query_database (run SQL or ask in English)
        - analyze_data (get statistics)
        - generate_insights (AI analysis)
        - detect_anomalies (find outliers)
        ↓
Step 4: Claude picks the right tool and calls it
        ↓
Step 5: MCP Server (our Python code) receives the call
        ↓
Step 6: MCP Server runs the query on Snowflake
        ↓
Step 7: Results flow back: Snowflake → MCP Server → Claude → You
```

### Why MCP Matters

- **Created by Anthropic** (the company behind Claude) in late 2024
- It's a new **open standard** — like USB but for AI tools
- Very few people know about it yet — having it in your portfolio is a differentiator
- Companies like Stripe, Notion, and GitHub are already building MCP servers

### The 4 MCP Tools We Built

| Tool | What It Does | Example |
|------|-------------|---------|
| **query_database** | Runs SQL or converts English to SQL | "Show me revenue by region" → generates and runs the SQL |
| **analyze_data** | Calculates statistics (mean, median, correlations, trends) | "Analyze the sales table" → returns summary stats |
| **generate_insights** | AI reads data and writes business analysis | "What are the key trends?" → "Revenue is up 15% in Q4..." |
| **detect_anomalies** | Finds unusual data points using math (Z-score, IQR) | "Find anomalies in revenue" → flags outlier transactions |

---

## 5. How the Data Works

### What Data Do We Have?

We generated realistic business data that mimics a real company:

| Table | Rows | What It Contains |
|-------|------|-----------------|
| **sales** | 10,050 | Every transaction — date, product, revenue, profit, customer, region |
| **customers** | 500 | Customer details — company name, segment, region, country |
| **products** | 80 | Product catalog — name, category, price, cost |

Plus 4 **analytics views** (pre-calculated summaries):
- **monthly_revenue** — revenue aggregated by month, category, region
- **daily_kpis** — daily transaction count, revenue, profit
- **top_products** — products ranked by revenue
- **customer_summary** — lifetime value per customer

### Data Features (Realistic Patterns)

The data isn't random — it has patterns like real business data:
- **Seasonal trends** — Q4 (Oct-Dec) has higher sales, Q1 (Jan-Feb) has a dip
- **Weekend dips** — fewer transactions on Saturday/Sunday
- **Outliers** — ~1% of transactions are unusually large (like bulk orders)
- **Missing data** — ~2-3% nulls in some columns (like real data)
- **Duplicates** — ~0.5% duplicate transactions (like real data)

---

## 6. Project Architecture

### The Big Picture

```
┌─────────────────────────────────────────────────────┐
│                    YOUR LAPTOP                       │
│                                                      │
│   VS Code + Claude ←──MCP──→ MCP Server (Python)    │
│                                    │                 │
│                                    ↓                 │
│   Streamlit Dashboard ──────→ Snowflake (Cloud DB)   │
│   (http://localhost:8501)                            │
│                                                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  AFTER DEPLOYMENT                     │
│                                                      │
│   AWS EC2 Server                                     │
│   ├── MCP Server (Python) ──→ Snowflake             │
│   └── Streamlit Dashboard ──→ Public URL             │
│                                                      │
│   VS Code + Claude (your laptop) ←──MCP──→ MCP Server│
│                                                      │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
real-time-bi-copilot/
├── mcp-server/              ← The brain (MCP server + AI logic)
│   ├── server.py            ← Main MCP server (registers tools)
│   ├── config.py            ← Reads settings from .env file
│   ├── tools/               ← The 4 MCP tools
│   │   ├── query_database.py
│   │   ├── analyze_data.py
│   │   ├── generate_insights.py
│   │   └── detect_anomalies.py
│   ├── resources/           ← MCP resources (dataset catalog, query history)
│   ├── prompts/             ← Pre-built analysis workflows
│   └── utils/               ← Database connector + AI client
│       ├── db_connector.py  ← Connects to DuckDB or Snowflake
│       └── ai_client.py     ← Talks to Claude API
│
├── streamlit-app/           ← The dashboard (what users see)
│   ├── app.py               ← Home page
│   ├── pages/
│   │   ├── 01_data_explorer.py      ← Browse tables and data
│   │   ├── 02_query_interface.py    ← Ask questions / write SQL
│   │   ├── 03_insights_dashboard.py ← Charts, KPIs, trends
│   │   └── 04_system_health.py      ← Monitor system status
│   └── components/          ← Reusable chart and metric components
│
├── data/                    ← Data files
│   ├── sample_data_generator.py  ← Generates the sample data
│   └── tableau_export/      ← CSV exports for Tableau/Power BI
│
├── scripts/                 ← Helper scripts
│   ├── load_snowflake.py    ← Loads data into Snowflake
│   └── setup.sh             ← One-command setup
│
├── tests/                   ← 31 automated tests
├── deployment/              ← Docker files
├── docs/                    ← Documentation
├── .env                     ← Secrets (API keys, passwords — never pushed to GitHub)
├── .mcp.json                ← MCP config for Claude Code
└── .vscode/mcp.json         ← MCP config for VS Code
```

---

## 7. Key Design Decisions

### Why Snowflake + DuckDB (not just one)?

- **DuckDB** for local development — works offline, no account needed, instant
- **Snowflake** for production — cloud-based, what real companies use
- A **factory pattern** (`create_connector()`) automatically picks the right one based on your `.env` setting
- This shows you understand both local development and cloud deployment

### Why MCP (not just a REST API)?

- MCP is the **new standard** for AI tool integration
- It works natively with Claude in VS Code — no extra setup
- REST APIs require building a separate frontend; MCP lets AI be the frontend
- It's what Anthropic (Claude's creator) recommends

### Why Streamlit (not React/Flask)?

- Python-only — no JavaScript/HTML/CSS needed
- Perfect for data dashboards — built-in charts, tables, metrics
- Fast to build — our 4-page dashboard is ~500 lines of Python
- Used widely in data science — interviewers recognize it

---

## 8. How Deployment Works

### Local (What You Have Now)

```
Your Mac
  └── python runs Streamlit → http://localhost:8501 (only you can see it)
  └── python runs MCP server → Claude in VS Code can query data
  └── Both connect to Snowflake (cloud) for data
```

### Production (AWS EC2)

```
AWS EC2 (cloud server)
  └── Same code runs on a Linux server in the cloud
  └── Streamlit → http://your-public-ip:8501 (anyone can see it)
  └── MCP server → accessible from your VS Code via SSH
  └── Both connect to Snowflake (cloud) for data
```

### Deployment Steps (What We Will Do)

1. **Create an AWS account** (free tier available)
2. **Launch an EC2 instance** (a virtual Linux server)
3. **SSH into the server** (connect from your terminal)
4. **Clone the GitHub repo** (`git clone your-repo`)
5. **Install Python and dependencies** (`pip install -r requirements.txt`)
6. **Set up .env** (add your API keys and Snowflake credentials)
7. **Run Streamlit** (it starts on a public URL)
8. **Optional: Add a domain name** (like `bi-copilot.yourdomain.com`)

---

## 9. How to Demo This in an Interview

### The 3-Minute Demo Script

**Step 1 — The Dashboard (30 seconds)**
> "I built a real-time BI dashboard connected to Snowflake. Here's the live URL."
> Show: KPIs, revenue trends, category breakdown

**Step 2 — The AI Copilot (60 seconds)**
> "But the real innovation is the AI copilot. Watch — I'll ask it a question in plain English."
> In VS Code, type: "What were the top 5 products by revenue last quarter?"
> Show: Claude calls MCP tool → SQL generated → Snowflake queried → results returned

**Step 3 — The Architecture (60 seconds)**
> "Under the hood, I built an MCP server — that's Anthropic's new protocol for connecting AI to tools."
> Explain: MCP server has 4 tools, connects to Snowflake, uses Claude API for NL-to-SQL
> Show: GitHub repo, clean code, tests passing

**Step 4 — The Technical Depth (30 seconds)**
> "The system supports both DuckDB for local dev and Snowflake for production, using a factory pattern."
> "It's containerized with Docker, has 31 passing tests, and is deployed on AWS."

### Questions Interviewers Might Ask

| Question | Your Answer |
|----------|-------------|
| "Why MCP instead of a REST API?" | "MCP is Anthropic's new standard for AI-tool integration. It works natively with Claude and is becoming an industry standard." |
| "How does the NL-to-SQL work?" | "The MCP server sends the user's question plus the database schema to Claude API. Claude generates SQL, which runs on Snowflake." |
| "How do you handle errors?" | "Rate limit retries with exponential backoff, SQL error suggestions, graceful fallbacks when AI is unavailable." |
| "Why both DuckDB and Snowflake?" | "DuckDB for fast local development, Snowflake for production. A factory pattern switches between them based on config." |
| "How is it deployed?" | "Docker containers on AWS EC2, with environment-based configuration. Streamlit serves the dashboard on a public URL." |
| "What about security?" | "API keys and credentials are in .env (gitignored). Snowflake uses role-based access. No secrets in the codebase." |

---

## 10. Glossary (Simple Definitions)

| Term | Simple Definition |
|------|------------------|
| **MCP** | A protocol that lets AI (Claude) use external tools — like giving AI hands to interact with your systems |
| **Snowflake** | A cloud database — like a giant spreadsheet in the cloud that can handle millions of rows |
| **DuckDB** | A small, fast database that runs on your laptop — great for testing |
| **Streamlit** | A Python library that turns scripts into web apps with charts and buttons |
| **Claude API** | A way to send text to Claude AI and get responses back, programmatically |
| **MCP Server** | Our Python program that receives requests from Claude and talks to the database |
| **MCP Tools** | Functions that Claude can call — like "query_database" or "detect_anomalies" |
| **stdio transport** | MCP communicates through standard input/output (like piping text between programs) |
| **Factory Pattern** | A coding pattern where one function decides which type of object to create (DuckDB or Snowflake connector) |
| **Docker** | Packages your app with all dependencies into a "container" — runs the same everywhere |
| **EC2** | Amazon's virtual servers — like renting a computer in the cloud |
| **ETL** | Extract, Transform, Load — the process of moving data from one place to another |
| **KPI** | Key Performance Indicator — important business metrics (revenue, profit, etc.) |
| **Z-score** | A statistical method to find outliers — measures how far a value is from the average |
| **Anomaly** | An unusual data point — like a transaction that's 10x larger than normal |
