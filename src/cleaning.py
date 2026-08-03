import pandas as pd
from typing import List, Dict, Tuple
from src.data_skills import DuplicateHandler, StringCleaner, DataValidator

def clean_transactions(df: pd.DataFrame, text_cols: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove duplicates and standardise text fields.
    """
    df_clean = df.copy()
    
    # 1. Duplicate Handling (Skill 2.20)
    subset_cols = ['transaction_id']
    if 'transaction_time' in df_clean.columns:
        subset_cols.append('transaction_time')
        
    df_clean, exact_duplicates = DuplicateHandler.detect_exact_duplicates(df_clean, subset=subset_cols)
    
    # 2. String Cleaning & Text Normalisation (Skill 2.21)
    if text_cols is None:
        text_cols = ['payment_method', 'bank_name', 'final_status', 'response_message']
        
    # Only clean columns that exist
    existing_text_cols = [c for c in text_cols if c in df_clean.columns]
    df_clean = StringCleaner.clean_text(df_clean, existing_text_cols)
    
    # Standardise Bank Name variations
    if 'bank_name' in df_clean.columns:
        bank_mapping = {
            'hdfc': 'HDFC Bank',
            'axis': 'Axis Bank',
            'icici': 'ICICI Bank',
            'pnb': 'Punjab National Bank',
            'bob': 'Bank of Baroda',
            'yes bank': 'Yes Bank',
            'canara': 'Canara Bank',
            'indusind': 'IndusInd Bank'
        }
        df_clean = StringCleaner.map_label_variations(df_clean, 'bank_name', bank_mapping)
        
    # Standardise Payment Method variations
    if 'payment_method' in df_clean.columns:
        pm_mapping = {
            'upi': 'UPI',
            'credit card': 'Credit Card',
            'debit card': 'Debit Card',
            'net banking': 'Net Banking',
            'wallet': 'Wallet'
        }
        df_clean = StringCleaner.map_label_variations(df_clean, 'payment_method', pm_mapping)
        
    # Standardise Final Status variations
    if 'final_status' in df_clean.columns:
        status_mapping = {
            'success': 'Success',
            'failed': 'Failed',
            'pending': 'Pending'
        }
        df_clean = StringCleaner.map_label_variations(df_clean, 'final_status', status_mapping)
        
    return df_clean, exact_duplicates

def validate_data_quality(df: pd.DataFrame) -> Dict:
    """
    Run data consistency checks and validation rules (Skill 2.24).
    """
    results = {}
    
    # Define validation rules
    range_rules = {}
    if 'amount' in df.columns:
        range_rules['amount'] = (0.01, 1000000.0)  # Positive transaction amounts up to 1M
    if 'retry_count' in df.columns:
        range_rules['retry_count'] = (0, 10)  # Standard retry limit
    if 'revenue_lost' in df.columns:
        range_rules['revenue_lost'] = (0, 1000000.0)
        
    null_rules = {
        'transaction_id': 0,  # 0% null tolerance for IDs
        'customer_id': 0
    }
    if 'amount' in df.columns:
        null_rules['amount'] = 5  # Max 5% nulls
        
    # Run checks
    print("📋 Running Data Quality Checks...")
    results['ranges'] = DataValidator.validate_ranges(df, range_rules)
    results['nulls'] = DataValidator.validate_nulls(df, null_rules)
    
    # Relationship validation: Revenue_Lost should equal Amount if Final_Status is Failed and Failure_Type is Permanent
    relationship_rules = {}
    if 'final_status' in df.columns and 'amount' in df.columns and 'revenue_lost' in df.columns:
        # Check if revenue lost has unexpected violations (simple rule format)
        relationship_rules['revenue_lost <= amount'] = True
        results['relationships'] = DataValidator.validate_relationships(df, relationship_rules)
        
    return results
