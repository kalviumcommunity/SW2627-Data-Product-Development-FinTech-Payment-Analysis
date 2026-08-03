import pandas as pd
import os

# Load dataset
file_path = "data/processed/cleaned_sample_10k.csv"

if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit()

df = pd.read_csv(file_path)

print("="*60)
print("STRING CLEANING")
print("="*60)

# String columns
string_columns = [
    "Payment_Method",
    "Bank_Name",
    "Response_Message",
    "Final_Status",
    "Failure_Type"
]

for col in string_columns:
    if col in df.columns:
        print(f"\nCleaning column: {col}")

        # Remove leading/trailing spaces
        df[col] = df[col].astype(str).str.strip()

        # Convert to lowercase
        df[col] = df[col].str.lower()

        # Remove special characters
        df[col] = df[col].str.replace(r'[^a-zA-Z0-9 ]', '', regex=True)

        # Remove multiple spaces
        df[col] = df[col].str.replace(r'\s+', ' ', regex=True)

        print(df[col].unique()[:10])

# Save
output = "data/processed/string_cleaned_data.csv"
df.to_csv(output, index=False)

print("\nString cleaning completed.")
print("Saved to:", output)