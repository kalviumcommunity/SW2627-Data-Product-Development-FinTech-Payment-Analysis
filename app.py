import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as ob
import streamlit as st

# Setup page config
st.set_page_config(
    page_title="FinTech Payment Analytics Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    }
    .alert-banner.warning {
        background-color: rgba(210, 153, 34, 0.1);
        border-left-color: #d29922;
        color: #d29922;
    }
    .alert-banner.success {
        background-color: rgba(63, 185, 80, 0.1);
        border-left-color: #3fb950;
        color: #3fb950;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load datasets safely
@st.cache_data
def load_data():
    enriched_path = "data/processed/enriched_transactions_10k.csv"
    customer_segments_path = "data/processed/customer_segments.csv"
    
    df_txn = pd.DataFrame()
    df_cust = pd.DataFrame()
    
    if os.path.exists(enriched_path):
        df_txn = pd.read_csv(enriched_path)
        # Parse datetime
        if 'transaction_time' in df_txn.columns:
            df_txn['transaction_time'] = pd.to_datetime(df_txn['transaction_time'])
    
    if os.path.exists(customer_segments_path):
        df_cust = pd.read_csv(customer_segments_path)
        
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
    st.error("Enriched transaction dataset not found. Please run the workflow script `python scripts/data_workflow.py` first to generate data.")
    st.stop()

# Sidebar navigation
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
        "📖 Transaction Ledger"
    ]
)

st.sidebar.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
st.sidebar.info("Course: Kalvium DPD\nTopics: 2.19 - 2.36\nDatabase: PostgreSQL ready")

# Filters (Global sidebar filters where appropriate)
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
    
    # 4 columns of high-fidelity KPI Cards
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
        
    # KPI Target checks (from json if available)
    st.markdown("### 🎯 Live KPI Target Framework (Skill 2.34)")
    kpi_file = "output/kpi_dashboard.csv"
    if os.path.exists(kpi_file):
        df_kpi = pd.read_csv(kpi_file)
        st.table(df_kpi)
    else:
        st.write("KPI Dashboard csv not generated.")
        
    # Charts: Daily Trend with 7-day Moving Average (Skill 2.31)
    st.markdown("### 📈 Time-Series Performance Trend (Skill 2.31)")
    
    # Calculate daily statistics
    df_filtered['date_only'] = df_filtered['transaction_time'].dt.date
    daily_stats = df_filtered.groupby('date_only')['amount'].sum().reset_index()
    daily_stats = daily_stats.rename(columns={'amount': 'daily_total'})
    daily_stats = daily_stats.sort_values('date_only')
    daily_stats['rolling_avg_7d'] = daily_stats['daily_total'].rolling(7).mean()
    
    fig_trend = ob.Figure()
    fig_trend.add_trace(ob.Scatter(
        x=daily_stats['date_only'], y=daily_stats['daily_total'],
        mode='lines', name='Daily Total Volume', line=dict(color='#58a6ff', width=1.5)
    ))
    fig_trend.add_trace(ob.Scatter(
        x=daily_stats['date_only'], y=daily_stats['rolling_avg_7d'],
        mode='lines', name='7-Day Moving Average', line=dict(color='#ff7b72', width=3, dash='dash')
    ))
    fig_trend.update_layout(
        title="Transaction Volume Daily Trend vs Rolling Average",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c9d1d9'),
        xaxis=dict(showgrid=True, gridcolor='#21262d'),
        yaxis=dict(showgrid=True, gridcolor='#21262d')
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Sub segment layouts
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Payment Methods Popularity & Volume")
        pm_stats = df_filtered.groupby('payment_method')['amount'].agg(['sum', 'count']).reset_index()
        fig_pm = px.pie(pm_stats, values='sum', names='payment_method', hole=.4,
                        color_discrete_sequence=px.colors.sequential.Plotlyfresh)
        fig_pm.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
        st.plotly_chart(fig_pm, use_container_width=True)
        
    with col_right:
        st.markdown("#### Top Bank Revenue Pipelines (Skill 2.30)")
        bank_stats = df_filtered.groupby('bank_name')['amount'].sum().reset_index().sort_values('amount', ascending=False)
        fig_bank = px.bar(bank_stats, x='amount', y='bank_name', orientation='h', color='amount',
                          color_continuous_scale='Bluered')
        fig_bank.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
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
        fee_by_bank = df_filtered.groupby('bank_name')['calculated_fee'].sum().reset_index().sort_values('calculated_fee', ascending=False)
        fig_fees = px.bar(fee_by_bank, x='calculated_fee', y='bank_name', orientation='h', color='calculated_fee',
                          color_continuous_scale='Teal')
        fig_fees.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
        st.plotly_chart(fig_fees, use_container_width=True)
        
    with col_disc:
        st.markdown("#### Discounts Granted by Customer Segment")
        # Ensure column exists or fallback to segment
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
    
    fig_cum = ob.Figure()
    fig_cum.add_trace(ob.Scatter(
        y=df_sorted['cumulative_amount'].values[::100], name='Cumulative Gross Volume', line=dict(color='#ff7b72', width=2)
    ))
    fig_cum.add_trace(ob.Scatter(
        y=df_sorted['cumulative_net'].values[::100], name='Cumulative Net Settled (Post Discounts)', line=dict(color='#58a6ff', width=3)
    ))
    fig_cum.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'),
        xaxis=dict(title='Transaction sample points (scaled down by 100x)', showgrid=True, gridcolor='#21262d'),
        yaxis=dict(title='Total Accumulated USD', showgrid=True, gridcolor='#21262d')
    )
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
        df_corr = pd.read_csv("output/correlation_matrix.csv", index=True if 'Unnamed: 0' in pd.read_csv("output/correlation_matrix.csv").columns else None)
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
        fig_funnel = px.funnel(df_funnel, x='customers', y='stage', color='percentage',
                               color_continuous_scale='Electric')
        fig_funnel.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
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
            # locate max drop off
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
        fig_anom = ob.Figure()
        fig_anom.add_trace(ob.Scatter(
            x=daily_rev['date_only'], y=daily_rev['daily_total'],
            mode='lines+markers', name='Daily Settled Revenue', line=dict(color='#58a6ff')
        ))
        fig_anom.add_trace(ob.Scatter(
            x=daily_rev['date_only'], y=daily_rev['upper'],
            mode='lines', name='Upper Boundary (Spike limit)', line=dict(color='#f85149', dash='dash')
        ))
        fig_anom.add_trace(ob.Scatter(
            x=daily_rev['date_only'], y=daily_rev['lower'],
            mode='lines', name='Lower Boundary (Dip limit)', line=dict(color='#d29922', dash='dash')
        ))
        
        # Highlight anomalous days
        anoms = daily_rev[daily_rev['is_anomaly']]
        fig_anom.add_trace(ob.Scatter(
            x=anoms['date_only'], y=anoms['daily_total'],
            mode='markers', name='Flagged Anomalies', marker=dict(color='#ff7b72', size=10, symbol='x')
        ))
        
        fig_anom.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#c9d1d9'))
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
else:
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
    
    # Export csv capability
    csv_data = df_ledger[existing_show_cols].head(500).to_csv(index=False)
    st.download_button(
        label="📥 Download current transaction view (CSV - Max 500 records)",
        data=csv_data,
        file_name="payment_ledger.csv",
        mime="text/csv"
    )
