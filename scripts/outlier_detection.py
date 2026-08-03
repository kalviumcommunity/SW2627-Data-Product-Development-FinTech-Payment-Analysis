import pandas as pd
import os

file_path = "data/processed/datatype_validated.csv"

if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit()

df = pd.read_csv(file_path)

print("="*60)
print("OUTLIER DETECTION")
print("="*60)

numeric_columns = [
    "Amount",
    "Retry_Count",
    "Revenue_Lost"
]

for col in numeric_columns:

    if col not in df.columns:
        continue

    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)

    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = df[(df[col] < lower) | (df[col] > upper)]

    print(f"\nColumn : {col}")
    print(f"Q1      : {Q1}")
    print(f"Q3      : {Q3}")
    print(f"IQR     : {IQR}")
    print(f"Lower   : {lower}")
    print(f"Upper   : {upper}")
    print(f"Outliers: {len(outliers)}")

print("\nOutlier detection completed.")