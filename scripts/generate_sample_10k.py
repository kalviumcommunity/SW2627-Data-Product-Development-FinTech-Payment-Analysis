"""
Generate a realistic 10k-row fintech transaction dataset with missing values.
Matches real payment transaction structure with various null patterns.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
N_ROWS = 10000
PAYMENT_METHODS = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet']
BANKS = ['BOB', 'ICICI', 'IndusInd', 'Canara', 'Yes Bank', 'PNB', 'HDFC', 'Axis']
RESPONSE_CODES = ['00', '08', '12', '51', '54', '55', '68', '96']
RESPONSE_MESSAGES = [
    'Approved', 'Network Error', 'Invalid Amount', 'Insufficient Funds', 
    'Card Declined', 'Expired Card', 'Response Timeout', 'System Error'
]
STATUSES = ['Success', 'Failed', 'Pending']
FAILURE_TYPES = ['Temporary', 'Permanent', 'Unknown']

# Generate Transaction IDs
txn_ids = [f"TXN{100000+i}" for i in range(N_ROWS)]

# Generate Customer IDs (format: C####)
customer_ids = [f"C{np.random.randint(1000, 9999)}" for _ in range(N_ROWS)]

# Generate Amounts - mostly present, some missing (~8%)
amount_missing_pct = 0.08
amounts = [np.random.randint(500, 100000) if np.random.random() > amount_missing_pct else None 
           for _ in range(N_ROWS)]

# Generate Payment Methods - mostly present, sparse missing (~5%)
payment_missing_pct = 0.05
payment_methods = [np.random.choice(PAYMENT_METHODS) if np.random.random() > payment_missing_pct else None 
                   for _ in range(N_ROWS)]

# Generate Bank Names - depends on payment method, some missing (~10%)
bank_missing_pct = 0.10
bank_names = []
for pm in payment_methods:
    if pm is None or np.random.random() < bank_missing_pct:
        bank_names.append(None)
    else:
        bank_names.append(np.random.choice(BANKS))

# Generate Response Codes - mostly present, some missing (~7%)
response_code_missing_pct = 0.07
response_codes = [np.random.choice(RESPONSE_CODES) if np.random.random() > response_code_missing_pct else None 
                  for _ in range(N_ROWS)]

# Generate Response Messages - based on codes, some missing (~8%)
response_msg_missing_pct = 0.08
response_messages = [np.random.choice(RESPONSE_MESSAGES) if np.random.random() > response_msg_missing_pct else None 
                     for _ in range(N_ROWS)]

# Generate Retry Counts - mostly present (~5% missing)
retry_missing_pct = 0.05
retry_counts = [np.random.randint(0, 5) if np.random.random() > retry_missing_pct else None 
                for _ in range(N_ROWS)]

# Generate Transaction Times - all present (critical)
base_date = datetime(2026, 1, 1)
txn_times = [base_date + timedelta(days=np.random.randint(0, 365), hours=np.random.randint(0, 24), 
                                   minutes=np.random.randint(0, 60))
             for _ in range(N_ROWS)]
txn_time_strings = [t.strftime('%Y-%m-%d %H:%M') for t in txn_times]

# Generate Retry Times - only if retries > 0, some missing (~15%)
retry_time_missing_pct = 0.15
retry_times = []
for i, rc in enumerate(retry_counts):
    if rc is None or rc == 0 or np.random.random() < retry_time_missing_pct:
        retry_times.append(None)
    else:
        retry_offset = np.random.randint(1, 60)  # retry happens 1-60 min later
        retry_time = txn_times[i] + timedelta(minutes=retry_offset)
        retry_times.append(retry_time.strftime('%Y-%m-%d %H:%M'))

# Generate Final Status - mostly Success, some Failed, sparse Pending (~10% missing)
final_status_missing_pct = 0.10
final_statuses = [np.random.choice(STATUSES, p=[0.85, 0.12, 0.03]) 
                  if np.random.random() > final_status_missing_pct else None 
                  for _ in range(N_ROWS)]

# Generate Failure Types - only when status is Failed, some missing (~12%)
failure_type_missing_pct = 0.12
failure_types = []
for fs in final_statuses:
    if fs == 'Failed' and np.random.random() > failure_type_missing_pct:
        failure_types.append(np.random.choice(FAILURE_TYPES))
    else:
        failure_types.append(None)

# Generate Revenue Lost - only when status is Failed and failure type is Permanent
revenue_lost = []
for i, fs in enumerate(final_statuses):
    if fs == 'Failed' and failure_types[i] == 'Permanent' and amounts[i] is not None:
        revenue_lost.append(amounts[i])
    else:
        revenue_lost.append(0)

# Create DataFrame
df = pd.DataFrame({
    'Transaction_ID': txn_ids,
    'Customer_ID': customer_ids,
    'Amount': amounts,
    'Payment_Method': payment_methods,
    'Bank_Name': bank_names,
    'Response_Code': response_codes,
    'Response_Message': response_messages,
    'Retry_Count': retry_counts,
    'Transaction_Time': txn_time_strings,
    'Retry_Time': retry_times,
    'Final_Status': final_statuses,
    'Failure_Type': failure_types,
    'Revenue_Lost': revenue_lost
})

# Save to CSV
output_path = os.path.join('data', 'raw', 'sample_10k.csv')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_csv(output_path, index=False)

print(f"✓ Generated {N_ROWS} fintech transaction rows with missing values")
print(f"✓ Saved to {output_path}")
print(f"\nDataset summary:")
print(df.info())
print(f"\nNull counts by column:")
print(df.isnull().sum())
print(f"\nNull percentages:")
print((df.isnull().sum() / len(df) * 100).round(2))
