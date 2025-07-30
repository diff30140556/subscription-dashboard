#!/usr/bin/env python3
"""
Simple connectivity test for Supabase connection.
Fetches 3 rows from churn_customers and prints row count and sample.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def test_supabase_connection():
    """Test Supabase connectivity by fetching sample data."""
    
    # Load environment variables from .env
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables!")
        print("Please ensure .env contains:")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by fetching 3 rows
        response = supabase.table("churn_customers").select("*").limit(3).execute()
        
        if response.data:
            print(f"✅ Connection successful!")
            print(f"📊 Row count in sample: {len(response.data)}")
            print(f"📋 Sample row:")
            if len(response.data) > 0:
                sample_row = response.data[0]
                for key, value in list(sample_row.items())[:5]:  # Show first 5 columns
                    print(f"  {key}: {value}")
                print("  ...")
            return True
        else:
            print("❌ No data returned from churn_customers table")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()