
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from typing import Tuple, Dict, List, Union

warnings.filterwarnings('ignore')


# ============================================
# 2.19: DATA TYPE ENFORCEMENT & STANDARDISATION
# ============================================

class DataTypeEnforcer:
    """
    Convert and standardise column data types safely with validation.
    """

    @staticmethod
    def infer_and_enforce_types(df: pd.DataFrame, type_hints: Dict = None) -> pd.DataFrame:
        """
        Infer and enforce appropriate data types for all columns.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        type_hints : Dict, optional
            Manual type specifications: {'column_name': 'int64', 'date_col': 'datetime64'}

        Returns
        -------
        pd.DataFrame
            Dataframe with enforced types
        """
        df_typed = df.copy()
        
        if type_hints is None:
            type_hints = {}

        for col in df_typed.columns:
            if col in type_hints:
                try:
                    df_typed[col] = df_typed[col].astype(type_hints[col])
                except Exception as e:
                    print(f"⚠️  Warning: Could not convert {col} to {type_hints[col]}: {e}")
                    continue

            # Auto-detect if not specified
            if col not in type_hints:
                # Try to convert to numeric
                if df_typed[col].dtype == 'object':
                    try:
                        converted = pd.to_numeric(df_typed[col], errors='coerce')
                        if converted.notna().sum() / len(df_typed) > 0.8:  # 80% success
                            df_typed[col] = converted
                            continue
                    except:
                        pass

                    # Try to convert to datetime
                    try:
                        converted = pd.to_datetime(df_typed[col], errors='coerce')
                        if converted.notna().sum() / len(df_typed) > 0.8:
                            df_typed[col] = converted
                            continue
                    except:
                        pass

        return df_typed

    @staticmethod
    def standardise_currency(df: pd.DataFrame, currency_cols: List[str], 
                            target_type: str = 'float64') -> pd.DataFrame:
        """
        Standardise currency columns by removing symbols and converting to numeric.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        currency_cols : List[str]
            Column names containing currency values
        target_type : str
            Target numeric type ('float64' or 'decimal')

        Returns
        -------
        pd.DataFrame
            Dataframe with standardised currency columns
        """
        df_clean = df.copy()
        
        for col in currency_cols:
            if col in df_clean.columns:
                # Remove currency symbols, commas, spaces
                df_clean[col] = (df_clean[col]
                                .astype(str)
                                .str.replace(r'[$,\s]', '', regex=True)
                                .str.strip())
                # Convert to numeric
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
        return df_clean

    @staticmethod
    def standardise_booleans(df: pd.DataFrame, bool_cols: List[str]) -> pd.DataFrame:
        """
        Standardise boolean columns with flexible input handling.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        bool_cols : List[str]
            Column names containing boolean values

        Returns
        -------
        pd.DataFrame
            Dataframe with standardised boolean columns
        """
        df_bool = df.copy()
        
        true_values = {'yes', 'y', 'true', '1', 'active', 'enabled', 't'}
        false_values = {'no', 'n', 'false', '0', 'inactive', 'disabled', 'f'}
        
        for col in bool_cols:
            if col in df_bool.columns:
                df_bool[col] = (df_bool[col]
                               .astype(str)
                               .str.lower()
                               .str.strip()
                               .map(lambda x: True if x in true_values else 
                                           False if x in false_values else np.nan))
        
        return df_bool


# ============================================
# 2.20: DUPLICATE DETECTION & RECORD DEDUPLICATION
# ============================================

class DuplicateHandler:
    """
    Find and handle exact and near-duplicate records intelligently.
    """

    @staticmethod
    def detect_exact_duplicates(df: pd.DataFrame, subset: List[str] = None, 
                               keep: str = 'first') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Detect and separate exact duplicate records.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        subset : List[str], optional
            Columns to consider for duplicates. If None, uses all columns
        keep : str
            Which duplicate to keep: 'first', 'last', or False (remove all)

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame]
            (cleaned_df, duplicates_df)
        """
        duplicates = df[df.duplicated(subset=subset, keep=False)].sort_values(
            by=subset if subset else list(df.columns)
        )
        
        cleaned = df.drop_duplicates(subset=subset, keep=keep)
        
        print(f"📊 Exact Duplicates Found: {len(duplicates)}")
        print(f"   Records Removed: {len(df) - len(cleaned)}")
        
        return cleaned, duplicates

    @staticmethod
    def detect_near_duplicates(df: pd.DataFrame, fuzzy_cols: List[str], 
                              similarity_threshold: float = 0.85) -> Dict:
        """
        Detect fuzzy/near-duplicate records using string similarity.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        fuzzy_cols : List[str]
            Columns to check for similarity
        similarity_threshold : float
            Similarity score threshold (0-1)

        Returns
        -------
        Dict
            Dictionary of near-duplicate groups
        """
        from difflib import SequenceMatcher
        
        near_dupes = {}
        processed = set()
        
        for idx in range(len(df)):
            if idx in processed:
                continue
                
            group = [idx]
            row_str = ' '.join(df.iloc[idx][fuzzy_cols].astype(str).values)
            
            for compare_idx in range(idx + 1, len(df)):
                if compare_idx in processed:
                    continue
                    
                compare_str = ' '.join(df.iloc[compare_idx][fuzzy_cols].astype(str).values)
                similarity = SequenceMatcher(None, row_str, compare_str).ratio()
                
                if similarity >= similarity_threshold:
                    group.append(compare_idx)
                    processed.add(compare_idx)
            
            if len(group) > 1:
                near_dupes[idx] = group
                processed.add(idx)
        
        print(f"🔍 Near-Duplicates Found: {len(near_dupes)} groups")
        
        return near_dupes

    @staticmethod
    def deduplicate_with_priority(df: pd.DataFrame, subset: List[str],
                                 priority_col: str = None) -> pd.DataFrame:
        """
        Remove duplicates keeping record with highest priority/value.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        subset : List[str]
            Columns defining duplicates
        priority_col : str, optional
            Column to use for priority (higher value = keep)

        Returns
        -------
        pd.DataFrame
            Deduplicated dataframe
        """
        if priority_col and priority_col in df.columns:
            df_sorted = df.sort_values(by=[priority_col], ascending=False)
            return df_sorted.drop_duplicates(subset=subset, keep='first')
        else:
            return df.drop_duplicates(subset=subset, keep='first')


# ============================================
# 2.21: STRING CLEANING & TEXT NORMALISATION
# ============================================

class StringCleaner:
    """
    Clean and normalise text data for consistent categorisation.
    """

    @staticmethod
    def clean_text(df: pd.DataFrame, text_cols: List[str]) -> pd.DataFrame:
        """
        Apply comprehensive text cleaning: trim, lowercase, remove symbols.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        text_cols : List[str]
            Columns to clean

        Returns
        -------
        pd.DataFrame
            Dataframe with cleaned text
        """
        df_clean = df.copy()
        
        for col in text_cols:
            if col in df_clean.columns:
                df_clean[col] = (df_clean[col]
                                .astype(str)
                                .str.strip()                    # Remove leading/trailing
                                .str.lower()                    # Normalise case
                                .str.replace(r'\s+', ' ', regex=True)  # Multiple spaces
                                .str.replace(r'[^\w\s]', '', regex=True))  # Remove symbols
        
        return df_clean

    @staticmethod
    def map_label_variations(df: pd.DataFrame, col: str, 
                            mapping_dict: Dict = None) -> pd.DataFrame:
        """
        Map variations of category labels to standard values.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        col : str
            Column with labels to standardise
        mapping_dict : Dict, optional
            Explicit mapping: {'old_value': 'new_value'}

        Returns
        -------
        pd.DataFrame
            Dataframe with mapped labels
        """
        df_mapped = df.copy()
        
        if mapping_dict:
            df_mapped[col] = df_mapped[col].map(mapping_dict).fillna(df_mapped[col])
        else:
            # Auto-detect common variations
            print(f"📋 Unique values in {col}: {df_mapped[col].nunique()}")
            
        return df_mapped

    @staticmethod
    def remove_special_chars(value: str, keep_alphanumeric: bool = True) -> str:
        """
        Remove special characters from string.

        Parameters
        ----------
        value : str
            Input string
        keep_alphanumeric : bool
            If True, keep only alphanumeric and spaces

        Returns
        -------
        str
            Cleaned string
        """
        if keep_alphanumeric:
            return ''.join(c for c in str(value) if c.isalnum() or c.isspace())
        return value


# ============================================
# 2.22: DATE & TIME TRANSFORMATION PIPELINE
# ============================================

class DateTimeTransformer:
    """
    Transform raw timestamps into business-useful features.
    """

    @staticmethod
    def parse_dates(df: pd.DataFrame, date_cols: List[str], 
                   format: str = None) -> pd.DataFrame:
        """
        Parse and standardise date columns.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        date_cols : List[str]
            Column names with dates
        format : str, optional
            Explicit date format

        Returns
        -------
        pd.DataFrame
            Dataframe with parsed datetime columns
        """
        df_dates = df.copy()
        
        for col in date_cols:
            if col in df_dates.columns:
                df_dates[col] = pd.to_datetime(df_dates[col], format=format, 
                                             errors='coerce')
        
        return df_dates

    @staticmethod
    def extract_time_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """
        Extract useful time-based features from datetime column.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        date_col : str
            Datetime column name

        Returns
        -------
        pd.DataFrame
            Dataframe with new time features
        """
        df_features = df.copy()
        
        if date_col not in df_features.columns:
            return df_features
        
        dt = pd.to_datetime(df_features[date_col], errors='coerce')
        
        df_features[f'{date_col}_year'] = dt.dt.year
        df_features[f'{date_col}_month'] = dt.dt.month
        df_features[f'{date_col}_day'] = dt.dt.day
        df_features[f'{date_col}_dayofweek'] = dt.dt.dayofweek
        df_features[f'{date_col}_hour'] = dt.dt.hour
        df_features[f'{date_col}_minute'] = dt.dt.minute
        df_features[f'{date_col}_quarter'] = dt.dt.quarter
        df_features[f'{date_col}_week'] = dt.dt.isocalendar().week
        df_features[f'{date_col}_is_weekend'] = dt.dt.dayofweek.isin([5, 6]).astype(int)
        df_features[f'{date_col}_is_month_start'] = dt.dt.is_month_start.astype(int)
        df_features[f'{date_col}_is_month_end'] = dt.dt.is_month_end.astype(int)
        
        return df_features

    @staticmethod
    def calculate_time_since(df: pd.DataFrame, from_col: str, to_col: str = None,
                            unit: str = 'days') -> pd.Series:
        """
        Calculate time elapsed between two dates.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        from_col : str
            Start date column
        to_col : str, optional
            End date column. If None, uses current date
        unit : str
            Time unit: 'days', 'hours', 'minutes', 'seconds'

        Returns
        -------
        pd.Series
            Time elapsed values
        """
        from_date = pd.to_datetime(df[from_col], errors='coerce')
        
        if to_col:
            to_date = pd.to_datetime(df[to_col], errors='coerce')
        else:
            to_date = pd.Timestamp.now()
        
        delta = to_date - from_date
        
        if unit == 'days':
            return delta.dt.days
        elif unit == 'hours':
            return delta.dt.total_seconds() / 3600
        elif unit == 'minutes':
            return delta.dt.total_seconds() / 60
        else:
            return delta.dt.total_seconds()


# ============================================
# 2.23: OUTLIER DETECTION WITH STATISTICAL METHODS
# ============================================

class OutlierDetector:
    """
    Detect and handle unusual numeric values using statistical methods.
    """

    @staticmethod
    def detect_iqr_outliers(df: pd.DataFrame, numeric_cols: List[str],
                           iqr_multiplier: float = 1.5) -> Dict:
        """
        Detect outliers using Interquartile Range (IQR) method.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        numeric_cols : List[str]
            Numeric columns to check
        iqr_multiplier : float
            IQR multiplier (default 1.5 for mild, 3.0 for extreme)

        Returns
        -------
        Dict
            Outlier information by column
        """
        outliers = {}
        
        for col in numeric_cols:
            if col not in df.columns:
                continue
                
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - (iqr_multiplier * IQR)
            upper_bound = Q3 + (iqr_multiplier * IQR)
            
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            outliers[col] = {
                'count': outlier_count,
                'percentage': (outlier_count / len(df)) * 100,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'indices': df[outlier_mask].index.tolist()
            }
            
            print(f"📊 {col}: {outlier_count} outliers ({outliers[col]['percentage']:.2f}%)")
        
        return outliers

    @staticmethod
    def detect_zscore_outliers(df: pd.DataFrame, numeric_cols: List[str],
                              threshold: float = 3.0) -> Dict:
        """
        Detect outliers using Z-score method (standard deviations from mean).

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        numeric_cols : List[str]
            Numeric columns to check
        threshold : float
            Z-score threshold (typically 2.0-3.0)

        Returns
        -------
        Dict
            Outlier information by column
        """
        outliers = {}
        
        for col in numeric_cols:
            if col not in df.columns:
                continue
            
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outlier_mask = z_scores > threshold
            outlier_count = outlier_mask.sum()
            
            outliers[col] = {
                'count': outlier_count,
                'percentage': (outlier_count / len(df)) * 100,
                'threshold': threshold,
                'indices': df[outlier_mask].index.tolist()
            }
        
        return outliers

    @staticmethod
    def cap_outliers(df: pd.DataFrame, numeric_cols: List[str],
                    method: str = 'iqr', percentile_bounds: Tuple = (1, 99)) -> pd.DataFrame:
        """
        Cap outliers at specified bounds instead of removing them.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        numeric_cols : List[str]
            Numeric columns to cap
        method : str
            'iqr' or 'percentile'
        percentile_bounds : Tuple
            Lower and upper percentiles for capping

        Returns
        -------
        pd.DataFrame
            Dataframe with capped values
        """
        df_capped = df.copy()
        
        for col in numeric_cols:
            if col not in df_capped.columns:
                continue
            
            if method == 'percentile':
                lower = df_capped[col].quantile(percentile_bounds[0] / 100)
                upper = df_capped[col].quantile(percentile_bounds[1] / 100)
            else:  # iqr
                Q1 = df_capped[col].quantile(0.25)
                Q3 = df_capped[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - (1.5 * IQR)
                upper = Q3 + (1.5 * IQR)
            
            df_capped[col] = df_capped[col].clip(lower=lower, upper=upper)
        
        return df_capped


# ============================================
# 2.24: DATA CONSISTENCY & VALIDATION RULES
# ============================================

class DataValidator:
    """
    Create rule-based data quality checks to protect downstream analysis.
    """

    @staticmethod
    def validate_ranges(df: pd.DataFrame, range_rules: Dict) -> Dict:
        """
        Validate numeric columns are within expected ranges.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        range_rules : Dict
            Rules: {'column': (min_val, max_val)}

        Returns
        -------
        Dict
            Validation results
        """
        results = {}
        
        for col, (min_val, max_val) in range_rules.items():
            if col not in df.columns:
                continue
            
            out_of_range = ((df[col] < min_val) | (df[col] > max_val)).sum()
            results[col] = {
                'out_of_range': out_of_range,
                'percentage': (out_of_range / len(df)) * 100,
                'valid': out_of_range == 0
            }
            
            status = "✓ PASS" if results[col]['valid'] else "✗ FAIL"
            print(f"{status} {col}: {out_of_range} values out of range [{min_val}, {max_val}]")
        
        return results

    @staticmethod
    def validate_nulls(df: pd.DataFrame, null_rules: Dict) -> Dict:
        """
        Validate null value constraints.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        null_rules : Dict
            Rules: {'column': max_null_percentage}

        Returns
        -------
        Dict
            Validation results
        """
        results = {}
        
        for col, max_pct in null_rules.items():
            if col not in df.columns:
                continue
            
            null_pct = (df[col].isnull().sum() / len(df)) * 100
            results[col] = {
                'null_percentage': null_pct,
                'valid': null_pct <= max_pct
            }
            
            status = "✓ PASS" if results[col]['valid'] else "✗ FAIL"
            print(f"{status} {col}: {null_pct:.2f}% nulls (max allowed: {max_pct}%)")
        
        return results

    @staticmethod
    def validate_relationships(df: pd.DataFrame, relationship_rules: Dict) -> Dict:
        """
        Validate relationships between columns (e.g., end_date > start_date).

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        relationship_rules : Dict
            Rules: {'col1 > col2': True, 'col1 + col2 == col3': True}

        Returns
        -------
        Dict
            Validation results
        """
        results = {}
        
        for rule, expected in relationship_rules.items():
            violations = 0
            try:
                # Parse and evaluate relationship
                if '>' in rule:
                    col1, col2 = rule.split('>')
                    col1, col2 = col1.strip(), col2.strip()
                    violations = (df[col1] <= df[col2]).sum()
                elif '<' in rule:
                    col1, col2 = rule.split('<')
                    col1, col2 = col1.strip(), col2.strip()
                    violations = (df[col1] >= df[col2]).sum()
                elif '==' in rule:
                    col1, col2 = rule.split('==')
                    col1, col2 = col1.strip(), col2.strip()
                    violations = (df[col1] != df[col2]).sum()
                
                results[rule] = {'violations': violations, 'valid': violations == 0}
                status = "✓ PASS" if violations == 0 else "✗ FAIL"
                print(f"{status} {rule}: {violations} violations")
            except Exception as e:
                results[rule] = {'error': str(e)}
        
        return results


# ============================================
# 2.25: MULTI-SOURCE MERGING & JOIN VALIDATION
# ============================================

class JoinValidator:
    """
    Merge datasets carefully with comprehensive join validation.
    """

    @staticmethod
    def validate_merge(left: pd.DataFrame, right: pd.DataFrame, on: str,
                      how: str = 'inner', validate: str = 'm:1') -> Tuple[pd.DataFrame, Dict]:
        """
        Merge two dataframes with detailed validation.

        Parameters
        ----------
        left : pd.DataFrame
            Left dataframe
        right : pd.DataFrame
            Right dataframe
        on : str
            Column(s) to join on
        how : str
            Join type: 'inner', 'left', 'right', 'outer'
        validate : str
            Expected join type: '1:1', '1:m', 'm:1', 'm:m'

        Returns
        -------
        Tuple[pd.DataFrame, Dict]
            (merged_df, validation_report)
        """
        left_before = len(left)
        right_before = len(right)
        
        merged = left.merge(right, on=on, how=how, validate=validate, indicator=True)
        
        report = {
            'left_rows_before': left_before,
            'right_rows_before': right_before,
            'merged_rows': len(merged),
            'rows_only_in_left': (merged['_merge'] == 'left_only').sum(),
            'rows_only_in_right': (merged['_merge'] == 'right_only').sum(),
            'rows_in_both': (merged['_merge'] == 'both').sum(),
            'expected_validate': validate,
            'actual_left_key_cardinality': left[on].nunique() / len(left),
            'actual_right_key_cardinality': right[on].nunique() / len(right)
        }
        
        print(f"✓ Merge Report for '{how}' join on '{on}':")
        print(f"  Left rows: {left_before} → Merged: {len(merged)}")
        print(f"  Right rows: {right_before}")
        print(f"  Rows only in left: {report['rows_only_in_left']}")
        print(f"  Rows only in right: {report['rows_only_in_right']}")
        print(f"  Rows in both: {report['rows_in_both']}")
        
        merged = merged.drop('_merge', axis=1)
        
        return merged, report

    @staticmethod
    def check_unmatched_keys(left: pd.DataFrame, right: pd.DataFrame, 
                            key: str) -> Dict:
        """
        Identify keys that don't match during join.

        Parameters
        ----------
        left : pd.DataFrame
            Left dataframe
        right : pd.DataFrame
            Right dataframe
        key : str
            Key column name

        Returns
        -------
        Dict
            Unmatched key information
        """
        left_keys = set(left[key].unique())
        right_keys = set(right[key].unique())
        
        unmatched = {
            'in_left_not_right': left_keys - right_keys,
            'in_right_not_left': right_keys - left_keys,
            'in_both': left_keys & right_keys
        }
        
        print(f"🔗 Key '{key}' Matching Report:")
        print(f"  Only in left: {len(unmatched['in_left_not_right'])}")
        print(f"  Only in right: {len(unmatched['in_right_not_left'])}")
        print(f"  In both: {len(unmatched['in_both'])}")
        
        return unmatched


# ============================================
# 2.26: FEATURE ENGINEERING & DERIVED BUSINESS COLUMNS
# ============================================

class FeatureEngineer:
    """
    Create useful business features from raw columns.
    """

    @staticmethod
    def create_transaction_scoring(df: pd.DataFrame, amount_col: str, 
                                  frequency_col: str = None) -> pd.Series:
        """
        Create transaction importance score based on amount and frequency.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        amount_col : str
            Column with transaction amounts
        frequency_col : str, optional
            Column with transaction frequency

        Returns
        -------
        pd.Series
            Transaction score (0-100)
        """
        amount_norm = (df[amount_col] - df[amount_col].min()) / (df[amount_col].max() - df[amount_col].min())
        
        if frequency_col and frequency_col in df.columns:
            freq_norm = (df[frequency_col] - df[frequency_col].min()) / (df[frequency_col].max() - df[frequency_col].min())
            score = (amount_norm * 0.6 + freq_norm * 0.4) * 100
        else:
            score = amount_norm * 100
        
        return score.fillna(0)

    @staticmethod
    def create_risk_tier(df: pd.DataFrame, score_col: str) -> pd.Series:
        """
        Create risk category from continuous score.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        score_col : str
            Column with risk scores

        Returns
        -------
        pd.Series
            Risk tier categories
        """
        return pd.cut(df[score_col], 
                     bins=[0, 30, 60, 90, 100],
                     labels=['Low', 'Medium', 'High', 'Critical'],
                     include_lowest=True)

    @staticmethod
    def create_ratio_features(df: pd.DataFrame, numerator: str, 
                             denominator: str, feature_name: str) -> pd.Series:
        """
        Create ratio-based features safely (handle zero division).

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        numerator : str
            Numerator column
        denominator : str
            Denominator column
        feature_name : str
            Name for the new feature

        Returns
        -------
        pd.Series
            Ratio values (NaN where denominator is 0)
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = df[numerator] / df[denominator]
            ratio = ratio.replace([np.inf, -np.inf], np.nan)
        
        return ratio

    @staticmethod
    def create_customer_lifetime_value(df: pd.DataFrame, customer_col: str,
                                      amount_col: str, 
                                      transaction_date_col: str) -> pd.DataFrame:
        """
        Calculate CLV metrics by customer.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe with transactions
        customer_col : str
            Customer identifier column
        amount_col : str
            Transaction amount column
        transaction_date_col : str
            Transaction date column

        Returns
        -------
        pd.DataFrame
            Customer CLV metrics
        """
        clv = df.groupby(customer_col).agg({
            amount_col: ['sum', 'mean', 'count', 'std'],
            transaction_date_col: ['min', 'max']
        }).round(2)
        
        clv.columns = ['total_value', 'avg_transaction', 'transaction_count', 
                      'transaction_std', 'first_date', 'last_date']
        
        return clv


# ============================================
# 2.27: NUMPY VECTORISED COMPUTATION WORKFLOW
# ============================================

class VectorisedComputation:
    """
    Use NumPy vectorisation for fast repeated calculations.
    """

    @staticmethod
    def vectorised_discount_calculator(amounts: np.ndarray, 
                                      tiers: np.ndarray) -> np.ndarray:
        """
        Apply tiered discounts using vectorised operations (no loops).

        Parameters
        ----------
        amounts : np.ndarray
            Array of transaction amounts
        tiers : np.ndarray
            Array of customer tiers (0-3)

        Returns
        -------
        np.ndarray
            Discounted amounts
        """
        discount_rates = np.array([0, 0.05, 0.10, 0.15])  # Tier 0-3 discount rates
        discounts = discount_rates[tiers]
        discounted = amounts * (1 - discounts)
        
        return discounted

    @staticmethod
    def vectorised_fee_calculator(amounts: np.ndarray, 
                                 merchant_types: np.ndarray) -> np.ndarray:
        """
        Calculate fees using vectorised lookups.

        Parameters
        ----------
        amounts : np.ndarray
            Array of amounts
        merchant_types : np.ndarray
            Array of merchant type codes (0-4)

        Returns
        -------
        np.ndarray
            Calculated fees
        """
        # Base fees by merchant type
        base_fees = np.array([0.01, 0.015, 0.02, 0.025, 0.03])
        
        # Calculate percentage-based fees
        fees = amounts * base_fees[merchant_types]
        
        return fees

    @staticmethod
    def vectorised_running_sum(values: np.ndarray) -> np.ndarray:
        """
        Calculate running sum without explicit loop.

        Parameters
        ----------
        values : np.ndarray
            Input array

        Returns
        -------
        np.ndarray
            Cumulative sum
        """
        return np.cumsum(values)

    @staticmethod
    def performance_comparison(loop_func, vectorised_func, data_size: int = 1000000):
        """
        Compare performance of loop-based vs vectorised computation.

        Parameters
        ----------
        loop_func : callable
            Loop-based function
        vectorised_func : callable
            Vectorised function
        data_size : int
            Size of test data

        Returns
        -------
        Dict
            Timing comparison
        """
        import time
        
        test_data = np.random.rand(data_size)
        
        start = time.time()
        loop_result = loop_func(test_data)
        loop_time = time.time() - start
        
        start = time.time()
        vec_result = vectorised_func(test_data)
        vec_time = time.time() - start
        
        speedup = loop_time / vec_time
        
        print(f"⚡ Performance Comparison ({data_size:,} elements):")
        print(f"   Loop-based: {loop_time:.4f}s")
        print(f"   Vectorised: {vec_time:.4f}s")
        print(f"   Speedup: {speedup:.1f}x faster")
        
        return {'loop_time': loop_time, 'vectorised_time': vec_time, 'speedup': speedup}


# ============================================
# 2.28: DISTRIBUTION ANALYSIS FOR BUSINESS TRENDS
# ============================================

class DistributionAnalyzer:
    """
    Study and visualise data distributions for insights.
    """

    @staticmethod
    def analyze_distribution(series: pd.Series, name: str = '') -> Dict:
        """
        Comprehensive distribution analysis.

        Parameters
        ----------
        series : pd.Series
            Data to analyse
        name : str
            Series name for reporting

        Returns
        -------
        Dict
            Distribution metrics
        """
        analysis = {
            'count': series.count(),
            'null_count': series.isnull().sum(),
            'unique': series.nunique(),
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'q1': series.quantile(0.25),
            'q3': series.quantile(0.75),
            'iqr': series.quantile(0.75) - series.quantile(0.25),
            'skewness': series.skew(),
            'kurtosis': series.kurtosis(),
            'percentile_10': series.quantile(0.10),
            'percentile_90': series.quantile(0.90)
        }
        
        print(f"📊 Distribution Analysis: {name}")
        print(f"   Mean: {analysis['mean']:.2f}, Median: {analysis['median']:.2f}")
        print(f"   Std Dev: {analysis['std']:.2f}")
        print(f"   Skewness: {analysis['skewness']:.2f}, Kurtosis: {analysis['kurtosis']:.2f}")
        print(f"   Range: [{analysis['min']:.2f}, {analysis['max']:.2f}]")
        
        return analysis

    @staticmethod
    def detect_distribution_shape(series: pd.Series) -> str:
        """
        Identify distribution shape (normal, skewed, bimodal, etc.).

        Parameters
        ----------
        series : pd.Series
            Data to analyse

        Returns
        -------
        str
            Distribution shape description
        """
        skewness = series.skew()
        kurtosis = series.kurtosis()
        
        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return 'Approximately Normal'
        elif skewness > 0.5:
            return 'Right-Skewed (Positive)'
        elif skewness < -0.5:
            return 'Left-Skewed (Negative)'
        else:
            return 'Slightly Skewed'


# ============================================
# 2.29: CORRELATION & RELATIONSHIP ANALYSIS
# ============================================

class CorrelationAnalyzer:
    """
    Find and interpret relationships between numeric variables.
    """

    @staticmethod
    def calculate_correlations(df: pd.DataFrame, numeric_cols: List[str],
                             method: str = 'pearson') -> pd.DataFrame:
        """
        Calculate Pearson or Spearman correlation matrix.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        numeric_cols : List[str]
            Columns to correlate
        method : str
            'pearson' or 'spearman'

        Returns
        -------
        pd.DataFrame
            Correlation matrix
        """
        return df[numeric_cols].corr(method=method)

    @staticmethod
    def find_strong_correlations(correlation_matrix: pd.DataFrame,
                                threshold: float = 0.7) -> List[Tuple]:
        """
        Find pairs of variables with strong correlation.

        Parameters
        ----------
        correlation_matrix : pd.DataFrame
            Correlation matrix
        threshold : float
            Minimum correlation strength (0-1)

        Returns
        -------
        List[Tuple]
            List of (var1, var2, correlation) tuples
        """
        pairs = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr = correlation_matrix.iloc[i, j]
                
                if abs(corr) >= threshold:
                    var1 = correlation_matrix.columns[i]
                    var2 = correlation_matrix.columns[j]
                    pairs.append((var1, var2, corr))
        
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        print(f"🔗 Strong Correlations (threshold: {threshold}):")
        for var1, var2, corr in pairs:
            print(f"   {var1} ↔ {var2}: {corr:.3f}")
        
        return pairs


# ============================================
# 2.30: GROUPBY AGGREGATION & SEGMENT INSIGHTS
# ============================================

class SegmentAnalyzer:
    """
    Break data into groups and compare segments.
    """

    @staticmethod
    def group_aggregate(df: pd.DataFrame, group_cols: Union[str, List[str]],
                       agg_dict: Dict) -> pd.DataFrame:
        """
        Group by columns and apply multiple aggregations.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        group_cols : Union[str, List[str]]
            Column(s) to group by
        agg_dict : Dict
            Aggregation spec: {'amount': ['sum', 'mean'], 'count': 'count'}

        Returns
        -------
        pd.DataFrame
            Grouped and aggregated data
        """
        return df.groupby(group_cols).agg(agg_dict).round(2)

    @staticmethod
    def segment_comparison(df: pd.DataFrame, segment_col: str,
                          metric_cols: List[str]) -> pd.DataFrame:
        """
        Compare metrics across segments side-by-side.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        segment_col : str
            Column defining segments
        metric_cols : List[str]
            Columns to compare

        Returns
        -------
        pd.DataFrame
            Segment comparison table
        """
        comparison = df.groupby(segment_col)[metric_cols].agg(['mean', 'median', 'std']).round(2)
        
        print(f"📊 Segment Comparison by '{segment_col}':")
        print(comparison)
        
        return comparison

    @staticmethod
    def rank_segments(df: pd.DataFrame, segment_col: str, 
                     metric_col: str, ascending: bool = False) -> pd.DataFrame:
        """
        Rank segments by metric value.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        segment_col : str
            Column defining segments
        metric_col : str
            Column to rank by
        ascending : bool
            Sort order

        Returns
        -------
        pd.DataFrame
            Segments ranked by metric
        """
        ranking = (df.groupby(segment_col)[metric_col]
                  .sum()
                  .sort_values(ascending=ascending)
                  .reset_index()
                  .reset_index(drop=False)
                  .rename(columns={'index': 'rank'}))
        ranking['rank'] = ranking['rank'] + 1
        
        return ranking


# ============================================
# 2.31: TIME-SERIES TREND & ROLLING METRICS
# ============================================

class TimeSeriesAnalyzer:
    """
    Track performance and trends over time.
    """

    @staticmethod
    def resample_timeseries(df: pd.DataFrame, date_col: str, value_col: str,
                           freq: str = 'D', method: str = 'sum') -> pd.Series:
        """
        Resample time series to different frequencies.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        date_col : str
            Date column name
        value_col : str
            Value column to aggregate
        freq : str
            Frequency: 'D'=Day, 'W'=Week, 'M'=Month, 'Q'=Quarter, 'Y'=Year
        method : str
            Aggregation: 'sum', 'mean', 'count'

        Returns
        -------
        pd.Series
            Resampled time series
        """
        ts = df.set_index(date_col)[value_col]
        
        if method == 'sum':
            return ts.resample(freq).sum()
        elif method == 'mean':
            return ts.resample(freq).mean()
        elif method == 'count':
            return ts.resample(freq).count()

    @staticmethod
    def rolling_average(series: pd.Series, window: int = 7) -> pd.Series:
        """
        Calculate rolling average (moving average).

        Parameters
        ----------
        series : pd.Series
            Time series data
        window : int
            Window size (e.g., 7 for 7-day moving average)

        Returns
        -------
        pd.Series
            Rolling average values
        """
        return series.rolling(window=window, center=False).mean()

    @staticmethod
    def percentage_change(series: pd.Series, periods: int = 1) -> pd.Series:
        """
        Calculate period-over-period percentage change.

        Parameters
        ----------
        series : pd.Series
            Time series data
        periods : int
            Number of periods for comparison

        Returns
        -------
        pd.Series
            Percentage change values
        """
        return series.pct_change(periods=periods) * 100

    @staticmethod
    def cumulative_sum(series: pd.Series) -> pd.Series:
        """
        Calculate cumulative sum (running total).

        Parameters
        ----------
        series : pd.Series
            Time series data

        Returns
        -------
        pd.Series
            Cumulative sum values
        """
        return series.cumsum()


# ============================================
# 2.32: BEHAVIOURAL ANALYSIS & USER SEGMENTATION
# ============================================

class BehaviourAnalyzer:
    """
    Compare behaviour across customer segments.
    """

    @staticmethod
    def create_behavioural_segments(df: pd.DataFrame, metrics: Dict) -> pd.DataFrame:
        """
        Create customer segments based on multiple behavioural metrics.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        metrics : Dict
            Metrics to segment on: {'rfm_score': (0, 100), 'transaction_count': (1, 100)}

        Returns
        -------
        pd.DataFrame
            Dataframe with segment assignment
        """
        df_seg = df.copy()
        
        # Normalise metrics (0-100 scale)
        for metric, (min_val, max_val) in metrics.items():
            if metric in df_seg.columns:
                df_seg[f'{metric}_norm'] = ((df_seg[metric] - min_val) / (max_val - min_val) * 100).clip(0, 100)
        
        # Calculate overall behaviour score
        score_cols = [f'{m}_norm' for m in metrics.keys() if f'{m}_norm' in df_seg.columns]
        if score_cols:
            df_seg['behaviour_score'] = df_seg[score_cols].mean(axis=1)
            
            # Create segments
            df_seg['segment'] = pd.cut(df_seg['behaviour_score'],
                                      bins=[0, 25, 50, 75, 100],
                                      labels=['Dormant', 'Low-Activity', 'Active', 'VIP'],
                                      include_lowest=True)
        
        return df_seg

    @staticmethod
    def behaviour_comparison_table(df: pd.DataFrame, segment_col: str,
                                  behaviour_metrics: List[str]) -> pd.DataFrame:
        """
        Create behaviour profile by segment.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe with segments
        segment_col : str
            Segment column name
        behaviour_metrics : List[str]
            Metrics to compare

        Returns
        -------
        pd.DataFrame
            Segment behaviour profiles
        """
        profile = df.groupby(segment_col)[behaviour_metrics].agg(['mean', 'median', 'count']).round(2)
        
        return profile


# ============================================
# 2.33: FUNNEL ANALYSIS & DROP-OFF DETECTION
# ============================================

class FunnelAnalyzer:
    """
    Track where customers or records drop out of a process.
    """

    @staticmethod
    def build_funnel(df: pd.DataFrame, customer_col: str, stage_col: str,
                    stages: List[str]) -> pd.DataFrame:
        """
        Build funnel analysis from transaction stages.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        customer_col : str
            Customer identifier column
        stage_col : str
            Column defining process stage
        stages : List[str]
            Ordered list of stages

        Returns
        -------
        pd.DataFrame
            Funnel metrics by stage
        """
        funnel_data = []
        
        for stage in stages:
            customers_at_stage = df[df[stage_col] == stage][customer_col].nunique()
            funnel_data.append({
                'stage': stage,
                'customers': customers_at_stage,
                'percentage': 100 if len(funnel_data) == 0 else (customers_at_stage / funnel_data[0]['customers']) * 100
            })
        
        funnel_df = pd.DataFrame(funnel_data)
        
        # Calculate drop-off rates
        funnel_df['drop_off_rate'] = funnel_df['customers'].pct_change() * -100
        funnel_df['drop_off_count'] = funnel_df['customers'].diff() * -1
        
        print("📊 Funnel Analysis:")
        for idx, row in funnel_df.iterrows():
            print(f"   {row['stage']}: {row['customers']} customers ({row['percentage']:.1f}%)")
            if pd.notna(row['drop_off_count']):
                print(f"      Drop-off: {int(row['drop_off_count'])} customers ({row['drop_off_rate']:.1f}%)")
        
        return funnel_df


# ============================================
# 2.34: KPI DEFINITION & BUSINESS METRIC DESIGN
# ============================================

class KPIFramework:
    """
    Define and track KPIs tied to business objectives.
    """

    @staticmethod
    def define_kpi(name: str, formula_description: str, target: float,
                  warning_threshold: float = None, 
                  critical_threshold: float = None) -> Dict:
        """
        Define a KPI with targets and thresholds.

        Parameters
        ----------
        name : str
            KPI name
        formula_description : str
            How KPI is calculated
        target : float
            Target value
        warning_threshold : float, optional
            Value below which to raise warning
        critical_threshold : float, optional
            Value below which to raise critical alert

        Returns
        -------
        Dict
            KPI definition
        """
        return {
            'name': name,
            'formula': formula_description,
            'target': target,
            'warning_threshold': warning_threshold or (target * 0.9),
            'critical_threshold': critical_threshold or (target * 0.75),
            'created_date': datetime.now().isoformat()
        }

    @staticmethod
    def calculate_kpi_status(actual_value: float, kpi_definition: Dict) -> Dict:
        """
        Evaluate KPI status against thresholds.

        Parameters
        ----------
        actual_value : float
            Actual KPI value
        kpi_definition : Dict
            KPI definition

        Returns
        -------
        Dict
            Status report
        """
        target = kpi_definition['target']
        percent_of_target = (actual_value / target * 100) if target != 0 else 0
        
        if actual_value >= target:
            status = '✓ EXCEEDS TARGET'
        elif actual_value >= kpi_definition['warning_threshold']:
            status = '⚠ WARNING'
        elif actual_value >= kpi_definition['critical_threshold']:
            status = '🔴 CRITICAL'
        else:
            status = '❌ SEVERE'
        
        return {
            'kpi': kpi_definition['name'],
            'actual': actual_value,
            'target': target,
            'percent_of_target': percent_of_target,
            'status': status,
            'variance': actual_value - target
        }

    @staticmethod
    def kpi_dashboard(df_kpis: pd.DataFrame, kpi_definitions: List[Dict]) -> pd.DataFrame:
        """
        Create KPI status dashboard.

        Parameters
        ----------
        df_kpis : pd.DataFrame
            Dataframe with KPI values
        kpi_definitions : List[Dict]
            List of KPI definitions

        Returns
        -------
        pd.DataFrame
            KPI dashboard
        """
        dashboard = []
        
        for kpi_def in kpi_definitions:
            kpi_name = kpi_def['name']
            if kpi_name in df_kpis.columns:
                actual = df_kpis[kpi_name].iloc[-1]
                status_info = KPIFramework.calculate_kpi_status(actual, kpi_def)
                dashboard.append(status_info)
        
        dashboard_df = pd.DataFrame(dashboard)
        
        print("\n📊 KPI DASHBOARD:")
        print(dashboard_df.to_string(index=False))
        
        return dashboard_df


# ============================================
# 2.35: ROOT CAUSE INVESTIGATION WORKFLOW
# ============================================

class RootCauseAnalyzer:
    """
    Systematically investigate data problems step by step.
    """

    @staticmethod
    def narrow_by_time(df: pd.DataFrame, date_col: str, value_col: str,
                      anomaly_start: pd.Timestamp, anomaly_end: pd.Timestamp) -> Dict:
        """
        Isolate problem to specific time period.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        date_col : str
            Date column
        value_col : str
            Metric column
        anomaly_start : pd.Timestamp
            Start of anomaly period
        anomaly_end : pd.Timestamp
            End of anomaly period

        Returns
        -------
        Dict
            Pre-anomaly and anomaly period analysis
        """
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        before_anomaly = df[df[date_col] < anomaly_start][value_col]
        during_anomaly = df[(df[date_col] >= anomaly_start) & (df[date_col] <= anomaly_end)][value_col]
        
        return {
            'period': f'{anomaly_start} to {anomaly_end}',
            'normal_mean': before_anomaly.mean(),
            'normal_std': before_anomaly.std(),
            'anomaly_mean': during_anomaly.mean(),
            'anomaly_median': during_anomaly.median(),
            'change_percent': ((during_anomaly.mean() - before_anomaly.mean()) / before_anomaly.mean() * 100),
            'records_affected': len(during_anomaly)
        }

    @staticmethod
    def narrow_by_segment(df: pd.DataFrame, segment_col: str, value_col: str,
                         overall_anomaly: float) -> Dict:
        """
        Isolate problem to specific segments/categories.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        segment_col : str
            Segment/category column
        value_col : str
            Metric column
        overall_anomaly : float
            Overall anomaly value

        Returns
        -------
        Dict
            Segment-level analysis
        """
        segment_analysis = df.groupby(segment_col)[value_col].agg(['mean', 'count']).round(2)
        segment_analysis['deviation_from_overall'] = (segment_analysis['mean'] - overall_anomaly).round(2)
        
        return segment_analysis


# ============================================
# 2.36: ANOMALY DETECTION & RISK IDENTIFICATION
# ============================================

class AnomalyDetector:
    """
    Detect and flag unusual metric behaviour and risks.
    """

    @staticmethod
    def detect_spikes_dips(series: pd.Series, threshold_std: float = 2.0) -> Dict:
        """
        Detect unusual spikes and dips in metrics.

        Parameters
        ----------
        series : pd.Series
            Time series data
        threshold_std : float
            Number of standard deviations for flagging (typically 2.0-3.0)

        Returns
        -------
        Dict
            Anomalies detected
        """
        mean = series.mean()
        std = series.std()
        
        lower_bound = mean - (threshold_std * std)
        upper_bound = mean + (threshold_std * std)
        
        spikes = series[series > upper_bound]
        dips = series[series < lower_bound]
        
        return {
            'mean': mean,
            'std': std,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'spike_count': len(spikes),
            'dip_count': len(dips),
            'spike_indices': spikes.index.tolist(),
            'dip_indices': dips.index.tolist()
        }

    @staticmethod
    def flag_anomalies(df: pd.DataFrame, value_col: str, 
                      anomaly_info: Dict) -> pd.DataFrame:
        """
        Flag anomalies with severity labels.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        value_col : str
            Column to check
        anomaly_info : Dict
            Anomaly detection parameters

        Returns
        -------
        pd.DataFrame
            Dataframe with anomaly flags
        """
        df_flagged = df.copy()
        
        upper_bound = anomaly_info['upper_bound']
        lower_bound = anomaly_info['lower_bound']
        
        df_flagged['anomaly_flag'] = 'Normal'
        df_flagged.loc[df_flagged[value_col] > upper_bound, 'anomaly_flag'] = 'Spike'
        df_flagged.loc[df_flagged[value_col] < lower_bound, 'anomaly_flag'] = 'Dip'
        
        # Calculate severity (deviation from normal)
        mean = anomaly_info['mean']
        df_flagged['anomaly_severity'] = abs(df_flagged[value_col] - mean)
        
        df_flagged['risk_level'] = 'Low'
        df_flagged.loc[df_flagged['anomaly_severity'] > anomaly_info['std'] * 2, 'risk_level'] = 'Medium'
        df_flagged.loc[df_flagged['anomaly_severity'] > anomaly_info['std'] * 3, 'risk_level'] = 'High'
        df_flagged.loc[df_flagged['anomaly_severity'] > anomaly_info['std'] * 4, 'risk_level'] = 'Critical'
        
        return df_flagged


# ============================================
# INTEGRATED PIPELINE
# ============================================

class DataQualityPipeline:
    """
    Orchestrate all data quality and transformation steps.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize pipeline with input dataframe."""
        self.df = df.copy()
        self.quality_report = {}
        self.transformations_applied = []

    def run_complete_pipeline(self, config: Dict) -> pd.DataFrame:
        """
        Execute complete data quality pipeline.

        Parameters
        ----------
        config : Dict
            Pipeline configuration with steps and parameters

        Returns
        -------
        pd.DataFrame
            Cleaned and transformed dataframe
        """
        print("🚀 Starting Data Quality Pipeline...\n")
        
        # Step 1: Type enforcement
        if 'type_hints' in config:
            print("Step 1: Data Type Enforcement")
            self.df = DataTypeEnforcer.infer_and_enforce_types(self.df, config['type_hints'])
            self.transformations_applied.append('type_enforcement')
        
        # Step 2: Deduplication
        if 'duplicate_cols' in config:
            print("\nStep 2: Duplicate Detection & Removal")
            self.df, _ = DuplicateHandler.detect_exact_duplicates(
                self.df, subset=config['duplicate_cols']
            )
            self.transformations_applied.append('deduplication')
        
        # Step 3: String cleaning
        if 'text_cols' in config:
            print("\nStep 3: String Cleaning & Normalisation")
            self.df = StringCleaner.clean_text(self.df, config['text_cols'])
            self.transformations_applied.append('string_cleaning')
        
        # Step 4: Date transformation
        if 'date_cols' in config:
            print("\nStep 4: Date & Time Transformation")
            self.df = DateTimeTransformer.parse_dates(self.df, config['date_cols'])
            self.df = DateTimeTransformer.extract_time_features(
                self.df, config['date_cols'][0]
            )
            self.transformations_applied.append('date_transformation')
        
        # Step 5: Outlier detection and handling
        if 'numeric_cols' in config:
            print("\nStep 5: Outlier Detection & Handling")
            OutlierDetector.detect_iqr_outliers(self.df, config['numeric_cols'])
            if 'cap_outliers' in config and config['cap_outliers']:
                self.df = OutlierDetector.cap_outliers(self.df, config['numeric_cols'])
            self.transformations_applied.append('outlier_handling')
        
        # Step 6: Validation rules
        if 'validation_rules' in config:
            print("\nStep 6: Data Consistency Validation")
            DataValidator.validate_nulls(self.df, config['validation_rules'].get('null_rules', {}))
            DataValidator.validate_ranges(self.df, config['validation_rules'].get('range_rules', {}))
            self.transformations_applied.append('validation')
        
        print(f"\n✅ Pipeline Complete! Applied {len(self.transformations_applied)} transformations")
        
        return self.df

    def generate_quality_report(self) -> Dict:
        """Generate data quality summary report."""
        report = {
            'input_rows': len(self.df),
            'input_columns': len(self.df.columns),
            'total_cells': len(self.df) * len(self.df.columns),
            'null_percentage': (self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns))) * 100,
            'transformations_applied': self.transformations_applied,
            'timestamp': datetime.now().isoformat()
        }
        
        return report


# ============================================
# EXAMPLE USAGE & DEMONSTRATION
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("DATA SKILLS MODULE - COMPREHENSIVE DEMONSTRATION")
    print("=" * 80)
    print("\nThis module implements 18 advanced data skills (2.19-2.36)")
    print("for production fintech analytics.\n")
    
    # Create sample dataset
    np.random.seed(42)
    sample_data = {
        'transaction_id': range(1, 101),
        'customer_id': np.random.randint(1000, 1050, 100),
        'amount': np.random.exponential(scale=500, size=100),
        'merchant_category': np.random.choice(['grocery', 'restaurant', 'gas', 'retail'], 100),
        'transaction_date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'status': np.random.choice(['completed', 'pending', 'failed'], 100, p=[0.8, 0.15, 0.05]),
        'is_fraud': np.random.choice(['yes', 'no', 'Yes', 'No'], 100),
    }
    
    df_sample = pd.DataFrame(sample_data)
    
    print("📊 Sample Dataset Created:")
    print(f"   Rows: {len(df_sample)}, Columns: {len(df_sample.columns)}")
    print(f"\nFirst few records:")
    print(df_sample.head())
    
    # Demonstrate key skills
    print("\n" + "=" * 80)
    print("SKILL DEMONSTRATIONS")
    print("=" * 80)
    
    # 2.19: Data Type Enforcement
    print("\n✓ 2.19 - Data Type Enforcement")
    df_typed = DataTypeEnforcer.infer_and_enforce_types(df_sample)
    print(f"   Dtypes: {df_typed.dtypes.to_dict()}")
    
    # 2.21: String Cleaning
    print("\n✓ 2.21 - String Cleaning & Normalisation")
    df_clean = StringCleaner.clean_text(df_sample, ['merchant_category', 'status'])
    print(f"   Cleaned merchant categories: {df_clean['merchant_category'].unique()}")
    
    # 2.22: Date Features
    print("\n✓ 2.22 - Date & Time Transformation")
    df_dates = DateTimeTransformer.extract_time_features(df_typed, 'transaction_date')
    print(f"   New date features: {[c for c in df_dates.columns if 'transaction_date_' in c][:3]}")
    
    # 2.23: Outlier Detection
    print("\n✓ 2.23 - Outlier Detection")
    outliers = OutlierDetector.detect_iqr_outliers(df_sample, ['amount'])
    
    # 2.26: Feature Engineering
    print("\n✓ 2.26 - Feature Engineering")
    df_features = df_typed.copy()
    df_features['transaction_score'] = FeatureEngineer.create_transaction_scoring(
        df_features, 'amount'
    )
    print(f"   Transaction scores: min={df_features['transaction_score'].min():.2f}, max={df_features['transaction_score'].max():.2f}")
    
    # 2.28: Distribution Analysis
    print("\n✓ 2.28 - Distribution Analysis")
    dist = DistributionAnalyzer.analyze_distribution(df_sample['amount'], 'Transaction Amount')
    
    # 2.30: Segment Analysis
    print("\n✓ 2.30 - Segment Analysis")
    segment_summary = SegmentAnalyzer.group_aggregate(
        df_clean,
        'merchant_category',
        {'amount': ['sum', 'mean', 'count']}
    )
    print(segment_summary)
    
    print("\n" + "=" * 80)
    print("✅ All demonstrations complete!")
    print("=" * 80)
