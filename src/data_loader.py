import os
import pandas as pd
from typing import Dict, Tuple
from src.data_skills import DataTypeEnforcer, JoinValidator

def load_transaction_data(filepath: str, type_hints: Dict = None) -> pd.DataFrame:
    """
    Load raw transaction data, normalize columns to lowercase, and enforce data types.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Transaction file not found: {filepath}")
        
    df = pd.read_csv(filepath)
    
    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]
    
    # Enforce data types (Skill 2.19)
    if type_hints is None:
        type_hints = {
            'transaction_id': 'object',
            'customer_id': 'object',
            'amount': 'float64',
            'retry_count': 'float64',
            'response_code': 'object',
            'revenue_lost': 'float64'
        }
    else:
        # Normalize type hints keys to lowercase
        type_hints = {k.lower(): v for k, v in type_hints.items()}
    
    df = DataTypeEnforcer.infer_and_enforce_types(df, type_hints)
    
    # Standardise boolean values
    if 'is_fraud' in df.columns:
        df = DataTypeEnforcer.standardise_booleans(df, ['is_fraud'])
        
    return df

def load_customer_master(filepath: str) -> pd.DataFrame:
    """
    Load customer master dataset and normalize columns to lowercase.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Customer master file not found: {filepath}")
    df = pd.read_csv(filepath)
    df.columns = [c.lower() for c in df.columns]
    return df

def merge_datasets(transactions_df: pd.DataFrame, customers_df: pd.DataFrame, 
                   on_col: str = 'customer_id', how_join: str = 'left') -> Tuple[pd.DataFrame, Dict]:
    """
    Merge transaction dataset with customer master data with join validation.
    """
    merged, report = JoinValidator.validate_merge(
        left=transactions_df,
        right=customers_df,
        on=on_col.lower(),
        how=how_join,
        validate='m:1'  # Many transactions to one customer
    )
    
    # Check for unmatched keys (Skill 2.25)
    unmatched = JoinValidator.check_unmatched_keys(transactions_df, customers_df, on_col.lower())
    report['unmatched_keys_info'] = unmatched
    
    return merged, report
