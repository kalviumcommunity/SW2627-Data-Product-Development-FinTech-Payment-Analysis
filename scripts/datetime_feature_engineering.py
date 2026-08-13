#!/usr/bin/env encoding=utf-8
"""
scripts/datetime_feature_engineering.py
Module 2.22 — Date & Time Transformation

This script converts transaction timestamps, extracts calendar features, 
calculates retry delay durations, and exports time-series analysis summaries.
"""

import os
import sys
import pandas as pd

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/4_string_cleaned.csv"
        output_path = "data/processed/5_datetime_engineered.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    print("======================================================================")
    print("DATE & TIME TRANSFORMATION PIPELINE")
    print("======================================================================")
    
    # 1. Parse dates safely
    date_cols = ["Transaction_Time", "Retry_Time"]
    for col in date_cols:
        if col in df.columns:
            # Report invalid timestamps before parsing
            raw_series = df[col].astype(str)
            # Safe conversion
            parsed = pd.to_datetime(df[col], errors="coerce")
            
            valid_count = parsed.notna().sum()
            invalid_count = parsed.isna().sum() - df[col].isnull().sum() # Invalid but not originally missing
            
            print(f"Parsing {col}:")
            print(f"  - Valid timestamps:   {valid_count}")
            print(f"  - Invalid format:     {invalid_count}")
            print(f"  - Missing/Null values: {df[col].isnull().sum()}")
            
            df[col] = parsed

    # 2. Handle missing Transaction_Time
    rows_before = len(df)
    # Drop rows where Transaction_Time is missing
    df = df.dropna(subset=["Transaction_Time"])
    rows_removed = rows_before - len(df)
    if rows_removed > 0:
        print(f"\n[WARNING] Removed {rows_removed} rows due to invalid/missing Transaction_Time.")
    
    # 3. Extract time features
    print("\nExtracting Calendar Features...")
    df["Day_of_Week"] = df["Transaction_Time"].dt.day_name()
    df["Hour"] = df["Transaction_Time"].dt.hour
    df["Month"] = df["Transaction_Time"].dt.month_name()
    df["Week_Number"] = df["Transaction_Time"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Transaction_Time"].dt.year
    print("  Calendar dimensions (Day_of_Week, Hour, Month, Week_Number, Year) successfully added.")

    # 4. Calculate Retry Delay
    if "Retry_Time" in df.columns:
        print("\nCalculating Retry Delays (Minutes)...")
        # Subtract transaction time from retry time
        delay_delta = df["Retry_Time"] - df["Transaction_Time"]
        df["Retry_Delay_Minutes"] = delay_delta.dt.total_seconds() / 60
        # If retry time is before transaction time, it is invalid (handled in validation phase)
        print(f"  Retry delay computed for {df['Retry_Delay_Minutes'].notna().sum()} records.")
        
    # 5. Days since transaction
    print("\nCalculating Recency (Days)...")
    # Base recency calculation on maximum transaction time in dataset + 1 day to represent a stable benchmark
    max_date = df["Transaction_Time"].max()
    benchmark_date = max_date + pd.Timedelta(days=1)
    df["Days_Since_Transaction"] = (benchmark_date - df["Transaction_Time"]).dt.days
    print(f"  Recency benchmark date used: {benchmark_date}")
    
    # 6. Time series summary aggregates
    print("\n" + "-" * 50)
    print("TIME-SERIES SUMMARY STATISTICS:")
    print("-" * 50)
    
    # Hourly volume
    print("\nHourly Transaction Count:")
    hourly_volume = df.groupby("Hour").size()
    print(hourly_volume.head(5).to_string())
    print("...")
    
    # Revenue by Day
    if "Amount" in df.columns:
        print("\nRevenue Volume by Day of Week:")
        rev_by_day = df.groupby("Day_of_Week")["Amount"].sum()
        print(rev_by_day.to_string())
        
    print("======================================================================")

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Datetime engineered dataset saved to {output_path}")

if __name__ == "__main__":
    main()