import os
import json
import pandas as pd
import numpy as np


def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.

    Returns: DataFrame with analysis of missing data by column
    """
    # Treat empty strings as missing
    df = df.replace('', np.nan)

    missing_analysis = pd.DataFrame({
        'column': df.columns,
        'null_count': df.isnull().sum().values,
        'null_percentage': (df.isnull().sum() / len(df) * 100).round(2).values,
        'data_type': df.dtypes.values,
        'null_meaning': ''
    })

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy='median'):
    """Fill numerical nulls with mean or median."""
    df_imputed = df.copy()
    for col in numerical_cols:
        if col not in df_imputed.columns:
            continue
        nulls = df_imputed[col].isnull().sum()
        if nulls > 0:
            fill_value = df_imputed[col].median() if strategy == 'median' else df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(fill_value)
            print(f"  ✓ {col}: filled {nulls} nulls with {strategy} ({fill_value:.2f})")
    return df_imputed


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with mode (most common value)."""
    df_imputed = df.copy()
    for col in categorical_cols:
        if col not in df_imputed.columns:
            continue
        nulls = df_imputed[col].isnull().sum()
        if nulls > 0:
            try:
                mode_val = df_imputed[col].mode(dropna=True)[0]
            except Exception:
                mode_val = None
            if pd.isna(mode_val):
                print(f"  ! {col}: unable to determine mode, skipping")
                continue
            df_imputed[col] = df_imputed[col].fillna(mode_val)
            print(f"  ✓ {col}: filled {nulls} nulls with mode '{mode_val}'")
    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Fill with previous value (for time-series data)."""
    df_imputed = df.copy()
    for col in time_series_cols:
        if col not in df_imputed.columns:
            continue
        nulls = df_imputed[col].isnull().sum()
        if nulls > 0:
            df_imputed[col] = df_imputed[col].ffill()
            print(f"  ✓ {col}: forward-filled {nulls} nulls")
    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""
    rows_before = len(df)
    df_imputed = df.dropna(subset=[c for c in critical_cols if c in df.columns])
    rows_dropped = rows_before - len(df_imputed)
    print(f"  ✓ Dropped {rows_dropped} rows with null in: {critical_cols}")
    return df_imputed


def document_imputation_decisions(df_original, df_imputed, out_path='output/imputation_decisions.json'):
    """Document imputation decisions per-column with business reasoning.

    Produces a JSON audit with before/after metrics, strategy, values used,
    and a lightweight risk/over-imputation flag so downstream analysts can
    inspect what was changed and why.
    """
    decisions = {}

    rows_before = len(df_original)
    rows_after = len(df_imputed)

    for col in df_original.columns:
        before_nulls = int(df_original[col].isnull().sum())
        after_nulls = int(df_imputed[col].isnull().sum()) if col in df_imputed.columns else None
        if before_nulls == 0 and (after_nulls == 0 or after_nulls is None):
            continue

        col_info = {
            'column_type': str(df_original[col].dtype),
            'null_count_before': before_nulls,
            'null_pct_before': round(before_nulls / rows_before * 100, 4) if rows_before else None,
            'null_count_after': after_nulls,
            'null_pct_after': round(after_nulls / rows_after * 100, 4) if (rows_after and after_nulls is not None) else None,
            'strategy': None,
            'value_used': None,
            'business_reasoning': None,
            'risk_assessment': None,
            'over_imputation': False
        }

        decisions[col] = col_info

    # If there are specific columns we changed or used values for, try to enrich
    # the decisions file by inferring strategy from differences between df_original and df_imputed.
    for col, info in decisions.items():
        before = info['null_count_before']
        after = info['null_count_after'] if info['null_count_after'] is not None else 0
        filled = max(before - after, 0)

        # infer strategy heuristics
        if before > 0 and after == 0 and filled > 0:
            # Assume imputation rather than drop when row counts equal or decreased only by drops on other columns
            # Try to locate a plausible value used
            # numeric
            try:
                numeric_vals = pd.to_numeric(df_original[col], errors='coerce')
                if numeric_vals.notnull().any():
                    med = numeric_vals.median()
                    info['strategy'] = 'median' if pd.notna(med) else 'mode'
                    info['value_used'] = float(med) if pd.notna(med) else None
                    info['business_reasoning'] = 'Median used for numerical robustness to outliers.'
                    info['risk_assessment'] = 'Low-to-Medium - creates synthetic numeric values.'
                else:
                    # categorical
                    try:
                        mode_val = df_original[col].mode(dropna=True).iloc[0]
                        info['strategy'] = 'mode'
                        info['value_used'] = mode_val
                        info['business_reasoning'] = 'Mode used to preserve categorical distribution.'
                        info['risk_assessment'] = 'Low - preserves category proportions.'
                    except Exception:
                        info['strategy'] = 'unknown'
                        info['business_reasoning'] = 'Could not infer strategy programmatically.'
                        info['risk_assessment'] = 'Unknown'
            except Exception:
                info['strategy'] = 'unknown'

        elif before > 0 and after is not None and after > 0 and filled == 0:
            # still missing after — likely left as-is
            info['strategy'] = 'left_as_missing'
            info['business_reasoning'] = 'Column left with remaining nulls for domain review.'
            info['risk_assessment'] = 'Varies'

        # Flag over-imputation: if more than 20% of rows were filled for this column
        if rows_before and filled / rows_before > 0.2:
            info['over_imputation'] = True

    summary = {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'total_nulls_before': int(df_original.isnull().sum().sum()),
        'total_nulls_after': int(df_imputed.isnull().sum().sum()),
        'columns': decisions
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"  ✓ Imputation decisions written to {out_path}")
    return summary


def validate_imputation(df_original, df_imputed):
    """Compare metrics before and after imputation."""
    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)
    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df_original) - len(df_imputed)}")
    print(f"\nTotal nulls before: {df_original.isnull().sum().sum()}")
    print(f"Total nulls after:  {df_imputed.isnull().sum().sum()}")

    missing_after = pd.DataFrame({
        'column': df_imputed.columns,
        'null_count_after': df_imputed.isnull().sum().values,
        'null_percentage_after': (df_imputed.isnull().sum() / len(df_imputed) * 100).round(2).values
    })

    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)

    return missing_after


def _detect_columns(df):
    numerical = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetimes = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    # common time-like columns
    for c in ['last_updated', 'status_date', 'timestamp']:
        if c in df.columns and c not in datetimes:
            datetimes.append(c)
    return numerical, categorical, datetimes


if __name__ == "__main__":
    import sys
    
    # Allow optional input/output paths as arguments
    if len(sys.argv) > 1:
        src = sys.argv[1]
        dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join('data', 'processed', 'cleaned_sample_10k.csv')
    else:
        src = os.path.join('data', 'raw', 'missing_data.csv')
        dst = os.path.join('data', 'processed', 'cleaned_data.csv')

    if not os.path.exists(src):
        print(f"Source file not found: {src}")
        raise SystemExit(1)

    df = pd.read_csv(src)
    # Normalize blank strings to NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)

    print("Step 1: Analyzing missing values...")
    analyze_missing_values(df)

    print("Step 2: Applying per-column imputation strategies...")

    # Start by dropping rows missing critical identifiers
    critical_cols = ['customer_id', 'email']
    df_work = drop_rows_with_nulls(df, critical_cols)

    # Detect columns after initial drops
    numerical_cols, categorical_cols, datetime_cols = _detect_columns(df_work)

    # Coerce numeric-like columns to numeric to make imputation robust
    for col in numerical_cols:
        df_work[col] = pd.to_numeric(df_work[col], errors='coerce')

    # Build per-column strategy (could be extended to read a config file)
    def choose_strategy(col):
        # user-config / business rules could override here
        if col in critical_cols:
            return 'drop'
        if col in numerical_cols:
            return 'median'
        if col in datetime_cols:
            return 'ffill'
        return 'mode'

    # Apply strategies column-by-column and record what was done
    df_before = df_work.copy()
    for col in df_before.columns:
        nulls_before = int(df_before[col].isnull().sum())
        if nulls_before == 0:
            continue
        strat = choose_strategy(col)
        print(f"Applying {strat} for column: {col} ({nulls_before} nulls)")
        if strat == 'drop':
            df_work = drop_rows_with_nulls(df_work, [col])
        elif strat in ('median', 'mean'):
            df_work = impute_mean_median(df_work, [col], strategy='median' if strat == 'median' else 'mean')
        elif strat == 'mode':
            df_work = impute_mode(df_work, [col])
        elif strat == 'ffill':
            df_work = impute_forward_fill(df_work, [col])

    df_imputed = df_work

    print("\nStep 3: Documenting imputation decisions...")
    decisions = document_imputation_decisions(df, df_imputed)

    print("\nStep 4: Validating imputation...")
    validate_imputation(df, df_imputed)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    df_imputed.to_csv(dst, index=False)
    print(f"\n✓ Cleaned data saved to {dst}")
