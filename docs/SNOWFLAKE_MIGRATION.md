# Snowflake Migration Guide

## Overview

This project uses DuckDB locally with Snowflake-compatible SQL. Migrating to Snowflake involves these steps:

## Step 1: Snowflake Account Setup

1. Create a Snowflake trial account at https://signup.snowflake.com
2. Note your account identifier (e.g., `xy12345.us-east-1`)
3. Create a warehouse, database, and schema:

```sql
CREATE WAREHOUSE BI_COPILOT_WH WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;
CREATE DATABASE BI_COPILOT;
CREATE SCHEMA BI_COPILOT.PUBLIC;
```

## Step 2: Update Environment Variables

```env
DATABASE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=BI_COPILOT_WH
SNOWFLAKE_DATABASE=BI_COPILOT
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN
```

## Step 3: Install Snowflake Connector

```bash
pip install snowflake-connector-python
```

## Step 4: Implement SnowflakeConnector

In `mcp-server/utils/db_connector.py`, implement the `SnowflakeConnector` class:

```python
import snowflake.connector

class SnowflakeConnector:
    def __init__(self, config: dict):
        self.conn = snowflake.connector.connect(
            account=config["account"],
            user=config["user"],
            password=config["password"],
            warehouse=config["warehouse"],
            database=config["database"],
            schema=config["schema"],
        )

    def execute_query(self, sql: str, params=None) -> dict:
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
```

## Step 5: Load Data into Snowflake

```sql
-- Create tables matching the DuckDB schema
CREATE TABLE sales (
    transaction_id VARCHAR,
    transaction_date DATE,
    customer_id VARCHAR,
    product_name VARCHAR,
    category VARCHAR,
    region VARCHAR,
    revenue FLOAT,
    profit FLOAT,
    -- ... (same columns as DuckDB)
);

-- Use Snowflake's COPY INTO for bulk loading
PUT file://data/sales_data.csv @~/staged;
COPY INTO sales FROM @~/staged FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);
```

## Step 6: SQL Compatibility Notes

Most queries work as-is. Key differences:
- DuckDB `DATE_TRUNC` → Snowflake `DATE_TRUNC` (same syntax)
- DuckDB `YEAR(date)` → Snowflake `YEAR(date)` (same syntax)
- DuckDB string functions are largely compatible

## Step 7: Performance Optimization

- Use Snowflake clustering keys for large tables
- Configure auto-suspend on the warehouse
- Use result caching (enabled by default in Snowflake)
