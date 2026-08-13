#!/usr/bin/env python3
"""
scripts/db_integration.py
Modules 2.37 — 2.44: SQL Environment & Database Integration, Business Query Design,
Filtering/Grouping, Joins, Window Functions, Optimisation, Views, and Validation.

This script sets up an SQLite database, creates tables for transactions and customer segments,
defines indexes, runs complex analytical queries, and validates the insights.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Config
DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "fintech_payment.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
OUTPUT_DIR = "output"

TXN_PROCESSED_PATH = "data/processed/enriched_transactions_10k.csv"
CUST_PROCESSED_PATH = "data/processed/customer_segments.csv"

def init_db():
    """Initialises the database and writes schema.sql."""
    os.makedirs(DB_DIR, exist_ok=True)
    
    # 2.37: SQL Environment & Database Integration (Schema Design)
    schema_sql = """-- Fintech Payment Analysis Schema
-- Automatically generated schema file

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    segment TEXT,
    transaction_count INTEGER,
    total_spend REAL,
    avg_spend REAL,
    days_since_first_txn REAL
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT,
    amount REAL,
    payment_method TEXT,
    bank_name TEXT,
    response_code REAL,
    response_message TEXT,
    retry_count REAL,
    transaction_time TEXT,
    retry_time TEXT,
    final_status TEXT,
    failure_type TEXT,
    revenue_lost REAL,
    calculated_fee REAL,
    net_amount REAL,
    calculated_discount REAL,
    transaction_score REAL,
    risk_level TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);
"""
    
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        f.write(schema_sql)
    print(f"[OK] Database schema written to {SCHEMA_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"[OK] SQLite database initialised at {DB_PATH}")

def populate_db():
    """Imports the processed CSV files into the SQLite database."""
    if not os.path.exists(TXN_PROCESSED_PATH) or not os.path.exists(CUST_PROCESSED_PATH):
        raise FileNotFoundError("Processed datasets must exist. Run data_workflow.py first.")
        
    df_txn = pd.read_csv(TXN_PROCESSED_PATH)
    df_cust = pd.read_csv(CUST_PROCESSED_PATH)
    
    # Align columns with schema
    txn_cols = [
        "transaction_id", "customer_id", "amount", "payment_method", "bank_name",
        "response_code", "response_message", "retry_count", "transaction_time",
        "retry_time", "final_status", "failure_type", "revenue_lost",
        "calculated_fee", "net_amount", "calculated_discount", "transaction_score", "risk_level"
    ]
    # Keep only columns defined in schema
    df_txn_filtered = df_txn[[c for c in txn_cols if c in df_txn.columns]]
    
    cust_cols = ["customer_id", "segment", "transaction_count", "total_spend", "avg_spend", "days_since_first_txn"]
    df_cust_filtered = df_cust[[c for c in cust_cols if c in df_cust.columns]]
    
    conn = sqlite3.connect(DB_PATH)
    # Load into SQL tables
    df_cust_filtered.to_sql("customers", conn, if_exists="append", index=False)
    df_txn_filtered.to_sql("transactions", conn, if_exists="append", index=False)
    conn.commit()
    
    # Check counts
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    txn_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customers")
    cust_count = cursor.fetchone()[0]
    
    conn.close()
    print(f"[OK] Populated database tables: {txn_count} transactions, {cust_count} customers.")

def create_optimization_and_views():
    """Creates indexes (2.42) and SQL views (2.43)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 2.42: Analytical SQL Query Optimisation (Indexes)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_customer_id ON transactions(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(final_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_bank ON transactions(bank_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_pm ON transactions(payment_method);")
    
    # Explain query plan validation
    cursor.execute("EXPLAIN QUERY PLAN SELECT t.transaction_id, c.segment FROM transactions t JOIN customers c ON t.customer_id = c.customer_id WHERE t.final_status = 'Success';")
    plan = cursor.fetchall()
    print("\n[Query Optimisation] SQL Query Plan Check:")
    for row in plan:
        print(f"  - Node {row[0]}: {row[3]}")
        
    # 2.43: SQL Views & Aggregation Layer Design
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_daily_settlement_summary AS
    SELECT 
        DATE(transaction_time) AS txn_date,
        COUNT(*) AS total_transactions,
        SUM(amount) AS total_amount,
        SUM(net_amount) AS net_settled_amount,
        SUM(calculated_fee) AS total_fees,
        SUM(CASE WHEN final_status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS success_rate,
        SUM(revenue_lost) AS total_revenue_lost
    FROM transactions
    GROUP BY txn_date;
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_bank_performance_summary AS
    SELECT 
        bank_name,
        COUNT(*) AS total_transactions,
        SUM(amount) AS total_amount,
        SUM(CASE WHEN final_status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS success_rate,
        SUM(calculated_fee) AS fees_earned
    FROM transactions
    WHERE bank_name IS NOT NULL
    GROUP BY bank_name;
    """)
    
    conn.commit()
    conn.close()
    print("[OK] SQL Optimization Indexes & Aggregation Views created successfully.")

def run_analytical_queries():
    """Runs window functions, joins, groupings, and filters (2.38 - 2.41)."""
    conn = sqlite3.connect(DB_PATH)
    
    # 2.41: SQL Window Functions & Ranking Systems (Rank customers by total spend)
    query_rank_customers = """
    SELECT 
        customer_id,
        segment,
        total_spend,
        RANK() OVER (ORDER BY total_spend DESC) as spend_rank,
        DENSE_RANK() OVER (PARTITION BY segment ORDER BY total_spend DESC) as segment_spend_rank
    FROM customers
    LIMIT 5;
    """
    df_ranked_cust = pd.read_sql_query(query_rank_customers, conn)
    print("\n[Window Functions] Top 5 Ranked Customers:")
    print(df_ranked_cust.to_string(index=False))
    
    # 2.40: SQL Joins & Multi-Table Analysis (Analyze transactions by customer segment)
    query_joins = """
    SELECT 
        c.segment,
        COUNT(t.transaction_id) as txn_count,
        AVG(t.amount) as avg_amount,
        SUM(t.revenue_lost) as total_rev_lost
    FROM transactions t
    INNER JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY c.segment;
    """
    df_join_analysis = pd.read_sql_query(query_joins, conn)
    print("\n[SQL Joins] Transactions Profile by Customer Segment:")
    print(df_join_analysis.to_string(index=False))
    
    # 2.39: SQL Filtering, Grouping & Aggregation (High fee banks with filter)
    query_grouping = """
    SELECT 
        bank_name,
        COUNT(*) as transactions_count,
        SUM(calculated_fee) as sum_fees
    FROM transactions
    WHERE final_status = 'Success' AND bank_name IS NOT NULL
    GROUP BY bank_name
    HAVING sum_fees > 100000.0
    ORDER BY sum_fees DESC;
    """
    df_groups = pd.read_sql_query(query_grouping, conn)
    print("\n[SQL Grouping & Filtering] High-Fee Banking Partners (> $100K in success fees):")
    print(df_groups.to_string(index=False))
    
    # Save a copy of bank rankings for streamlit database display
    df_groups.to_csv(os.path.join(OUTPUT_DIR, "db_bank_rankings.csv"), index=False)
    
    conn.close()

def validate_insights():
    """2.44: SQL-Based Insight Validation (Compares SQL metrics with Pandas metrics)."""
    conn = sqlite3.connect(DB_PATH)
    
    # Query metrics from database
    query = """
    SELECT 
        COUNT(*) as count,
        SUM(amount) as sum_amount,
        SUM(revenue_lost) as sum_lost
    FROM transactions;
    """
    sql_metrics = pd.read_sql_query(query, conn).iloc[0]
    conn.close()
    
    # Load same metrics in Pandas from CSV
    df_pandas = pd.read_csv(TXN_PROCESSED_PATH)
    pandas_count = len(df_pandas)
    pandas_sum_amount = df_pandas["amount"].sum()
    pandas_sum_lost = df_pandas["revenue_lost"].sum()
    
    # Validate
    count_match = sql_metrics["count"] == pandas_count
    amount_match = abs(sql_metrics["sum_amount"] - pandas_sum_amount) < 1e-2
    lost_match = abs(sql_metrics["sum_lost"] - pandas_sum_lost) < 1e-2
    
    print("\n" + "=" * 60)
    print("SQL INSIGHT VALIDATION REPORT:")
    print("=" * 60)
    print(f"Metrics           | SQL Database    | Python Pandas   | Validation Status")
    print(f"------------------+-----------------+-----------------+-------------------")
    print(f"Txn Count         | {sql_metrics['count']:<15} | {pandas_count:<15} | {'✓ PASSED' if count_match else '✗ FAILED'}")
    print(f"Gross Amount      | {sql_metrics['sum_amount']:<15,.2f} | {pandas_sum_amount:<15,.2f} | {'✓ PASSED' if amount_match else '✗ FAILED'}")
    print(f"Revenue Lost      | {sql_metrics['sum_lost']:<15,.2f} | {pandas_sum_lost:<15,.2f} | {'✓ PASSED' if lost_match else '✗ FAILED'}")
    print("=" * 60)
    
    if count_match and amount_match and lost_match:
        print("✓ SQL database insights match Python computations perfectly.")
    else:
        print("✗ Inconsistency detected between SQL Database and Python CSV files.")

def main():
    print("=" * 60)
    print("SQL DATABASE INTEGRATION & ANALYTICS PIPELINE")
    print("=" * 60)
    
    init_db()
    populate_db()
    create_optimization_and_views()
    run_analytical_queries()
    validate_insights()

if __name__ == "__main__":
    main()
