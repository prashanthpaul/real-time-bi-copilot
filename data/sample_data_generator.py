"""
Sample Data Generator for Real-Time BI Copilot
================================================
Generates realistic sales, products, customers, and transaction data
with seasonal trends, weekly patterns, outliers, and data quality issues.

Usage:
    python data/sample_data_generator.py
    python data/sample_data_generator.py --rows 50000
"""

import os
import random
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Constants ---

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
COUNTRIES = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["United Kingdom", "Germany", "France", "Netherlands", "Spain"],
    "Asia Pacific": ["Japan", "Australia", "India", "Singapore", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Colombia", "Chile"],
    "Middle East & Africa": ["UAE", "South Africa", "Saudi Arabia", "Nigeria"],
}

CATEGORIES = ["Electronics", "Software", "Services", "Hardware", "Cloud Infrastructure"]
SUBCATEGORIES = {
    "Electronics": ["Laptops", "Monitors", "Accessories", "Networking"],
    "Software": ["Licenses", "SaaS Subscriptions", "Custom Development", "Support Plans"],
    "Services": ["Consulting", "Training", "Implementation", "Managed Services"],
    "Hardware": ["Servers", "Storage", "Peripherals", "Components"],
    "Cloud Infrastructure": ["Compute", "Storage", "Database", "AI/ML Services"],
}

PRODUCTS = {
    "Laptops": ["ProBook 450", "EliteBook 840", "ThinkPad X1", "MacBook Pro 14"],
    "Monitors": ["UltraSharp 27", "ProDisplay 32", "ThinkVision 24", "Studio Display"],
    "Accessories": ["Wireless Mouse", "Mechanical Keyboard", "USB-C Hub", "Webcam HD"],
    "Networking": ["Managed Switch 24P", "WiFi 6E Router", "Access Point Pro", "Firewall UTM"],
    "Licenses": ["Office Suite", "Security Platform", "DevOps Tools", "Analytics Pro"],
    "SaaS Subscriptions": ["CRM Cloud", "ERP Online", "HR Suite", "Project Manager"],
    "Custom Development": ["API Integration", "Dashboard Build", "Data Pipeline", "Mobile App"],
    "Support Plans": ["Basic Support", "Premium Support", "Enterprise Support", "24/7 Critical"],
    "Consulting": ["Strategy Review", "Architecture Design", "Security Audit", "Cloud Migration"],
    "Training": ["Admin Training", "Developer Bootcamp", "Executive Briefing", "Certification Prep"],
    "Implementation": ["System Setup", "Data Migration", "Integration Setup", "Go-Live Support"],
    "Managed Services": ["Infrastructure Mgmt", "App Monitoring", "Security Ops", "Database Admin"],
    "Servers": ["Rack Server 1U", "Tower Server", "Blade Server", "GPU Server"],
    "Storage": ["NAS 8-Bay", "SAN Array", "Backup Appliance", "Flash Storage"],
    "Peripherals": ["Docking Station", "KVM Switch", "UPS 1500VA", "Label Printer"],
    "Components": ["RAM 32GB", "SSD 1TB", "CPU Xeon", "GPU Tesla"],
    "Compute": ["EC2 Instance", "Lambda Function", "Container Service", "Batch Processing"],
    "Storage": ["S3 Bucket", "Block Storage", "Archive Storage", "CDN Distribution"],
    "Database": ["SQL Managed", "NoSQL Service", "Cache Cluster", "Data Lake"],
    "AI/ML Services": ["Model Training", "Inference API", "AutoML Pipeline", "Vision Service"],
}

SALES_CHANNELS = ["Direct", "Partner", "Online", "Reseller"]
PAYMENT_METHODS = ["Credit Card", "Wire Transfer", "Purchase Order", "Net 30", "Net 60"]
CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government"]


def generate_customers(n: int = 500) -> pd.DataFrame:
    """Generate a customer master dataset."""
    logger.info(f"Generating {n} customers...")

    customers = []
    for i in range(1, n + 1):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES[region])
        segment = random.choice(CUSTOMER_SEGMENTS)
        created = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1800))

        customers.append({
            "customer_id": f"CUST-{i:05d}",
            "company_name": f"{random.choice(['Acme', 'Global', 'Tech', 'Prime', 'Atlas', 'Nexus', 'Vertex', 'Apex', 'Core', 'Nova'])} {random.choice(['Corp', 'Inc', 'Ltd', 'Group', 'Solutions', 'Systems', 'Technologies', 'Industries', 'Partners', 'Dynamics'])}",
            "segment": segment,
            "region": region,
            "country": country,
            "created_date": created.strftime("%Y-%m-%d"),
            "is_active": random.random() > 0.1,
        })

    df = pd.DataFrame(customers)
    # Introduce ~2% nulls in company_name
    null_mask = np.random.random(len(df)) < 0.02
    df.loc[null_mask, "company_name"] = None
    return df


def generate_products_catalog() -> pd.DataFrame:
    """Generate a flat product catalog from nested dictionaries."""
    logger.info("Generating product catalog...")

    rows = []
    pid = 1
    for category, subcats in SUBCATEGORIES.items():
        for subcat in subcats:
            product_list = PRODUCTS.get(subcat, [f"{subcat} Standard"])
            for product_name in product_list:
                base_price = round(random.uniform(20, 15000), 2)
                rows.append({
                    "product_id": f"PROD-{pid:04d}",
                    "product_name": product_name,
                    "category": category,
                    "subcategory": subcat,
                    "base_price": base_price,
                    "cost": round(base_price * random.uniform(0.3, 0.75), 2),
                    "is_active": random.random() > 0.05,
                })
                pid += 1
    return pd.DataFrame(rows)


def generate_sales(n: int = 10000, customers: pd.DataFrame = None, products: pd.DataFrame = None) -> pd.DataFrame:
    """Generate sales transactions with realistic patterns."""
    logger.info(f"Generating {n} sales records...")

    customer_ids = customers["customer_id"].tolist()
    product_rows = products.to_dict("records")

    sales = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    for i in range(1, n + 1):
        # Date with seasonal weighting (more sales in Q4)
        day_offset = random.randint(0, date_range_days)
        sale_date = start_date + timedelta(days=day_offset)
        month = sale_date.month

        # Seasonal multiplier: Q4 boost, Q1 dip
        if month in (10, 11, 12):
            seasonal = random.uniform(1.2, 1.8)
        elif month in (1, 2):
            seasonal = random.uniform(0.6, 0.9)
        elif month in (6, 7):
            seasonal = random.uniform(0.8, 1.0)
        else:
            seasonal = random.uniform(0.9, 1.2)

        # Weekend dip
        if sale_date.weekday() >= 5:
            seasonal *= 0.4

        product = random.choice(product_rows)
        quantity = max(1, int(random.expovariate(0.3) * seasonal))
        unit_price = product["base_price"] * random.uniform(0.85, 1.15)  # price variation
        discount_pct = random.choice([0, 0, 0, 0, 5, 10, 15, 20, 25])
        revenue = round(quantity * unit_price * (1 - discount_pct / 100), 2)

        # Outlier injection (~1%)
        if random.random() < 0.01:
            revenue = round(revenue * random.uniform(5, 20), 2)
            quantity = quantity * random.randint(5, 15)

        sales.append({
            "transaction_id": f"TXN-{i:06d}",
            "transaction_date": sale_date.strftime("%Y-%m-%d"),
            "customer_id": random.choice(customer_ids),
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
            "subcategory": product["subcategory"],
            "region": random.choice(REGIONS),
            "quantity": quantity,
            "unit_price": round(unit_price, 2),
            "discount_pct": discount_pct,
            "revenue": revenue,
            "cost": round(product["cost"] * quantity, 2),
            "profit": round(revenue - product["cost"] * quantity, 2),
            "sales_channel": random.choice(SALES_CHANNELS),
            "payment_method": random.choice(PAYMENT_METHODS),
            "customer_segment": random.choice(CUSTOMER_SEGMENTS),
        })

    df = pd.DataFrame(sales)

    # Introduce ~3% nulls scattered across some columns
    for col in ["discount_pct", "payment_method", "customer_segment"]:
        null_mask = np.random.random(len(df)) < 0.03
        df.loc[null_mask, col] = None

    # Introduce ~0.5% duplicate transactions
    n_dupes = int(len(df) * 0.005)
    if n_dupes > 0:
        dupes = df.sample(n=n_dupes)
        df = pd.concat([df, dupes], ignore_index=True)

    logger.info(f"Generated {len(df)} sales records (including {n_dupes} intentional duplicates)")
    return df


def load_into_duckdb(
    sales: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    db_path: str,
) -> None:
    """Load all dataframes into DuckDB and create analytics views."""
    logger.info(f"Loading data into DuckDB at {db_path}...")

    # Remove existing db to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)

    con = duckdb.connect(db_path)

    # Create tables
    con.execute("CREATE TABLE sales AS SELECT * FROM sales")
    con.execute("CREATE TABLE customers AS SELECT * FROM customers")
    con.execute("CREATE TABLE products AS SELECT * FROM products")

    # Create analytics views
    con.execute("""
        CREATE VIEW monthly_revenue AS
        SELECT
            DATE_TRUNC('month', CAST(transaction_date AS DATE)) AS month,
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

    con.execute("""
        CREATE VIEW top_products AS
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

    con.execute("""
        CREATE VIEW customer_summary AS
        SELECT
            s.customer_id,
            c.company_name,
            c.segment,
            c.region,
            c.country,
            COUNT(*) AS total_orders,
            SUM(s.revenue) AS lifetime_revenue,
            AVG(s.revenue) AS avg_order_value,
            MIN(s.transaction_date) AS first_order,
            MAX(s.transaction_date) AS last_order
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY lifetime_revenue DESC
    """)

    con.execute("""
        CREATE VIEW daily_kpis AS
        SELECT
            CAST(transaction_date AS DATE) AS date,
            COUNT(*) AS transactions,
            SUM(revenue) AS revenue,
            SUM(profit) AS profit,
            AVG(revenue) AS avg_order_value,
            COUNT(DISTINCT customer_id) AS unique_customers
        FROM sales
        GROUP BY 1
        ORDER BY 1
    """)

    # Verify
    tables = con.execute("SHOW TABLES").fetchall()
    logger.info(f"Tables created: {[t[0] for t in tables]}")
    for t in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        logger.info(f"  {t[0]}: {count} rows")

    views = con.execute("SELECT view_name FROM duckdb_views() WHERE NOT internal").fetchall()
    logger.info(f"Views created: {[v[0] for v in views]}")

    con.close()
    logger.info("Database setup complete.")


def export_csv(sales: pd.DataFrame, output_path: str) -> None:
    """Export sales data to CSV for reference."""
    sales.to_csv(output_path, index=False)
    logger.info(f"Exported {len(sales)} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate sample data for BI Copilot")
    parser.add_argument("--rows", type=int, default=10000, help="Number of sales records")
    parser.add_argument("--customers", type=int, default=500, help="Number of customers")
    args = parser.parse_args()

    data_dir = Path(__file__).parent
    db_path = str(data_dir / "database.duckdb")
    csv_path = str(data_dir / "sales_data.csv")

    # Generate datasets
    customers = generate_customers(args.customers)
    products = generate_products_catalog()
    sales = generate_sales(args.rows, customers, products)

    # Export CSV
    export_csv(sales, csv_path)

    # Load into DuckDB
    load_into_duckdb(sales, customers, products, db_path)

    logger.info("Sample data generation complete!")
    logger.info(f"  Database: {db_path}")
    logger.info(f"  CSV:      {csv_path}")
    logger.info(f"  Sales:    {len(sales)} rows")
    logger.info(f"  Customers:{len(customers)} rows")
    logger.info(f"  Products: {len(products)} rows")


if __name__ == "__main__":
    main()
