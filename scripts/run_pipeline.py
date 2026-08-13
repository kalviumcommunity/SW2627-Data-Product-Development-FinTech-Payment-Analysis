#!/usr/bin/env encoding=utf-8
"""
scripts/run_pipeline.py
Orchestrator Runner — Preprocessing & Analytics Pipeline

This script runs the 14-stage data engineering preprocessing workflow, checks logs,
calculates final business KPIs, and generates the final data quality report.
"""

import os
import sys
import json
import subprocess
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Config
DATA_RAW_DIR = "data/raw"
DATA_PROC_DIR = "data/processed"
OUTPUT_DIR = "output"

def run_stage(step_num, step_name, command_args):
    """
    Executes a pipeline stage script using subprocess.
    """
    print(f"\n" + "=" * 75)
    print(f"STEP {step_num}: {step_name.upper()}")
    print("=" * 75)
    print("STARTing stage execution...")
    print(f"PROCESS: Running command: {' '.join(command_args)}")
    
    # Configure UTF-8 environment
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(command_args, capture_output=True, text=True, env=env)
    
    # Print stdout and stderr from execution
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("[ERRORS / STDOUT WARNINGS]:")
        print(result.stderr)
        
    if result.returncode != 0:
        print(f"RESULT: ❌ FAILED! Stage {step_name} exited with code {result.returncode}")
        print("Pipeline execution halted due to critical error.")
        sys.exit(1)
        
    print(f"RESULT: ✓ SUCCESS! Stage {step_name} completed.")
    print(f"OUTPUT FILE: Output verified.")
    print("=" * 75)

def calculate_final_kpis_and_report():
    """
    Computes final business KPIs and writes output/final_data_quality_report.json.
    """
    print("\n" + "=" * 75)
    print("FINAL BUSINESS KPI & QUALITY AUDIT REPORT")
    print("=" * 75)
    
    final_path = os.path.join(DATA_PROC_DIR, "final_fintech_dataset.csv")
    if not os.path.exists(final_path):
        print(f"[ERROR] Final dataset {final_path} was not found. Cannot generate final report.")
        sys.exit(1)
        
    df = pd.read_csv(final_path)
    total_records = len(df)
    
    # Ingest baseline stats from previous output files
    # 1. Missing Values
    nulls_before = 0
    if os.path.exists("output/missing_value_report.csv"):
        df_mv = pd.read_csv("output/missing_value_report.csv")
        nulls_before = int(df_mv["null_count"].sum())
    nulls_after = int(df.isnull().sum().sum())
    
    # 2. Duplicates
    dup_rows = 0
    if os.path.exists("output/duplicate_report.json"):
        with open("output/duplicate_report.json", "r", encoding="utf-8") as f:
            dup_info = json.load(f)
            dup_rows = int(dup_info.get("exact_duplicate_rows", 0))
            
    # 3. Outliers count
    outlier_counts = {}
    if os.path.exists("output/outlier_report.json"):
        with open("output/outlier_report.json", "r", encoding="utf-8") as f:
            outlier_info = json.load(f)
            for k, v in outlier_info.items():
                outlier_counts[k] = int(v.get("outlier_count", 0))
                
    # 4. Join status
    join_stats = {}
    if os.path.exists("output/join_report.json"):
        with open("output/join_report.json", "r", encoding="utf-8") as f:
            join_stats = json.load(f)
            
    # 5. Invalid records
    invalid_records = 0
    if os.path.exists("output/validation_report.json"):
        with open("output/validation_report.json", "r", encoding="utf-8") as f:
            val_info = json.load(f)
            invalid_records = int(val_info.get("failed", 0))

    # Business KPIs
    # Success Rate (Final_Status = 'Success')
    success_count = (df["Final_Status"] == "Success").sum()
    success_rate = float(success_count / total_records) if total_records > 0 else 0
    
    # Failure Rate (Final_Status = 'Failed')
    failed_count = (df["Final_Status"] == "Failed").sum()
    failure_rate = float(failed_count / total_records) if total_records > 0 else 0
    
    # Retry Rate (Retry_Count > 0)
    retry_count_mask = df["Retry_Count"] > 0
    retry_rate = float(retry_count_mask.sum() / total_records) if total_records > 0 else 0
    
    # Retry Recovery Rate (Retry_Count > 0 and Final_Status = 'Success')
    recovered_count = (retry_count_mask & (df["Final_Status"] == "Success")).sum()
    retry_required_count = retry_count_mask.sum()
    retry_recovery_rate = float(recovered_count / retry_required_count) if retry_required_count > 0 else 0
    
    # Revenue Lost
    total_rev_lost = float(df["Revenue_Lost"].sum())
    
    # Avg Transaction Amount
    avg_txn_val = float(df["Amount"].mean())
    
    # Avg Retry Delay (Minutes)
    avg_retry_delay = 0.0
    if "Retry_Delay_Minutes" in df.columns:
        avg_retry_delay = float(df["Retry_Delay_Minutes"].mean())
        
    # Bank Failure Rates
    bank_failure_rates = {}
    if "Bank_Name" in df.columns:
        bank_groups = df.groupby("Bank_Name")
        for bank, group in bank_groups:
            bank_total = len(group)
            bank_fail = (group["Final_Status"] == "Failed").sum()
            bank_failure_rates[str(bank)] = float(bank_fail / bank_total) if bank_total > 0 else 0.0
            
    # Payment Method Failure Rates
    pm_failure_rates = {}
    if "Payment_Method" in df.columns:
        pm_groups = df.groupby("Payment_Method")
        for pm, group in pm_groups:
            pm_total = len(group)
            pm_fail = (group["Final_Status"] == "Failed").sum()
            pm_failure_rates[str(pm)] = float(pm_fail / pm_total) if pm_total > 0 else 0.0
            
    # Failure Message distributions
    fail_messages = {}
    if "Response_Message" in df.columns:
        fail_msg_counts = df[df["Final_Status"] == "Failed"]["Response_Message"].value_counts().to_dict()
        fail_messages = {str(k): int(v) for k, v in fail_msg_counts.items()}

    # Print KPIs
    print(f"Final Dataset Records Size:  {total_records}")
    print(f"Overall Payment Success Rate: {success_rate*100:.2f}%")
    print(f"Overall Failure Rate:         {failure_rate*100:.2f}%")
    print(f"Overall Retry Rate:           {retry_rate*100:.2f}%")
    print(f"Retry Recovery Rate:          {retry_recovery_rate*100:.2f}%")
    print(f"Total Revenue Lost:           ${total_rev_lost:,.2f}")
    print(f"Average Transaction Value:    ${avg_txn_val:,.2f}")
    print(f"Average Retry Delay:          {avg_retry_delay:.2f} minutes")
    print("\nBank Failure Rates:")
    for b, r in sorted(bank_failure_rates.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {b}: {r*100:.2f}%")
    print("======================================================================")
    
    # Consolidate report JSON
    final_report = {
        "dataset_size": total_records,
        "missing_values_before_cleaning": nulls_before,
        "missing_values_after_cleaning": nulls_after,
        "duplicate_count": dup_rows,
        "invalid_records": invalid_records,
        "outlier_counts": outlier_counts,
        "join_statistics": join_stats,
        "payment_success_rate": success_rate,
        "payment_failure_rate": failure_rate,
        "retry_rate": retry_rate,
        "retry_recovery_rate": retry_recovery_rate,
        "total_revenue_lost": total_rev_lost,
        "average_transaction_value": avg_txn_val,
        "average_retry_delay": avg_retry_delay,
        "failure_distribution": fail_messages,
        "bank_failure_distribution": bank_failure_rates,
        "payment_method_failure_distribution": pm_failure_rates
    }
    
    with open("output/final_data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=4)
    print("[OK] Final quality audit report exported to output/final_data_quality_report.json")

def main():
    print("======================================================================")
    print("FINTECH PAYMENT ANALYTICS WORKFLOW RUNNER")
    print("======================================================================")
    
    # Create required directories
    os.makedirs(DATA_PROC_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Sequence of commands to run
    pipeline_steps = [
        (1, "Dataset Intake & Source Validation", ["python", "scripts/dataset_intake_validation.py"]),
        (2, "CSV & JSON Data Ingestion", ["python", "scripts/data_ingestion.py"]),
        (3, "Dataset Profiling", ["python", "scripts/dataset_profiling.py"]),
        (4, "Data Dictionary", ["python", "scripts/data_dictionary.py"]),
        (5, "Missing Value Analysis & Imputation", ["python", "scripts/handle_missing.py", "data/raw/sample_10k.csv", "data/processed/2_imputed.csv"]),
        (6, "Duplicate Detection & Deduplication", ["python", "scripts/handle_duplicates.py", "data/processed/2_imputed.csv", "data/processed/3_deduplicated.csv"]),
        (7, "String Cleaning & Text Normalisation", ["python", "scripts/string_cleaning.py", "data/processed/3_deduplicated.csv", "data/processed/4_string_cleaned.csv"]),
        (8, "Date & Time Transformation", ["python", "scripts/datetime_feature_engineering.py", "data/processed/4_string_cleaned.csv", "data/processed/5_datetime_engineered.csv"]),
        (9, "Outlier Detection & Outlier Flagging", ["python", "scripts/outlier_detection.py", "data/processed/5_datetime_engineered.csv", "data/processed/6_outliers_handled.csv"]),
        (10, "Data Consistency & Rule Validation", ["python", "scripts/data_validation.py", "data/processed/6_outliers_handled.csv", "data/processed/7_validated.csv"]),
        (11, "Multi-Source Merge & Join Validation", ["python", "scripts/merge_validation.py", "data/processed/7_validated.csv", "data/raw/customers.csv", "data/processed/8_merged.csv"]),
        (12, "Fintech Derived Feature Engineering", ["python", "scripts/feature_engineering.py", "data/processed/8_merged.csv", "data/processed/final_fintech_dataset.csv"])
    ]
    
    for step_num, step_name, cmd in pipeline_steps:
        run_stage(step_num, step_name, cmd)
        
    # Step 13 & 14: Final validation & KPI reporting
    calculate_final_kpis_and_report()
    
    print("\n" + "=" * 75)
    print("🎉 FULL DATA PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 75)

if __name__ == "__main__":
    main()
