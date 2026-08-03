"""
File: data_workflow.py
Project: FinTech Payment Analytics Dashboard

Description:
This script orchestrates the complete 18-step data workflow:
1. Generates sample datasets if missing.
2. Performs missing value imputation.
3. Loads data and enforces types.
4. Performs cleaning, deduplication, and quality validation.
5. Performs multi-source merge and join validation.
6. Conducts feature engineering and vectorised computations.
7. Executes advanced statistical, segmentation, and time-series analytics.
8. Conducts anomaly detection and root cause investigations.
9. Exports final processed datasets and analytics summary files.
"""

import os
import sys

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime

# Import modular components
from src.data_loader import load_transaction_data, load_customer_master, merge_datasets
from src.cleaning import clean_transactions, validate_data_quality
from src.feature_engineering import engineer_time_features, engineer_business_features
from src.analytics import (
    compute_vectorised_fees_discounts,
    analyze_amount_distribution,
    analyze_numerical_correlations,
    analyze_merchant_and_bank_segments,
    analyze_time_series_trends,
    perform_behavioural_segmentation,
    analyze_payment_funnel,
    build_kpi_dashboard,
    detect_revenue_anomalies,
    run_root_cause_investigation
)

# Configuration
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_DIR = "output"

TXN_RAW_PATH = os.path.join(RAW_DIR, "sample_10k.csv")
CUSTOMER_RAW_PATH = os.path.join(RAW_DIR, "customer_master.csv")
TXN_IMPUTED_PATH = os.path.join(PROCESSED_DIR, "cleaned_sample_10k.csv")
TXN_ENRICHED_PATH = os.path.join(PROCESSED_DIR, "enriched_transactions_10k.csv")
CUSTOMER_SEGMENTS_PATH = os.path.join(PROCESSED_DIR, "customer_segments.csv")

def ensure_raw_datasets():
    """Ensure raw dataset files are present in data/raw/."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Generate sample_10k.csv if missing
    if not os.path.exists(TXN_RAW_PATH):
        print("Generating raw transaction dataset sample_10k.csv...")
        # Run generate_sample_10k.py
        subprocess.run(["python", "scripts/generate_sample_10k.py"], check=True)
    else:
        print("[OK] Raw transaction dataset already exists.")
        
    # 2. Generate customer_master.csv if missing
    if not os.path.exists(CUSTOMER_RAW_PATH):
        print("Generating customer master dataset customer_master.csv...")
        # Load transaction customer IDs to ensure overlap
        df_txn = pd.read_csv(TXN_RAW_PATH)
        unique_customers = df_txn['Customer_ID'].unique()
        
        # Keep 95% of customers in customer master to simulate mismatch in join validation
        np.random.seed(42)
        matched_customers = np.random.choice(unique_customers, size=int(len(unique_customers) * 0.95), replace=False)
        
        df_cust = pd.DataFrame({
            'Customer_ID': unique_customers,
            'Customer_Name': [f"Customer {cid}" for cid in unique_customers],
            'Customer_Segment': np.random.choice(['Bronze', 'Silver', 'Gold'], size=len(unique_customers), p=[0.6, 0.3, 0.1]),
            'Customer_Age': np.random.randint(18, 75, size=len(unique_customers)),
            'Account_Created_Time': [datetime(2025, 1, 1).strftime('%Y-%m-%d') for _ in unique_customers]
        })
        
        # Remove the 5% mismatched customers
        df_cust_partial = df_cust[df_cust['Customer_ID'].isin(matched_customers)]
        df_cust_partial.to_csv(CUSTOMER_RAW_PATH, index=False)
        print(f"[OK] Saved customer master to {CUSTOMER_RAW_PATH} with {len(df_cust_partial)} records.")
    else:
        print("[OK] Customer master dataset already exists.")

def run_missing_value_imputation():
    """Orchestrate missing value imputation by calling handle_missing.py script."""
    print("\nRunning Missing Value Imputation pipeline...")
    # Invoke handle_missing.py script
    subprocess.run(["python", "scripts/handle_missing.py", TXN_RAW_PATH, TXN_IMPUTED_PATH], check=True)
    print("[OK] Imputation pipeline completed successfully.")

def main():
    print("=" * 80)
    print("FINTECH PAYMENT ANALYTICS WORKFLOW")
    print("=" * 80)
    
    # Setup
    ensure_raw_datasets()
    run_missing_value_imputation()
    
    # Phase 1: Load Imputed Data & Enforce Types (2.19)
    print("\n[Phase 1] Ingestion & Type Standardisation (Skill 2.19)...")
    type_hints = {
        'Transaction_ID': 'object',
        'Customer_ID': 'object',
        'Amount': 'float64',
        'Retry_Count': 'float64',
        'Response_Code': 'object',
        'Revenue_Lost': 'float64',
        'Transaction_Time': 'object',
        'Retry_Time': 'object'
    }
    df = load_transaction_data(TXN_IMPUTED_PATH, type_hints=type_hints)
    print(f"  Loaded {len(df)} transactions. Schema:")
    for col, dtype in df.dtypes.items():
        print(f"    - {col}: {dtype}")
        
    # Phase 2: Deduplication & Cleaning (2.20 & 2.21)
    print("\n[Phase 2] Cleaning & Record Deduplication (Skill 2.20 & 2.21)...")
    df_clean, duplicates = clean_transactions(df)
    print(f"  Exact duplicates removed: {len(df) - len(df_clean)}")
    if len(duplicates) > 0:
        duplicates.to_csv(os.path.join(OUTPUT_DIR, "duplicates_audit.csv"), index=False)
        print(f"  Saved duplicates audit log to output/duplicates_audit.csv")
        
    # Phase 3: Date & Time Features (2.22)
    print("\n[Phase 3] Date & Time Feature Pipeline (Skill 2.22)...")
    df_features = engineer_time_features(df_clean, date_col='transaction_time')
    print("  Extracted year, month, day, hour, dayofweek, and is_weekend variables.")
    
    # Phase 4: Data Consistency Validation (2.24)
    print("\n[Phase 4] Consistency Checks & Validation Rules (Skill 2.24)...")
    validation_results = validate_data_quality(df_features)
    
    # Save validation rules results
    with open(os.path.join(OUTPUT_DIR, "validation_results.json"), "w") as f:
        json.dump(validation_results, f, indent=2, default=str)
    print("  Saved data consistency checklist to output/validation_results.json")
    
    # Phase 5: Multi-Source Merge & Join Validation (2.25)
    print("\n[Phase 5] Multi-Source Merging & Join Validation (Skill 2.25)...")
    df_customers = load_customer_master(CUSTOMER_RAW_PATH)
    df_merged, join_report = merge_datasets(df_features, df_customers, on_col='customer_id')
    
    with open(os.path.join(OUTPUT_DIR, "join_validation_report.json"), "w") as f:
        json.dump(join_report, f, indent=2, default=str)
    print(f"  Successfully joined transactions with customer master data.")
    print(f"  Unmatched transactions (in left but not in right): {join_report['rows_only_in_left']}")
    
    # Phase 6: Feature Engineering (2.26)
    print("\n[Phase 6] Derived Business Features & CLV (Skill 2.26)...")
    df_features_eng = engineer_business_features(df_merged)
    print("  Calculated Customer transaction scores, risk tiers, and lifetime value.")
    
    # Phase 7: NumPy Vectorisation (2.27)
    print("\n[Phase 7] NumPy Vectorised Computation Workflow (Skill 2.27)...")
    # Fee rates: UPI(1.0%), CC(1.5%), DC(2.0%), NetBank(2.5%), Wallet(3.0%)
    # Discount rates: Tier 0(0%), Tier 1(5%), Tier 2(10%), Tier 3(15%)
    start_time = datetime.now()
    df_computed = compute_vectorised_fees_discounts(df_features_eng)
    elapsed = (datetime.now() - start_time).total_seconds() * 1000
    print(f"  Vectorised calculations complete in {elapsed:.3f} ms.")
    print(f"  Calculated net amounts, merchant processing fees, and customer discounts.")
    
    # Phase 8: Statistical & Segment Analytics (2.28, 2.29, 2.30)
    print("\n[Phase 8] Distribution, Correlation & Segment Analysis (Skills 2.28-2.30)...")
    
    # Distribution
    dist_analysis = analyze_amount_distribution(df_computed)
    with open(os.path.join(OUTPUT_DIR, "amount_distribution.json"), "w") as f:
        json.dump(dist_analysis, f, indent=2, default=str)
    print(f"  Amount distribution shape: {dist_analysis['shape']} (skewness: {dist_analysis['skewness']:.2f})")
    
    # Correlations
    corr_matrix, strong_corrs = analyze_numerical_correlations(df_computed)
    corr_matrix.to_csv(os.path.join(OUTPUT_DIR, "correlation_matrix.csv"))
    print(f"  Computed correlation matrix. Strongest correlations found: {len(strong_corrs)}")
    
    # Segments
    segment_metrics = analyze_merchant_and_bank_segments(df_computed)
    for seg_name, seg_df in segment_metrics.items():
        seg_df.to_csv(os.path.join(OUTPUT_DIR, f"{seg_name}.csv"))
    print("  Computed bank revenue breakdowns and segment comparisons.")
    
    # Phase 9: Time-Series Trend & Rolling Metrics (2.31)
    print("\n[Phase 9] Time-Series Trend & Rolling Metrics (Skill 2.31)...")
    ts_trends = analyze_time_series_trends(df_computed)
    ts_trends['daily_revenue'].to_csv(os.path.join(OUTPUT_DIR, "daily_revenue_trend.csv"))
    print("  Calculated daily transactions resampled trend with 7-day rolling average.")
    
    # Phase 10: Behavioural Segmentation (2.32)
    print("\n[Phase 10] Customer Behavioural Segments (Skill 2.32)...")
    df_customer_segments = perform_behavioural_segmentation(df_computed)
    df_customer_segments.to_csv(CUSTOMER_SEGMENTS_PATH, index=False)
    print(f"  Segmented {len(df_customer_segments)} customers. Profiles saved to {CUSTOMER_SEGMENTS_PATH}")
    print("  Segment count breakdown:")
    print(df_customer_segments['segment'].value_counts())
    
    # Phase 11: Funnel Drop-off Analysis (2.33)
    print("\n[Phase 11] Funnel Analysis & Drop-Off Detection (Skill 2.33)...")
    funnel_df = analyze_payment_funnel(df_computed)
    funnel_df.to_csv(os.path.join(OUTPUT_DIR, "payment_funnel.csv"), index=False)
    print("  Funnel conversion stages:")
    print(funnel_df.to_string(index=False))
    
    # Phase 12: KPI Status Dashboard (2.34)
    print("\n[Phase 12] KPI Definition & Dashboard Design (Skill 2.34)...")
    kpi_dashboard = build_kpi_dashboard(df_computed)
    kpi_dashboard.to_csv(os.path.join(OUTPUT_DIR, "kpi_dashboard.csv"), index=False)
    
    # Phase 13: Anomaly Detection & Flagging (2.36)
    print("\n[Phase 13] Anomaly Detection & Anomaly Flags (Skill 2.36)...")
    daily_rev_series = ts_trends['daily_revenue']
    anomalies, df_flagged = detect_revenue_anomalies(daily_rev_series, df_computed)
    
    # Export flagged records
    df_flagged.to_csv(TXN_ENRICHED_PATH, index=False)
    print(f"  Flagged anomaly records. Saved enriched data to {TXN_ENRICHED_PATH}")
    print(f"  Spikes detected: {anomalies['spike_count']}, Dips detected: {anomalies['dip_count']}")
    
    # Phase 14: Root Cause Investigation (2.35)
    print("\n[Phase 14] Root Cause Investigation Workflow (Skill 2.35)...")
    root_cause = run_root_cause_investigation(df_computed)
    print(f"  Worst payment failure date identified: {root_cause['worst_date']}")
    print(f"  Revenue change percent during worst day: {root_cause['time_isolation']['change_percent']:.1f}%")
    print("\n  Segment failure deviation stats on worst day:")
    print(root_cause['segment_isolation'].head(5))
    
    # Save root cause findings
    with open(os.path.join(OUTPUT_DIR, "root_cause_findings.json"), "w") as f:
        # segment isolation to dict
        findings = {
            'worst_date': str(root_cause['worst_date']),
            'time_isolation': root_cause['time_isolation'],
            'segment_isolation': root_cause['segment_isolation'].to_dict(orient='index')
        }
        json.dump(findings, f, indent=2, default=str)
        
    print("\n" + "=" * 80)
    print("[SUCCESS] Pipeline Execution Successful!")
    print(f"  - Total transactions processed: {len(df_flagged)}")
    print(f"  - Output datasets saved to: {PROCESSED_DIR}")
    print(f"  - Analytics reports exported to: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()