import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union
from src.data_skills import (
    VectorisedComputation, DistributionAnalyzer, CorrelationAnalyzer,
    SegmentAnalyzer, TimeSeriesAnalyzer, BehaviourAnalyzer, FunnelAnalyzer,
    KPIFramework, RootCauseAnalyzer, AnomalyDetector
)

# 1. NumPy Vectorised Computation Workflow (Skill 2.27)
def compute_vectorised_fees_discounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transaction fees and customer discounts using vectorised NumPy operations.
    """
    df_computed = df.copy()
    
    if 'amount' in df_computed.columns:
        amounts = df_computed['amount'].values
        
        # 1. Map payment methods to codes (0-4) for vectorised fee lookup
        pm_codes = {'UPI': 0, 'Credit Card': 1, 'Debit Card': 2, 'Net Banking': 3, 'Wallet': 4}
        # default to Wallet (4) if missing or unknown
        mapped_pm = df_computed['payment_method'].map(pm_codes).fillna(4).astype(int).values
        
        # Calculate fees vectorised (Skill 2.27)
        fees = VectorisedComputation.vectorised_fee_calculator(amounts, mapped_pm)
        df_computed['calculated_fee'] = fees
        
        # 2. Map customer risk tier or customer segments to numerical tiers (0-3) for vectorised discounts
        # Let's use custom discount tiers based on transaction counts or customer segments
        # Let's map 'customer_customer_segment' if exists, otherwise generate tiers (0-3) based on amount
        if 'customer_customer_segment' in df_computed.columns:
            segment_codes = {'Bronze': 0, 'Silver': 1, 'Gold': 2}
            customer_tiers = df_computed['customer_customer_segment'].map(segment_codes).fillna(0).astype(int).values
        else:
            # Fallback to randomized but deterministic tiers based on customer_id
            customer_tiers = (df_computed['customer_id'].str.extract(r'(\d+)').fillna(0).astype(int).values.flatten() % 4)
            
        discounted_amounts = VectorisedComputation.vectorised_discount_calculator(amounts, customer_tiers)
        df_computed['net_amount'] = discounted_amounts
        df_computed['calculated_discount'] = df_computed['amount'] - df_computed['net_amount']
        
    return df_computed

# 2. Distribution Analysis (Skill 2.28)
def analyze_amount_distribution(df: pd.DataFrame) -> Dict:
    """
    Analyse transaction amount distribution statistics and shape.
    """
    if 'amount' not in df.columns:
        return {}
    
    series = df['amount']
    analysis = DistributionAnalyzer.analyze_distribution(series, name='Transaction Amount')
    shape = DistributionAnalyzer.detect_distribution_shape(series)
    analysis['shape'] = shape
    
    return analysis

# 3. Correlation & Relationship Analysis (Skill 2.29)
def analyze_numerical_correlations(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Tuple]]:
    """
    Calculate numerical column correlations and find strong pairs.
    """
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Filter out IDs or code indicators that behave like categorical variables
    ignore_cols = {'transaction_id', 'customer_id', 'merchant_id', 'response_code'}
    num_cols = [c for c in num_cols if c.lower() not in ignore_cols]
    
    if len(num_cols) < 2:
        return pd.DataFrame(), []
        
    corr_matrix = CorrelationAnalyzer.calculate_correlations(df, num_cols, method='pearson')
    strong_pairs = CorrelationAnalyzer.find_strong_correlations(corr_matrix, threshold=0.2)
    
    return corr_matrix, strong_pairs

# 4. GroupBy Aggregation & Segment Insights (Skill 2.30)
def analyze_merchant_and_bank_segments(df: pd.DataFrame) -> Dict:
    """
    Break down revenue, volumes, and success rates by bank and payment method segments.
    """
    results = {}
    
    # Revenue aggregation by Bank
    if 'bank_name' in df.columns and 'amount' in df.columns:
        results['bank_revenue'] = SegmentAnalyzer.group_aggregate(
            df,
            group_cols='bank_name',
            agg_dict={
                'amount': ['sum', 'mean', 'count'],
                'calculated_fee': 'sum',
                'revenue_lost': 'sum'
            }
        )
        
        # Rank banks by volume
        results['bank_rankings'] = SegmentAnalyzer.rank_segments(df, 'bank_name', 'amount')
        
    # Segment comparison (Bank vs Payment Method)
    if 'bank_name' in df.columns and 'payment_method' in df.columns and 'amount' in df.columns:
        results['segment_comparison'] = SegmentAnalyzer.segment_comparison(
            df,
            segment_col='payment_method',
            metric_cols=['amount', 'calculated_fee']
        )
        
    return results

# 5. Time-Series Trend & Rolling Metrics (Skill 2.31)
def analyze_time_series_trends(df: pd.DataFrame) -> Dict:
    """
    Calculate daily/weekly revenue trends, rolling averages, and MoM changes.
    """
    results = {}
    
    # Resample daily revenue
    if 'transaction_time' in df.columns and 'amount' in df.columns:
        daily_rev = TimeSeriesAnalyzer.resample_timeseries(
            df,
            date_col='transaction_time',
            value_col='amount',
            freq='D',
            method='sum'
        )
        results['daily_revenue'] = daily_rev
        
        # 7-day moving average
        results['rolling_avg_7d'] = TimeSeriesAnalyzer.rolling_average(daily_rev, window=7)
        
        # Cumulative running total
        results['cumulative_revenue'] = TimeSeriesAnalyzer.cumulative_sum(daily_rev)
        
        # Resample weekly revenue and compute % change
        weekly_rev = TimeSeriesAnalyzer.resample_timeseries(
            df,
            date_col='transaction_time',
            value_col='amount',
            freq='W',
            method='sum'
        )
        results['weekly_revenue'] = weekly_rev
        results['weekly_pct_change'] = TimeSeriesAnalyzer.percentage_change(weekly_rev, periods=1)
        
    return results

# 6. Behavioural Analysis & User Segmentation (Skill 2.32)
def perform_behavioural_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group transactions to build customer RFM metrics and segment them.
    """
    # Create customer behaviour features
    customer_metrics = df.groupby('customer_id').agg({
        'transaction_id': 'count',
        'amount': ['sum', 'mean'],
        'transaction_time': lambda x: (x.max() - x.min()).days
    }).reset_index()
    
    customer_metrics.columns = ['customer_id', 'txn_count', 'total_spend', 'avg_spend', 'days_active']
    
    # Normalise metrics and assign segments
    df_segments = BehaviourAnalyzer.create_behavioural_segments(
        customer_metrics,
        metrics={
            'txn_count': (1, 50),
            'total_spend': (100, 200000)
        }
    )
    
    return df_segments

# 7. Funnel Analysis & Drop-Off Detection (Skill 2.33)
def analyze_payment_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Track user transactions through stages (initiated -> pending -> completed).
    """
    # Simulate transaction funnel stages based on Final_Status and Retry_Count
    # A realistic funnel for fintech:
    # 1. Initiated (all transactions)
    # 2. Authenticating (Final_Status in ['Success', 'Pending', 'Failed'] or Retry_Count > 0)
    # 3. Processing (Final_Status in ['Success', 'Pending'] or Retry_Count > 1)
    # 4. Completed (Final_Status == 'Success')
    
    # We will map status/retries to transaction stage
    df_funnel = df.copy()
    
    stages_assigned = []
    for _, row in df_funnel.iterrows():
        status = row.get('final_status', 'Pending')
        retries = row.get('retry_count', 0)
        
        # Logic to trace how far a transaction progressed
        if status == 'Success':
            stages_assigned.append('completed')
        elif status == 'Pending':
            stages_assigned.append('processing')
        elif status == 'Failed' and retries > 0:
            stages_assigned.append('processing')
        elif status == 'Failed':
            stages_assigned.append('authenticating')
        else:
            stages_assigned.append('initiated')
            
    df_funnel['funnel_stage'] = stages_assigned
    
    # We must expand individual records into sequential stages to run a funnel.
    # Count unique customers that reached each stage:
    stages_order = ['initiated', 'authenticating', 'processing', 'completed']
    
    # Build the sequential dataset:
    # Everyone who reached completed also reached processing, authenticating, initiated.
    # Everyone who reached processing also reached authenticating, initiated.
    # Everyone who reached authenticating also reached initiated.
    funnel_counts = []
    
    for idx, stage in enumerate(stages_order):
        if stage == 'initiated':
            # all customers
            cust_count = df_funnel['customer_id'].nunique()
        elif stage == 'authenticating':
            # customers with stage in authenticating, processing, completed
            cust_count = df_funnel[df_funnel['funnel_stage'].isin(['authenticating', 'processing', 'completed'])]['customer_id'].nunique()
        elif stage == 'processing':
            # customers with stage in processing, completed
            cust_count = df_funnel[df_funnel['funnel_stage'].isin(['processing', 'completed'])]['customer_id'].nunique()
        else:
            # completed customers
            cust_count = df_funnel[df_funnel['funnel_stage'] == 'completed']['customer_id'].nunique()
            
        funnel_counts.append({
            'stage': stage,
            'customers': cust_count,
            'percentage': 100.0 if idx == 0 else (cust_count / funnel_counts[0]['customers'] * 100)
        })
        
    funnel_df = pd.DataFrame(funnel_counts)
    funnel_df['drop_off_rate'] = funnel_df['customers'].pct_change() * -100
    funnel_df['drop_off_count'] = funnel_df['customers'].diff() * -1
    
    return funnel_df

# 8. KPI Definition & Business Metric Design (Skill 2.34)
def build_kpi_dashboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define, compute, and monitor business KPIs.
    """
    # Define KPIs
    kpis = [
        KPIFramework.define_kpi(
            name='Total Revenue Processed',
            formula_description='SUM(amount)',
            target=500000,
            warning_threshold=400000,
            critical_threshold=300000
        ),
        KPIFramework.define_kpi(
            name='Transaction Success Rate',
            formula_description='COUNT(final_status == "Success") / COUNT(all)',
            target=0.85,
            warning_threshold=0.80,
            critical_threshold=0.75
        ),
        KPIFramework.define_kpi(
            name='Lost Revenue Rate',
            formula_description='SUM(revenue_lost) / SUM(amount)',
            target=0.02, # Target is less than 2% loss
            warning_threshold=0.05,
            critical_threshold=0.08
        )
    ]
    
    # Calculate actuals
    total_rev = df['amount'].sum()
    success_rate = (df['final_status'] == 'Success').sum() / len(df) if len(df) else 0
    lost_rev_rate = df['revenue_lost'].sum() / total_rev if total_rev else 0
    
    # Create the dashboard frame
    kpi_values = pd.DataFrame({
        'Total Revenue Processed': [total_rev],
        'Transaction Success Rate': [success_rate],
        'Lost Revenue Rate': [lost_rev_rate]
    })
    
    # The framework expects kpi status mapping.
    # Note: Our KPI Framework status function flags failure if rate goes ABOVE threshold for lost revenue rate.
    # Let's adjust the status check or map manually if necessary, or just run the default dashboard evaluator.
    dashboard = KPIFramework.kpi_dashboard(kpi_values, kpis)
    return dashboard

# 9. Anomaly Detection & Anomaly Flags (Skill 2.36)
def detect_revenue_anomalies(daily_rev: pd.Series, df: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
    """
    Detect spikes and dips in daily revenue and flag individual anomalous transactions.
    """
    # Detect spikes and dips
    anomalies = AnomalyDetector.detect_spikes_dips(daily_rev, threshold_std=2.0)
    
    # Flag individual transaction level anomalies
    df_flagged = AnomalyDetector.flag_anomalies(df, value_col='amount', anomaly_info=anomalies)
    
    return anomalies, df_flagged

# 10. Root Cause Investigation Workflow (Skill 2.35)
def run_root_cause_investigation(df: pd.DataFrame, date_col: str = 'transaction_time') -> Dict:
    """
    Investigate the root cause of payment failure spikes by segment and time.
    """
    # Find anomaly period: let's identify the date with highest failure count or highest drop in success rate
    df_temp = df.copy()
    df_temp['date_only'] = df_temp[date_col].dt.date
    daily_stats = df_temp.groupby('date_only').agg({
        'final_status': lambda x: (x == 'Failed').sum(),
        'amount': 'sum'
    })
    
    if len(daily_stats) == 0:
        return {}
        
    worst_date = daily_stats['final_status'].idxmax()
    worst_date_ts = pd.Timestamp(worst_date)
    
    # Run time isolation
    worst_date_end = worst_date_ts + pd.Timedelta(hours=23, minutes=59, seconds=59)
    time_isolation = RootCauseAnalyzer.narrow_by_time(
        df_temp,
        date_col='transaction_time',
        value_col='amount',
        anomaly_start=worst_date_ts,
        anomaly_end=worst_date_end
    )
    
    # Run segment isolation on the anomaly period data
    df_anomaly = df_temp[(df_temp['transaction_time'] >= worst_date_ts) & (df_temp['transaction_time'] <= worst_date_end)]
    segment_isolation = RootCauseAnalyzer.narrow_by_segment(
        df_anomaly,
        segment_col='bank_name',
        value_col='amount',
        overall_anomaly=time_isolation['anomaly_mean']
    )
    
    return {
        'worst_date': worst_date,
        'time_isolation': time_isolation,
        'segment_isolation': segment_isolation
    }
