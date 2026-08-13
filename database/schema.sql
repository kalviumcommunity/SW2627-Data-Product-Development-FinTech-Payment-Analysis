-- Fintech Payment Analysis Schema
-- Automatically generated schema file

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    segment TEXT,
    transaction_count INTEGER,
    total_spend REAL,
    avg_spend REAL,
    days_since_first_txn REAL
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT,
    amount REAL,
    payment_method TEXT,
    bank_name TEXT,
    response_code REAL,
    response_message TEXT,
    retry_count REAL,
    transaction_time TEXT,
    retry_time TEXT,
    final_status TEXT,
    failure_type TEXT,
    revenue_lost REAL,
    calculated_fee REAL,
    net_amount REAL,
    calculated_discount REAL,
    transaction_score REAL,
    risk_level TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);
