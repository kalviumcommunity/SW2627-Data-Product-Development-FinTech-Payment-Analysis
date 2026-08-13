#!/usr/bin/env encoding=utf-8
"""
scripts/data_validation.py
Module 2.24 — Data Consistency & Validation

This script implements rule-based data validation, checks transaction constraints,
isolates failures to a CSV, and writes a validation report JSON.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def validate_dataset(df):
    """
    Apply consistency rules to the dataset.
    """
    df_eval = df.copy()
    
    # Rule 1: Amount >= 0
    df_eval["v_amount"] = df_eval["Amount"] >= 0
    
    # Rule 2: Customer_ID is not null
    df_eval["v_customer_id"] = df_eval["Customer_ID"].notna() & (df_eval["Customer_ID"].astype(str).str.strip() != "")
    
    # Rule 3: Retry_Count >= 0
    df_eval["v_retry_count"] = df_eval["Retry_Count"] >= 0
    
    # Rule 4: Retry_Time >= Transaction_Time (if Retry_Time is present)
    # Safely convert to dates for check
    tx_time = pd.to_datetime(df_eval["Transaction_Time"], errors="coerce")
    rt_time = pd.to_datetime(df_eval["Retry_Time"], errors="coerce")
    # Rule passes if Retry_Time is null OR if Retry_Time >= Transaction_Time
    df_eval["v_retry_time"] = rt_time.isnull() | (rt_time >= tx_time)
    
    # Rule 5: Final Status is in Success, Failed, Pending
    valid_statuses = ["Success", "Failed", "Pending"]
    df_eval["v_final_status"] = df_eval["Final_Status"].isin(valid_statuses)
    
    # Rule 6: Revenue Lost >= 0
    df_eval["v_revenue_lost"] = df_eval["Revenue_Lost"] >= 0
    
    # Rule 7: Response Code is numeric and exists
    df_eval["v_response_code"] = df_eval["Response_Code"].notna()
    
    validation_cols = ["v_amount", "v_customer_id", "v_retry_count", "v_retry_time", "v_final_status", "v_revenue_lost", "v_response_code"]
    
    # Passes all check constraints
    df_eval["passes_all_checks"] = df_eval[validation_cols].all(axis=1)
    
    return df_eval, validation_cols

def generate_report(df_eval, validation_cols):
    """
    Constructs and exports validation report and failure rows.
    """
    total_records = len(df_eval)
    passed_count = int(df_eval["passes_all_checks"].sum())
    failed_count = total_records - passed_count
    
    pass_pct = float((passed_count / total_records) * 100)
    fail_pct = float((failed_count / total_records) * 100)
    
    # Failures by rule
    failures_by_rule = {}
    for col in validation_cols:
        rule_name = col.replace("v_", "rule_")
        failed_rule_count = int((~df_eval[col]).sum())
        failures_by_rule[rule_name] = failed_rule_count
        
    print("======================================================================")
    print("DATA CONSISTENCY VALIDATION")
    print("======================================================================")
    print(f"Total Records:      {total_records}")
    print(f"Passed All Rules:   {passed_count} ({pass_pct:.2f}%)")
    print(f"Failed Rules:       {failed_count} ({fail_pct:.2f}%)")
    print("\nRule Violations Breakdown:")
    for rule, count in failures_by_rule.items():
        print(f"  - {rule}: {count} violations")
    print("======================================================================")
    
    # Save Report JSON
    report = {
        "total_records": total_records,
        "passed": passed_count,
        "failed": failed_count,
        "pass_percentage": pass_pct,
        "failure_percentage": fail_pct,
        "failed_records_by_rule": failures_by_rule
    }
    
    os.makedirs("output", exist_ok=True)
    with open("output/validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print("[OK] Validation report saved to output/validation_report.json")
    
    # Isolate failures
    failures_df = df_eval[~df_eval["passes_all_checks"]].copy()
    # Remove validation prefix cols before export to keep clean
    clean_export_failures = failures_df.drop(columns=validation_cols)
    clean_export_failures.to_csv("output/validation_failures.csv", index=False)
    print(f"[OK] {len(clean_export_failures)} failed rows isolated to output/validation_failures.csv")

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/6_outliers_handled.csv"
        output_path = "data/processed/7_validated.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    df_eval, validation_cols = validate_dataset(df)
    generate_report(df_eval, validation_cols)
    
    # Export clean validated df
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_eval.to_csv(output_path, index=False)
    print(f"[OK] Validated dataset saved to {output_path}")

if __name__ == "__main__":
    main()
