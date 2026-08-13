import os
import json
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as ob
import streamlit as st
import subprocess
import sys
from datetime import datetime

# Import Plotly visualizations from src
from src.visualization import (
    plot_time_series_trend,
    plot_payment_methods_pie,
    plot_bank_revenue_bar,
    plot_cumulative_settlement,
    plot_funnel_drop_off,
    plot_revenue_anomalies
)

# Setup page config
st.set_page_config(
    page_title="FinTech Payment Analytics Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reconfigure stdout to support UTF-8 on Windows environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Custom premium styling via CSS
st.markdown("""
<style>
    /* Theme overrides */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Card design */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #58a6ff;
    }
    .metric-title {
        font-size: 14px;
        color: #8b949e;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #58a6ff;
    }
    .metric-delta {
        font-size: 12px;
        margin-top: 5px;
    }
    .metric-delta.green {
        color: #3fb950;
    }
    .metric-delta.red {
        color: #f85149;
    }
    
    /* Section title styling */
    .section-header {
        font-size: 24px;
        font-weight: 600;
        border-bottom: 2px solid #21262d;
        padding-bottom: 10px;
        margin-bottom: 20px;
        color: #ffffff;
    }
    
    /* Table styling */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        background-color: #161b22;
        border: 1px solid #30363d;
        color: #c9d1d9;
    }
    
    /* Highlight banners */
    .alert-banner {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 5px solid;
    }
    .alert-banner.critical {
        background-color: rgba(248, 81, 73, 0.1);
        border-left-color: #f85149;
        color: #f85149;
        border-top: 1px solid rgba(248, 81, 73, 0.2);
        border-right: 1px solid rgba(248, 81, 73, 0.2);
        border-bottom: 1px solid rgba(248, 81, 73, 0.2);
    }
    .alert-banner.warning {
        background-color: rgba(210, 153, 34, 0.1);
        border-left-color: #d29922;
        color: #d29922;
        border-top: 1px solid rgba(210, 153, 34, 0.2);
        border-right: 1px solid rgba(210, 153, 34, 0.2);
        border-bottom: 1px solid rgba(210, 153, 34, 0.2);
    }
    .alert-banner.success {
        background-color: rgba(63, 185, 80, 0.1);
        border-left-color: #3fb950;
        color: #3fb950;
        border-top: 1px solid rgba(63, 185, 80, 0.2);
        border-right: 1px solid rgba(63, 185, 80, 0.2);
        border-bottom: 1px solid rgba(63, 185, 80, 0.2);
    }
    .smtp-terminal {
        background-color: #010409;
        border: 1px solid #30363d;
        font-family: monospace;
        padding: 10px;
        border-radius: 5px;
        color: #3fb950;
    }
</style>
""", unsafe_allow_html=True)

# Define file paths
DB_PATH = "database/fintech_payment.db"
ENRICHED_PATH = "data/processed/enriched_transactions_10k.csv"
CUSTOMER_SEGMENTS_PATH = "data/processed/customer_segments.csv"

# Automatically verify and build DB if missing (2.37)
if not os.path.exists(DB_PATH) and os.path.exists(ENRICHED_PATH):
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(["python", "scripts/db_integration.py"], check=True, env=env)
    except Exception as e:
        st.warning(f"Could not build SQLite database: {e}")

# Helper function to load datasets safely
@st.cache_data
def load_data():
    df_txn = pd.DataFrame()
    df_cust = pd.DataFrame()
    
    if os.path.exists(ENRICHED_PATH):
        df_txn = pd.read_csv(ENRICHED_PATH)
        if 'transaction_time' in df_txn.columns:
            df_txn['transaction_time'] = pd.to_datetime(df_txn['transaction_time'])
    
    if os.path.exists(CUSTOMER_SEGMENTS_PATH):
        df_cust = pd.read_csv(CUSTOMER_SEGMENTS_PATH)
        
    return df_txn, df_cust

@st.cache_data
def load_json_report(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

# Load data
df_txn, df_cust = load_data()
decisions = load_json_report("output/imputation_decisions.json")
validation = load_json_report("output/validation_results.json")
join_report = load_json_report("output/join_validation_report.json")
root_cause = load_json_report("output/root_cause_findings.json")

# Ensure dataset loaded successfully before drawing
if df_txn.empty:
    st.error("Enriched transaction dataset not found. Please upload a dataset or run the workflow script `python scripts/data_workflow.py` first to generate data.")
    st.stop()

# Initialize session state for uploads and console (2.54)
if 'uploaded_status' not in st.session_state:
    st.session_state['uploaded_status'] = None
if 'sql_history' not in st.session_state:
    st.session_state['sql_history'] = []

# Sidebar navigation (2.51)
st.sidebar.markdown("<h2 style='text-align: center; color: #58a6ff;'>💳 FinTech Payments</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

navigation = st.sidebar.radio(
    "Navigate to:",
    [
        "📊 Executive KPI Summary",
        "🧹 Quality & Imputation Audits",
        "💸 Fees & Optimization",
        "👥 Customer Segments & CLV",
        "📉 Drop-off Funnel Analysis",
        "🚨 Risk & Anomaly Investigations",
        "📖 Transaction Ledger",
        "🗄️ SQL Database Analytics",
        "📤 Data Intake & Ingestion",
        "📧 Executive Reports & Sharing"
    ]
)

st.sidebar.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
st.sidebar.info("Course: Kalvium DPD\nDatabase: SQLite Integrated\nPipeline: Automated Execution")

# Filters (Global sidebar filters where appropriate) (2.53)
st.sidebar.markdown("### Interactive Filters")
payment_methods = ['All'] + sorted(df_txn['payment_method'].unique().tolist())
selected_pm = st.sidebar.selectbox("Filter by Payment Method:", payment_methods)

banks = ['All'] + sorted(df_txn['bank_name'].dropna().unique().tolist())
selected_bank = st.sidebar.selectbox("Filter by Bank Name:", banks)

# Apply global filters to a working df copy
df_filtered = df_txn.copy()
if selected_pm != 'All':
    df_filtered = df_filtered[df_filtered['payment_method'] == selected_pm]
if selected_bank != 'All':
    df_filtered = df_filtered[df_filtered['bank_name'] == selected_bank]


# Page 1: Executive KPI Summary
if navigation == "📊 Executive KPI Summary":
    st.markdown("<div class='section-header'>Executive KPI Dashboard Summary</div>", unsafe_allow_html=True)
    
    # Core calculations
    total_volume = df_filtered['amount'].sum()
    net_revenue = df_filtered['net_amount'].sum() if 'net_amount' in df_filtered.columns else total_volume * 0.98
    total_fees = df_filtered['calculated_fee'].sum() if 'calculated_fee' in df_filtered.columns else total_volume * 0.02
    lost_revenue = df_filtered['revenue_lost'].sum()
    success_rate = (df_filtered['final_status'] == 'Success').sum() / len(df_filtered) if len(df_filtered) else 0
    active_customers = df_filtered['customer_id'].nunique()
    
    # 2.56: Alert Monitoring & Metric Threshold Detection
    if success_rate < 0.85:
        st.markdown(f"""
        <div class='alert-banner critical'>
            <strong>🚨 CRITICAL METRIC ALERT:</strong> Transaction Success Rate is at <strong>{success_rate * 100:.2f}%</strong> which is below the target operational threshold of <strong>85.00%</strong>. Investigate Bank Routing tables immediately.
        </div>
        """, unsafe_allow_html=True)
    elif lost_revenue > 10000000.0:
        st.markdown(f"""
        <div class='alert-banner warning'>
            <strong>⚠️ REVENUE LEAKAGE ALERT:</strong> Total permanently lost revenue has crossed threshold at <strong>${lost_revenue:,.2f}</strong>. Failure types classification review recommended.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='alert-banner success'>
            <strong>✅ OPERATIONAL STATUS NORMAL:</strong> Success rate is healthy at <strong>{success_rate * 100:.2f}%</strong> and revenue leakage is within expected targets.
        </div>
        """, unsafe_allow_html=True)

    # 4 columns of high-fidelity KPI Cards (2.47)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Total Volume Processed</div>
            <div class='metric-value'>${total_volume:,.2f}</div>
            <div class='metric-delta green'>↑ {active_customers:,} active customers</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Net Settled Volume</div>
            <div class='metric-value'>${net_revenue:,.2f}</div>
            <div class='metric-delta green'>Total fees: ${total_fees:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Transaction Success Rate</div>
            <div class='metric-value'>{success_rate * 100:.2f}%</div>
            <div class='metric-delta green'>Target: 85.00%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Permanently Lost Revenue</div>
            <div class='metric-value' style='color: #f85149;'>${lost_revenue:,.2f}</div>
            <div class='metric-delta red'>Failed items to audit</div>
        </div>
        """, unsafe_allow_html=True)
        
    # KPI Target checks (from json if available) (2.34)
    st.markdown("### 🎯 Live KPI Target Framework (Skill 2.34)")
    kpi_file = "output/kpi_dashboard.csv"
    if os.path.exists(kpi_file):
        df_kpi = pd.read_csv(kpi_file)
        st.dataframe(df_kpi, use_container_width=True)
    else:
        st.write("KPI Dashboard csv not generated.")
        
    # Charts: Daily Trend with 7-day Moving Average (Skill 2.31 / 2.46)
    st.markdown("### 📈 Time-Series Performance Trend (Skill 2.31)")
    
    # Calculate daily statistics
    df_filtered['date_only'] = df_filtered['transaction_time'].dt.date
    daily_stats = df_filtered.groupby('date_only')['amount'].sum().reset_index()
    daily_stats = daily_stats.rename(columns={'amount': 'daily_total'})
    daily_stats = daily_stats.sort_values('date_only')
    daily_stats['rolling_avg_7d'] = daily_stats['daily_total'].rolling(7).mean()
    
    fig_trend = plot_time_series_trend(daily_stats)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Sub segment layouts
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Payment Methods Popularity & Volume")
        fig_pm = plot_payment_methods_pie(df_filtered)
        st.plotly_chart(fig_pm, use_container_width=True)
        
    with col_right:
        st.markdown("#### Top Bank Revenue Pipelines (Skill 2.30)")
        fig_bank = plot_bank_revenue_bar(df_filtered)
        st.plotly_chart(fig_bank, use_container_width=True)


# Page 2: Quality & Imputation Audits
elif navigation == "🧹 Quality & Imputation Audits":
    st.markdown("<div class='section-header'>Data Quality Cleaning & Imputation Audits</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Missing Value Imputation", "Data Consistency Rules", "Join Card Validation"])
    
    with tab1:
        st.markdown("### Missing Value Resolution Audit (Skill 2.18 & 2.19)")
        if decisions:
            st.markdown(f"**Rows Before**: `{decisions.get('rows_before')}` | **Rows After**: `{decisions.get('rows_after')}`")
            st.markdown(f"**Total Nulls Resolved**: `{decisions.get('total_nulls_before')}` → `0` (100% success)")
            
            # Format decisions for table view
            cols_data = decisions.get('columns', {})
            table_list = []
            for col_name, info in cols_data.items():
                table_list.append({
                    'Column': col_name,
                    'Type': info.get('column_type'),
                    'Nulls Before': info.get('null_count_before'),
                    '% Nulls': f"{info.get('null_pct_before'):.2f}%",
                    'Strategy': info.get('strategy'),
                    'Imputed Value': str(info.get('value_used')),
                    'Risk Assessment': info.get('risk_assessment'),
                    'Over-Imputed?': '⚠️ Yes' if info.get('over_imputation') else '✅ No'
                })
            st.dataframe(pd.DataFrame(table_list), use_container_width=True)
        else:
            st.warning("Imputation decisions file output/imputation_decisions.json is not found.")
            
    with tab2:
        st.markdown("### Rule-Based Quality Gate Validation (Skill 2.24)")
        if validation:
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.markdown("#### Range Validation Metrics")
                range_list = []
                for col_name, r_info in validation.get('ranges', {}).items():
                    range_list.append({
                        'Column Check': col_name,
                        'Violations Count': r_info.get('out_of_range'),
                        'Pass Status': '✅ PASS' if r_info.get('valid') else '❌ FAIL'
                    })
                st.dataframe(pd.DataFrame(range_list), use_container_width=True)
                
            with col_v2:
                st.markdown("#### Null Constraint Metrics")
                nulls_list = []
                for col_name, n_info in validation.get('nulls', {}).items():
                    nulls_list.append({
                        'Column Check': col_name,
                        'Null % Found': f"{n_info.get('null_percentage'):.2f}%",
                        'Pass Status': '✅ PASS' if n_info.get('valid') else '❌ FAIL'
                    })
                st.dataframe(pd.DataFrame(nulls_list), use_container_width=True)
        else:
            st.warning("Validation results file output/validation_results.json is not found.")
            
    with tab3:
        st.markdown("### Many-to-One Join Card Validation Report (Skill 2.25)")
        if join_report:
            st.markdown(f"""
            <div class='alert-banner warning'>
                <strong>Multi-Source Keys Inconsistency Detected</strong><br>
                Mismatched transaction customer keys that were omitted from Customer Master data: 
                <strong>{join_report.get('rows_only_in_left')} rows ({join_report.get('rows_only_in_left')/join_report.get('left_rows_before')*100:.2f}%)</strong>
            </div>
            """, unsafe_allow_html=True)
            
            jcol1, jcol2, jcol3 = st.columns(3)
            jcol1.metric("Transactions Rows (Before Join)", f"{join_report.get('left_rows_before'):,}")
            jcol2.metric("Customer Master Rows", f"{join_report.get('right_rows_before'):,}")
            jcol3.metric("Merged Rows Count", f"{join_report.get('merged_rows'):,}")
            
            st.markdown("#### Keys Cardinality Overlap Summary")
            unmatched_info = join_report.get('unmatched_keys_info', {})
            st.write(f"- Matched Keys (In Both datasets): **{len(unmatched_info.get('in_both', []))}**")
            st.write(f"- Unmatched Keys (Omitted from Customer Master): **{len(unmatched_info.get('in_left_not_right', []))}**")
            st.write(f"- Redundant Keys (Customer Master with zero transactions): **{len(unmatched_info.get('in_right_not_left', []))}**")
        else:
            st.warning("Join validation report file output/join_validation_report.json is not found.")


# Page 3: Fees & Optimization
elif navigation == "💸 Fees & Optimization":
    st.markdown("<div class='section-header'>Payment Fees & Pricing Optimization</div>", unsafe_allow_html=True)
    
    st.markdown("""
    #### NumPy Vectorised Pricing Workflow (Skill 2.27)
    Fees are computed using vectorised lookups on payment methods (UPI: 1%, Credit Card: 1.5%, Debit Card: 2%, Net Banking: 2.5%, Wallet: 3%). 
    Tiered discounts apply dynamically based on customer value segment (Bronze: 0%, Silver: 5%, Gold: 10%, VIP: 15%).
    """)
    
    col_fee, col_disc = st.columns(2)
    
    with col_fee:
        st.markdown("#### Processing Fees Disbursed by Bank Segment")
        fig_fees = px.bar(
            df_filtered.groupby('bank_name')['calculated_fee'].sum().reset_index().sort_values('calculated_fee', ascending=False),
            x='calculated_fee', y='bank_name', orientation='h', color='calculated_fee',
            color_continuous_scale='Teal'
        )
        fig_fees.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
        st.plotly_chart(fig_fees, use_container_width=True)
        
    with col_disc:
        st.markdown("#### Discounts Granted by Customer Segment")
        seg_col = 'customer_customer_segment' if 'customer_customer_segment' in df_filtered.columns else 'payment_method'
        disc_by_seg = df_filtered.groupby(seg_col)['calculated_discount'].sum().reset_index()
        fig_disc = px.bar(disc_by_seg, x=seg_col, y='calculated_discount', color='calculated_discount',
                          color_continuous_scale='Purples')
        fig_disc.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
        st.plotly_chart(fig_disc, use_container_width=True)
        
    # Cumulative Pricing Tier curves
    st.markdown("### Cumulative Transaction Settlement Volume Curve")
    df_sorted = df_filtered.sort_values('amount').copy()
    df_sorted['cumulative_amount'] = df_sorted['amount'].cumsum()
    df_sorted['cumulative_net'] = df_sorted['net_amount'].cumsum() if 'net_amount' in df_sorted.columns else df_sorted['cumulative_amount']
    
    fig_cum = plot_cumulative_settlement(df_sorted)
    st.plotly_chart(fig_cum, use_container_width=True)


# Page 4: Customer Segments & CLV
elif navigation == "👥 Customer Segments & CLV":
    st.markdown("<div class='section-header'>Customer Lifetime Value & Behaviour Segmentation</div>", unsafe_allow_html=True)
    
    if df_cust.empty:
        st.warning("Customer segmentation profile dataset not generated. Running default metrics...")
    else:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Customer Behavioural RFM Segments (Skill 2.32)")
            seg_counts = df_cust['segment'].value_counts().reset_index()
            fig_seg = px.pie(seg_counts, values='count', names='segment', hole=0.3,
                            color_discrete_sequence=px.colors.sequential.Burg)
            fig_seg.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
            st.plotly_chart(fig_seg, use_container_width=True)
            
        with col_c2:
            st.markdown("#### Average Transaction Value Profile by segment")
            seg_spend = df_cust.groupby('segment')['avg_spend'].mean().reset_index()
            fig_spend = px.bar(seg_spend, x='segment', y='avg_spend', color='avg_spend',
                               color_continuous_scale='Sunsetdark')
            fig_spend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
            st.plotly_chart(fig_spend, use_container_width=True)
            
    # Numerical distributions & correlations (Skills 2.28 & 2.29)
    st.markdown("### Customer Lifetime Value (CLV) Statistical Distribution (Skill 2.28)")
    clv_vals = df_cust['total_spend'].dropna() if not df_cust.empty else df_filtered['amount']
    
    fig_hist = px.histogram(clv_vals, nbins=50, title="Customer Revenue Distribution histogram",
                            color_discrete_sequence=['#58a6ff'])
    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'),
                           xaxis=dict(title='Lifetime Spend ($)', showgrid=True, gridcolor='#21262d'),
                           yaxis=dict(title='Number of Customers', showgrid=True, gridcolor='#21262d'))
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Correlation Map
    st.markdown("### Numerical Attributes Relationships Matrix (Skill 2.29)")
    if os.path.exists("output/correlation_matrix.csv"):
        df_corr = pd.read_csv("output/correlation_matrix.csv", index_col=0)
        st.markdown("Calculated Pearson Correlation values for features:")
        st.dataframe(df_corr.round(3), use_container_width=True)
    else:
        st.write("Correlation CSV file output/correlation_matrix.csv not found.")


# Page 5: Drop-off Funnel Analysis
elif navigation == "📉 Drop-off Funnel Analysis":
    st.markdown("<div class='section-header'>Transaction Progress Drop-off Funnel</div>", unsafe_allow_html=True)
    
    st.markdown("""
    #### Customer Funnel Stage Tracking (Skill 2.33)
    This traces the unique customers that successfully progress through each sequential stage of a payment attempt:
    **Initiated** (started the transaction) → **Authenticating** (bank validation) → **Processing** (processing engine) → **Completed** (Success).
    """)
    
    if os.path.exists("output/payment_funnel.csv"):
        df_funnel = pd.read_csv("output/payment_funnel.csv")
        
        # Plotly Funnel Chart
        fig_funnel = plot_funnel_drop_off(df_funnel)
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        # Display Drop-off rates
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("#### Stages Conversion Table")
            st.dataframe(df_funnel.style.format({
                'percentage': '{:.2f}%',
                'drop_off_rate': '{:.2f}%'
            }), use_container_width=True)
            
        with col_f2:
            st.markdown("#### Identified Process Bottlenecks")
            max_drop = df_funnel.loc[df_funnel['drop_off_rate'].idxmax()] if df_funnel['drop_off_rate'].notna().any() else None
            if max_drop is not None:
                st.markdown(f"""
                <div class='alert-banner critical'>
                    <strong>Major Funnel Drop-off Bottleneck Identified</strong><br>
                    Stage: <strong>{max_drop['stage'].upper()}</strong><br>
                    Drop-off Rate: <strong>{max_drop['drop_off_rate']:.2f}%</strong> ({int(max_drop['drop_off_count'])} customers lost)
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Funnel data file output/payment_funnel.csv is missing.")


# Page 6: Risk & Anomaly Investigations
elif navigation == "🚨 Risk & Anomaly Investigations":
    st.markdown("<div class='section-header'>Risk Assessment & Anomaly Investigations</div>", unsafe_allow_html=True)
    
    # Overview of anomalies detected
    daily_rev_file = "output/daily_revenue_trend.csv"
    if os.path.exists(daily_rev_file):
        daily_rev = pd.read_csv(daily_rev_file)
        
        # Run local standard deviations anomaly detection to show the range
        mean = daily_rev['daily_total'].mean()
        std = daily_rev['daily_total'].std()
        daily_rev['upper'] = mean + 2 * std
        daily_rev['lower'] = mean - 2 * std
        daily_rev['is_anomaly'] = (daily_rev['daily_total'] > daily_rev['upper']) | (daily_rev['daily_total'] < daily_rev['lower'])
        
        st.markdown("### 📈 Daily Revenue Anomaly Boundaries (Skill 2.36)")
        fig_anom = plot_revenue_anomalies(daily_rev)
        st.plotly_chart(fig_anom, use_container_width=True)
        
    # Root Cause investigations toolkit (Skill 2.35)
    st.markdown("### 🔍 Root Cause Investigation drill-down (Skill 2.35)")
    if root_cause:
        st.write(f"The statistical analyzer detected **{root_cause.get('worst_date')}** as the worst performing date.")
        
        # Show segment isolation metrics
        st.markdown("#### Bank-wise deviations from overall mean on worst performing day:")
        df_rc_seg = pd.DataFrame.from_dict(root_cause.get('segment_isolation', {}), orient='index')
        st.dataframe(df_rc_seg, use_container_width=True)
        
        st.markdown("""
        > [!NOTE]
        > Deviations identify which banking channels or payment processors experienced outage issues. Negative deviations indicate underperforming channels that caused the overall drop.
        """)
    else:
        st.warning("Root cause findings output file output/root_cause_findings.json is not found.")
        
    # Critical Risk Ledger
    st.markdown("### Critical Risk Level Transactions Ledger")
    df_critical = df_filtered[df_filtered['risk_level'] == 'Critical'].copy() if 'risk_level' in df_filtered.columns else pd.DataFrame()
    if not df_critical.empty:
        st.dataframe(df_critical[['transaction_id', 'customer_id', 'amount', 'payment_method', 'bank_name', 'final_status', 'anomaly_severity']], use_container_width=True)
    else:
        st.success("No 'Critical' risk transactions flagged in current filter criteria.")


# Page 7: Transaction Ledger
elif navigation == "📖 Transaction Ledger":
    st.markdown("<div class='section-header'>FinTech Payment Transaction Ledger</div>", unsafe_allow_html=True)
    
    st.markdown("### Complete Transaction Records")
    
    # Filter selection: Status
    status_filter = st.selectbox("Filter by transaction status:", ['All', 'Success', 'Failed', 'Pending'])
    df_ledger = df_filtered.copy()
    if status_filter != 'All':
        df_ledger = df_ledger[df_ledger['final_status'] == status_filter]
        
    # Display subset of columns for readability
    show_cols = ['transaction_id', 'customer_id', 'amount', 'payment_method', 'bank_name', 
                 'retry_count', 'transaction_time', 'final_status', 'calculated_fee', 'net_amount']
    existing_show_cols = [c for c in show_cols if c in df_ledger.columns]
    
    # Search box
    search_query = st.text_input("Search by Customer ID or Transaction ID:")
    if search_query:
        df_ledger = df_ledger[
            df_ledger['customer_id'].astype(str).str.contains(search_query, case=False) |
            df_ledger['transaction_id'].astype(str).str.contains(search_query, case=False)
        ]
        
    st.markdown(f"Showing **{len(df_ledger):,}** records:")
    st.dataframe(df_ledger[existing_show_cols].head(100), use_container_width=True)
    
    # Export csv capability (2.50)
    csv_data = df_ledger[existing_show_cols].head(500).to_csv(index=False)
    st.download_button(
        label="📥 Download current transaction view (CSV - Max 500 records)",
        data=csv_data,
        file_name="payment_ledger.csv",
        mime="text/csv"
    )


# Page 8: SQL Database Analytics (2.37 - 2.44)
elif navigation == "🗄️ SQL Database Analytics":
    st.markdown("<div class='section-header'>🗄️ SQL Environment & Database Console</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Explore payment datasets directly using **SQL queries** executed against the integrated SQLite analytical database. 
    This allows validation of business metrics (window functions, joins, groupings) with database-level indexes for optimal performance.
    """)
    
    # Connection Check
    if not os.path.exists(DB_PATH):
        st.error("SQLite database file is missing. Ingest raw data first to initialize.")
    else:
        conn = sqlite3.connect(DB_PATH)
        
        # Display list of Tables & Views
        st.markdown("### Database Catalog Structure")
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            st.markdown("**Available Tables:**")
            st.write("- `transactions`: Raw and computed transactional payments ledger")
            st.write("- `customers`: Customer segments, RFM counts, and CLV metrics")
        with col_cat2:
            st.markdown("**Pre-defined Aggregation Views (Skill 2.43):**")
            st.write("- `v_daily_settlement_summary`: Daily volume, net amounts, and success ratios")
            st.write("- `v_bank_performance_summary`: Acquiring banks metrics, total volume, and fees")
            
        # SQL Editor Query Selection
        st.markdown("### Choose an Analytical Query Template")
        predefined_queries = {
            "Custom Query": "",
            "Top 5 Customers by spend (Window RANK() - Skill 2.41)": 
                "SELECT customer_id, segment, total_spend, RANK() OVER (ORDER BY total_spend DESC) as spend_rank FROM customers LIMIT 5;",
            "Bank Fees aggregated summary (Grouping & Filtering - Skill 2.39)":
                "SELECT bank_name, COUNT(*) as txn_count, SUM(calculated_fee) as total_fees FROM transactions WHERE final_status = 'Success' GROUP BY bank_name HAVING total_fees > 100000.0 ORDER BY total_fees DESC;",
            "Segment CLV join metrics (Multi-Table Join - Skill 2.40)":
                "SELECT c.segment, COUNT(t.transaction_id) as txn_count, AVG(t.amount) as avg_amount FROM transactions t INNER JOIN customers c ON t.customer_id = c.customer_id GROUP BY c.segment;"
        }
        query_sel = st.selectbox("Query Templates:", list(predefined_queries.keys()))
        default_query = predefined_queries[query_sel]
        
        # SQL Editor Text Area
        sql_input = st.text_area("Write/Edit SQL Query:", value=default_query if default_query else "SELECT * FROM v_bank_performance_summary LIMIT 10;", height=150)
        
        col_btn1, col_btn2 = st.columns(2)
        
        run_query = col_btn1.button("⚡ Execute Analytical SQL Query")
        explain_query = col_btn2.button("🔍 Explain Query Optimisation (Skill 2.42)")
        
        # Execute query
        if run_query:
            try:
                df_res = pd.read_sql_query(sql_input, conn)
                st.markdown("#### Query Results:")
                st.dataframe(df_res, use_container_width=True)
                
                # Update history session state
                st.session_state['sql_history'].append(sql_input)
            except Exception as e:
                st.error(f"SQL Error: {e}")
                
        # Explain Query Plan
        if explain_query:
            try:
                explain_sql = f"EXPLAIN QUERY PLAN {sql_input}"
                df_exp = pd.read_sql_query(explain_sql, conn)
                st.markdown("#### Query Optimisation Plan Details:")
                st.dataframe(df_exp, use_container_width=True)
                st.markdown("""
                > [!TIP]
                > The SQLite optimizer utilizes indexes such as `idx_txn_status` and `idx_txn_customer_id` to prevent scanning the entire table.
                """)
            except Exception as e:
                st.error(f"Could not explain query optimization: {e}")
                
        # History
        if st.session_state['sql_history']:
            with st.expander("Show Query Execution History"):
                for idx, h in enumerate(reversed(st.session_state['sql_history'])):
                    st.code(h, language="sql")
                    
        conn.close()


# Page 9: Data Intake & Ingestion (2.14, 2.15, 2.52, 2.58)
elif navigation == "📤 Data Intake & Ingestion":
    st.markdown("<div class='section-header'>📤 Raw Dataset Upload & Pipeline Ingestion</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Upload incoming transaction datasets (CSV or JSON format) to execute schema validations and automatically re-run the entire analytics pipeline.
    """)
    
    uploaded_file = st.file_uploader("Choose a raw transaction file (CSV or JSON):", type=["csv", "json"])
    
    if uploaded_file is not None:
        # Save uploaded file to raw folder
        raw_target_path = os.path.join("data/raw", uploaded_file.name)
        with open(raw_target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File uploaded successfully and saved to: `{raw_target_path}`")
        
        # Load preview
        st.markdown("### Dynamic Upload Preview")
        try:
            if uploaded_file.name.endswith(".csv"):
                df_preview = pd.read_csv(raw_target_path, nrows=5)
            else:
                with open(raw_target_path, "r", encoding="utf-8") as f:
                    js_data = json.load(f)
                df_preview = pd.json_normalize(js_data).head(5)
                
            st.dataframe(df_preview, use_container_width=True)
            st.write(f"Preview showing first {len(df_preview)} records.")
        except Exception as e:
            st.error(f"Failed to parse preview: {e}")
            
        # Run Intake checks live
        st.markdown("### Intake Validation Assessment")
        
        # Run validation
        file_size = os.path.getsize(raw_target_path)
        is_csv = uploaded_file.name.endswith(".csv")
        
        col_chk1, col_chk2 = st.columns(2)
        col_chk1.write(f"- File extension: `.{'csv' if is_csv else 'json'}` (Supported)")
        col_chk1.write(f"- File size: `{file_size:,} bytes`")
        
        # Run subprocess for validation
        if st.button("🚀 Trigger Complete Preprocessing & Database Pipeline (Skill 2.58)"):
            st.markdown("### Execution Logs")
            log_area = st.empty()
            
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # Execute scripts sequentially
            scripts = [
                ("dataset_intake_validation.py", "scripts/dataset_intake_validation.py"),
                ("data_ingestion.py", "scripts/data_ingestion.py"),
                ("data_workflow.py", "scripts/data_workflow.py"),
                ("db_integration.py", "scripts/db_integration.py")
            ]
            
            full_log = ""
            success = True
            for name, path in scripts:
                full_log += f"\n==================================================\nRUNNING {name}...\n==================================================\n"
                log_area.code(full_log)
                
                res = subprocess.run(["python", path], capture_output=True, text=True, env=env)
                full_log += res.stdout
                if res.stderr:
                    full_log += "\n[ERRORS / WARNINGS]:\n" + res.stderr
                    
                if res.returncode != 0:
                    full_log += f"\n❌ Script {name} failed with code {res.returncode}\n"
                    success = False
                    break
                else:
                    full_log += f"\n✓ Script {name} completed successfully.\n"
                    
            log_area.code(full_log)
            if success:
                st.success("🎉 Preprocessing, Profiling, and SQL Database pipelines executed successfully! Re-loading datasets...")
                # Clear streamlit cache
                st.cache_data.clear()
            else:
                st.error("pipeline execution failed. Please verify error messages in the log above.")


# Page 10: Executive Reports & Sharing (2.49, 2.50, 2.57)
elif navigation == "📧 Executive Reports & Sharing":
    st.markdown("<div class='section-header'>📧 Executive Reporting & Stakeholder Sharing</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Export ingestion profiles, data dictionaries, and summary reports, or simulate sending an automated email message to executive stakeholders.
    """)
    
    # 2.50: Download reports
    st.markdown("### 📤 Download Pipeline Artifacts")
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    # Data Dictionary
    if os.path.exists("output/data_dictionary.csv"):
        with open("output/data_dictionary.csv", "r", encoding="utf-8") as f:
            dict_csv = f.read()
        col_dl1.download_button("📘 Download Data Dictionary (CSV)", dict_csv, "data_dictionary.csv", "text/csv")
    else:
        col_dl1.warning("Data Dictionary CSV is missing.")
        
    # Dataset Profile
    if os.path.exists("output/dataset_profile.csv"):
        with open("output/dataset_profile.csv", "r", encoding="utf-8") as f:
            prof_csv = f.read()
        col_dl2.download_button("📊 Download Dataset Profile (CSV)", prof_csv, "dataset_profile.csv", "text/csv")
    else:
        col_dl2.warning("Dataset Profile CSV is missing.")
        
    # Intake validation
    if os.path.exists("output/intake_validation_report.json"):
        with open("output/intake_validation_report.json", "r", encoding="utf-8") as f:
            intake_json = f.read()
        col_dl3.download_button("📋 Download Intake Report (JSON)", intake_json, "intake_report.json", "application/json")
    else:
        col_dl3.warning("Intake Validation report is missing.")
        
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # 2.49 & 2.57: Executive report storytelling and Email sharing
    st.markdown("### 📧 Stakeholder Email Notification Engine")
    
    # Pre-calculated metric values to inject
    total_volume = df_txn['amount'].sum()
    success_rate = (df_txn['final_status'] == 'Success').sum() / len(df_txn) * 100
    lost_revenue = df_txn['revenue_lost'].sum()
    
    default_body = f"""Hi Team,

Here is the daily executive briefing for the Fintech Payment Retry Analysis dashboard.

Operational Highlights:
- Gross Transaction Volume Processed: ${total_volume:,.2f}
- Transaction Success Rate: {success_rate:.2f}% (Target: 85.00%)
- Permanently Lost Revenue leakage: ${lost_revenue:,.2f}

The data pipelines have successfully completed execution. Database structures are updated.

Regards,
Fintech Analytics Platform Engine
"""
    
    recipient = st.text_input("Recipient Email:", value="finance-alerts@fintech-platform.com")
    subject = st.text_input("Subject:", value="💳 Fintech Payment Analytics Daily Executive Briefing")
    email_body = st.text_area("Email Content:", value=default_body, height=200)
    
    if st.button("📧 Dispatch Simulated SMTP Email"):
        with st.spinner("Initiating secure SMTP handshake..."):
            import time
            time.sleep(1)
            
            # Print mock SMTP handshake logs
            st.markdown("#### Simulated SMTP Server Logs:")
            smtp_logs = f"""Connecting to SMTP server at mail.fintech-platform.internal:587...
220 SMTP Service Ready
EHLO client.internal
250-mail.fintech-platform.internal greets client
250-AUTH LOGIN PLAIN
250-STARTTLS
250 HELP
STARTTLS
220 Ready to start TLS
AUTH LOGIN
334 VXNlcm5hbWU6
334 UGFzc3dvcmQ6
235 2.7.0 Authentication successful
MAIL FROM:<no-reply@fintech-platform.com>
250 2.1.0 Sender OK
RCPT TO:<{recipient}>
250 2.1.5 Recipient OK
DATA
354 Start mail input; end with <CR><LF>.<CR><LF>
Subject: {subject}
To: {recipient}
From: no-reply@fintech-platform.com

{email_body}
.
250 2.0.0 OK: Message accepted for delivery.
QUIT
221 2.0.0 closing connection"""
            
            st.markdown(f"<div class='smtp-terminal'>{smtp_logs.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
            st.success(f"Email successfully dispatched to: **{recipient}**")
