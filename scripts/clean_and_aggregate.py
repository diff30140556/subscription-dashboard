#!/usr/bin/env python3
"""
Main data cleaning and aggregation pipeline for churn analysis.
Fetches data from Supabase, cleans it, aggregates summaries, and writes back to churn_summary table.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client

# Debug switch - set to True to print JSON instead of writing to database
DEBUG_PRINT_JSON = False

def load_and_clean_data(supabase):
    """Load churn_customers data and perform cleaning transformations."""
    
    print("📥 Fetching data from churn_customers table...")
    response = supabase.table("churn_customers").select("*").execute()
    
    if not response.data:
        raise ValueError("No data returned from churn_customers table")
    
    # Convert to DataFrame
    df = pd.DataFrame(response.data)
    print(f"📊 Loaded {len(df)} rows")
    
    # Data cleaning
    print("🧹 Cleaning data...")
    
    # Convert TotalCharges to numeric
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    
    # Convert SeniorCitizen to integers, fill missing with 0
    df['SeniorCitizen'] = df['SeniorCitizen'].fillna(0).astype(int)
    
    # Fill missing categorical values with "Unknown"
    categorical_cols = [
        'gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
        'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
        'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
        'PaperlessBilling', 'PaymentMethod'
    ]
    
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")
    
    print(f"✅ Data cleaning completed. Shape: {df.shape}")
    return df

def create_bins(df):
    """Create binned versions of continuous variables."""
    
    # Tenure bins
    df['tenure_range'] = pd.cut(
        df['tenure'], 
        bins=[0, 12, 24, 48, 120], 
        labels=["0-12", "13-24", "25-48", "49+"],
        include_lowest=True
    )
    
    # Monthly charges bins
    df['monthly_charge_range'] = pd.cut(
        df['MonthlyCharges'],
        bins=[0, 35, 65, 95, 1e6],
        labels=["0-35", "36-65", "66-95", "96+"],
        include_lowest=True
    )
    
    return df

def calculate_aggregations(df):
    """Calculate all required aggregations and return as a summary dict."""
    
    print("📈 Calculating aggregations...")
    
    # Filter for churned customers only
    churned_df = df[df['Churn'] == 'Yes'].copy()
    print(f"🔍 Analyzing {len(churned_df)} churned customers")
    
    summary = {}
    
    # Averages for churned customers
    summary['averages'] = {
        'avg_tenure': float(churned_df['tenure'].mean()),
        'avg_monthly': float(churned_df['MonthlyCharges'].mean()),
        'avg_total': float(churned_df['TotalCharges'].mean()),
        'count': int(len(churned_df))
    }
    
    # Contract analysis (churned customers only)
    contract_counts = churned_df['Contract'].value_counts()
    total_churned = len(churned_df)
    summary['by_contract'] = [
        {
            'key': str(contract),
            'count': int(count),
            'pct': float(count / total_churned * 100)
        }
        for contract, count in contract_counts.items()
    ]
    
    # Payment method analysis (churned customers only)
    payment_counts = churned_df['PaymentMethod'].value_counts()
    summary['by_payment'] = [
        {
            'key': str(payment),
            'count': int(count),
            'pct': float(count / total_churned * 100)
        }
        for payment, count in payment_counts.items()
    ]
    
    # Tenure ranges (churned customers only)
    tenure_counts = churned_df['tenure_range'].value_counts()
    summary['tenure_ranges'] = [
        {
            'range': str(tenure_range),
            'count': int(count),
            'pct': float(count / total_churned * 100)
        }
        for tenure_range, count in tenure_counts.items()
    ]
    
    # Monthly charge ranges (churned customers only)
    charge_counts = churned_df['monthly_charge_range'].value_counts()
    summary['monthly_charge_ranges'] = [
        {
            'range': str(charge_range),
            'count': int(count),
            'pct': float(count / total_churned * 100)
        }
        for charge_range, count in charge_counts.items()
    ]
    
    # Churn rates by contract (across full dataset)
    contract_churn = df.groupby('Contract')['Churn'].apply(
        lambda x: (x == 'Yes').mean() * 100
    )
    summary['churn_rate_by_contract'] = [
        {
            'key': str(contract),
            'churn_rate': float(rate)
        }
        for contract, rate in contract_churn.items()
    ]
    
    # Churn rates by payment method (across full dataset)
    payment_churn = df.groupby('PaymentMethod')['Churn'].apply(
        lambda x: (x == 'Yes').mean() * 100
    )
    summary['churn_rate_by_payment'] = [
        {
            'key': str(payment),
            'churn_rate': float(rate)
        }
        for payment, rate in payment_churn.items()
    ]
    
    print("✅ Aggregations completed")
    return summary

def write_to_supabase(supabase, summary):
    """Write summary to churn_summary table."""
    
    try:
        response = supabase.table("churn_summary").insert({
            "payload": summary
        }).execute()
        
        if response.data:
            print("✅ Wrote summary to churn_summary.")
            return True
        else:
            print("❌ Failed to write to churn_summary table")
            return False
            
    except Exception as e:
        print(f"❌ Error writing to database: {str(e)}")
        print("\n📝 If churn_summary table doesn't exist, run this SQL in Supabase:")
        print("""
create table if not exists churn_summary (
  id uuid primary key default gen_random_uuid(),
  snapshot_ts timestamptz not null default now(),
  payload jsonb not null
);
create index if not exists idx_churn_summary_snapshot on churn_summary (snapshot_ts desc);
        """)
        return False

def main():
    """Main pipeline execution."""
    
    print("🚀 Starting churn data aggregation pipeline...")
    
    # Load environment variables
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables!")
        print("Please ensure .env contains:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
        return
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Load and clean data
        df = load_and_clean_data(supabase)
        
        # Create bins
        df = create_bins(df)
        
        # Calculate aggregations
        summary = calculate_aggregations(df)
        
        # Add metadata
        summary['generated_at'] = datetime.now().isoformat()
        summary['total_customers'] = int(len(df))
        
        if DEBUG_PRINT_JSON:
            print("🐛 DEBUG MODE - Printing JSON instead of writing to database:")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            # Write to Supabase
            write_to_supabase(supabase, summary)
        
        print("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"💥 Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()