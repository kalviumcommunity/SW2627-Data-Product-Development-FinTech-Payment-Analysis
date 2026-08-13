#!/usr/bin/env python3
"""
scripts/dataset_profiling.py
Module 2.16 — Dataset Profiling & Quality Assessment

This script analyzes the fintech transactions dataset to identify dimensions,
datatypes, missing values, duplicates, and statistical descriptions of numerical,
categorical, and date/time fields. It exports a summary profile csv.
"""

import os
import sys
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Config
RAW_DIR = "data/raw"
OUTPUT_DIR = "output"
CSV_PATH = os.path.join(RAW_DIR, "sample_10k.csv")
PROFILE_REPORT_PATH = os.path.join(OUTPUT_DIR, "dataset_profile.csv")

def main():
    print("=" * 60)
    print("MODULE 2.16: DATASET PROFILING & QUALITY ASSESSMENT")
    print("=" * 60)

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Main dataset {CSV_PATH} not found. Cannot profile.")
        return

    # Ingest data (without modification)
    df = pd.read_csv(CSV_PATH)
    
    # 1. Dataset dimensions
    num_rows = len(df)
    num_cols = len(df.columns)
    total_cells = num_rows * num_cols
    
    print("\nDataset Dimensions:")
    print("-" * 40)
    print(f"Rows:         {num_rows}")
    print(f"Columns:      {num_cols}")
    print(f"Total cells:  {total_cells}")
    print("-" * 40)

    # 2. Data types
    print("\nData Types:")
    print("-" * 40)
    print(df.dtypes)
    print("-" * 40)

    # 3. Missing values
    print("\nMissing Values Profile:")
    print("-" * 40)
    missing_count = df.isnull().sum()
    missing_percentage = df.isnull().mean() * 100
    missing_df = pd.DataFrame({
        "Null Count": missing_count,
        "Null Percentage": missing_percentage
    })
    print(missing_df.to_string())
    print("-" * 40)

    # 4. Duplicate records
    print("\nDuplicate Records Profile:")
    print("-" * 40)
    duplicate_rows = df.duplicated().sum()
    print(f"Duplicate rows count: {duplicate_rows}")
    print("-" * 40)

    # 5. Numerical profiling
    print("\nNumerical Profiling:")
    print("-" * 40)
    # Ensure numerical columns are profiled properly
    numerical_cols = ["Amount", "Response_Code", "Retry_Count", "Revenue_Lost"]
    
    # Convert Response_Code to numeric for profiling purposes (temporary copy)
    temp_df = df.copy()
    temp_df["Response_Code"] = pd.to_numeric(temp_df["Response_Code"], errors="coerce")
    
    num_profile = temp_df[numerical_cols].describe().T
    # Add median explicitly as it is required but not in describe() by default
    num_profile["median"] = temp_df[numerical_cols].median()
    # Reorder columns to match request: Count, Mean, Median, Minimum, Maximum, Std
    num_profile = num_profile[["count", "mean", "median", "min", "max", "std"]]
    num_profile.columns = ["Count", "Mean", "Median", "Minimum", "Maximum", "Std Dev"]
    print(num_profile.to_string())
    print("-" * 40)

    # 6. Categorical profiling
    print("\nCategorical Profiling:")
    print("-" * 40)
    categorical_cols = ["Payment_Method", "Bank_Name", "Response_Message", "Final_Status", "Failure_Type"]
    for col in categorical_cols:
        if col in df.columns:
            print(f"\nValue Counts for '{col}' (including nulls):")
            print(df[col].value_counts(dropna=False).to_string())
    print("-" * 40)

    # 7. Date/time profiling
    print("\nDate/Time Profiling:")
    print("-" * 40)
    datetime_cols = ["Transaction_Time", "Retry_Time"]
    for col in datetime_cols:
        if col in df.columns:
            # Create a temporary datetime series to profile
            dt_series = pd.to_datetime(df[col], errors="coerce")
            print(f"Column: {col}")
            print(f"  - Inferred Data Type: {dt_series.dtype}")
            print(f"  - Minimum Value:      {dt_series.min()}")
            print(f"  - Maximum Value:      {dt_series.max()}")
            print(f"  - Missing Values:     {dt_series.isnull().sum()}")
    print("-" * 40)

    # 8. Generate profile report csv
    profile_rows = []
    for col in df.columns:
        dt = str(df[col].dtype)
        null_c = int(df[col].isnull().sum())
        null_p = float(df[col].isnull().mean() * 100)
        uniq_c = int(df[col].nunique())
        dup_c = int(df[col].duplicated().sum())
        
        # Calculate min and max
        min_val = None
        max_val = None
        
        if col in datetime_cols:
            dt_series = pd.to_datetime(df[col], errors="coerce")
            if not dt_series.isnull().all():
                min_val = str(dt_series.min())
                max_val = str(dt_series.max())
        elif np.issubdtype(df[col].dtype, np.number) or col == "Response_Code":
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            if not numeric_series.isnull().all():
                min_val = float(numeric_series.min())
                max_val = float(numeric_series.max())
        else:
            non_nulls = df[col].dropna()
            if not non_nulls.empty:
                min_val = str(non_nulls.min())
                max_val = str(non_nulls.max())
                
        profile_rows.append({
            "column": col,
            "data_type": dt,
            "row_count": num_rows,
            "null_count": null_c,
            "null_percentage": round(null_p, 4),
            "unique_count": uniq_c,
            "duplicate_count": dup_c,
            "min_value": min_val,
            "max_value": max_val
        })
        
    profile_df = pd.DataFrame(profile_rows)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    profile_df.to_csv(PROFILE_REPORT_PATH, index=False)
    print(f"\n[OK] Profiling report exported to {PROFILE_REPORT_PATH}")
    
    print("\n" + "=" * 60)
    print("PROFILING SUMMARY CHECKLIST:")
    print("=" * 60)
    print("✓ Dataset dimensions identified")
    print("✓ Missing values profiled")
    print("✓ Duplicate records profiled")
    print("✓ Data types profiled")
    print("✓ Numerical columns profiled")
    print("✓ Categorical columns profiled")
    print("=" * 60)

if __name__ == "__main__":
    main()
