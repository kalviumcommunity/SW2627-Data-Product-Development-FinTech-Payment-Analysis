"""
File: FINTECH_DATA_SKILLS_GUIDE.md

# Complete Guide: Advanced Data Skills in Fintech Analytics

This guide demonstrates practical application of all 18 data skills (2.19-2.36)
to your fintech payment analytics project.

---

## Quick Reference: Skill-to-Use-Case Mapping

## Workflow: Complete Data Pipeline

### Phase 1: Ingestion & Type Standardisation (Skill 2.19)

**Objective:** Load raw data and enforce correct types

```python
import pandas as pd
from src.data_skills import DataTypeEnforcer

# Load raw transaction data
df = pd.read_csv('data/raw/transactions.csv')

# Define expected types
type_hints = {
    'transaction_id': 'int64',
    'customer_id': 'int64',
    'amount': 'float64',
    'transaction_date': 'datetime64[ns]',
    'status': 'category',
    'merchant_category': 'category',
    'is_fraud': 'bool'
}

# Apply type enforcement
df = DataTypeEnforcer.infer_and_enforce_types(df, type_hints)

# Standardise currency
df = DataTypeEnforcer.standardise_currency(df, ['amount'])

print(df.dtypes)  # Verify all types correct
```

**Output:** Dataframe with correct types, preventing downstream errors

---

### Phase 2: Deduplication (Skill 2.20)

**Objective:** Find and remove duplicate records

```python
from src.data_skills import DuplicateHandler

# Detect exact duplicates on key columns
df_clean, duplicates = DuplicateHandler.detect_exact_duplicates(
    df,
    subset=['transaction_id', 'customer_id', 'amount', 'transaction_date']
)

# Export duplicates for investigation
duplicates.to_csv('output/duplicates_review.csv', index=False)

# Find near-duplicates (fuzzy match)
near_dupes = DuplicateHandler.detect_near_duplicates(
    df,
    fuzzy_cols=['customer_id', 'amount', 'merchant_id'],
    similarity_threshold=0.95
)

print(f"Exact duplicates removed: {len(df) - len(df_clean)}")
print(f"Near-duplicate groups found: {len(near_dupes)}")
```

**Output:** Cleaned dataframe without duplicates

---

### Phase 3: Text Standardisation (Skill 2.21)

**Objective:** Normalise merchant categories and status values

```python
from src.data_skills import StringCleaner

# Clean text columns
df_clean = StringCleaner.clean_text(df_clean, ['merchant_category', 'status', 'merchant_name'])

# Map variations to standard values
merchant_mapping = {
    'grocery store': 'grocery',
    'supermarket': 'grocery',
    'food market': 'grocery',
    'petrol station': 'gas',
    'fuel': 'gas',
    'restaurant/cafe': 'restaurant',
    'fast food': 'restaurant'
}

df_clean = StringCleaner.map_label_variations(df_clean, 'merchant_category', merchant_mapping)

print(f"Unique categories before: {len(df['merchant_category'].unique())}")
print(f"Unique categories after: {len(df_clean['merchant_category'].unique())}")
print(f"Categories: {df_clean['merchant_category'].unique()}")
```

**Output:** Standardised text columns for accurate grouping

---

### Phase 4: Date Transformation (Skill 2.22)

**Objective:** Extract temporal features for pattern analysis

```python
from src.data_skills import DateTimeTransformer

# Parse dates (already done in phase 1)
df_clean = DateTimeTransformer.parse_dates(df_clean, ['transaction_date'])

# Extract time features
df_clean = DateTimeTransformer.extract_time_features(df_clean, 'transaction_date')

# Example: Identify patterns
print("\nTransactions by Day of Week:")
dow_summary = df_clean.groupby('transaction_date_dayofweek').size()
print(dow_summary)

print("\nWeekend vs Weekday:")
weekend_comparison = df_clean.groupby('transaction_date_is_weekend')['amount'].agg(['count', 'mean', 'sum'])
print(weekend_comparison)

# Calculate days since customer first transaction
df_clean['days_since_first_transaction'] = DateTimeTransformer.calculate_time_since(
    df_clean,
    'transaction_date',
    unit='days'
)
```

**Output:** Enhanced dataframe with temporal features

---

### Phase 5: Outlier Detection (Skill 2.23)

**Objective:** Identify unusual transactions for fraud or quality checks

```python
from src.data_skills import OutlierDetector

# Detect using IQR method
iqr_outliers = OutlierDetector.detect_iqr_outliers(
    df_clean,
    ['amount', 'transaction_count'],
    iqr_multiplier=1.5
)

# Detect using Z-score
zscore_outliers = OutlierDetector.detect_zscore_outliers(
    df_clean,
    ['amount'],
    threshold=3.0  # More aggressive
)

# Option 1: Remove outliers
df_filtered = df_clean[~df_clean.index.isin(iqr_outliers['amount']['indices'])]

# Option 2: Cap outliers
df_capped = OutlierDetector.cap_outliers(
    df_clean,
    ['amount'],
    method='percentile',
    percentile_bounds=(1, 99)
)

# Option 3: Flag for review
df_clean['is_outlier'] = False
df_clean.loc[iqr_outliers['amount']['indices'], 'is_outlier'] = True

print(f"Total outliers flagged: {df_clean['is_outlier'].sum()}")
```

**Output:** Outlier information for downstream handling

---

### Phase 6: Validation Rules (Skill 2.24)

**Objective:** Ensure data meets quality standards

```python
from src.data_skills import DataValidator

# Define validation rules
range_rules = {
    'amount': (0.01, 10000),  # Valid transaction range
    'customer_id': (1000, 99999),  # Valid customer ID range
}

null_rules = {
    'transaction_id': 0,  # No nulls allowed
    'customer_id': 0,     # No nulls allowed
    'amount': 1,          # Max 1% nulls tolerated
    'merchant_category': 5  # Max 5% nulls tolerated
}

relationship_rules = {
    'transaction_date > completion_date': False,  # Should not happen
}

# Run validations
print("📋 Validation Results:\n")
DataValidator.validate_ranges(df_clean, range_rules)
print()
DataValidator.validate_nulls(df_clean, null_rules)
print()
DataValidator.validate_relationships(df_clean, relationship_rules)

# Create validation summary
validation_passing = True
print("\n✅ Data passed quality gates!" if validation_passing else "❌ Data quality issues found!")
```

**Output:** Quality assurance report

---

### Phase 7: Data Merging (Skill 2.25)

**Objective:** Combine customer and transaction data

```python
from src.data_skills import JoinValidator

# Load customer master data
df_customers = pd.read_csv('data/customer_master.csv')
df_transactions = df_clean

# Validate merge
merged_df, report = JoinValidator.validate_merge(
    left=df_transactions,
    right=df_customers,
    on='customer_id',
    how='left',
    validate='m:1'  # Many transactions per customer
)

# Check unmatched keys
unmatched = JoinValidator.check_unmatched_keys(
    df_transactions,
    df_customers,
    key='customer_id'
)

print("\n📊 Merge Report:")
for key, value in report.items():
    print(f"  {key}: {value}")

# Investigate unmatched customers
if unmatched['in_left_not_right']:
    print(f"\n⚠️  {len(unmatched['in_left_not_right'])} customers in transactions but not in master!")
    print(f"   Examples: {list(unmatched['in_left_not_right'])[:5]}")
```

**Output:** Complete customer + transaction view

---

### Phase 8: Feature Engineering (Skill 2.26)

**Objective:** Create business-meaningful derived features

```python
from src.data_skills import FeatureEngineer

# Create transaction importance score
df_merged['transaction_score'] = FeatureEngineer.create_transaction_scoring(
    df_merged,
    amount_col='amount',
    frequency_col='transaction_count'
)

# Create risk tier
df_merged['risk_tier'] = FeatureEngineer.create_risk_tier(
    df_merged,
    score_col='transaction_score'
)

# Create merchant-specific ratios
df_merged['successful_transaction_rate'] = FeatureEngineer.create_ratio_features(
    df_merged,
    numerator='successful_transactions',
    denominator='total_transactions',
    feature_name='success_rate'
)

# Calculate Customer Lifetime Value
clv_metrics = FeatureEngineer.create_customer_lifetime_value(
    df_merged,
    customer_col='customer_id',
    amount_col='amount',
    transaction_date_col='transaction_date'
)

print("\n💰 Customer Lifetime Value Sample:")
print(clv_metrics.head())

# Add CLV back to main dataframe
df_merged = df_merged.merge(clv_metrics, left_on='customer_id', right_index=True)
```

**Output:** Enriched dataframe with business features

---

### Phase 9: Vectorised Computation (Skill 2.27)

**Objective:** Fast bulk calculations

```python
import numpy as np
from src.data_skills import VectorisedComputation

# Convert to numpy for speed
amounts_array = df_merged['amount'].values
merchant_types_array = df_merged['merchant_type_code'].values

# Calculate fees using vectorised operations
fees = VectorisedComputation.vectorised_fee_calculator(
    amounts_array,
    merchant_types_array
)

df_merged['calculated_fee'] = fees

# Apply tiered discounts
customer_tiers = df_merged['customer_tier_code'].values
discounted_amounts = VectorisedComputation.vectorised_discount_calculator(
    amounts_array,
    customer_tiers
)

df_merged['net_amount'] = discounted_amounts

# Calculate running totals for each customer
# (This would typically be done with groupby().cumsum() or pandas groupby)

print(f"✓ Processed {len(df_merged)} fees in vectorised operations")
print(f"  Average fee: ${df_merged['calculated_fee'].mean():.2f}")
```

**Output:** Performance-optimised calculations

---

### Phase 10: Distribution Analysis (Skill 2.28)

**Objective:** Understand data patterns and trends

```python
from src.data_skills import DistributionAnalyzer

# Analyse transaction amount distribution
dist_analysis = DistributionAnalyzer.analyze_distribution(
    df_merged['amount'],
    name='Transaction Amount'
)

# Identify distribution shape
shape = DistributionAnalyzer.detect_distribution_shape(df_merged['amount'])
print(f"\nDistribution Shape: {shape}")

# Summary statistics by merchant category
print("\n📊 Amount Distribution by Merchant Category:")
for category in df_merged['merchant_category'].unique():
    category_amounts = df_merged[df_merged['merchant_category'] == category]['amount']
    print(f"\n{category}:")
    print(f"  Mean: ${category_amounts.mean():.2f}")
    print(f"  Median: ${category_amounts.median():.2f}")
    print(f"  Std Dev: ${category_amounts.std():.2f}")
    print(f"  Skewness: {category_amounts.skew():.2f}")
```

**Output:** Statistical insights into data patterns

---

### Phase 11: Correlation Analysis (Skill 2.29)

**Objective:** Find relationships between variables

```python
from src.data_skills import CorrelationAnalyzer

# Select numeric columns for correlation
numeric_cols = ['amount', 'transaction_count', 'customer_age', 'account_days', 'total_value']

# Calculate correlations
corr_matrix = CorrelationAnalyzer.calculate_correlations(
    df_merged,
    numeric_cols,
    method='pearson'
)

# Find strong relationships
strong_pairs = CorrelationAnalyzer.find_strong_correlations(
    corr_matrix,
    threshold=0.7
)

print("\n🔗 Strong Correlations Found:")
for var1, var2, corr in strong_pairs:
    print(f"  {var1} ↔ {var2}: {corr:.3f}")

# Spearman correlation for rank-based relationships
corr_spearman = CorrelationAnalyzer.calculate_correlations(
    df_merged,
    numeric_cols,
    method='spearman'
)
```

**Output:** Correlation matrix and insights

---

### Phase 12: Segment Analysis (Skill 2.30)

**Objective:** Break down data by customer segments

```python
from src.data_skills import SegmentAnalyzer

# Group by merchant category and analyse
segment_metrics = SegmentAnalyzer.group_aggregate(
    df_merged,
    group_cols=['merchant_category', 'customer_tier'],
    agg_dict={
        'amount': ['sum', 'mean', 'count'],
        'is_fraud': 'sum',
        'customer_id': 'nunique'
    }
)

print("\n📊 Revenue by Merchant & Customer Tier:")
print(segment_metrics)

# Compare segments side-by-side
comparison = SegmentAnalyzer.segment_comparison(
    df_merged,
    segment_col='merchant_category',
    metric_cols=['amount', 'transaction_count', 'success_rate']
)

print("\n📈 Segment Comparison:")
print(comparison)

# Rank merchants by total value
merchant_ranking = SegmentAnalyzer.rank_segments(
    df_merged,
    segment_col='merchant_id',
    metric_col='amount',
    ascending=False
)

print("\n🏆 Top 10 Merchants by Transaction Value:")
print(merchant_ranking.head(10))
```

**Output:** Segment performance summaries

---

### Phase 13: Time-Series Analysis (Skill 2.31)

**Objective:** Track trends and patterns over time

```python
from src.data_skills import TimeSeriesAnalyzer

# Resample to daily revenue
daily_revenue = TimeSeriesAnalyzer.resample_timeseries(
    df_merged,
    date_col='transaction_date',
    value_col='amount',
    freq='D',
    method='sum'
)

# Calculate 7-day rolling average
rolling_avg = TimeSeriesAnalyzer.rolling_average(daily_revenue, window=7)

# Calculate month-over-month change
monthly_revenue = TimeSeriesAnalyzer.resample_timeseries(
    df_merged,
    date_col='transaction_date',
    value_col='amount',
    freq='M',
    method='sum'
)

monthly_pct_change = TimeSeriesAnalyzer.percentage_change(monthly_revenue, periods=1)

print("\n📈 Monthly Revenue % Change:")
print(monthly_pct_change)

# Cumulative revenue over time
cumulative = TimeSeriesAnalyzer.cumulative_sum(daily_revenue)

print(f"\nDaily Revenue Statistics:")
print(f"  Total: ${daily_revenue.sum():.2f}")
print(f"  Average: ${daily_revenue.mean():.2f}")
print(f"  7-day MA: ${rolling_avg.iloc[-1]:.2f}")
```

**Output:** Time-series metrics and trends

---

### Phase 14: Behavioural Analysis (Skill 2.32)

**Objective:** Segment customers by behaviour

```python
from src.data_skills import BehaviourAnalyzer

# Create behavioural segments
df_segments = BehaviourAnalyzer.create_behavioural_segments(
    df_merged,
    metrics={
        'rfm_score': (0, 100),
        'transaction_count': (1, 100),
        'total_spend': (10, 50000)
    }
)

print("\n👥 Customer Segments:")
print(df_segments['segment'].value_counts())

# Analyse behaviour by segment
behaviour_profile = BehaviourAnalyzer.behaviour_comparison_table(
    df_segments,
    segment_col='segment',
    behaviour_metrics=['transaction_count', 'avg_amount', 'days_active']
)

print("\n📊 Behaviour Profile by Segment:")
print(behaviour_profile)

# Identify VIPs vs dormant customers
vip_customers = df_segments[df_segments['segment'] == 'VIP']['customer_id'].unique()
dormant_customers = df_segments[df_segments['segment'] == 'Dormant']['customer_id'].unique()

print(f"\nVIP Customers: {len(vip_customers)}")
print(f"Dormant Customers: {len(dormant_customers)}")
print(f"VIP avg spend: ${df_segments[df_segments['segment'] == 'VIP']['total_spend'].mean():.2f}")
```

**Output:** Customer segments with profiles

---

### Phase 15: Funnel Analysis (Skill 2.33)

**Objective:** Track conversion through transaction lifecycle

```python
from src.data_skills import FunnelAnalyzer

# Define transaction stages
stages = ['initiated', 'pending', 'processing', 'completed', 'settled']

# Build funnel
funnel = FunnelAnalyzer.build_funnel(
    df_merged,
    customer_col='customer_id',
    stage_col='transaction_status',
    stages=stages
)

print("\n🔔 Transaction Funnel:")
print(funnel)

# Analyse drop-offs
print("\nDrop-off Analysis:")
for idx, row in funnel.iterrows():
    if pd.notna(row['drop_off_rate']):
        print(f"  {row['stage']}: {row['drop_off_rate']:.1f}% drop-off ({int(row['drop_off_count'])} customers)")

# Identify bottleneck stage
bottleneck = funnel.loc[funnel['drop_off_rate'].idxmax()]
print(f"\n⚠️  Biggest drop-off at: {bottleneck['stage']} ({bottleneck['drop_off_rate']:.1f}%)")
```

**Output:** Funnel metrics and bottleneck identification

---

### Phase 16: KPI Framework (Skill 2.34)

**Objective:** Define and monitor business KPIs

```python
from src.data_skills import KPIFramework

# Define key KPIs
kpis = [
    KPIFramework.define_kpi(
        name='Daily Active Users',
        formula_description='COUNT(DISTINCT customer_id) WHERE transaction_date = TODAY',
        target=5000,
        warning_threshold=4500,
        critical_threshold=4000
    ),
    KPIFramework.define_kpi(
        name='Average Transaction Value',
        formula_description='SUM(amount) / COUNT(transaction_id)',
        target=450,
        warning_threshold=400,
        critical_threshold=350
    ),
    KPIFramework.define_kpi(
        name='Transaction Success Rate',
        formula_description='COUNT(status=completed) / COUNT(total_transactions)',
        target=0.98,
        warning_threshold=0.95,
        critical_threshold=0.90
    )
]

# Calculate actual KPI values
daily_active_users = df_merged[df_merged['transaction_date'] == df_merged['transaction_date'].max()]['customer_id'].nunique()
avg_transaction_value = df_merged['amount'].mean()
success_rate = (df_merged['status'] == 'completed').sum() / len(df_merged)

# Create KPI status report
kpi_values = pd.DataFrame({
    'Daily Active Users': [daily_active_users],
    'Average Transaction Value': [avg_transaction_value],
    'Transaction Success Rate': [success_rate]
})

kpi_dashboard = KPIFramework.kpi_dashboard(kpi_values, kpis)

print("\n📊 KPI Status Dashboard:")
print(kpi_dashboard)
```

**Output:** Executive KPI dashboard

---

### Phase 17: Root Cause Analysis (Skill 2.35)

**Objective:** Investigate anomalies systematically

```python
from src.data_skills import RootCauseAnalyzer

# Scenario: Transaction volume dropped on specific date
anomaly_start = pd.Timestamp('2024-06-15')
anomaly_end = pd.Timestamp('2024-06-15')

# Narrow by time
time_analysis = RootCauseAnalyzer.narrow_by_time(
    df_merged,
    date_col='transaction_date',
    value_col='amount',
    anomaly_start=anomaly_start,
    anomaly_end=anomaly_end
)

print("\n📋 Time-Based Analysis:")
for key, value in time_analysis.items():
    if key != 'period':
        print(f"  {key}: {value}")

# Narrow by segment
segment_analysis = RootCauseAnalyzer.narrow_by_segment(
    df_merged,
    segment_col='merchant_category',
    value_col='amount',
    overall_anomaly=time_analysis['anomaly_mean']
)

print("\n📊 Segment-Based Analysis:")
print(segment_analysis)

# Hypothesis: Gas/fuel merchants affected by external event
print("\nGas merchant impact:")
print(segment_analysis.loc['gas'] if 'gas' in segment_analysis.index else "No gas merchants in data")
```

**Output:** Root cause findings

---

### Phase 18: Anomaly Detection (Skill 2.36)

**Objective:** Continuously flag unusual patterns

```python
from src.data_skills import AnomalyDetector

# Detect spikes and dips in daily revenue
daily_revenue_series = TimeSeriesAnalyzer.resample_timeseries(
    df_merged,
    date_col='transaction_date',
    value_col='amount',
    freq='D',
    method='sum'
)

anomalies = AnomalyDetector.detect_spikes_dips(
    daily_revenue_series,
    threshold_std=2.5
)

print("\n🚨 Anomaly Detection Report:")
print(f"  Spikes detected: {anomalies['spike_count']}")
print(f"  Dips detected: {anomalies['dip_count']}")
print(f"  Normal range: ${anomalies['lower_bound']:.2f} - ${anomalies['upper_bound']:.2f}")

# Flag transaction-level anomalies
df_flagged = AnomalyDetector.flag_anomalies(
    df_merged,
    value_col='amount',
    anomaly_info=anomalies
)

print("\n⚠️  Flagged Transactions:")
print(f"  Spikes: {(df_flagged['anomaly_flag'] == 'Spike').sum()}")
print(f"  Dips: {(df_flagged['anomaly_flag'] == 'Dip').sum()}")

# Group by risk level
print("\nRisk Level Distribution:")
print(df_flagged['risk_level'].value_counts())

# Export critical flagged records
critical_records = df_flagged[df_flagged['risk_level'] == 'Critical'].sort_values('anomaly_severity', ascending=False)
critical_records.to_csv('output/critical_anomalies.csv', index=False)
```

**Output:** Anomaly flags for alerting

---

## Complete Pipeline Execution

```python
from src.data_skills import DataQualityPipeline

# Configure complete pipeline
pipeline_config = {
    'type_hints': {
        'transaction_id': 'int64',
        'amount': 'float64',
        'transaction_date': 'datetime64[ns]'
    },
    'duplicate_cols': ['transaction_id', 'customer_id'],
    'text_cols': ['merchant_category', 'status'],
    'date_cols': ['transaction_date'],
    'numeric_cols': ['amount', 'transaction_count'],
    'cap_outliers': True,
    'validation_rules': {
        'null_rules': {
            'transaction_id': 0,
            'amount': 1
        },
        'range_rules': {
            'amount': (0.01, 10000)
        }
    }
}

# Run pipeline
pipeline = DataQualityPipeline(df_raw)
df_processed = pipeline.run_complete_pipeline(pipeline_config)

# Generate quality report
quality_report = pipeline.generate_quality_report()
print("\n✅ Final Quality Report:")
print(quality_report)

# Save processed data
df_processed.to_csv('data/processed/transactions_processed.csv', index=False)
```

---

## Performance Checklist

- [x] All 18 skills implemented
- [x] Production-ready error handling
- [x] Vectorised NumPy operations
- [x] Comprehensive logging
- [x] Export capabilities
- [x] Quality gates integrated

---

## Next Steps

1. **Test each skill** with your actual data
2. **Benchmark performance** on full dataset
3. **Create dashboards** using KPI framework
4. **Set up alerts** using anomaly detection
5. **Document conventions** for your team

---

## Support & Troubleshooting

### Common Issues

**Issue:** Type conversion fails for mixed-type column
**Solution:** Use `errors='coerce'` to convert failures to NaN, then handle separately

**Issue:** Merge results in duplicate columns
**Solution:** Specify `validate='m:1'` to catch cardinality issues before merge

**Issue:** Outlier detection removes too many records
**Solution:** Adjust `iqr_multiplier` (use 3.0 for more conservative) or `threshold_std` (use 3.5)

**Issue:** Performance slow on large dataset
**Solution:** Use vectorised operations (Skill 2.27), filter data before aggregation

---

## Resources

- Source code: `src/data_skills.py`
- Example usage: Run `python -m src.data_skills` for demonstrations
- Sample data: `data/raw/` and `data/processed/`

"""

# PRACTICAL EXAMPLES

print(__doc__)
