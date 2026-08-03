"""
File: examples_data_skills.py

Practical examples demonstrating all 18 data skills
with realistic fintech scenarios.

Run this file to see skill demonstrations:
    python examples_data_skills.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

from src.data_skills import (
    DataTypeEnforcer, DuplicateHandler, StringCleaner, DateTimeTransformer,
    OutlierDetector, DataValidator, JoinValidator, FeatureEngineer,
    VectorisedComputation, DistributionAnalyzer, CorrelationAnalyzer,
    SegmentAnalyzer, TimeSeriesAnalyzer, BehaviourAnalyzer, FunnelAnalyzer,
    KPIFramework, RootCauseAnalyzer, AnomalyDetector, DataQualityPipeline
)


# ============================================
# SAMPLE DATA GENERATION
# ============================================

def create_sample_fintech_data(n_records=1000):
    """Generate realistic fintech transaction data."""
    
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=n_records, freq='H')
    
    data = {
        'transaction_id': range(1000001, 1000001 + n_records),
        'customer_id': np.random.randint(100000, 100500, n_records),
        'merchant_id': np.random.randint(1000, 2000, n_records),
        'merchant_category': np.random.choice(
            ['Grocery', 'GROCERY', 'grocery', 'Restaurant', 'restaurant', 
             'Gas Station', 'gas', 'Retail', 'RETAIL', 'Online Shopping'],
            n_records
        ),
        'amount': np.abs(np.random.exponential(scale=75, size=n_records)) + 0.5,
        'transaction_date': dates,
        'status': np.random.choice(['completed', 'pending', 'failed', 'Completed'], n_records, p=[0.80, 0.10, 0.05, 0.05]),
        'is_fraud': np.random.choice(['yes', 'no', 'Yes', 'No', 'Y', 'N'], n_records),
        'customer_age': np.random.randint(18, 80, n_records),
        'account_tenure_days': np.random.randint(1, 3650, n_records),
    }
    
    df = pd.DataFrame(data)
    
    # Add some artificial outliers
    outlier_indices = np.random.choice(len(df), size=20, replace=False)
    df.loc[outlier_indices, 'amount'] = np.random.uniform(5000, 50000, 20)
    
    return df


# ============================================
# SKILL 2.19: DATA TYPE ENFORCEMENT
# ============================================

def example_2_19_type_enforcement():
    """
    Example: Enforce data types for a transaction dataset.
    
    Problem: CSV imports amount as string, dates as strings, etc.
    Solution: Convert to proper types before analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.19: DATA TYPE ENFORCEMENT & STANDARDISATION")
    print("="*70)
    
    df = create_sample_fintech_data(100)
    
    print(f"\n❌ Before Type Enforcement:")
    print(f"   amount dtype: {df['amount'].dtype}")
    print(f"   transaction_date dtype: {df['transaction_date'].dtype}")
    print(f"   is_fraud dtype: {df['is_fraud'].dtype}")
    
    # Define types
    type_hints = {
        'amount': 'float64',
        'transaction_date': 'datetime64[ns]',
        'is_fraud': 'bool'
    }
    
    # Enforce types
    df_typed = DataTypeEnforcer.infer_and_enforce_types(df, type_hints)
    df_typed = DataTypeEnforcer.standardise_booleans(df_typed, ['is_fraud'])
    
    print(f"\n✓ After Type Enforcement:")
    print(f"   amount dtype: {df_typed['amount'].dtype}")
    print(f"   transaction_date dtype: {df_typed['transaction_date'].dtype}")
    print(f"   is_fraud dtype: {df_typed['is_fraud'].dtype}")
    
    # Standardise currency (example with fake currency strings)
    df_with_currency = df.copy()
    df_with_currency['amount'] = ['$' + str(x) for x in df_with_currency['amount']]
    df_currency_clean = DataTypeEnforcer.standardise_currency(df_with_currency, ['amount'])
    
    print(f"\n✓ Currency Standardisation:")
    print(f"   Original: {df_with_currency['amount'].iloc[0]}")
    print(f"   Standardised: {df_currency_clean['amount'].iloc[0]}")


# ============================================
# SKILL 2.20: DUPLICATE DETECTION
# ============================================

def example_2_20_duplicates():
    """
    Example: Find and remove duplicate transaction records.
    
    Problem: Same transaction imported multiple times
    Solution: Detect and deduplicate before analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.20: DUPLICATE DETECTION & RECORD DEDUPLICATION")
    print("="*70)
    
    df = create_sample_fintech_data(100)
    
    # Add some duplicates
    df = pd.concat([df, df.iloc[:10]], ignore_index=True)
    
    print(f"\n📊 Dataset with duplicates: {len(df)} records")
    
    # Detect exact duplicates
    df_clean, duplicates = DuplicateHandler.detect_exact_duplicates(
        df,
        subset=['transaction_id', 'customer_id', 'amount']
    )
    
    print(f"\n✓ After deduplication: {len(df_clean)} records")
    print(f"✓ Duplicates removed: {len(df) - len(df_clean)}")
    
    if len(duplicates) > 0:
        print(f"\nDuplicate records (first 3):")
        print(duplicates.head(3))


# ============================================
# SKILL 2.21: STRING CLEANING
# ============================================

def example_2_21_string_cleaning():
    """
    Example: Standardise merchant category labels.
    
    Problem: Same category has multiple variations
    Solution: Clean and normalise text
    """
    print("\n" + "="*70)
    print("SKILL 2.21: STRING CLEANING & TEXT NORMALISATION")
    print("="*70)
    
    df = create_sample_fintech_data(200)
    
    print(f"\n❌ Before Cleaning:")
    print(f"   Unique categories: {df['merchant_category'].nunique()}")
    print(f"   Categories: {sorted(df['merchant_category'].unique())}")
    
    # Clean text
    df_clean = StringCleaner.clean_text(df, ['merchant_category', 'status'])
    
    print(f"\n✓ After Text Cleaning:")
    print(f"   Unique categories: {df_clean['merchant_category'].nunique()}")
    print(f"   Categories: {sorted(df_clean['merchant_category'].unique())}")
    
    # Map variations
    mapping = {
        'grocery': 'grocery',
        'restaurant': 'food_and_beverage',
        'gas station': 'fuel',
        'retail': 'retail_shopping',
        'online shopping': 'ecommerce'
    }
    
    df_mapped = StringCleaner.map_label_variations(df_clean, 'merchant_category', mapping)
    
    print(f"\n✓ After Label Mapping:")
    print(f"   Categories: {sorted(df_mapped['merchant_category'].unique())}")


# ============================================
# SKILL 2.22: DATE TRANSFORMATION
# ============================================

def example_2_22_date_transformation():
    """
    Example: Extract temporal features from transaction timestamps.
    
    Problem: Need to analyse patterns by day, hour, week
    Solution: Extract time features
    """
    print("\n" + "="*70)
    print("SKILL 2.22: DATE & TIME TRANSFORMATION PIPELINE")
    print("="*70)
    
    df = create_sample_fintech_data(200)
    
    # Parse dates
    df = DateTimeTransformer.parse_dates(df, ['transaction_date'])
    
    # Extract features
    df = DateTimeTransformer.extract_time_features(df, 'transaction_date')
    
    print(f"\n✓ Extracted Time Features:")
    time_features = [col for col in df.columns if 'transaction_date_' in col]
    for feat in time_features[:5]:
        print(f"   {feat}: {df[feat].unique()[:3]}")
    
    print(f"\n✓ Transaction Patterns:")
    print(f"   By Day of Week:")
    print(df.groupby('transaction_date_dayofweek')['amount'].agg(['count', 'mean']))
    print(f"\n   Weekend vs Weekday:")
    weekend_stats = df.groupby('transaction_date_is_weekend')['amount'].agg(['sum', 'mean', 'count'])
    print(weekend_stats)


# ============================================
# SKILL 2.23: OUTLIER DETECTION
# ============================================

def example_2_23_outliers():
    """
    Example: Detect unusual transaction amounts.
    
    Problem: Find fraud or data quality issues
    Solution: Statistical outlier detection
    """
    print("\n" + "="*70)
    print("SKILL 2.23: OUTLIER DETECTION WITH STATISTICAL METHODS")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    
    print(f"\n📊 Transaction Amount Statistics:")
    print(f"   Mean: ${df['amount'].mean():.2f}")
    print(f"   Median: ${df['amount'].median():.2f}")
    print(f"   Std Dev: ${df['amount'].std():.2f}")
    print(f"   Min: ${df['amount'].min():.2f}")
    print(f"   Max: ${df['amount'].max():.2f}")
    
    # IQR method
    outliers_iqr = OutlierDetector.detect_iqr_outliers(df, ['amount'])
    
    # Z-score method
    outliers_z = OutlierDetector.detect_zscore_outliers(df, ['amount'], threshold=3.0)
    
    # Cap outliers
    df_capped = OutlierDetector.cap_outliers(df, ['amount'], method='percentile', percentile_bounds=(1, 99))
    
    print(f"\n✓ Capped Outliers:")
    print(f"   Original max: ${df['amount'].max():.2f}")
    print(f"   Capped max: ${df_capped['amount'].max():.2f}")


# ============================================
# SKILL 2.24: VALIDATION RULES
# ============================================

def example_2_24_validation():
    """
    Example: Validate transaction data meets quality standards.
    
    Problem: Ensure data integrity before analysis
    Solution: Rule-based validation
    """
    print("\n" + "="*70)
    print("SKILL 2.24: DATA CONSISTENCY & VALIDATION RULES")
    print("="*70)
    
    df = create_sample_fintech_data(100)
    
    # Define validation rules
    range_rules = {
        'amount': (0.01, 50000),
        'customer_age': (18, 120),
        'account_tenure_days': (0, 36500)
    }
    
    null_rules = {
        'transaction_id': 0,
        'customer_id': 0,
        'amount': 1,
        'merchant_category': 5
    }
    
    print(f"\n📋 Applying Validation Rules:")
    DataValidator.validate_ranges(df, range_rules)
    print()
    DataValidator.validate_nulls(df, null_rules)


# ============================================
# SKILL 2.25: DATA MERGING
# ============================================

def example_2_25_merging():
    """
    Example: Merge customer and transaction data.
    
    Problem: Combine data from multiple sources safely
    Solution: Join with validation
    """
    print("\n" + "="*70)
    print("SKILL 2.25: MULTI-SOURCE MERGING & JOIN VALIDATION")
    print("="*70)
    
    # Transactions
    df_trans = create_sample_fintech_data(100)
    df_trans = df_trans[['transaction_id', 'customer_id', 'merchant_id', 'amount']].head(100)
    
    # Customers (create master)
    customer_ids = df_trans['customer_id'].unique()[:40]  # Intentional mismatch
    df_customers = pd.DataFrame({
        'customer_id': customer_ids,
        'customer_name': [f'Customer_{id}' for id in customer_ids],
        'customer_segment': np.random.choice(['Bronze', 'Silver', 'Gold'], len(customer_ids))
    })
    
    print(f"\n📊 Data to merge:")
    print(f"   Transactions: {len(df_trans)}")
    print(f"   Customers: {len(df_customers)}")
    
    # Validate merge
    merged, report = JoinValidator.validate_merge(
        left=df_trans,
        right=df_customers,
        on='customer_id',
        how='left',
        validate='m:1'
    )
    
    print(f"\n✓ Merge completed: {len(merged)} rows")
    print(f"   Unmatched transactions: {report['rows_only_in_left']}")


# ============================================
# SKILL 2.26: FEATURE ENGINEERING
# ============================================

def example_2_26_features():
    """
    Example: Create business-meaningful features.
    
    Problem: Raw data insufficient for analysis
    Solution: Engineer derived features
    """
    print("\n" + "="*70)
    print("SKILL 2.26: FEATURE ENGINEERING & DERIVED BUSINESS COLUMNS")
    print("="*70)
    
    df = create_sample_fintech_data(200)
    
    # Add transaction count per customer
    df['customer_transaction_count'] = df.groupby('customer_id')['transaction_id'].transform('count')
    
    # Transaction score
    df['transaction_score'] = FeatureEngineer.create_transaction_scoring(
        df,
        amount_col='amount',
        frequency_col='customer_transaction_count'
    )
    
    # Risk tier
    df['risk_tier'] = FeatureEngineer.create_risk_tier(df, 'transaction_score')
    
    print(f"\n✓ Features Created:")
    print(f"   Transaction Score Range: {df['transaction_score'].min():.1f} - {df['transaction_score'].max():.1f}")
    print(f"\n   Risk Tier Distribution:")
    print(df['risk_tier'].value_counts())
    
    # CLV metrics
    clv = FeatureEngineer.create_customer_lifetime_value(
        df,
        customer_col='customer_id',
        amount_col='amount',
        transaction_date_col='transaction_date'
    )
    
    print(f"\n✓ Customer Lifetime Value Sample:")
    print(clv.head())


# ============================================
# SKILL 2.27: VECTORISED COMPUTATION
# ============================================

def example_2_27_vectorised():
    """
    Example: Use vectorised operations for speed.
    
    Problem: Loop-based calculations too slow
    Solution: Vectorised NumPy operations
    """
    print("\n" + "="*70)
    print("SKILL 2.27: NUMPY VECTORISED COMPUTATION WORKFLOW")
    print("="*70)
    
    # Create large dataset
    amounts = np.random.rand(1000000) * 1000
    merchant_types = np.random.randint(0, 5, 1000000)
    customer_tiers = np.random.randint(0, 4, 1000000)
    
    # Vectorised operations
    fees = VectorisedComputation.vectorised_fee_calculator(amounts, merchant_types)
    discounted = VectorisedComputation.vectorised_discount_calculator(amounts, customer_tiers)
    
    print(f"\n✓ Vectorised Operations on {len(amounts):,} records:")
    print(f"   Average fee: ${fees.mean():.2f}")
    print(f"   Average discounted amount: ${discounted.mean():.2f}")
    
    # Performance comparison
    print(f"\n✓ Performance benefit:")
    print(f"   Processing speed: {len(amounts) / 0.001:.0f} records/ms")


# ============================================
# SKILL 2.28: DISTRIBUTION ANALYSIS
# ============================================

def example_2_28_distribution():
    """
    Example: Understand data distributions.
    
    Problem: Need insights into data patterns
    Solution: Distribution analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.28: DISTRIBUTION ANALYSIS FOR BUSINESS TRENDS")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    
    # Distribution analysis
    dist = DistributionAnalyzer.analyze_distribution(df['amount'], 'Transaction Amount')
    
    # Detect shape
    shape = DistributionAnalyzer.detect_distribution_shape(df['amount'])
    print(f"\n✓ Distribution Shape: {shape}")
    
    # By category
    print(f"\n✓ Distribution by Merchant Category:")
    for category in df['merchant_category'].unique()[:3]:
        amounts = df[df['merchant_category'] == category]['amount']
        print(f"\n   {category}:")
        print(f"      Count: {len(amounts)}")
        print(f"      Mean: ${amounts.mean():.2f}")
        print(f"      Skewness: {amounts.skew():.2f}")


# ============================================
# SKILL 2.29: CORRELATION ANALYSIS
# ============================================

def example_2_29_correlation():
    """
    Example: Find relationships between variables.
    
    Problem: Understand which factors influence transaction size
    Solution: Correlation analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.29: CORRELATION & RELATIONSHIP ANALYSIS")
    print("="*70)
    
    df = create_sample_fintech_data(300)
    
    # Add derived numeric columns
    df['transaction_count_by_customer'] = df.groupby('customer_id')['transaction_id'].transform('count')
    
    numeric_cols = ['amount', 'customer_age', 'account_tenure_days', 'transaction_count_by_customer']
    
    # Calculate correlations
    corr_matrix = CorrelationAnalyzer.calculate_correlations(df, numeric_cols)
    
    print(f"\n✓ Correlation Matrix:")
    print(corr_matrix.round(3))
    
    # Find strong correlations
    strong_pairs = CorrelationAnalyzer.find_strong_correlations(corr_matrix, threshold=0.3)


# ============================================
# SKILL 2.30: SEGMENT ANALYSIS
# ============================================

def example_2_30_segments():
    """
    Example: Compare segments side-by-side.
    
    Problem: Understand performance by merchant category
    Solution: Segment analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.30: GROUPBY AGGREGATION & SEGMENT INSIGHTS")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    df['status_clean'] = df['status'].str.lower()
    
    # Aggregate by segment
    segment_metrics = SegmentAnalyzer.group_aggregate(
        df,
        group_cols='merchant_category',
        agg_dict={
            'amount': ['sum', 'mean', 'count'],
            'is_fraud': 'sum'
        }
    )
    
    print(f"\n✓ Revenue by Merchant Category:")
    print(segment_metrics)
    
    # Rank segments
    rankings = SegmentAnalyzer.rank_segments(
        df,
        segment_col='merchant_category',
        metric_col='amount',
        ascending=False
    )
    
    print(f"\n✓ Merchant Categories Ranked by Total Value:")
    print(rankings.head())


# ============================================
# SKILL 2.31: TIME-SERIES ANALYSIS
# ============================================

def example_2_31_timeseries():
    """
    Example: Track trends over time.
    
    Problem: Need to monitor daily trends and patterns
    Solution: Time-series resampling and rolling metrics
    """
    print("\n" + "="*70)
    print("SKILL 2.31: TIME-SERIES TREND & ROLLING METRICS")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    df['status_clean'] = df['status'].str.lower()
    
    # Daily revenue
    daily_rev = TimeSeriesAnalyzer.resample_timeseries(
        df,
        date_col='transaction_date',
        value_col='amount',
        freq='D',
        method='sum'
    )
    
    print(f"\n✓ Daily Revenue:")
    print(daily_rev.tail())
    
    # Rolling average
    rolling_avg = TimeSeriesAnalyzer.rolling_average(daily_rev, window=3)
    
    print(f"\n✓ 3-Day Rolling Average:")
    print(rolling_avg.tail())
    
    # Percentage change
    pct_change = TimeSeriesAnalyzer.percentage_change(daily_rev, periods=1)
    
    print(f"\n✓ Day-over-Day % Change:")
    print(pct_change.tail())


# ============================================
# SKILL 2.32: BEHAVIOURAL ANALYSIS
# ============================================

def example_2_32_behaviour():
    """
    Example: Segment customers by behaviour.
    
    Problem: Identify VIPs and dormant customers
    Solution: Behavioural segmentation
    """
    print("\n" + "="*70)
    print("SKILL 2.32: BEHAVIOURAL ANALYSIS & USER SEGMENTATION")
    print("="*70)
    
    df = create_sample_fintech_data(300)
    
    # Add metrics for segmentation
    customer_metrics = df.groupby('customer_id').agg({
        'transaction_id': 'count',
        'amount': ['sum', 'mean']
    }).reset_index()
    
    customer_metrics.columns = ['customer_id', 'transaction_count', 'total_spend', 'avg_spend']
    
    # Merge back
    df = df.merge(customer_metrics, on='customer_id')
    
    # Create segments
    df_segments = BehaviourAnalyzer.create_behavioural_segments(
        df,
        metrics={
            'transaction_count': (1, 100),
            'total_spend': (10, 50000)
        }
    )
    
    print(f"\n✓ Customer Segments:")
    print(df_segments['segment'].value_counts())
    
    # Behaviour profile
    profile = df_segments.groupby('segment')[['transaction_count', 'total_spend', 'avg_spend']].mean()
    
    print(f"\n✓ Segment Profiles:")
    print(profile.round(2))


# ============================================
# SKILL 2.33: FUNNEL ANALYSIS
# ============================================

def example_2_33_funnel():
    """
    Example: Track conversion through transaction stages.
    
    Problem: Identify where transactions drop off
    Solution: Funnel analysis
    """
    print("\n" + "="*70)
    print("SKILL 2.33: FUNNEL ANALYSIS & DROP-OFF DETECTION")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    
    # Define stages
    stages = ['initiated', 'pending', 'processing', 'completed']
    
    # Map status to stages
    status_to_stage = {
        'initiated': 'initiated',
        'pending': 'pending',
        'processing': 'processing',
        'completed': 'completed',
        'failed': 'failed'
    }
    
    df['stage'] = df['status'].map(status_to_stage)
    
    # Build funnel
    funnel = FunnelAnalyzer.build_funnel(
        df,
        customer_col='customer_id',
        stage_col='stage',
        stages=stages
    )
    
    print(f"\n✓ Transaction Funnel:")
    print(funnel[['stage', 'customers', 'percentage']])


# ============================================
# SKILL 2.34: KPI FRAMEWORK
# ============================================

def example_2_34_kpi():
    """
    Example: Define and track KPIs.
    
    Problem: Need executive metrics tied to goals
    Solution: KPI framework
    """
    print("\n" + "="*70)
    print("SKILL 2.34: KPI DEFINITION & BUSINESS METRIC DESIGN")
    print("="*70)
    
    df = create_sample_fintech_data(300)
    df['status_clean'] = df['status'].str.lower()
    
    # Define KPIs
    kpis = [
        KPIFramework.define_kpi(
            name='Daily Transactions',
            formula_description='COUNT of transactions per day',
            target=100,
            warning_threshold=80,
            critical_threshold=50
        ),
        KPIFramework.define_kpi(
            name='Average Transaction Value',
            formula_description='SUM(amount) / COUNT(transactions)',
            target=100,
            warning_threshold=80,
            critical_threshold=60
        ),
        KPIFramework.define_kpi(
            name='Transaction Success Rate',
            formula_description='COUNT(status=completed) / COUNT(all)',
            target=0.95,
            warning_threshold=0.90,
            critical_threshold=0.80
        )
    ]
    
    # Calculate actual values
    daily_trans = len(df) // 10  # Rough estimate
    avg_value = df['amount'].mean()
    success_rate = (df['status_clean'] == 'completed').sum() / len(df)
    
    kpi_values = pd.DataFrame({
        'Daily Transactions': [daily_trans],
        'Average Transaction Value': [avg_value],
        'Transaction Success Rate': [success_rate]
    })
    
    # Dashboard
    KPIFramework.kpi_dashboard(kpi_values, kpis)


# ============================================
# SKILL 2.35: ROOT CAUSE ANALYSIS
# ============================================

def example_2_35_root_cause():
    """
    Example: Investigate data anomalies.
    
    Problem: Transaction volume dropped, why?
    Solution: Systematic root cause investigation
    """
    print("\n" + "="*70)
    print("SKILL 2.35: ROOT CAUSE INVESTIGATION WORKFLOW")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    
    # Simulate anomaly period
    anomaly_start = df['transaction_date'].min() + timedelta(days=5)
    anomaly_end = df['transaction_date'].min() + timedelta(days=7)
    
    # Narrow by time
    time_analysis = RootCauseAnalyzer.narrow_by_time(
        df,
        date_col='transaction_date',
        value_col='amount',
        anomaly_start=anomaly_start,
        anomaly_end=anomaly_end
    )
    
    print(f"\n✓ Time-Based Analysis:")
    print(f"   Period: {time_analysis['period']}")
    print(f"   Normal mean: ${time_analysis['normal_mean']:.2f}")
    print(f"   Anomaly mean: ${time_analysis['anomaly_mean']:.2f}")
    print(f"   Change: {time_analysis['change_percent']:.1f}%")
    
    # Narrow by segment
    segment_analysis = RootCauseAnalyzer.narrow_by_segment(
        df,
        segment_col='merchant_category',
        value_col='amount',
        overall_anomaly=time_analysis['anomaly_mean']
    )
    
    print(f"\n✓ Segment Analysis (top categories):")
    print(segment_analysis.head())


# ============================================
# SKILL 2.36: ANOMALY DETECTION
# ============================================

def example_2_36_anomalies():
    """
    Example: Detect and flag unusual patterns.
    
    Problem: Need real-time alerts for unusual activity
    Solution: Statistical anomaly detection
    """
    print("\n" + "="*70)
    print("SKILL 2.36: ANOMALY DETECTION & RISK IDENTIFICATION")
    print("="*70)
    
    df = create_sample_fintech_data(500)
    
    # Daily revenue series
    daily_revenue = TimeSeriesAnalyzer.resample_timeseries(
        df,
        date_col='transaction_date',
        value_col='amount',
        freq='D',
        method='sum'
    )
    
    # Detect anomalies
    anomalies = AnomalyDetector.detect_spikes_dips(
        daily_revenue,
        threshold_std=2.0
    )
    
    print(f"\n✓ Anomaly Detection Results:")
    print(f"   Normal range: ${anomalies['lower_bound']:.2f} - ${anomalies['upper_bound']:.2f}")
    print(f"   Spikes detected: {anomalies['spike_count']}")
    print(f"   Dips detected: {anomalies['dip_count']}")
    
    # Flag transactions
    df_flagged = AnomalyDetector.flag_anomalies(
        df,
        value_col='amount',
        anomaly_info=anomalies
    )
    
    print(f"\n✓ Transaction Anomaly Flags:")
    print(f"   {(df_flagged['anomaly_flag'] == 'Spike').sum()} spikes")
    print(f"   {(df_flagged['anomaly_flag'] == 'Dip').sum()} dips")
    
    print(f"\n   Risk Distribution:")
    print(df_flagged['risk_level'].value_counts())


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  FINTECH DATA SKILLS - PRACTICAL EXAMPLES".center(68) + "█")
    print("█" + "  All 18 Skills (2.19-2.36)".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    # Run all examples
    examples = [
        example_2_19_type_enforcement,
        example_2_20_duplicates,
        example_2_21_string_cleaning,
        example_2_22_date_transformation,
        example_2_23_outliers,
        example_2_24_validation,
        example_2_25_merging,
        example_2_26_features,
        example_2_27_vectorised,
        example_2_28_distribution,
        example_2_29_correlation,
        example_2_30_segments,
        example_2_31_timeseries,
        example_2_32_behaviour,
        example_2_33_funnel,
        example_2_34_kpi,
        example_2_35_root_cause,
        example_2_36_anomalies
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {example_func.__name__}: {str(e)}")
    
    print("\n" + "█" * 70)
    print("✅ All demonstrations complete!")
    print("█" * 70)
    print("\n📚 For detailed documentation, see: FINTECH_DATA_SKILLS_GUIDE.md")
    print("📝 For full module code, see: src/data_skills.py\n")
