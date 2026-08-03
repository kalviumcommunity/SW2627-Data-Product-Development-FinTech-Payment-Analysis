import pandas as pd
import os

file_path = "data/processed/string_cleaned_data.csv"

if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit()

df = pd.read_csv(file_path)

print("="*60)
print("DATA TYPE VALIDATION")
print("="*60)

print("\nCurrent Data Types:\n")
print(df.dtypes)

print("\nConverting Data Types...")

# Numeric columns
numeric_columns = [
    "Amount",
    "Response_Code",
    "Retry_Count",
    "Revenue_Lost"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Datetime columns
datetime_columns = [
    "Transaction_Time",
    "Retry_Time"
]

for col in datetime_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

print("\nUpdated Data Types:\n")
print(df.dtypes)

output = "data/processed/datatype_validated.csv"
df.to_csv(output, index=False)

print("\nSaved to:", output)