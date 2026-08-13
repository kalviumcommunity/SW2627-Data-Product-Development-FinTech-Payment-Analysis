#!/usr/bin/env python3
"""
scripts/dataset_intake_validation.py
Module 2.14 — Dataset Intake & Source Validation

This script validates incoming datasets to check if they are ready for ingestion
and analysis. It checks file existence, extensions, encoding, parsing structure,
and required fintech column schema.
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
OUTPUT_DIR = "output"
MAIN_TXN_FILE = os.path.join(RAW_DIR, "sample_10k.csv")
REPORT_PATH = os.path.join(OUTPUT_DIR, "intake_validation_report.json")

REQUIRED_TRANSACTION_COLUMNS = [
    "Transaction_ID",
    "Customer_ID",
    "Amount",
    "Payment_Method",
    "Bank_Name",
    "Response_Code",
    "Response_Message",
    "Retry_Count",
    "Transaction_Time",
    "Retry_Time",
    "Final_Status",
    "Failure_Type",
    "Revenue_Lost"
]

def check_file_metadata(file_path):
    """
    Check if a file exists, get its name, size, and type.
    """
    file_name = os.path.basename(file_path)
    exists = os.path.exists(file_path)
    
    if not exists:
        return {
            "file_name": file_name,
            "exists": False,
            "size_bytes": 0,
            "file_type": "unknown"
        }
    
    size_bytes = os.path.getsize(file_path)
    _, ext = os.path.splitext(file_name)
    file_type = ext.lower().replace('.', '')
    
    return {
        "file_name": file_name,
        "exists": True,
        "size_bytes": size_bytes,
        "file_type": file_type
    }

def check_file_encoding(file_path):
    """
    Validate that the file can be decoded using UTF-8.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(4096)  # Read initial chunk to verify encoding
        return "utf-8", None
    except UnicodeDecodeError as e:
        # If UTF-8 fails, try to identify what's wrong (without modifying)
        return None, str(e)
    except Exception as e:
        return None, f"Failed to open file: {str(e)}"

def check_csv_structure(file_path):
    """
    Verify CSV parsing structure, row/column counts, delimiter, and column names.
    """
    delimiters = [',', ';', '\t', '|']
    valid_delimiter = None
    
    # Simple delimiter heuristic
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        # Find which delimiter appears most frequently in the header
        counts = {d: first_line.count(d) for d in delimiters}
        best_delim = max(counts, key=counts.get)
        if counts[best_delim] > 0:
            valid_delimiter = best_delim
        else:
            valid_delimiter = ','
    except Exception:
        valid_delimiter = ','

    try:
        # Load csv without modifying data
        df = pd.read_csv(file_path, sep=valid_delimiter, nrows=5)
        # Try full parse to verify
        df_full = pd.read_csv(file_path, sep=valid_delimiter)
        
        return {
            "parsable": True,
            "delimiter": valid_delimiter,
            "rows": len(df_full),
            "columns": len(df_full.columns),
            "column_names": df_full.columns.tolist(),
            "error": None
        }
    except Exception as e:
        return {
            "parsable": False,
            "delimiter": valid_delimiter,
            "rows": 0,
            "columns": 0,
            "column_names": [],
            "error": str(e)
        }

def check_json_structure(file_path):
    """
    Validate JSON structure: valid json, container type (list/dict), nestedness,
    and whether it can be loaded into a DataFrame.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        is_list = isinstance(data, list)
        is_dict = isinstance(data, dict)
        
        # Check if nested (if any value is list or dict)
        is_nested = False
        if is_list and len(data) > 0:
            is_nested = any(isinstance(v, (dict, list)) for v in data[0].values() if isinstance(data[0], dict))
        elif is_dict:
            is_nested = any(isinstance(v, (dict, list)) for v in data.values())

        # Check DataFrame convertibility
        can_convert = False
        try:
            if is_nested:
                pd.json_normalize(data)
            else:
                pd.DataFrame(data)
            can_convert = True
        except Exception:
            pass

        structure_type = "list" if is_list else ("dict" if is_dict else "scalar")
        if is_nested:
            structure_type += " (nested)"

        return {
            "valid": True,
            "structure_type": structure_type,
            "convertible_to_df": can_convert,
            "error": None
        }
    except Exception as e:
        return {
            "valid": False,
            "structure_type": "unknown",
            "convertible_to_df": False,
            "error": str(e)
        }

def validate_fintech_schema(columns):
    """
    Check columns against REQUIRED_TRANSACTION_COLUMNS.
    Returns (missing_required, extra_columns)
    """
    existing_cols_set = set(columns)
    required_cols_set = set(REQUIRED_TRANSACTION_COLUMNS)
    
    missing_required = list(required_cols_set - existing_cols_set)
    extra_columns = list(existing_cols_set - required_cols_set)
    
    return missing_required, extra_columns

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    print("=" * 60)
    print("MODULE 2.14: DATASET INTAKE & SOURCE VALIDATION")
    print("=" * 60)

    # Track overall statuses for terminal print
    dataset_exists = False
    format_validated = True
    encoding_validated = True
    schema_validated = True
    
    # 1. Look for all files in data/raw
    all_files = [os.path.join(RAW_DIR, f) for f in os.listdir(RAW_DIR) if os.path.isfile(os.path.join(RAW_DIR, f))]
    if not all_files:
        print("No files found in data/raw/ to validate.")
        return

    # Check if main dataset exists
    dataset_exists = os.path.exists(MAIN_TXN_FILE)

    reports = []
    main_report = None

    for file_path in all_files:
        meta = check_file_metadata(file_path)
        file_name = meta["file_name"]
        
        print(f"\nAnalyzing file: {file_name}")
        print(f"  - Path: {file_path}")
        print(f"  - Exists: {meta['exists']}")
        if not meta["exists"]:
            print(f"  - Size: 0 bytes")
            continue
        print(f"  - Size: {meta['size_bytes']} bytes")
        print(f"  - Extension: .{meta['file_type']}")

        # Validate file extension
        if meta["file_type"] not in ["csv", "json"]:
            print(f"  - [WARNING] Unsupported format: .{meta['file_type']}")
            format_validated = False
            continue

        # Validate encoding
        enc, enc_err = check_file_encoding(file_path)
        if enc_err:
            print(f"  - [ERROR] Encoding failure: {enc_err}")
            encoding_validated = False
            continue
        print(f"  - Encoding: {enc}")

        # Structure analysis
        rows = 0
        cols = 0
        missing_req = []
        extra_cols = []
        parsable = False

        if meta["file_type"] == "csv":
            csv_info = check_csv_structure(file_path)
            if not csv_info["parsable"]:
                print(f"  - [ERROR] CSV parsing error: {csv_info['error']}")
                parsable = False
            else:
                parsable = True
                rows = csv_info["rows"]
                cols = csv_info["columns"]
                print(f"  - Parsable: Yes (Delimiter: '{csv_info['delimiter']}')")
                print(f"  - Rows: {rows}, Columns: {cols}")
                
                # If this is the main dataset, or contains transaction fields, check required columns
                # Let's perform schema check for sample_10k.csv and transactions.csv
                if file_name == "sample_10k.csv" or "transaction" in file_name.lower():
                    missing_req, extra_cols = validate_fintech_schema(csv_info["column_names"])
                    if missing_req:
                        print(f"  - Missing Required Columns: {missing_req}")
                        schema_validated = False
                    else:
                        print(f"  - Schema Validated: All {len(REQUIRED_TRANSACTION_COLUMNS)} required columns present.")
                    if extra_cols:
                        print(f"  - Extra Columns: {extra_cols}")
                        
        elif meta["file_type"] == "json":
            json_info = check_json_structure(file_path)
            if not json_info["valid"]:
                print(f"  - [ERROR] JSON parsing error: {json_info['error']}")
                parsable = False
            else:
                parsable = True
                print(f"  - Parsable: Yes (Structure: {json_info['structure_type']})")
                print(f"  - Convertible to DataFrame: {'Yes' if json_info['convertible_to_df'] else 'No'}")
                # Load to get rows/cols for report
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        df_json = pd.json_normalize(data)
                        rows = len(df_json)
                        cols = len(df_json.columns)
                    else:
                        rows = 1
                        cols = len(data.keys())
                except Exception:
                    pass

        # Build report dict
        ingestion_ready = parsable and len(missing_req) == 0
        file_report = {
            "file_name": file_name,
            "file_exists": meta["exists"],
            "file_type": meta["file_type"],
            "encoding": enc or "unknown",
            "rows": rows,
            "columns": cols,
            "required_columns_missing": missing_req,
            "extra_columns": extra_cols,
            "ingestion_ready": ingestion_ready
        }
        
        reports.append(file_report)
        if file_name == "sample_10k.csv":
            main_report = file_report

    # If main report wasn't identified by name, use the first ingestion_ready CSV with most columns
    if main_report is None and reports:
        csv_reports = [r for r in reports if r["file_type"] == "csv" and r["ingestion_ready"]]
        if csv_reports:
            main_report = max(csv_reports, key=lambda r: r["columns"])
        else:
            main_report = reports[0]

    # Write report
    if main_report:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(main_report, f, indent=4)
        print(f"\n[OK] Intake report written to {REPORT_PATH}")
    else:
        print("\n[WARNING] Could not determine main dataset to write intake report.")

    print("\n" + "=" * 60)
    print("INTAKE SUMMARY CHECKLIST:")
    print("=" * 60)
    if dataset_exists:
        print("✓ Dataset exists")
    else:
        print("✗ Dataset missing")
        
    if format_validated:
        print("✓ File format validated")
    else:
        print("✗ File format contains errors/unsupported extensions")
        
    if encoding_validated:
        print("✓ Encoding validated")
    else:
        print("✗ Encoding issues detected")
        
    if schema_validated:
        print("✓ Schema validated")
    else:
        print("✗ Schema contains missing required columns")

if __name__ == "__main__":
    main()
