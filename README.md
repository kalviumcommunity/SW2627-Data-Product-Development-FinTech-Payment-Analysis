# 💳 FinTech Payment Analytics Dashboard

An end-to-end **Data Analytics Product** that helps finance teams analyze payment transactions, identify temporary payment failures, detect permanently lost revenue, and generate actionable business insights through an interactive dashboard.

---

## 📌 Project Overview

FinTech platforms process thousands of digital payment transactions every day. Payment retries, bank response codes, and transaction timestamps are often stored separately, making it difficult for finance teams to understand whether a failed payment was eventually recovered or resulted in permanent revenue loss.

This project integrates multiple datasets, cleans and transforms the data, calculates business KPIs, and visualizes insights using an interactive **Streamlit Dashboard**.

---

## 🎯 Problem Statement

Finance teams cannot easily distinguish between:

* Temporary payment friction (payments that succeed after retries)
* Permanently lost revenue (payments that never succeed)

Without a unified analytics platform, organizations struggle to measure revenue loss, analyze payment failures, and improve payment recovery strategies.

---

## 🚀 Features

* Upload payment datasets (CSV)
* Data validation and preprocessing
* Missing value handling
* Duplicate removal
* Feature engineering
* SQL-based business analytics
* KPI calculation
* Interactive Plotly visualizations
* Payment failure classification
* Revenue recovery analysis
* Downloadable reports

---

## 🛠️ Tech Stack

| Category             | Technology         |
| -------------------- | ------------------ |
| Programming Language | Python             |
| Data Processing      | Pandas, NumPy      |
| Database             | PostgreSQL         |
| Query Language       | SQL                |
| Dashboard            | Streamlit          |
| Visualization        | Plotly             |
| Version Control      | Git & GitHub       |
| IDE                  | Visual Studio Code |

---

## 📂 Project Structure

```text
FinTech-Payment-Analytics/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│
├── src/
│   ├── data_loader.py
│   ├── cleaning.py
│   ├── feature_engineering.py
│   ├── analytics.py
│   └── visualization.py
│
├── database/
│   └── schema.sql
│
├── reports/
├── assets/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/FinTech-Payment-Analytics.git
cd FinTech-Payment-Analytics
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser.

---

## 📊 Datasets

### transactions.csv

Contains transaction details.

Columns:

* transaction_id
* customer_id
* amount
* payment_method
* status
* transaction_time

### payment_attempts.csv

Contains retry history.

Columns:

* attempt_id
* transaction_id
* attempt_number
* response_code
* attempt_time

### bank_response_codes.csv

Maps bank response codes to business meaning.

Columns:

* response_code
* description
* category

---

## 📈 Key Performance Indicators (KPIs)

* Total Transactions
* Successful Payments
* Failed Payments
* Retry Rate
* Recovery Rate
* Revenue Recovered
* Lost Revenue
* Average Retry Count
* Top Failure Reasons
* Bank-wise Failure Rate

---

## 📱 Dashboard Modules

* Dashboard
* Transactions
* Revenue Analytics
* Failure Analysis
* Upload Dataset
* Reports
* Settings

---

## 🔄 Workflow

```text
Upload Dataset
        ↓
Data Validation
        ↓
Data Cleaning
        ↓
Feature Engineering
        ↓
Database (PostgreSQL)
        ↓
SQL Analytics
        ↓
Plotly Visualizations
        ↓
Streamlit Dashboard
```

---

## 👥 Team Members

| Name     | Responsibility                               |
| -------- | -------------------------------------------- |
| Member 1 | Data Cleaning & Feature Engineering          |
| Member 2 | Database Design & SQL Analytics              |
| Member 3 | Dashboard Development, UI/UX & Documentation |

---

## 🌟 Future Enhancements

* Machine Learning for payment failure prediction
* Fraud detection
* Real-time payment monitoring
* Email notifications
* Cloud deployment (AWS/Azure)
* REST API integration
* Role-based authentication

---

## 📄 License

This project is developed for academic purposes as part of the **Kalvium End-to-End Data Product** course.

---

## 🙏 Acknowledgements

* Kalvium
* Streamlit
* Plotly
* Pandas
* NumPy
* PostgreSQL
* Open Source Community
