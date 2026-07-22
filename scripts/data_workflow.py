"""
File: data_workflow.py

Project: FinTech Payment Analytics Dashboard

Description:
This script demonstrates a simple data pipeline consisting of:

1. Data Ingestion
2. Data Processing
3. Output Generation

Author: Your Name
"""

import os
import pandas as pd


# ============================================
# CONFIGURATION
# ============================================

INPUT_FILE = "data/raw/transactions.csv"
OUTPUT_FILE = "data/processed/transactions_clean.csv"


# ============================================
# FUNCTION 1 : INGEST DATA
# ============================================

def ingest_data(filepath):
    """
    Load payment transaction data from a CSV file.

    Parameters
    ----------
    filepath : str
        Path of the CSV file.

    Returns
    -------
    pandas.DataFrame
        Raw transaction dataset.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    print("Reading transaction dataset...")

    df = pd.read_csv(filepath)

    print(f"Loaded {len(df)} records.")

    return df


# ============================================
# FUNCTION 2 : PROCESS DATA
# ============================================

def process_data(df):
    """
    Clean and transform the transaction dataset.

    Processing Steps
    ----------------
    1. Remove duplicate rows.
    2. Fill missing numeric values with median.
    3. Fill missing text values with 'Unknown'.
    4. Standardize status column.
    5. Create a Payment_Result column.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    print("Processing data...")

    rows_before = len(df)

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Fill missing numeric values
    numeric_columns = df.select_dtypes(include="number").columns

    for column in numeric_columns:
        df[column] = df[column].fillna(df[column].median())

    # Fill missing text values
    object_columns = df.select_dtypes(include="object").columns

    for column in object_columns:
        df[column] = df[column].fillna("Unknown")

    # Standardize payment status
    if "status" in df.columns:
        df["status"] = df["status"].str.upper()

    # Create Payment_Result column
    if "status" in df.columns:
        df["Payment_Result"] = df["status"].apply(
            lambda x: "Successful" if x == "SUCCESS" else "Failed"
        )

    rows_after = len(df)

    print(f"Duplicates Removed : {rows_before - rows_after}")

    return df


# ============================================
# FUNCTION 3 : OUTPUT RESULTS
# ============================================

def output_results(df, output_path):
    """
    Save processed dataset.

    Parameters
    ----------
    df : pandas.DataFrame

    output_path : str
        Destination CSV path.

    Returns
    -------
    None
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)

    print("\n===================================")
    print("✓ Data successfully processed")
    print(f"✓ Rows processed : {len(df)}")
    print(f"✓ Output saved to : {output_path}")
    print("===================================")


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":

    try:

        print("\nStarting FinTech Payment Data Workflow...\n")

        # Step 1 : Load data
        transactions = ingest_data(INPUT_FILE)

        # Step 2 : Process data
        cleaned_transactions = process_data(transactions)

        # Step 3 : Save output
        output_results(cleaned_transactions, OUTPUT_FILE)

        print("\nWorkflow completed successfully!")

    except FileNotFoundError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected Error: {error}")