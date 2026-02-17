"""
MCP Prompts: analytics_workflows
===================================
Pre-configured analysis workflow prompts that guide users through
common BI tasks step by step.
"""

WORKFLOW_PROMPTS = {
    "sales_analysis": {
        "name": "sales_analysis",
        "description": "Comprehensive sales performance analysis workflow",
        "arguments": [
            {"name": "time_period", "description": "Time period to analyze (e.g., '2024', 'last_quarter')", "required": False},
            {"name": "region", "description": "Region to focus on (optional)", "required": False},
        ],
        "template": """Perform a comprehensive sales analysis with the following steps:

1. **Overview**: Use the `query_database` tool to get total revenue, transaction count, and average order value{time_filter}.
2. **Top Products**: Query the top 10 products by revenue{time_filter}.
3. **Regional Breakdown**: Get revenue breakdown by region{time_filter}.
4. **Trends**: Analyze monthly revenue trends using `analyze_data` on the sales table.
5. **Anomalies**: Run `detect_anomalies` on the revenue column to find unusual transactions.
6. **Insights**: Use `generate_insights` to get AI-powered recommendations.

{region_filter}
Present findings as a structured report with charts where applicable.""",
    },
    "customer_segmentation": {
        "name": "customer_segmentation",
        "description": "Customer segmentation and lifetime value analysis",
        "arguments": [
            {"name": "segment", "description": "Customer segment to focus on (optional)", "required": False},
        ],
        "template": """Perform customer segmentation analysis:

1. Use `query_database` to get the customer_summary view data.
2. Analyze customer segments by total revenue, order frequency, and average order value.
3. Identify top 10 customers by lifetime revenue.
4. Compare segment performance (Enterprise vs Mid-Market vs SMB vs Startup vs Government).
5. Use `generate_insights` to identify churn risks and growth opportunities.
{segment_filter}
Return a segmentation report with actionable recommendations.""",
    },
    "revenue_forecast": {
        "name": "revenue_forecast",
        "description": "Revenue trend analysis and projection",
        "arguments": [],
        "template": """Analyze revenue trends and provide forecasting inputs:

1. Query monthly_revenue view for all available periods.
2. Use `analyze_data` to identify trends, seasonality, and growth rates.
3. Calculate month-over-month and year-over-year growth.
4. Run `detect_anomalies` on monthly revenue to identify unusual months.
5. Use `generate_insights` with the question: "Based on historical trends, what is the revenue outlook?"

Present the analysis with trend charts and growth projections.""",
    },
    "performance_dashboard": {
        "name": "performance_dashboard",
        "description": "Generate a comprehensive KPI dashboard",
        "arguments": [
            {"name": "time_period", "description": "Dashboard time period", "required": False},
        ],
        "template": """Build a performance dashboard with these KPIs:

1. **Revenue KPIs**: Total revenue, MoM growth, YoY growth
2. **Transaction KPIs**: Count, average value, channel mix
3. **Product KPIs**: Top categories, product mix, discount impact
4. **Customer KPIs**: Active customers, new vs returning, segment distribution
5. **Profitability**: Gross margin, profit by category, cost trends

Use `query_database` for each KPI, then `generate_insights` for executive summary.
{time_filter}
Format as a dashboard-ready data package.""",
    },
    "custom_analysis": {
        "name": "custom_analysis",
        "description": "Build a custom analysis workflow from scratch",
        "arguments": [
            {"name": "objective", "description": "What do you want to analyze?", "required": True},
            {"name": "tables", "description": "Which tables to use (comma-separated)", "required": False},
        ],
        "template": """Custom analysis workflow:

Objective: {objective}

Steps:
1. First, explore the available datasets using the datasets resource.
2. Examine the schema of relevant tables{table_list}.
3. Query the data based on the objective.
4. Use `analyze_data` for statistical analysis.
5. Use `detect_anomalies` if time-series patterns are relevant.
6. Use `generate_insights` to get AI-powered conclusions.

Adapt the steps as needed to best answer the objective.""",
    },
}


def get_prompt(workflow_name: str, arguments: dict | None = None) -> dict:
    """Get a workflow prompt with arguments filled in."""
    if workflow_name not in WORKFLOW_PROMPTS:
        return {"error": f"Unknown workflow: {workflow_name}. Available: {list(WORKFLOW_PROMPTS.keys())}"}

    workflow = WORKFLOW_PROMPTS[workflow_name]
    template = workflow["template"]

    args = arguments or {}

    # Apply argument substitutions
    time_filter = f" for {args['time_period']}" if args.get("time_period") else ""
    template = template.replace("{time_filter}", time_filter)

    region_filter = f"Focus on region: {args['region']}" if args.get("region") else ""
    template = template.replace("{region_filter}", region_filter)

    segment_filter = f"Focus on segment: {args['segment']}" if args.get("segment") else ""
    template = template.replace("{segment_filter}", segment_filter)

    objective = args.get("objective", "General data exploration")
    template = template.replace("{objective}", objective)

    table_list = f" ({args['tables']})" if args.get("tables") else ""
    template = template.replace("{table_list}", table_list)

    return {
        "name": workflow_name,
        "description": workflow["description"],
        "messages": [{"role": "user", "content": {"type": "text", "text": template}}],
    }


def list_prompts() -> list[dict]:
    """List all available workflow prompts."""
    return [
        {
            "name": w["name"],
            "description": w["description"],
            "arguments": w.get("arguments", []),
        }
        for w in WORKFLOW_PROMPTS.values()
    ]
