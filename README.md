# 💳 Fintech Payment Analysis — Payment Retry, Failure & Revenue Loss Analytics

An end-to-end data engineering and analytics pipeline built for Fintech payment processing. This project helps finance and operations teams distinguish between temporary payment friction (payments that succeed after retrying) and permanently lost revenue from failed transactions.

---

## 🎯 Business Problem

Fintech platforms process thousands of digital transactions daily. Payment retries, gateway error codes, and timestamps are often stored separately, causing the following issues:
* Finance teams cannot distinguish temporary transaction friction from permanent revenue leakage.
* There is no visibility into which acquiring banks or payment channels experience the highest failure rates.
* Calculating operational metrics such as retry delay, recovery rates, and transaction value tiers is difficult.

This project delivers a 14-stage data engineering preprocessing pipeline to ingest, clean, validate, and enrich transaction logs. The resulting analysis-ready dataset allows stakeholders to segment customers, audit quality gates, and query business insights.

---

## 📂 Project Structure

```text
Fintech/
│
├── data/
│   ├── raw/
│   │   ├── missing_data.csv        # Baseline missing data check
│   │   ├── customers.csv           # Customer profiles database
│   │   ├── transactions.csv        # Raw payment transaction logs
│   │   └── sample.json             # Raw transactions JSON preview
│   │
│   └── processed/
│       └── final_fintech_dataset.csv # Cleaned & enriched target dataset
│
├── output/
│   ├── intake_validation_report.json  # File structure validation metadata
│   ├── dataset_profile.csv           # Baseline numerical/categorical counts
│   ├── data_dictionary.csv            # Structured data field business mapping
│   ├── missing_value_report.csv       # Analysis of null counts and percentages
│   ├── duplicate_report.json          # Row-level and primary key duplicates
│   ├── validation_failures.csv        # Extracted records violating business rules
│   ├── validation_report.json         # Checkpoint summary of rule violations
│   ├── unmatched_customers.csv        # Customers with zero logged transactions
│   ├── unmatched_transactions.csv     # Transactions lacking a customer profile
│   ├── join_report.json               # Merge overlap statistics
│   ├── feature_validation_report.json # Derived columns profiling analysis
│   └── final_data_quality_report.json # Overall pipeline metrics & business KPIs
│
├── scripts/
│   ├── dataset_intake_validation.py  # Module 2.14: Pre-ingestion validation
│   ├── data_ingestion.py              # Module 2.15: CSV and JSON reader utilities
│   ├── dataset_profiling.py           # Module 2.16: Pre-cleaning data profiler
│   ├── data_dictionary.py             # Module 2.17: Business context mapper
│   ├── handle_missing.py              # Module 2.18: Contextual missing value handler
│   ├── handle_duplicates.py           # Module 2.20: Deduplication script
│   ├── string_cleaning.py             # Module 2.21: Text normalisation engine
│   ├── datetime_feature_engineering.py# Module 2.22: Date features & intervals
│   ├── outlier_detection.py           # Module 2.23: Outlier bounds & flagger
│   ├── data_validation.py             # Module 2.24: Rule consistency checks
│   ├── merge_validation.py            # Module 2.25: Multi-source join validation
│   ├── feature_engineering.py         # Module 2.26: Business features generator
│   └── run_pipeline.py                # Pipeline orchestrator
│
├── requirements.txt                   # Project package dependencies
├── README.md                          # Project documentation
└── .gitignore                         # Git exclusion rules
```

---

## ⚙️ Installation & Setup (Windows PowerShell)

Follow these steps to set up the environment and run the pipeline locally:

### 1. Clone the repository
```powershell
git clone https://github.com/kalviumcommunity/SW2627-Data-Product-Development-FinTech-Payment-Analysis.git
cd SW2627-Data-Product-Development-FinTech-Payment-Analysis
```

### 2. Set up Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## ▶️ Pipeline Execution

Run the complete pipeline from dataset intake validation through feature engineering:
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/run_pipeline.py
```
This orchestrator automatically invokes all 14 stages, prints structured checklists to the console, generates output reports under `output/`, and exports the final file `data/processed/final_fintech_dataset.csv`.

---

## 🔍 Preprocessing Modules Breakdown

### 1. Dataset Intake & Source Validation (`dataset_intake_validation.py`)
Validates whether incoming datasets are ready for ingestion. Checks file existence, formats, encoding, parsability, column count, and searches for missing required transaction columns.

### 2. Ingestion (`data_ingestion.py`)
Loads CSV and JSON datasets into Pandas DataFrames. Flattens nested JSON records using `pd.json_normalize()` and runs basic structural checks.

### 3. Dataset Profiling (`dataset_profiling.py`)
Profiles the raw data before modification, summarizing dataset dimensions, missing percentages, duplicate row counts, and data types.

### 4. Data Dictionary (`data_dictionary.py`)
Generates metadata mapping for all 13 transaction fields, defining business roles, expected formats, and key KPI usages.

### 5. Missing Value Imputation (`handle_missing.py`)
Imputes missing fields using context-aware rules:
*   `Amount` / `Retry_Count` / `Response_Code` → Filled with median values.
*   `Payment_Method` / `Bank_Name` / `Final_Status` → Filled with mode values.
*   `Failure_Type` → Infilled with "No Failure" if transaction succeeded.
*   `Retry_Time` → Kept null if no retry occurred (`Retry_Count` = 0), otherwise infilled with `Transaction_Time` + median retry delay. Prevents negative retry durations.

### 6. Deduplication (`handle_duplicates.py`)
Identifies and audits exact row duplicates and primary key (`Transaction_ID`) collisions, removing exact duplicate entries.

### 7. String Cleaning (`string_cleaning.py`)
Cleans text spacing, normalizes casing, handles special characters via regex, and maps variable representations (e.g. `credit card` / `credit-card` → `Credit Card`).

### 8. Date & Time Transformation (`datetime_feature_engineering.py`)
Parses transaction timestamps, extracts calendar indicators (Hour, Day, Month, Week), and calculates `Retry_Delay_Minutes` and transaction recency.

### 9. Outlier Detection (`outlier_detection.py`)
Computes Q1, Q3, and IQR boundaries to identify outliers in amounts and retries. Rather than deleting financial transactions, it adds logical outlier flags.

### 10. Data Consistency Validation (`data_validation.py`)
Enforces 7 transaction rules (e.g. positive amounts, chronological retry order, status category checks), isolating violations to [`validation_failures.csv`](file:///c:/Users/saray/OneDrive/Desktop/Fintech/output/validation_failures.csv).

### 11. Multi-Source Merging (`merge_validation.py`)
Joins validated transaction records with the Customer Master (`customers.csv`). Audits cardinality and isolates unmatched records to unmatched CSV files.

### 12. Feature Engineering (`feature_engineering.py`)
Derives 7 business-relevant columns:
*   `Transaction_Value_Tier` (Low, Medium, High)
*   `Retry_Intensity` (No, Low, High Retry)
*   `Retry_Recovery_Status` (No Retry, Recovered, Failed after retry)
*   `Revenue_Status` (No Loss vs Revenue Lost)
*   `Payment_Friction_Category` (Low, Medium, High Friction)
*   `Retry_Delay_Category` (Short, Medium, Long Delay)
*   `Risk_Score` (Weighted calculation based on failure, retry intensity, and leakage)

---

## 📈 Key Performance Indicators (KPIs) Computed
*   **Payment Success Rate:** Transactions ending in 'Success' / Total transactions.
*   **Failure Rate:** Transactions ending in 'Failed' / Total transactions.
*   **Retry Rate:** Transactions containing at least one retry attempt / Total transactions.
*   **Retry Recovery Rate:** Failed payments successfully resolved on subsequent retries.
*   **Revenue Lost:** Total transaction value representing permanently lost revenue.
*   **Average Retry Delay:** Average time duration elapsed between initial failure and retry.
