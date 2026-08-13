#!/usr/bin/env encoding=utf-8
"""
scripts/merge_validation.py
Module 2.25 — Multi-Source Merging & Join Validation

This script joins validated transaction records with the customer master data,
compares inner/left/right/outer joins, isolates unmatched records, and saves reports.
"""

import os
import sys
import json
import pandas as pd

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def perform_join_checks(df_txn, df_cust):
    """
    Demonstrates joins, prints row count statistics, and returns join dataframes.
    """
    # Align join keys to clean string
    txn_keys = set(df_txn["Customer_ID"].dropna().astype(str).str.strip().unique())
    cust_keys = set(df_cust["Customer_ID"].dropna().astype(str).str.strip().unique())
    
    # 1. Demonstrate joins
    df_inner = pd.merge(df_txn, df_cust, on="Customer_ID", how="inner", suffixes=("_txn", "_cust"))
    df_left = pd.merge(df_txn, df_cust, on="Customer_ID", how="left", suffixes=("_txn", "_cust"))
    df_right = pd.merge(df_txn, df_cust, on="Customer_ID", how="right", suffixes=("_txn", "_cust"))
    df_outer = pd.merge(df_txn, df_cust, on="Customer_ID", how="outer", suffixes=("_txn", "_cust"))
    
    print("======================================================================")
    print("MULTI-SOURCE JOIN CARDINALITY SUMMARY")
    print("======================================================================")
    print(f"Transactions (Left Source) Rows:  {len(df_txn)}")
    print(f"Customers (Right Source) Rows:    {len(df_cust)}")
    print(f"Inner Join Rows:                  {len(df_inner)}")
    print(f"Left Join Rows (Transactions):    {len(df_left)}")
    print(f"Right Join Rows (Customers):      {len(df_right)}")
    print(f"Outer Join Rows:                  {len(df_outer)}")
    print("======================================================================")
    
    # 2. Detect unmatched keys
    unmatched_txns_mask = ~df_txn["Customer_ID"].astype(str).str.strip().isin(cust_keys)
    df_unmatched_txns = df_txn[unmatched_txns_mask].copy()
    
    unmatched_custs_mask = ~df_cust["Customer_ID"].astype(str).str.strip().isin(txn_keys)
    df_unmatched_custs = df_cust[unmatched_custs_mask].copy()
    
    print(f"Transactions without matching customers: {len(df_unmatched_txns)}")
    print(f"Customers without any transactions:      {len(df_unmatched_custs)}")
    print("======================================================================")
    
    # Check duplicate keys injection (validation of unexpected duplication)
    cust_key_duplicates = df_cust["Customer_ID"].duplicated().sum()
    if cust_key_duplicates > 0:
        print(f"[WARNING] Customer Master contains {cust_key_duplicates} duplicate Customer_IDs. Left join will cause duplication!")
    else:
        print("✓ Customer Master contains no duplicate Customer_IDs. Join cardinality is valid (m:1).")
        
    return df_left, df_unmatched_txns, df_unmatched_custs, df_inner, df_right, df_outer

def main():
    if len(sys.argv) < 4:
        input_txn_path = "data/processed/7_validated.csv"
        input_cust_path = "data/raw/customers.csv"
        output_path = "data/processed/8_merged.csv"
    else:
        input_txn_path = sys.argv[1]
        input_cust_path = sys.argv[2]
        output_path = sys.argv[3]
        
    if not os.path.exists(input_txn_path):
        print(f"[ERROR] Transaction file {input_txn_path} does not exist.")
        sys.exit(1)
        
    if not os.path.exists(input_cust_path):
        print(f"[ERROR] Customer file {input_cust_path} does not exist.")
        sys.exit(1)
        
    df_txn = pd.read_csv(input_txn_path)
    df_cust = pd.read_csv(input_cust_path)
    
    # Clean keys for joining
    df_txn["Customer_ID"] = df_txn["Customer_ID"].astype(str).str.strip()
    df_cust["Customer_ID"] = df_cust["Customer_ID"].astype(str).str.strip()
    
    df_left, df_unmatched_txns, df_unmatched_custs, df_inner, df_right, df_outer = perform_join_checks(df_txn, df_cust)
    
    # Save isolated unmatched rows
    os.makedirs("output", exist_ok=True)
    df_unmatched_txns.to_csv("output/unmatched_transactions.csv", index=False)
    df_unmatched_custs.to_csv("output/unmatched_customers.csv", index=False)
    print("[OK] Unmatched transactions saved to output/unmatched_transactions.csv")
    print("[OK] Unmatched customers saved to output/unmatched_customers.csv")
    
    # Save join report json
    join_report = {
        "transactions_rows": len(df_txn),
        "customers_rows": len(df_cust),
        "inner_join_rows": len(df_inner),
        "left_join_rows": len(df_left),
        "right_join_rows": len(df_right),
        "outer_join_rows": len(df_outer),
        "transactions_unmatched_count": len(df_unmatched_txns),
        "customers_unmatched_count": len(df_unmatched_custs),
        "business_rationale": "A left join preserves all customers while adding transaction information where available."
    }
    
    with open("output/join_report.json", "w", encoding="utf-8") as f:
        json.dump(join_report, f, indent=4)
    print("[OK] Join validation report saved to output/join_report.json")
    
    # Save merged dataset (left join preserving transactions)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_left.to_csv(output_path, index=False)
    print(f"[OK] Merged dataset saved to {output_path}")

if __name__ == "__main__":
    main()
