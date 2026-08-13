#!/usr/bin/env python3
"""
scripts/handle_missing.py
Module: Missing Value Analysis & Imputation Handling

This script profiles missing values, saves a report, applies sensible business
imputation strategies, audits the before/after state, and saves the decisions.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    total_missing_cells = df.isnull().sum().sum()
    
    missing_analysis = pd.DataFrame({
        'column': df.columns,
        'null_count': df.isnull().sum().values,
        'null_percentage': (df.isnull().sum() / total_rows * 100).round(4).values,
        'data_type': [str(t) for t in df.dtypes.values],
        'null_meaning': ''
    })
    
    # Add potential meanings based on columns
    meanings = {
        'Retry_Time': 'No retry occurred for successful transactions',
        'Failure_Type': 'Not a failure, or missing classification',
        'Bank_Name': 'Failed before reaching banking routing gateway',
        'Response_Message': 'Processor did not return text response',
        'Response_Code': 'Processor did not return numerical code',
        'Amount': 'Missing financial amount'
    }
    missing_analysis['null_meaning'] = missing_analysis['column'].map(meanings).fillna('')

    print("======================================================================")
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("======================================================================")
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {total_rows}")
    print(f"Total columns: {total_cols}")
    print(f"Total cells: {total_cells}")
    print(f"Missing cells: {total_missing_cells}")
    print("======================================================================")
    
    # Export report
    os.makedirs("output", exist_ok=True)
    missing_analysis.to_csv("output/missing_value_report.csv", index=False)
    print("[OK] Missing values report exported to output/missing_value_report.csv")
    
    return missing_analysis, total_missing_cells

def handle_imputations(df):
    """
    Impute columns using context-aware business strategies.
    """
    df_imputed = df.copy()
    decisions = {
        "rows_before": len(df),
        "total_nulls_before": int(df.isnull().sum().sum()),
        "columns": {}
    }
    
    # Track strategies
    # 1. Amount -> median
    if 'Amount' in df_imputed.columns:
        null_count = int(df_imputed['Amount'].isnull().sum())
        median_val = float(df_imputed['Amount'].median())
        df_imputed['Amount'] = df_imputed['Amount'].fillna(median_val)
        decisions["columns"]["Amount"] = {
            "column_type": str(df_imputed['Amount'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "median",
            "value_used": median_val,
            "risk_assessment": "Low risk; amount distribution is preserved",
            "over_imputation": False
        }
        
    # 2. Retry_Count -> median
    if 'Retry_Count' in df_imputed.columns:
        null_count = int(df_imputed['Retry_Count'].isnull().sum())
        median_val = float(df_imputed['Retry_Count'].median())
        df_imputed['Retry_Count'] = df_imputed['Retry_Count'].fillna(median_val)
        decisions["columns"]["Retry_Count"] = {
            "column_type": str(df_imputed['Retry_Count'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "median",
            "value_used": median_val,
            "risk_assessment": "Low risk; retry counts cluster around 0-4",
            "over_imputation": False
        }
        
    # 3. Response_Code -> median if statistically appropriate
    if 'Response_Code' in df_imputed.columns:
        null_count = int(df_imputed['Response_Code'].isnull().sum())
        median_val = float(df_imputed['Response_Code'].median())
        df_imputed['Response_Code'] = df_imputed['Response_Code'].fillna(median_val)
        decisions["columns"]["Response_Code"] = {
            "column_type": str(df_imputed['Response_Code'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "median",
            "value_used": median_val,
            "risk_assessment": "Medium risk; response codes are technically categorical, but numerical median represents a typical failure state",
            "over_imputation": False
        }

    # 4. Payment_Method -> mode
    if 'Payment_Method' in df_imputed.columns:
        null_count = int(df_imputed['Payment_Method'].isnull().sum())
        mode_val = str(df_imputed['Payment_Method'].mode().iloc[0])
        df_imputed['Payment_Method'] = df_imputed['Payment_Method'].fillna(mode_val)
        decisions["columns"]["Payment_Method"] = {
            "column_type": str(df_imputed['Payment_Method'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "mode",
            "value_used": mode_val,
            "risk_assessment": "Low risk; assigned most common channel",
            "over_imputation": False
        }
        
    # 5. Bank_Name -> mode
    if 'Bank_Name' in df_imputed.columns:
        null_count = int(df_imputed['Bank_Name'].isnull().sum())
        mode_val = str(df_imputed['Bank_Name'].dropna().mode().iloc[0])
        df_imputed['Bank_Name'] = df_imputed['Bank_Name'].fillna(mode_val)
        decisions["columns"]["Bank_Name"] = {
            "column_type": str(df_imputed['Bank_Name'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "mode",
            "value_used": mode_val,
            "risk_assessment": "Medium risk; could obscure banking pipeline failures if overimputed",
            "over_imputation": False
        }

    # 6. Response_Message -> mode
    if 'Response_Message' in df_imputed.columns:
        null_count = int(df_imputed['Response_Message'].isnull().sum())
        mode_val = str(df_imputed['Response_Message'].dropna().mode().iloc[0])
        df_imputed['Response_Message'] = df_imputed['Response_Message'].fillna(mode_val)
        decisions["columns"]["Response_Message"] = {
            "column_type": str(df_imputed['Response_Message'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "mode",
            "value_used": mode_val,
            "risk_assessment": "Low risk",
            "over_imputation": False
        }

    # 7. Final_Status -> mode
    if 'Final_Status' in df_imputed.columns:
        null_count = int(df_imputed['Final_Status'].isnull().sum())
        mode_val = str(df_imputed['Final_Status'].dropna().mode().iloc[0])
        df_imputed['Final_Status'] = df_imputed['Final_Status'].fillna(mode_val)
        decisions["columns"]["Final_Status"] = {
            "column_type": str(df_imputed['Final_Status'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "mode",
            "value_used": mode_val,
            "risk_assessment": "Low risk",
            "over_imputation": False
        }

    # 8. Failure_Type -> Contextual (If success -> 'No Failure'; else failure mode)
    if 'Failure_Type' in df_imputed.columns:
        null_count = int(df_imputed['Failure_Type'].isnull().sum())
        # Fill based on Final_Status
        success_mask = df_imputed['Final_Status'].str.lower() == 'success'
        df_imputed.loc[success_mask & df_imputed['Failure_Type'].isnull(), 'Failure_Type'] = 'No Failure'
        
        # Fill remaining failures with mode (e.g. 'Temporary' or 'Permanent')
        remaining_nulls = df_imputed['Failure_Type'].isnull().sum()
        if remaining_nulls > 0:
            valid_modes = df_imputed['Failure_Type'].dropna()
            valid_modes = valid_modes[valid_modes.str.lower() != 'no failure']
            mode_val = str(valid_modes.mode().iloc[0]) if not valid_modes.empty else 'Unknown'
            df_imputed['Failure_Type'] = df_imputed['Failure_Type'].fillna(mode_val)
        else:
            mode_val = "N/A (All resolved by status)"
            
        decisions["columns"]["Failure_Type"] = {
            "column_type": str(df_imputed['Failure_Type'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "contextual (success -> 'No Failure'; else failure mode)",
            "value_used": mode_val,
            "risk_assessment": "Low risk; prevents misclassifying success transactions as failures",
            "over_imputation": False
        }

    # 9. Retry_Time -> Contextual (Leave null/NaT if Retry_Count is 0, else Transaction_Time + Median Delay)
    if 'Retry_Time' in df_imputed.columns:
        null_count = int(df_imputed['Retry_Time'].isnull().sum())
        
        # Calculate median delay from non-null valid records
        temp_tx = pd.to_datetime(df_imputed['Transaction_Time'], errors='coerce')
        temp_rt = pd.to_datetime(df_imputed['Retry_Time'], errors='coerce')
        valid_delays = (temp_rt - temp_tx).dt.total_seconds() / 60
        valid_delays = valid_delays[valid_delays >= 0]
        median_delay_min = float(valid_delays.median()) if not valid_delays.empty else 15.0
        
        # Calculate imputed values (Transaction_Time + median_delay_min)
        imputed_rt = temp_tx + pd.to_timedelta(median_delay_min, unit='m')
        # Convert back to string representation matching the format
        imputed_rt_str = imputed_rt.dt.strftime('%Y-%m-%d %H:%M')
        
        # Apply imputation only if Retry_Count > 0 and Retry_Time is null
        rt_is_null = df_imputed['Retry_Time'].isnull()
        has_retries = df_imputed['Retry_Count'] > 0
        
        df_imputed.loc[rt_is_null & has_retries, 'Retry_Time'] = imputed_rt_str[rt_is_null & has_retries]
        
        decisions["columns"]["Retry_Time"] = {
            "column_type": str(df_imputed['Retry_Time'].dtype),
            "null_count_before": null_count,
            "null_pct_before": float((null_count / len(df)) * 100),
            "strategy": "contextual (Retry_Count > 0 -> Transaction_Time + median delay; else keep null)",
            "value_used": f"Transaction_Time + {median_delay_min:.1f}m",
            "risk_assessment": "Low risk; prevents negative retry delays and preserves temporal order",
            "over_imputation": False
        }


    decisions["rows_after"] = len(df_imputed)
    decisions["total_nulls_after"] = int(df_imputed.isnull().sum().sum())
    
    # Save Decisions
    with open("output/imputation_decisions.json", "w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=4)
        
    return df_imputed

def main():
    if len(sys.argv) < 3:
        input_path = "data/raw/sample_10k.csv"
        output_path = "data/processed/2_imputed.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    # Analyze
    _, nulls_before = analyze_missing_values(df)
    
    # Impute
    df_imputed = handle_imputations(df)
    
    # Verify
    nulls_after = df_imputed.isnull().sum().sum()
    
    print("\n======================================================================")
    print("AFTER IMPUTATION - Validation Report")
    print("======================================================================")
    print(f"Total rows before: {len(df)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df) - len(df_imputed)}")
    print(f"\nTotal nulls before: {nulls_before}")
    print(f"Total nulls after:  {nulls_after}")
    print("======================================================================")
    
    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_imputed.to_csv(output_path, index=False)
    print(f"[OK] Cleaned data saved to {output_path}")

if __name__ == "__main__":
    main()
