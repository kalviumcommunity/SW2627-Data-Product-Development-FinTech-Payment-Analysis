import os
import pandas as pd

# =====================================================
# Load Dataset
# =====================================================

file_path = "data/processed/datatype_validated.csv"

if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit()

df = pd.read_csv(file_path)

print("=" * 70)
print("DATE & TIME TRANSFORMATION PIPELINE")
print("=" * 70)

# =====================================================
# Parse Date Columns
# =====================================================

date_columns = ["Transaction_Time", "Retry_Time"]

for col in date_columns:
    if col in df.columns:
        print(f"\nParsing {col}...")

        # Automatically detect the format
        df[col] = pd.to_datetime(df[col], errors="coerce")

        print(f"Valid Dates : {df[col].notna().sum()}")
        print(f"Invalid Dates : {df[col].isna().sum()}")

print("\nData Types")
print(df[date_columns].dtypes)

# Remove rows where Transaction_Time is invalid
rows_before = len(df)

df = df.dropna(subset=["Transaction_Time"])

rows_after = len(df)

print(f"\nRows Before : {rows_before}")
print(f"Rows After  : {rows_after}")
print(f"Rows Removed: {rows_before - rows_after}")

# =====================================================
# Feature Engineering
# =====================================================

print("\nExtracting Date Features...")

df["Day_of_Week"] = df["Transaction_Time"].dt.day_name()
df["Hour"] = df["Transaction_Time"].dt.hour
df["Month"] = df["Transaction_Time"].dt.month_name()
df["Week_Number"] = df["Transaction_Time"].dt.isocalendar().week
df["Year"] = df["Transaction_Time"].dt.year

print("Done.")

# =====================================================
# Retry Delay
# =====================================================

if "Retry_Time" in df.columns:

    df["Retry_Delay_Minutes"] = (
        df["Retry_Time"] -
        df["Transaction_Time"]
    ).dt.total_seconds() / 60

print("Retry Delay Created.")

# =====================================================
# Days Since Transaction
# =====================================================

today = pd.Timestamp.now()

df["Days_Since_Transaction"] = (
    today -
    df["Transaction_Time"]
).dt.days

print("Days Since Transaction Created.")

# =====================================================
# Hourly Volume
# =====================================================

print("\nHourly Transaction Volume")

hourly = df.groupby("Hour").size()

print(hourly)

# =====================================================
# Revenue By Day
# =====================================================

if "Amount" in df.columns:

    print("\nRevenue by Day")

    revenue_day = df.groupby("Day_of_Week")["Amount"].sum()

    print(revenue_day)

# =====================================================
# Weekly Revenue
# =====================================================

if "Amount" in df.columns:

    print("\nWeekly Revenue")

    weekly = (
        df
        .set_index("Transaction_Time")
        .resample("W")["Amount"]
        .sum()
    )

    print(weekly)

# =====================================================
# Payment Method Analysis
# =====================================================

if "Payment_Method" in df.columns:

    print("\nPayment Method Analysis")

    payment = df.groupby("Payment_Method")["Amount"].agg(
        ["count", "sum", "mean"]
    )

    print(payment)

# =====================================================
# Failure Analysis
# =====================================================

if "Failure_Type" in df.columns:

    print("\nFailure Types")

    print(df["Failure_Type"].value_counts())

# =====================================================
# Peak Window
# =====================================================

if "Amount" in df.columns:

    print("\nHour × Day Revenue")

    pivot = pd.pivot_table(
        df,
        values="Amount",
        index="Hour",
        columns="Day_of_Week",
        aggfunc="sum"
    )

    print(pivot)

# =====================================================
# Save
# =====================================================

output = "data/processed/datetime_feature_engineered.csv"

df.to_csv(output, index=False)

print("\n" + "=" * 70)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)
print("Saved to:", output)