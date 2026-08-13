#!/usr/bin/env encoding=utf-8
"""
scripts/feature_engineering.py
Module 2.26 — Feature Engineering & Feature Validation

This script derives analytical fintech attributes from payments data (value tiers,
retry intensity, recovery states, friction classes, delay buckets, and risk scores),
profiles their validation statistics, and exports the final dataset.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def derive_business_features(df):
    """
    Creates derived business features adapted specifically for fintech payment retry analysis.
    """
    df_feat = df.copy()
    
    # 1. Transaction Value Tier
    # bins: [0, 10000, 50000, inf]
    df_feat["Transaction_Value_Tier"] = pd.cut(
        df_feat["Amount"],
        bins=[-np.inf, 10000.0, 50000.0, np.inf],
        labels=["Low", "Medium", "High"]
    ).astype(str)
    
    # 2. Retry Intensity
    df_feat["Retry_Intensity"] = "No Retry"
    df_feat.loc[(df_feat["Retry_Count"] >= 1) & (df_feat["Retry_Count"] <= 2), "Retry_Intensity"] = "Low Retry"
    df_feat.loc[df_feat["Retry_Count"] >= 3, "Retry_Intensity"] = "High Retry"
    
    # 3. Retry Recovery Status
    df_feat["Retry_Recovery_Status"] = "No Retry"
    df_feat.loc[(df_feat["Retry_Count"] > 0) & (df_feat["Final_Status"] == "Success"), "Retry_Recovery_Status"] = "Recovered After Retry"
    df_feat.loc[(df_feat["Retry_Count"] > 0) & (df_feat["Final_Status"] == "Failed"), "Retry_Recovery_Status"] = "Failed After Retry"
    df_feat.loc[(df_feat["Retry_Count"] > 0) & (~df_feat["Final_Status"].isin(["Success", "Failed"])), "Retry_Recovery_Status"] = "Other Status"

    # 4. Revenue Status
    df_feat["Revenue_Status"] = "No Revenue Loss"
    df_feat.loc[df_feat["Revenue_Lost"] > 0, "Revenue_Status"] = "Revenue Lost"
    
    # 5. Payment Friction Category
    df_feat["Payment_Friction_Category"] = "Low Friction" # default success, no retry
    df_feat.loc[(df_feat["Retry_Count"] > 0) & (df_feat["Final_Status"] == "Success"), "Payment_Friction_Category"] = "Medium Friction"
    df_feat.loc[df_feat["Final_Status"] == "Failed", "Payment_Friction_Category"] = "High Friction"
    df_feat.loc[df_feat["Final_Status"] == "Pending", "Payment_Friction_Category"] = "Medium Friction"

    # 6. Retry Delay Category
    # If no retry occurred, value will be 'No Retry'. Else, bin based on minutes
    df_feat["Retry_Delay_Category"] = "No Retry"
    if "Retry_Delay_Minutes" in df_feat.columns:
        retry_mask = df_feat["Retry_Count"] > 0
        df_feat.loc[retry_mask & (df_feat["Retry_Delay_Minutes"] < 10), "Retry_Delay_Category"] = "Short Delay"
        df_feat.loc[retry_mask & (df_feat["Retry_Delay_Minutes"] >= 10) & (df_feat["Retry_Delay_Minutes"] < 30), "Retry_Delay_Category"] = "Medium Delay"
        df_feat.loc[retry_mask & (df_feat["Retry_Delay_Minutes"] >= 30), "Retry_Delay_Category"] = "Long Delay"
        
    # 7. Customer/Transaction Risk Score
    # Risk score calculation logic:
    # - Start at 0 points.
    # - If Final_Status is Failed -> add 45 points (critical operational loss)
    # - If Revenue_Lost > 0 -> add 25 points (financial loss)
    # - If Retry_Count is high (>= 3) -> add 20 points (high friction)
    # - If Retry_Count is low (1 or 2) -> add 10 points (some friction)
    # Maximum risk score is 90 points (representing critical failure).
    risk = np.zeros(len(df_feat))
    
    risk += np.where(df_feat["Final_Status"] == "Failed", 45.0, 0.0)
    risk += np.where(df_feat["Revenue_Lost"] > 0, 25.0, 0.0)
    risk += np.where(df_feat["Retry_Count"] >= 3, 20.0, 0.0)
    risk += np.where((df_feat["Retry_Count"] >= 1) & (df_feat["Retry_Count"] <= 2), 10.0, 0.0)
    
    df_feat["Risk_Score"] = risk
    
    return df_feat

def run_feature_validation(df_feat, new_cols):
    """
    Validates engineered features for nulls, value distributions, and categories.
    """
    validation_report = {}
    
    for col in new_cols:
        if col in df_feat.columns:
            null_count = int(df_feat[col].isnull().sum())
            val_counts = df_feat[col].value_counts(dropna=False).to_dict()
            # Convert keys to string for JSON serialization
            val_counts = {str(k): int(v) for k, v in val_counts.items()}
            
            if np.issubdtype(df_feat[col].dtype, np.number):
                min_val = float(df_feat[col].min())
                max_val = float(df_feat[col].max())
            else:
                min_val = str(df_feat[col].min())
                max_val = str(df_feat[col].max())
                
            validation_report[col] = {
                "null_count": null_count,
                "min_value": min_val,
                "max_value": max_val,
                "value_distribution": val_counts
            }
            
            # Print check status in terminal
            print(f"Feature Validation: '{col}' (non-null: {df_feat[col].notna().sum()}/{len(df_feat)})")
            
    # Save Report JSON
    os.makedirs("output", exist_ok=True)
    with open("output/feature_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=4)
    print("[OK] Feature validation report saved to output/feature_validation_report.json")

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/8_merged.csv"
        output_path = "data/processed/final_fintech_dataset.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Merged input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    print("======================================================================")
    print("FEATURE ENGINEERING & VALIDATION")
    print("======================================================================")
    
    df_features = derive_business_features(df)
    
    new_features = [
        "Transaction_Value_Tier", 
        "Retry_Intensity", 
        "Retry_Recovery_Status", 
        "Revenue_Status", 
        "Payment_Friction_Category", 
        "Retry_Delay_Category", 
        "Risk_Score"
    ]
    
    run_feature_validation(df_features, new_features)
    print("======================================================================")
    
    # Save Final output dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_features.to_csv(output_path, index=False)
    print(f"[OK] Final feature-engineered dataset saved to {output_path}")

if __name__ == "__main__":
    main()
