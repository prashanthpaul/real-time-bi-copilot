"""
Snowflake Data Loader
========================
Loads sample data from CSV into Snowflake tables and creates analytics views.

Prerequisites:
    pip install snowflake-connector-python
    Set Snowflake credentials in .env

Usage:
    python scripts/load_snowflake.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.config import settings


def main():
    try:
        import snowflake.connector
    except ImportError:
        print("ERROR: Install snowflake-connector-python first:")
        print("  pip install snowflake-connector-python")
        sys.exit(1)

    # Validate config
    if not settings.snowflake_account or not settings.snowflake_user:
        print("ERROR: Snowflake credentials not configured in .env")
        print("Set: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD")
        sys.exit(1)

    print("=" * 50)
    print(" Snowflake Data Loader")
    print("=" * 50)
    print(f"Account:   {settings.snowflake_account}")
    print(f"Database:  {settings.snowflake_database}")
    print(f"Schema:    {settings.snowflake_schema}")
    print(f"Warehouse: {settings.snowflake_warehouse}")

    # Connect
    print("\n[1/5] Connecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=settings.snowflake_password,
        warehouse=settings.snowflake_warehouse,
    )
    cursor = conn.cursor()
    print("  Connected!")

    # Create database and schema
    print("\n[2/5] Creating database and schema...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
    cursor.execute(f"USE DATABASE {settings.snowflake_database}")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
    cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
    print(f"  Using {settings.snowflake_database}.{settings.snowflake_schema}")

    # Create tables
    print("\n[3/5] Creating tables...")

    cursor.execute("""
        CREATE OR REPLACE TABLE sales (
            transaction_id VARCHAR,
            transaction_date VARCHAR,
            customer_id VARCHAR,
            product_id VARCHAR,
            product_name VARCHAR,
            category VARCHAR,
            subcategory VARCHAR,
            region VARCHAR,
            quantity INTEGER,
            unit_price FLOAT,
            discount_pct FLOAT,
            revenue FLOAT,
            cost FLOAT,
            profit FLOAT,
            sales_channel VARCHAR,
            payment_method VARCHAR,
            customer_segment VARCHAR
        )
    """)
    print("  Created: sales")

    cursor.execute("""
        CREATE OR REPLACE TABLE customers (
            customer_id VARCHAR,
            company_name VARCHAR,
            segment VARCHAR,
            region VARCHAR,
            country VARCHAR,
            created_date VARCHAR,
            is_active BOOLEAN
        )
    """)
    print("  Created: customers")

    cursor.execute("""
        CREATE OR REPLACE TABLE products (
            product_id VARCHAR,
            product_name VARCHAR,
            category VARCHAR,
            subcategory VARCHAR,
            base_price FLOAT,
            cost FLOAT,
            is_active BOOLEAN
        )
    """)
    print("  Created: products")

    # Load data from CSV
    print("\n[4/5] Loading data from CSV...")
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "sales_data.csv"

    if not csv_path.exists():
        print("  ERROR: sales_data.csv not found. Run sample_data_generator.py first.")
        sys.exit(1)

    # Stage and load
    cursor.execute("CREATE OR REPLACE STAGE bi_copilot_stage")
    cursor.execute(f"PUT file://{csv_path} @bi_copilot_stage AUTO_COMPRESS=TRUE")
    cursor.execute("""
        COPY INTO sales
        FROM @bi_copilot_stage/sales_data.csv.gz
        FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
        ON_ERROR = 'CONTINUE'
    """)
    result = cursor.fetchone()
    print(f"  Loaded sales: {result}")

    # Verify row counts
    cursor.execute("SELECT COUNT(*) FROM sales")
    count = cursor.fetchone()[0]
    print(f"  Sales rows: {count:,}")

    # Create views
    print("\n[5/5] Creating analytics views...")

    cursor.execute("""
        CREATE OR REPLACE VIEW monthly_revenue AS
        SELECT
            DATE_TRUNC('month', TO_DATE(transaction_date)) AS month,
            category,
            region,
            COUNT(*) AS transaction_count,
            SUM(revenue) AS total_revenue,
            SUM(profit) AS total_profit,
            AVG(revenue) AS avg_revenue,
            AVG(discount_pct) AS avg_discount
        FROM sales
        GROUP BY 1, 2, 3
        ORDER BY 1
    """)
    print("  Created: monthly_revenue")

    cursor.execute("""
        CREATE OR REPLACE VIEW top_products AS
        SELECT
            product_name,
            category,
            subcategory,
            COUNT(*) AS times_sold,
            SUM(quantity) AS total_units,
            SUM(revenue) AS total_revenue,
            SUM(profit) AS total_profit,
            ROUND(AVG(unit_price), 2) AS avg_unit_price
        FROM sales
        GROUP BY 1, 2, 3
        ORDER BY total_revenue DESC
    """)
    print("  Created: top_products")

    cursor.execute("""
        CREATE OR REPLACE VIEW daily_kpis AS
        SELECT
            TO_DATE(transaction_date) AS date,
            COUNT(*) AS transactions,
            SUM(revenue) AS revenue,
            SUM(profit) AS profit,
            AVG(revenue) AS avg_order_value,
            COUNT(DISTINCT customer_id) AS unique_customers
        FROM sales
        GROUP BY 1
        ORDER BY 1
    """)
    print("  Created: daily_kpis")

    cursor.execute("""
        CREATE OR REPLACE VIEW customer_summary AS
        SELECT
            s.customer_id,
            MAX(s.customer_segment) AS segment,
            MAX(s.region) AS region,
            COUNT(*) AS total_orders,
            SUM(s.revenue) AS lifetime_revenue,
            AVG(s.revenue) AS avg_order_value,
            MIN(s.transaction_date) AS first_order,
            MAX(s.transaction_date) AS last_order
        FROM sales s
        GROUP BY 1
        ORDER BY lifetime_revenue DESC
    """)
    print("  Created: customer_summary")

    # Done
    cursor.close()
    conn.close()

    print("\n" + "=" * 50)
    print(" Snowflake setup complete!")
    print("=" * 50)
    print("\nTo switch the app to Snowflake, update .env:")
    print("  DATABASE_TYPE=snowflake")
    print(f"  SNOWFLAKE_ACCOUNT={settings.snowflake_account}")
    print(f"  SNOWFLAKE_DATABASE={settings.snowflake_database}")
    print("\nThen restart the MCP server and Streamlit dashboard.")


if __name__ == "__main__":
    main()
