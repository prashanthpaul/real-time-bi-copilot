# Power BI Integration Guide

## Overview

This guide covers connecting the BI Copilot data to Power BI for enterprise reporting and visualization.

## Option 1: Connect Power BI to DuckDB (Local)

### Install ODBC Driver
1. Download the DuckDB ODBC driver from https://duckdb.org/docs/api/odbc/overview
2. Configure ODBC data source pointing to `data/database.duckdb`

### Power BI Desktop
1. Open Power BI Desktop → Get Data → ODBC
2. Select the DuckDB ODBC data source
3. Import tables: `sales`, `customers`, `products`
4. Import views: `monthly_revenue`, `top_products`, `daily_kpis`

## Option 2: Connect Power BI to Snowflake (Cloud)

### Setup
1. Power BI Desktop → Get Data → Snowflake
2. Enter server: `your_account.snowflakecomputing.com`
3. Enter warehouse: `BI_COPILOT_WH`
4. Authenticate with Snowflake credentials
5. Select database and tables

### Recommended Reports

#### Executive Dashboard
- Revenue KPIs (total, MoM, YoY)
- Revenue by region (map visual)
- Category breakdown (donut chart)
- Monthly trend (line chart)

#### Product Performance
- Top products by revenue
- Category comparison
- Discount impact analysis
- Product mix over time

#### Customer Analytics
- Segment distribution
- Customer lifetime value
- Acquisition trends
- Churn indicators

### DAX Formulas

```dax
// Year-over-Year Growth
YoY Growth =
VAR CurrentYear = SUM(sales[revenue])
VAR PreviousYear = CALCULATE(SUM(sales[revenue]), SAMEPERIODLASTYEAR(sales[transaction_date]))
RETURN DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0)

// Profit Margin
Profit Margin = DIVIDE(SUM(sales[profit]), SUM(sales[revenue]), 0)

// Running Total
Running Total Revenue =
CALCULATE(SUM(sales[revenue]), FILTER(ALL(sales[transaction_date]), sales[transaction_date] <= MAX(sales[transaction_date])))
```

## Option 3: Power BI Embedded (API)

For programmatic access, use the Power BI REST API to push data from the MCP server directly into Power BI datasets. This enables real-time updates.

### Architecture
```
MCP Server → Python Power BI Client → Power BI REST API → Power BI Service
```

This requires Azure AD authentication and a Power BI Pro license.
