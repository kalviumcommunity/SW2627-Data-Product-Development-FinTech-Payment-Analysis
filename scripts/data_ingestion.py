#!/usr/bin/env python3
"""
scripts/data_ingestion.py
Module 2.15 — CSV & JSON Data Ingestion

This script provides reusable functions to load CSV and JSON datasets correctly
using Pandas. It also runs basic ingestion checks without cleaning or imputing.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Config
RAW_DIR = "data/raw"
CSV_PATH = os.path.join(RAW_DIR, "sample_10k.csv")
JSON_PATH = os.path.join(RAW_DIR, "sample_nested_transactions.json")

def load_csv(file_path, delimiter=',', encoding='utf-8'):
    """
    Ingests a CSV file into a Pandas DataFrame.
    Does not silently ignore parsing errors.
    """
    print(f"Attempting to load CSV: {file_path}")
    print(f"  - Expected Encoding: {encoding}")
    print(f"  - Expected Delimiter: '{delimiter}'")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
        
    try:
        # Load the CSV. Explicitly raise parser errors if any.
        df = pd.read_csv(file_path, sep=delimiter, encoding=encoding, on_bad_lines='error')
        return df
    except Exception as e:
        print(f"[ERROR] Failed to ingest CSV {file_path}: {str(e)}")
        raise e

def load_json(file_path, encoding='utf-8'):
    """
    Ingests a JSON file into a Pandas DataFrame.
    If the JSON is nested, flattens it using pd.json_normalize().
    """
    print(f"Attempting to load JSON: {file_path}")
    print(f"  - Expected Encoding: {encoding}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
        
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
            
        # Determine if JSON is a nested structure
        is_nested = False
        if isinstance(data, list):
            # Check if list elements contain dicts or lists
            for item in data:
                if isinstance(item, dict):
                    for val in item.values():
                        if isinstance(val, (dict, list)):
                            is_nested = True
                            break
                if is_nested:
                    break
            
            if is_nested:
                print("  - Structure: Nested list of objects. Applying pd.json_normalize().")
                df = pd.json_normalize(data)
            else:
                print("  - Structure: Flat list of objects. Applying pd.DataFrame().")
                df = pd.DataFrame(data)
                
        elif isinstance(data, dict):
            # Check if dict values contain nested containers
            is_nested = any(isinstance(val, (dict, list)) for val in data.values())
            if is_nested:
                print("  - Structure: Nested object. Applying pd.json_normalize().")
                df = pd.json_normalize(data)
            else:
                print("  - Structure: Flat object. Applying pd.DataFrame([data]).")
                df = pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported JSON root type: {type(data)}")
            
        return df
    except Exception as e:
        print(f"[ERROR] Failed to ingest JSON {file_path}: {str(e)}")
        raise e

def run_basic_checks(df, label="Dataset"):
    """
    Prints dimensions, columns, head, and data types of the loaded DataFrame.
    Verifies that the DataFrame is not empty.
    """
    print(f"\nIngestion checks for: {label}")
    print("-" * 40)
    
    # 1. Dimensions
    shape = df.shape
    print(f"Shape: {shape[0]} rows, {shape[1]} columns")
    
    # 2. Check for empty
    if df.empty or shape[0] == 0:
        raise ValueError(f"The loaded DataFrame '{label}' is empty.")
    
    # 3. Columns list
    print(f"Columns: {df.columns.tolist()}")
    
    # 4. Data Types
    print("\nData Types:")
    print(df.dtypes)
    
    # 5. Head preview
    print("\nFirst 3 rows preview:")
    print(df.head(3))
    print("-" * 40)

def main():
    print("=" * 60)
    print("MODULE 2.15: CSV & JSON DATA INGESTION")
    print("=" * 60)
    
    success = True
    
    # 1. Load CSV
    try:
        df_csv = load_csv(CSV_PATH)
        run_basic_checks(df_csv, label="Main Transaction CSV (sample_10k.csv)")
    except Exception as e:
        print(f"CSV Ingestion Failed: {str(e)}")
        success = False

    # 2. Load JSON
    try:
        if os.path.exists(JSON_PATH):
            df_json = load_json(JSON_PATH)
            run_basic_checks(df_json, label="Sample Nested JSON (sample_nested_transactions.json)")
        else:
            print(f"\n[INFO] Optional JSON dataset {JSON_PATH} does not exist.")
    except Exception as e:
        print(f"JSON Ingestion Failed: {str(e)}")
        success = False

    if success:
        print("\n" + "=" * 60)
        print("✓ Dataset successfully ingested")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Ingestion validation failed")
        print("=" * 60)

if __name__ == "__main__":
    main()
