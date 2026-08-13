#!/usr/bin/env encoding=utf-8
"""
scripts/string_cleaning.py
Module 2.21 — String Cleaning & Text Normalisation

This script provides text cleaning functions to normalise case formats, remove 
excess spacing and special characters, and resolve variations in categories.
"""

import os
import sys
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def clean_text_column(
    series,
    lowercase=True,
    strip=True,
    remove_special=False,
    mapping=None
):
    """
    Cleans a text series by applying stripping, casing, regex cleanup,
    and category mapping variations.
    """
    # Force to string and fill nulls with empty first
    s_cleaned = series.fillna("").astype(str)
    
    if strip:
        s_cleaned = s_cleaned.str.strip()
        
    if lowercase:
        s_cleaned = s_cleaned.str.lower()
        
    if remove_special:
        # Keep letters, numbers, and spaces
        s_cleaned = s_cleaned.str.replace(r'[^a-zA-Z0-9 ]', ' ', regex=True)
        
    # Replace multiple spaces with a single space
    s_cleaned = s_cleaned.str.replace(r'\s+', ' ', regex=True).str.strip()
    
    if mapping:
        # Standardise values based on user mapping (using lowercase keys)
        mapping_lower = {k.lower().strip(): v for k, v in mapping.items()}
        s_cleaned = s_cleaned.map(lambda x: mapping_lower.get(x.lower().strip(), x))
        
    return s_cleaned

def main():
    if len(sys.argv) < 3:
        input_path = "data/processed/3_deduplicated.csv"
        output_path = "data/processed/4_string_cleaned.csv"
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    
    print("======================================================================")
    print("STRING CLEANING & TEXT NORMALISATION")
    print("======================================================================")
    
    # Custom business category mappings
    pm_mapping = {
        "credit card": "Credit Card",
        "credit-card": "Credit Card",
        "debit card": "Debit Card",
        "debit-card": "Debit Card",
        "net banking": "Net Banking",
        "net-banking": "Net Banking",
        "upi": "UPI",
        "wallet": "Wallet"
    }
    
    status_mapping = {
        "success": "Success",
        "failed": "Failed",
        "pending": "Pending"
    }
    
    failure_mapping = {
        "temporary": "Temporary",
        "permanent": "Permanent",
        "no failure": "No Failure",
        "unknown": "Unknown"
    }
    
    clean_configs = {
        "Payment_Method": {"mapping": pm_mapping, "remove_special": True},
        "Bank_Name": {"remove_special": True},
        "Response_Message": {"remove_special": True},
        "Final_Status": {"mapping": status_mapping, "remove_special": True},
        "Failure_Type": {"mapping": failure_mapping, "remove_special": True}
    }
    
    for col, config in clean_configs.items():
        if col in df.columns:
            print(f"\nProcessing column: {col}")
            # Display unique before
            before_unique = df[col].dropna().unique()
            print(f"  - Unique values before (up to 5): {before_unique[:5]}")
            
            # Clean
            df[col] = clean_text_column(
                df[col],
                lowercase=True,
                strip=True,
                remove_special=config.get("remove_special", False),
                mapping=config.get("mapping", None)
            )
            
            # Recast "no failure" back to capitalized or null if required?
            # We explicitly mapped "no failure" to "No Failure".
            
            # Display unique after
            after_unique = df[col].unique()
            print(f"  - Unique values after (up to 5):  {after_unique[:5]}")
            
    print("======================================================================")
    
    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] String cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    main()