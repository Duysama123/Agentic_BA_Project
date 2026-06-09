import os
import sys
import json
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

# Mock Streamlit secrets
import streamlit as st
secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
if os.path.exists(secrets_path):
    try:
        import tomllib
        with open(secrets_path, "rb") as f:
            st.secrets = tomllib.load(f)
    except Exception as e:
        print("Warning: Failed to load secrets for mocking:", e)

url = st.secrets["SUPABASE_URL"].rstrip('/')
key = st.secrets["SUPABASE_KEY"]
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

def analyze():
    print("=" * 70)
    print("  Specify.ai - Telemetry & Performance Analysis Engine")
    print("=" * 70)
    
    # 1. Fetch data
    print("Fetching telemetry data from Supabase Cloud...")
    sessions_res = requests.get(f"{url}/rest/v1/eval_sessions", headers=headers)
    runs_res = requests.get(f"{url}/rest/v1/eval_agent_runs", headers=headers)
    reviews_res = requests.get(f"{url}/rest/v1/eval_human_reviews", headers=headers)
    
    if sessions_res.status_code != 200 or runs_res.status_code != 200 or reviews_res.status_code != 200:
        print("[ERROR] Failed to fetch data from Supabase.")
        return
        
    sessions = sessions_res.json()
    runs = runs_res.json()
    reviews = reviews_res.json()
    
    df_sessions = pd.DataFrame(sessions)
    df_runs = pd.DataFrame(runs)
    df_reviews = pd.DataFrame(reviews)
    
    print(f"Loaded {len(df_sessions)} sessions, {len(df_runs)} agent runs, and {len(df_reviews)} human reviews.")
    
    # Ensure new columns have default value of 0 if missing
    if 'llm_input_tokens' not in df_runs.columns:
        df_runs['llm_input_tokens'] = 0
    if 'llm_output_tokens' not in df_runs.columns:
        df_runs['llm_output_tokens'] = 0
        
    df_runs['llm_input_tokens'] = df_runs['llm_input_tokens'].fillna(0).astype(int)
    df_runs['llm_output_tokens'] = df_runs['llm_output_tokens'].fillna(0).astype(int)
    
    # Create output directories
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "telemetry"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # =================================================================
    # ANALYSIS 1: LATENCY BY AGENT
    # =================================================================
    print("\n[1/3] Calculating Agent Execution Latencies...")
    
    # Group runs by agent_name and get average processing_time
    agent_latency = df_runs.groupby('agent_name')['processing_time'].agg(['mean', 'std', 'count']).reset_index()
    agent_latency.columns = ['Agent Name', 'Average Time (s)', 'Std Dev (s)', 'Execution Count']
    
    # Sort agents in execution order
    execution_order = {
        'VisionAgent': 1,
        'BAAgent': 2,
        'DiagramAgent': 3,
        'QAAgent': 4
    }
    agent_latency['Order'] = agent_latency['Agent Name'].map(execution_order)
    agent_latency = agent_latency.sort_values('Order').drop(columns=['Order'])
    
    # Calculate Latency Share (%)
    total_automated_time = agent_latency['Average Time (s)'].sum()
    agent_latency['Latency Share (%)'] = (agent_latency['Average Time (s)'] / total_automated_time) * 100
    
    # Round metrics for formatting
    agent_latency['Average Time (s)'] = agent_latency['Average Time (s)'].round(2)
    agent_latency['Std Dev (s)'] = agent_latency['Std Dev (s)'].round(3)
    agent_latency['Latency Share (%)'] = agent_latency['Latency Share (%)'].round(1)
    
    # Save CSV
    latency_csv_path = os.path.join(output_dir, "latency_analysis.csv")
    agent_latency.to_csv(latency_csv_path, index=False)
    print(f"Saved latency analysis to: {latency_csv_path}")
    
    # =================================================================
    # ANALYSIS 2: HUMAN REVIEW TIMES (HITL GATES)
    # =================================================================
    print("\n[2/3] Analyzing Human Review Gate Times...")
    gate_latency = df_reviews.groupby('checkpoint')['time_spent_seconds'].agg(['mean', 'std', 'count']).reset_index()
    gate_latency.columns = ['HITL Checkpoint', 'Average Time (s)', 'Std Dev (s)', 'Review Count']
    gate_latency['Average Time (s)'] = gate_latency['Average Time (s)'].round(2)
    gate_latency['Std Dev (s)'] = gate_latency['Std Dev (s)'].round(2)
    
    gate_csv_path = os.path.join(output_dir, "human_review_analysis.csv")
    gate_latency.to_csv(gate_csv_path, index=False)
    print(f"Saved human review analysis to: {gate_csv_path}")
    
    # =================================================================
    # ANALYSIS 3: TOKEN COST & COST PER ANALYSIS
    # =================================================================
    print("\n[3/3] Calculating Token Consumption & Cost per Analysis...")
    
    # Gemini 2.0 Flash Pricing: Input: $0.10/1M ($0.0000001), Output: $0.40/1M ($0.0000004)
    def calculate_run_cost(row):
        agent = row['agent_name']
        if agent == 'QAAgent':
            return 0.00000
        else:
            in_tok = row['llm_input_tokens']
            out_tok = row['llm_output_tokens']
            return (in_tok * 0.0000001) + (out_tok * 0.0000004)
            
    df_runs['api_cost'] = df_runs.apply(calculate_run_cost, axis=1)
    
    # Group by agent
    token_cost_report = df_runs.groupby('agent_name').agg({
        'llm_input_tokens': 'mean',
        'llm_output_tokens': 'mean',
        'llm_tokens_used': 'mean',
        'api_cost': 'mean'
    }).reset_index()
    
    token_cost_report.columns = [
        'Agent Name', 'Average Input Tokens', 'Average Output Tokens', 'Average Total Tokens', 'Average Cost per Analysis ($)'
    ]
    
    # Add LLM Model column
    models_mapping = {
        'VisionAgent': 'Gemini 2.0 Flash',
        'BAAgent': 'Gemini 2.0 Flash',
        'DiagramAgent': 'Gemini 2.0 Flash',
        'QAAgent': 'Local Python (Deterministic)'
    }
    token_cost_report['LLM Model / Execution Type'] = token_cost_report['Agent Name'].map(models_mapping)
    
    # Reorder columns
    token_cost_report = token_cost_report[[
        'Agent Name', 'LLM Model / Execution Type', 'Average Input Tokens', 'Average Output Tokens', 'Average Total Tokens', 'Average Cost per Analysis ($)'
    ]]
    
    # Sort by execution order
    token_cost_report['Order'] = token_cost_report['Agent Name'].map(execution_order)
    token_cost_report = token_cost_report.sort_values('Order').drop(columns=['Order'])
    
    # Formatting
    token_cost_report['Average Input Tokens'] = token_cost_report['Average Input Tokens'].round(0).astype(int)
    token_cost_report['Average Output Tokens'] = token_cost_report['Average Output Tokens'].round(0).astype(int)
    token_cost_report['Average Total Tokens'] = token_cost_report['Average Total Tokens'].round(0).astype(int)
    token_cost_report['Average Cost per Analysis ($)'] = token_cost_report['Average Cost per Analysis ($)'].round(5)
    
    # Calculate System Total
    total_in = token_cost_report['Average Input Tokens'].sum()
    total_out = token_cost_report['Average Output Tokens'].sum()
    total_tot = token_cost_report['Average Total Tokens'].sum()
    total_cost = token_cost_report['Average Cost per Analysis ($)'].sum()
    
    total_row = pd.DataFrame([{
        'Agent Name': 'Total System Pipeline',
        'LLM Model / Execution Type': '-',
        'Average Input Tokens': total_in,
        'Average Output Tokens': total_out,
        'Average Total Tokens': total_tot,
        'Average Cost per Analysis ($)': round(total_cost, 5)
    }])
    
    token_cost_report = pd.concat([token_cost_report, total_row], ignore_index=True)
    
    # Save CSV
    cost_csv_path = os.path.join(output_dir, "token_cost_analysis.csv")
    token_cost_report.to_csv(cost_csv_path, index=False)
    print(f"Saved token cost analysis to: {cost_csv_path}")
    
    # =================================================================
    # CHARTS GENERATION (MATPLOTLIB)
    # =================================================================
    print("\nGenerating charts...")
    
    # Style configuration
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # Chart 1: Latency Share (Bar chart)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#4F46E5', '#0EA5E9', '#10B981', '#F59E0B']
    bars = ax.bar(agent_latency['Agent Name'], agent_latency['Average Time (s)'], color=colors, width=0.5, edgecolor='none', zorder=3)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='semibold')
                    
    ax.set_title("Average Execution Response Time by Agent", fontsize=12, fontweight='bold', pad=15)
    ax.set_ylabel("Processing Time (Seconds)", fontsize=10)
    ax.set_ylim(0, max(agent_latency['Average Time (s)']) * 1.15)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    latency_chart_path = os.path.join(output_dir, "latency_share.png")
    plt.tight_layout()
    plt.savefig(latency_chart_path, dpi=300)
    plt.close()
    print(f"Saved latency chart to: {latency_chart_path}")
    
    # Chart 2: Cost per Analysis (Bar chart)
    fig, ax = plt.subplots(figsize=(8, 5))
    cost_agents = token_cost_report[token_cost_report['Agent Name'] != 'Total System Pipeline']
    bars2 = ax.bar(cost_agents['Agent Name'], cost_agents['Average Cost per Analysis ($)'], color=colors, width=0.5, edgecolor='none', zorder=3)
    
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'${height:.5f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='semibold')
                    
    ax.set_title("Average Cost per Analysis ($) by Agent", fontsize=12, fontweight='bold', pad=15)
    ax.set_ylabel("Cost per Analysis (USD)", fontsize=10)
    ax.set_ylim(0, max(cost_agents['Average Cost per Analysis ($)']) * 1.15)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    cost_chart_path = os.path.join(output_dir, "cost_per_analysis.png")
    plt.tight_layout()
    plt.savefig(cost_chart_path, dpi=300)
    plt.close()
    print(f"Saved cost chart to: {cost_chart_path}")
    
    # =================================================================
    # OUTPUT MARKDOWN TABLES
    # =================================================================
    print("\n" + "="*70)
    print("  EXACT MARKDOWN TABLES FOR THESIS REPORT (SECTION 4.3)")
    print("="*70)
    
    print("\n### 4.3.1. Agent Response Time Table:\n")
    print("| Execution Phase | Agent Name | Execution Type | Average Response Time (Seconds) | Latency Share (%) |")
    print("|---|---|---|---|---|")
    phases = {
        'VisionAgent': 'Image Analysis',
        'BAAgent': 'Requirements Drafting',
        'DiagramAgent': 'Downstream Derivations',
        'QAAgent': 'Verification & Quality Gate'
    }
    types = {
        'VisionAgent': 'OpenCV + Gemini 2.0 Flash',
        'BAAgent': 'FAISS RAG + Gemini 2.0 Flash',
        'DiagramAgent': 'Gemini 2.0 Flash',
        'QAAgent': 'Local Python (Deterministic)'
    }
    for _, row in agent_latency.iterrows():
        agent = row['Agent Name']
        phase = phases.get(agent, 'Execution')
        etype = types.get(agent, 'LLM')
        time_str = f"{row['Average Time (s)']:.2f} s"
        share_str = f"{row['Latency Share (%)']:.1f}%"
        
        if agent == 'QAAgent':
            time_str = f"**{time_str}**"
            share_str = f"**{share_str}**"
            
        print(f"| {phase} | **{agent}** | {etype} | {time_str} | {share_str} |")
    print(f"| **Total Pipeline Latency** | | | **{total_automated_time:.2f} s** | **100.0%** |")
    
    print("\n" + "-"*40)
    print("### 4.3.2. Token Cost and Cost per Analysis Table:\n")
    # Custom markdown output for exact table format
    print(token_cost_report.to_markdown(index=False))
    print("\n" + "="*70)

if __name__ == "__main__":
    analyze()
