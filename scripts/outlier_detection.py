#!/usr/bin/env encoding=utf-8
"""
scripts/outlier_detection.py
Module 2.23 — Outlier Detection

This script calculates statistical outliers for Amount, Retry_Count, and 
Revenue_Lost using the IQR (Interquartile Range) method, flags outliers,
and outputs a summary JSON report.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/5_datetime_engineered.csv"
        output_path = "data/processed/6_outliers_handled.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    print("======================================================================")
    print("OUTLIER DETECTION (IQR METHOD)")
    print("======================================================================")
    
    numeric_cols = ["Amount", "Retry_Count", "Revenue_Lost"]
    outlier_report = {}
    
    for col in numeric_cols:
        if col in df.columns:
            # Handle non-null values for IQR calculation
            series = df[col].dropna()
            
            Q1 = float(series.quantile(0.25))
            Q3 = float(series.quantile(0.75))
            IQR = Q3 - Q1
            
            lower_bound = float(Q1 - 1.5 * IQR)
            upper_bound = float(Q3 + 1.5 * IQR)
            
            # Count outliers
            outliers_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = int(outliers_mask.sum())
            
            print(f"\nColumn: {col}")
            print(f"  - Q1 (25th pct):   {Q1:,.2f}")
            print(f"  - Q3 (75th pct):   {Q3:,.2f}")
            print(f"  - IQR:             {IQR:,.2f}")
            print(f"  - Lower Boundary:  {lower_bound:,.2f}")
            print(f"  - Upper Boundary:  {upper_bound:,.2f}")
            print(f"  - Outlier Count:   {outlier_count} ({(outlier_count / len(df) * 100):.2f}%)")
            
            # Save stats to report
            outlier_report[col] = {
                "Q1": Q1,
                "Q3": Q3,
                "IQR": IQR,
                "lower_boundary": lower_bound,
                "upper_boundary": upper_bound,
                "outlier_count": outlier_count,
                "outlier_percentage": float((outlier_count / len(df) * 100))
            }
            
            # Flag outliers (keep the data intact as requested by business context)
            df[f"{col}_Is_Outlier"] = outliers_mask.astype(int)
            
    print("======================================================================")
    
    # Save Report
    os.makedirs("output", exist_ok=True)
    with open("output/outlier_report.json", "w", encoding="utf-8") as f:
        json.dump(outlier_report, f, indent=4)
    print("[OK] Outlier stats report saved to output/outlier_report.json")
    
    # Save Output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Outliers flagged and dataset saved to {output_path}")

if __name__ == "__main__":
    main()