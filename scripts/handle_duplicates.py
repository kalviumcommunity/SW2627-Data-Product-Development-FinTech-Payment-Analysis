#!/usr/bin/env python3
"""
scripts/handle_duplicates.py
Module: Duplicate Detection & Handling

This script finds row-level and Transaction_ID duplicates, creates a report,
removes exact duplicates, and saves the cleaned dataset.
"""

import os
import sys
import json
import pandas as pd

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_duplicates(df):
    """
    Analyzes duplicate records inside the dataset.
    """
    total_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())
    
    txn_id_duplicates = 0
    txn_dup_list = []
    if 'Transaction_ID' in df.columns:
        txn_id_duplicates = int(df['Transaction_ID'].duplicated().sum())
        # Find which transaction IDs are duplicated
        dup_series = df[df['Transaction_ID'].duplicated(keep=False)]
        txn_dup_list = dup_series['Transaction_ID'].unique().tolist()[:20] # Limit to top 20 for JSON sizing
        
    print("======================================================================")
    print("DUPLICATE RECORD DETECTION")
    print("======================================================================")
    print(f"Total Rows Analyzed:         {total_rows}")
    print(f"Exact Duplicate Rows:        {exact_duplicates}")
    print(f"Duplicate Transaction_ID:    {txn_id_duplicates}")
    print("======================================================================")
    
    # Save Report
    report = {
        "total_rows": total_rows,
        "exact_duplicate_rows": exact_duplicates,
        "duplicate_transaction_ids": txn_id_duplicates,
        "sample_duplicate_ids": txn_dup_list
    }
    
    os.makedirs("output", exist_ok=True)
    with open("output/duplicate_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print("[OK] Duplicate report saved to output/duplicate_report.json")
    
    return exact_duplicates, txn_id_duplicates

def handle_deduplication(df):
    """
    Removes exact duplicate rows from the dataset.
    Does not delete customer records with duplicate customer IDs.
    """
    rows_before = len(df)
    df_clean = df.drop_duplicates()
    rows_after = len(df_clean)
    
    print(f"Deduplication complete: {rows_before - rows_after} exact duplicate rows removed.")
    return df_clean

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/2_imputed.csv"
        output_path = "data/processed/3_deduplicated.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    # Analyze
    analyze_duplicates(df)
    
    # Clean
    df_clean = handle_deduplication(df)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    print(f"[OK] Deduplicated dataset saved to {output_path}")

if __name__ == "__main__":
    main()
