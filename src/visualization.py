"""
src/visualization.py
Modules 2.45 & 2.46: Business Visualisation Principles & Interactive Plotly Chart Design

This module provides reusable visualization components for the Fintech Payment Analytics
dashboard, separating presentation logic from data loading.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_time_series_trend(daily_stats: pd.DataFrame) -> go.Figure:
    """
    Generate a Plotly line chart displaying daily transactions total volume
    against a 7-day rolling average.
    """
    fig = go.Figure()
    
    if 'date_only' in daily_stats.columns:
        fig.add_trace(go.Scatter(
            x=daily_stats['date_only'], y=daily_stats['daily_total'],
            mode='lines', name='Daily Total Volume', line=dict(color='#58a6ff', width=1.5)
        ))
        
        if 'rolling_avg_7d' in daily_stats.columns:
            fig.add_trace(go.Scatter(
                x=daily_stats['date_only'], y=daily_stats['rolling_avg_7d'],
                mode='lines', name='7-Day Moving Average', line=dict(color='#ff7b72', width=3, dash='dash')
            ))
            
    fig.update_layout(
        title="Transaction Volume Daily Trend vs Rolling Average",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c9d1d9'),
        xaxis=dict(showgrid=True, gridcolor='#21262d', title="Date"),
        yaxis=dict(showgrid=True, gridcolor='#21262d', title="Amount ($)"),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(22,27,34,0.8)')
    )
    return fig

def plot_payment_methods_pie(df: pd.DataFrame) -> go.Figure:
    """
    Generate a Plotly pie chart showing distribution of transaction volume
    by payment method.
    """
    pm_stats = df.groupby('payment_method')['amount'].agg(['sum', 'count']).reset_index()
    fig = px.pie(
        pm_stats, 
        values='sum', 
        names='payment_method', 
        hole=.4,
        color_discrete_sequence=px.colors.sequential.Plotlyfresh
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#c9d1d9'),
        legend=dict(bgcolor='rgba(22,27,34,0.8)')
    )
    return fig

def plot_bank_revenue_bar(df: pd.DataFrame) -> go.Figure:
    """
    Generate a Plotly horizontal bar chart showing top bank revenue pipelines.
    """
    bank_stats = df.groupby('bank_name')['amount'].sum().reset_index().sort_values('amount', ascending=False)
    fig = px.bar(
        bank_stats, 
        x='amount', 
        y='bank_name', 
        orientation='h', 
        color='amount',
        color_continuous_scale='Bluered'
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#c9d1d9'),
        xaxis=dict(showgrid=True, gridcolor='#21262d', title="Total Volume ($)"),
        yaxis=dict(title="Bank Name")
    )
    return fig

def plot_cumulative_settlement(df_sorted: pd.DataFrame) -> go.Figure:
    """
    Generate a cumulative line chart demonstrating gross volume versus net settled volume.
    """
    fig = go.Figure()
    
    if 'cumulative_amount' in df_sorted.columns:
        fig.add_trace(go.Scatter(
            y=df_sorted['cumulative_amount'].values[::100], 
            name='Cumulative Gross Volume', 
            line=dict(color='#ff7b72', width=2)
        ))
        
    if 'cumulative_net' in df_sorted.columns:
        fig.add_trace(go.Scatter(
            y=df_sorted['cumulative_net'].values[::100], 
            name='Cumulative Net Settled (Post Discounts)', 
            line=dict(color='#58a6ff', width=3)
        ))
        
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#c9d1d9'),
        xaxis=dict(title='Transaction Sample Points (100x scale)', showgrid=True, gridcolor='#21262d'),
        yaxis=dict(title='Total Accumulated USD ($)', showgrid=True, gridcolor='#21262d'),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(22,27,34,0.8)')
    )
    return fig

def plot_funnel_drop_off(df_funnel: pd.DataFrame) -> go.Figure:
    """
    Generate a Plotly Funnel chart for transaction process stages.
    """
    fig = px.funnel(
        df_funnel, 
        x='customers', 
        y='stage', 
        color='percentage',
        color_continuous_scale='Electric'
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#c9d1d9')
    )
    return fig

def plot_revenue_anomalies(daily_rev: pd.DataFrame) -> go.Figure:
    """
    Generate an anomaly boundary line plot highlighting spikes/dips.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_rev['date_only'], y=daily_rev['daily_total'],
        mode='lines+markers', name='Daily Settled Revenue', line=dict(color='#58a6ff')
    ))
    
    if 'upper' in daily_rev.columns:
        fig.add_trace(go.Scatter(
            x=daily_rev['date_only'], y=daily_rev['upper'],
            mode='lines', name='Upper Boundary (Spike Limit)', line=dict(color='#f85149', dash='dash')
        ))
        
    if 'lower' in daily_rev.columns:
        fig.add_trace(go.Scatter(
            x=daily_rev['date_only'], y=daily_rev['lower'],
            mode='lines', name='Lower Boundary (Dip Limit)', line=dict(color='#d29922', dash='dash')
        ))
        
    if 'is_anomaly' in daily_rev.columns:
        anoms = daily_rev[daily_rev['is_anomaly']]
        fig.add_trace(go.Scatter(
            x=anoms['date_only'], y=anoms['daily_total'],
            mode='markers', name='Flagged Anomalies', marker=dict(color='#ff7b72', size=10, symbol='x')
        ))
        
    fig.update_layout(
        title="Daily Revenue Outlier Boundaries & Anomaly Detection",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='#c9d1d9'),
        xaxis=dict(showgrid=True, gridcolor='#21262d', title="Date"),
        yaxis=dict(showgrid=True, gridcolor='#21262d', title="Revenue ($)"),
        legend=dict(bgcolor='rgba(22,27,34,0.8)')
    )
    return fig
