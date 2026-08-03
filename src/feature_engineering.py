import pandas as pd
from src.data_skills import DateTimeTransformer, FeatureEngineer

def engineer_time_features(df: pd.DataFrame, date_col: str = 'transaction_time') -> pd.DataFrame:
    """
    Parse transaction date and extract temporal attributes (Skill 2.22).
    """
    df_features = df.copy()
    
    if date_col in df_features.columns:
        df_features = DateTimeTransformer.parse_dates(df_features, [date_col])
        df_features = DateTimeTransformer.extract_time_features(df_features, date_col)
        
        # Calculate days active since customer first transaction (time since event)
        first_txn_dates = df_features.groupby('customer_id')[date_col].transform('min')
        df_features['days_since_first_txn'] = (df_features[date_col] - first_txn_dates).dt.days
        
    return df_features

def engineer_business_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create business-derived metrics and categories (Skill 2.26).
    """
    df_features = df.copy()
    
    # Calculate transaction count per customer for scoring frequency
    df_features['customer_txn_count'] = df_features.groupby('customer_id')['transaction_id'].transform('count')
    
    # Create transaction score
    if 'amount' in df_features.columns:
        df_features['transaction_score'] = FeatureEngineer.create_transaction_scoring(
            df_features,
            amount_col='amount',
            frequency_col='customer_txn_count'
        )
        
        # Classify risk tier
        df_features['risk_tier'] = FeatureEngineer.create_risk_tier(df_features, 'transaction_score')
        
    # Calculate Customer Lifetime Value metrics
    if 'customer_id' in df_features.columns and 'amount' in df_features.columns and 'transaction_time' in df_features.columns:
        clv_df = FeatureEngineer.create_customer_lifetime_value(
            df_features,
            customer_col='customer_id',
            amount_col='amount',
            transaction_date_col='transaction_time'
        )
        
        # Prefix the clv columns so we know they are aggregated customer features
        clv_df.columns = [f'customer_{col}' for col in clv_df.columns]
        
        # Merge CLV aggregations back into the main transactions dataframe
        df_features = df_features.merge(clv_df, left_on='customer_id', right_index=True, how='left')
        
    # Calculate ratio features safely (e.g. successful transaction rate per bank)
    # Note: Can be computed dynamically or on aggregated tables
    return df_features
