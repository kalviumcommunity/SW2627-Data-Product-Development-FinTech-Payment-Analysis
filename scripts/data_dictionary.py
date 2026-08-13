#!/usr/bin/env python3
"""
scripts/data_dictionary.py
Module 2.17 — Data Dictionary & Business Context Mapping

This script creates a structured data dictionary for the Fintech Payment Analysis
dataset, documents how the columns map to business KPIs, and maps ambiguous fields
separately.
"""

import os
import sys
import pandas as pd

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Config
OUTPUT_DIR = "output"
DICTIONARY_PATH = os.path.join(OUTPUT_DIR, "data_dictionary.csv")

def main():
    print("=" * 60)
    print("MODULE 2.17: DATA DICTIONARY & BUSINESS CONTEXT MAPPING")
    print("=" * 60)

    # 1. Structured data dictionary entries
    dictionary_data = [
        {
            "column_name": "Transaction_ID",
            "data_type": "object",
            "business_meaning": "Unique identifier for a payment transaction.",
            "example_value": "TXN100001",
            "business_role": "Primary transaction identifier.",
            "expected_format": "Alphanumeric string (starts with 'TXN')",
            "possible_values": "Unique transaction codes",
            "KPI_or_usage": "Transaction tracking and deduplication",
            "ambiguity_notes": "None"
        },
        {
            "column_name": "Customer_ID",
            "data_type": "object",
            "business_meaning": "Identifier representing the customer who initiated the transaction.",
            "example_value": "C1001",
            "business_role": "Customer-level join key.",
            "expected_format": "Alphanumeric string (starts with 'C')",
            "possible_values": "Unique customer codes",
            "KPI_or_usage": "Customer-level behavior tracking and behavioral segmentation",
            "ambiguity_notes": "None"
        },
        {
            "column_name": "Amount",
            "data_type": "float64",
            "business_meaning": "Monetary value of the payment transaction.",
            "example_value": "2500.0",
            "business_role": "Used for revenue and transaction-value analysis.",
            "expected_format": "Positive float or integer",
            "possible_values": "Values greater than 0",
            "KPI_or_usage": "Average Transaction Value, Total Transaction Volume",
            "ambiguity_notes": "Currency is assumed to be local currency (INR) but requires confirmation."
        },
        {
            "column_name": "Payment_Method",
            "data_type": "object",
            "business_meaning": "Payment channel used by the customer.",
            "example_value": "UPI",
            "business_role": "Categorical grouping variable for transaction routing.",
            "expected_format": "Text string (capitalized words)",
            "possible_values": "UPI, Credit Card, Debit Card, Net Banking, Wallet",
            "KPI_or_usage": "Payment Method Failure Rate",
            "ambiguity_notes": "Contains some casing variation in raw input that needs standardization later."
        },
        {
            "column_name": "Bank_Name",
            "data_type": "object",
            "business_meaning": "Bank or financial institution associated with the payment.",
            "example_value": "HDFC",
            "business_role": "Categorical grouping variable for acquiring banks.",
            "expected_format": "Text string (short uppercase bank names)",
            "possible_values": "SBI, HDFC, ICICI, Axis, Kotak, Canara, PNB, BOB, Yes Bank, IndusInd",
            "KPI_or_usage": "Bank Failure Rate",
            "ambiguity_notes": "Can be null if a transaction fails before routing to the partner bank."
        },
        {
            "column_name": "Response_Code",
            "data_type": "object",
            "business_meaning": "Code returned by the bank/payment processor describing the transaction outcome.",
            "example_value": "68",
            "business_role": "Outcome code for failure categorization.",
            "expected_format": "2-digit alphanumeric code",
            "possible_values": "00, 12, 51, 54, 55, 96, 08, 68",
            "KPI_or_usage": "Failure Distribution, error categorisation",
            "ambiguity_notes": "Assumption: Code '00' is Success. Others are failures. Meaning of codes varies slightly by banking partner."
        },
        {
            "column_name": "Response_Message",
            "data_type": "object",
            "business_meaning": "Human-readable explanation associated with the response code.",
            "example_value": "Card Declined",
            "business_role": "Human-readable error description.",
            "expected_format": "Text string",
            "possible_values": "Approved, Insufficient Funds, Expired Card, Network Error, Response Timeout, System Error, Card Declined, Invalid Amount",
            "KPI_or_usage": "Failure Distribution and customer messaging analysis",
            "ambiguity_notes": "Messages are sometimes missing or vary in description for the same error code."
        },
        {
            "column_name": "Retry_Count",
            "data_type": "float64",
            "business_meaning": "Number of payment retry attempts associated with the transaction.",
            "example_value": "4.0",
            "business_role": "Friction metric.",
            "expected_format": "Numeric integer represented as float",
            "possible_values": "Integers greater than or equal to 0",
            "KPI_or_usage": "Retry Recovery Rate, Payment Friction analysis",
            "ambiguity_notes": "Reported as float in raw data due to missing values."
        },
        {
            "column_name": "Transaction_Time",
            "data_type": "object",
            "business_meaning": "Timestamp when the original payment transaction occurred.",
            "example_value": "2026-03-09 23:18",
            "business_role": "Temporal dimension.",
            "expected_format": "YYYY-MM-DD HH:MM string",
            "possible_values": "Valid datetime strings",
            "KPI_or_usage": "Average Retry Delay, Temporal Trend analysis",
            "ambiguity_notes": "Stored as string in raw files; timezone offset is unstated."
        },
        {
            "column_name": "Retry_Time",
            "data_type": "object",
            "business_meaning": "Timestamp associated with the retry attempt.",
            "example_value": "2026-03-09 23:27",
            "business_role": "Temporal dimension for retries.",
            "expected_format": "YYYY-MM-DD HH:MM string",
            "possible_values": "Valid datetime strings or null (if no retry occurred)",
            "KPI_or_usage": "Average Retry Delay calculation",
            "ambiguity_notes": "Assumption: Represents final retry timestamp. Empty if Retry_Count is 0. Validation required: confirm if it represents the first or last retry attempt."
        },
        {
            "column_name": "Final_Status",
            "data_type": "object",
            "business_meaning": "Final outcome of the payment after the transaction and retry process.",
            "example_value": "Success",
            "business_role": "Final categorical outcome.",
            "expected_format": "Text string",
            "possible_values": "Success, Failed, Pending",
            "KPI_or_usage": "Payment Success Rate, Retry Recovery Rate",
            "ambiguity_notes": "None"
        },
        {
            "column_name": "Failure_Type",
            "data_type": "object",
            "business_meaning": "Classification of the payment failure based on whether the issue is temporary or permanent.",
            "example_value": "Temporary",
            "business_role": "Categorical categorization of transaction failure dynamics.",
            "expected_format": "Text string",
            "possible_values": "Temporary, Permanent",
            "KPI_or_usage": "Failure Distribution, revenue recovery prioritization",
            "ambiguity_notes": "Assumption: Temporary failure represents issues like network errors or timeouts that can succeed on retry, while Permanent failure represents issues like insufficient funds. Validation required: confirm categorization rules with payment operations team."
        },
        {
            "column_name": "Revenue_Lost",
            "data_type": "float64",
            "business_meaning": "Monetary value associated with a transaction that ultimately represents lost revenue.",
            "example_value": "0.0",
            "business_role": "Financial loss metric.",
            "expected_format": "Numeric float",
            "possible_values": "Numeric >= 0",
            "KPI_or_usage": "Revenue Lost, leakage tracking",
            "ambiguity_notes": "Assumption: Represents the transaction amount considered unrecovered after final failure. For successful or pending transactions, this value should be 0. Validation required: confirm business definition and logic for revenue loss calculation with finance department."
        }
    ]

    # Convert to DataFrame
    df_dict = pd.DataFrame(dictionary_data)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_dict.to_csv(DICTIONARY_PATH, index=False)
    print(f"[OK] Data dictionary successfully written to {DICTIONARY_PATH}")

    # 2. Document how columns support the fintech business problem (KPIs)
    print("\n" + "=" * 60)
    print("BUSINESS KPI MAPPING:")
    print("=" * 60)
    
    kpis = {
        "Payment Success Rate": {
            "Description": "Percentage of transactions that ultimately succeed.",
            "Columns Used": ["Final_Status"]
        },
        "Retry Recovery Rate": {
            "Description": "Percentage of initially failing transactions that succeed after retrying.",
            "Columns Used": ["Retry_Count", "Final_Status"]
        },
        "Revenue Lost": {
            "Description": "Monetary value of lost revenue opportunities from permanent failures.",
            "Columns Used": ["Revenue_Lost"]
        },
        "Average Transaction Value": {
            "Description": "Average size of transactions processed on the platform.",
            "Columns Used": ["Amount"]
        },
        "Average Retry Delay": {
            "Description": "Mean duration of time between initial failure and final retry.",
            "Columns Used": ["Transaction_Time", "Retry_Time"]
        },
        "Failure Distribution": {
            "Description": "Share of different failure reasons and classifications.",
            "Columns Used": ["Failure_Type", "Response_Code", "Response_Message"]
        },
        "Bank Failure Rate": {
            "Description": "Percentage of failed payments grouped by acquiring bank.",
            "Columns Used": ["Bank_Name", "Final_Status"]
        },
        "Payment Method Failure Rate": {
            "Description": "Percentage of failed payments grouped by payment channel.",
            "Columns Used": ["Payment_Method", "Final_Status"]
        }
    }
    
    for kpi, details in kpis.items():
        print(f"\n- {kpi}")
        print(f"  Description:  {details['Description']}")
        print(f"  Columns Used: {', '.join(details['Columns Used'])}")

    # 3. Document ambiguous fields separately
    print("\n" + "=" * 60)
    print("AMBIGUOUS FIELD DOCUMENTATION & ASSUMPTIONS:")
    print("=" * 60)
    
    ambiguous_fields = {
        "Revenue_Lost": {
            "Assumption": "Represents the transaction amount considered unrecovered after final failure.",
            "Validation Required": "Confirm business definition and logic for revenue loss calculation with finance department."
        },
        "Response_Code": {
            "Assumption": "Code '00' is Success. Others are failures. Meaning of codes varies slightly by banking partner.",
            "Validation Required": "Verify code-to-meaning mapping across all integrated banking gateways with domain owner."
        },
        "Failure_Type": {
            "Assumption": "Temporary failure represents issues like network errors or timeouts that can succeed on retry, while Permanent failure represents issues like insufficient funds.",
            "Validation Required": "Confirm classification rules for temporary vs permanent failures with payment operations team."
        },
        "Retry_Time": {
            "Assumption": "Represents final retry timestamp. Empty if Retry_Count is 0.",
            "Validation Required": "Confirm if it represents the first or last retry attempt."
        }
    }

    for field, details in ambiguous_fields.items():
        print(f"\n* Field: {field}")
        print(f"  - Assumption:          {details['Assumption']}")
        print(f"  - Validation Required: {details['Validation Required']}")

    print("\n" + "=" * 60)
    print("DOCUMENTATION CHECKLIST:")
    print("=" * 60)
    print("✓ Data dictionary generated")
    print("✓ Business context documented")
    print("=" * 60)

if __name__ == "__main__":
    main()
