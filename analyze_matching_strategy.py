#!/usr/bin/env python3
"""
Analyze potential matching strategies between HubSpot and SalesCookie
"""
import pandas as pd
from datetime import datetime
import re

def analyze_matching_options():
    print("=== Analyzing Matching Strategies ===\n")
    
    # Load HubSpot data
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_deals = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    
    print(f"HubSpot Closed & Won deals: {len(hs_deals)}")
    
    # Analyze HubSpot fields
    print("\n--- HubSpot Key Fields ---")
    print(f"Deals with Company IDs: {hs_deals['Associated Company IDs (Primary)'].notna().sum()}")
    print(f"Deals with Company Name: {hs_deals['Associated Company (Primary)'].notna().sum()}")
    print(f"Deals with Close Date: {hs_deals['Close Date'].notna().sum()}")
    print(f"Deals with TCV advisory: {hs_deals['Weigh. ACV product & MS & TCV advisory'].notna().sum()}")
    
    # Sample data
    print("\nSample HubSpot data:")
    sample_cols = ['Deal Name', 'Associated Company (Primary)', 'Associated Company IDs (Primary)', 
                   'Close Date', 'Amount', 'Weigh. ACV product & MS & TCV advisory']
    for idx, row in hs_deals.head(5).iterrows():
        print(f"\n{row['Deal Name']}")
        print(f"  Company: {row['Associated Company (Primary)']} (ID: {row['Associated Company IDs (Primary)']})")
        print(f"  Close Date: {row['Close Date']}")
        print(f"  Amount: {row['Amount']}")
        print(f"  TCV Advisory: {row['Weigh. ACV product & MS & TCV advisory']}")
    
    # Load SalesCookie data from multiple quarters
    all_sc_data = []
    quarters = ['Q1_2024', 'Q2_2024', 'Q3_2024', 'Q4_2024', 'Q1_2025', 'Q2_2025', 'Q3_2025']
    
    for quarter in quarters:
        try:
            path = f'../sales_cookie_all_plans_20250729/Account Managers & Sales - 2024/{quarter}/credited_transactions_*.csv'
            import glob
            files = glob.glob(path)
            if files:
                df = pd.read_csv(files[0], encoding='utf-8-sig', sep=';', on_bad_lines='skip')
                if 'Unique ID' in df.columns:
                    df = df[df['Unique ID'].notna()].copy()
                    df['Quarter'] = quarter
                    all_sc_data.append(df)
                    print(f"\nLoaded {len(df)} transactions from {quarter}")
        except Exception as e:
            print(f"Error loading {quarter}: {e}")
    
    if all_sc_data:
        sc_df = pd.concat(all_sc_data, ignore_index=True)
        print(f"\n\nTotal SalesCookie transactions: {len(sc_df)}")
        
        # Analyze SalesCookie fields
        print("\n--- SalesCookie Key Fields ---")
        print(f"Columns: {list(sc_df.columns)[:15]}...")
        
        if 'Customer' in sc_df.columns:
            print(f"\nTransactions with Customer: {sc_df['Customer'].notna().sum()}")
            print("\nSample customers:")
            for customer in sc_df['Customer'].dropna().head(10):
                print(f"  - {customer}")
        
        if 'Close Date' in sc_df.columns:
            print(f"\nTransactions with Close Date: {sc_df['Close Date'].notna().sum()}")
        
        # Analyze potential matches
        print("\n\n=== Matching Strategy Analysis ===")
        
        # Strategy 1: Company Name matching
        print("\n1. Company Name Analysis:")
        if 'Customer' in sc_df.columns:
            # Extract company names from both systems
            hs_companies = set()
            for company in hs_deals['Associated Company (Primary)'].dropna():
                # Normalize company name
                normalized = company.lower().strip()
                # Remove common suffixes
                normalized = re.sub(r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc).*$', '', normalized)
                hs_companies.add(normalized)
            
            sc_companies = set()
            for customer in sc_df['Customer'].dropna():
                # Extract company from format like "100449; Aktia Bank Abp"
                if ';' in str(customer):
                    parts = str(customer).split(';')
                    if len(parts) > 1:
                        company = parts[1].strip()
                        normalized = company.lower()
                        normalized = re.sub(r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc).*$', '', normalized)
                        sc_companies.add(normalized)
            
            matches = hs_companies.intersection(sc_companies)
            print(f"  Potential company matches: {len(matches)}")
            if matches:
                print("  Sample matches:")
                for match in list(matches)[:10]:
                    print(f"    - {match}")
        
        # Strategy 2: Deal Name matching
        print("\n2. Deal Name Analysis:")
        if 'Deal Name' in sc_df.columns:
            hs_deal_names = {name.lower() for name in hs_deals['Deal Name'].dropna()}
            sc_deal_names = {name.lower() for name in sc_df['Deal Name'].dropna()}
            
            name_matches = hs_deal_names.intersection(sc_deal_names)
            print(f"  Direct deal name matches: {len(name_matches)}")
            
            # Check partial matches
            partial_matches = 0
            for hs_name in list(hs_deal_names)[:20]:
                for sc_name in sc_deal_names:
                    if hs_name in sc_name or sc_name in hs_name:
                        partial_matches += 1
                        break
            print(f"  Partial name matches (sample of 20): {partial_matches}")
        
        # Strategy 3: Date matching
        print("\n3. Date Analysis:")
        if 'Close Date' in sc_df.columns:
            # Parse dates
            hs_dates = pd.to_datetime(hs_deals['Close Date'], errors='coerce')
            sc_dates = pd.to_datetime(sc_df['Close Date'], errors='coerce')
            
            # Count dates
            print(f"  HubSpot unique close dates: {hs_dates.dropna().nunique()}")
            print(f"  SalesCookie unique close dates: {sc_dates.dropna().nunique()}")
            
            # Find matching dates
            hs_date_set = set(hs_dates.dropna().dt.date)
            sc_date_set = set(sc_dates.dropna().dt.date)
            date_matches = hs_date_set.intersection(sc_date_set)
            print(f"  Matching dates: {len(date_matches)}")
        
        # Strategy 4: Combined matching
        print("\n4. Combined Strategy Analysis:")
        print("  Testing Company + Date combination...")
        
        # Create combination keys
        hs_keys = set()
        for _, row in hs_deals.iterrows():
            if pd.notna(row['Associated Company (Primary)']) and pd.notna(row['Close Date']):
                company = row['Associated Company (Primary)'].lower().strip()
                company = re.sub(r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc).*$', '', company)
                try:
                    date = pd.to_datetime(row['Close Date']).date()
                    key = f"{company}|{date}"
                    hs_keys.add(key)
                except:
                    pass
        
        sc_keys = set()
        for _, row in sc_df.iterrows():
            if 'Customer' in sc_df.columns and pd.notna(row.get('Customer')) and pd.notna(row.get('Close Date')):
                customer_str = str(row['Customer'])
                if ';' in customer_str:
                    parts = customer_str.split(';')
                    if len(parts) > 1:
                        company = parts[1].strip().lower()
                        company = re.sub(r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc).*$', '', company)
                        try:
                            date = pd.to_datetime(row['Close Date']).date()
                            key = f"{company}|{date}"
                            sc_keys.add(key)
                        except:
                            pass
        
        combo_matches = hs_keys.intersection(sc_keys)
        print(f"  Company + Date matches: {len(combo_matches)}")
        if combo_matches:
            print("  Sample combination matches:")
            for match in list(combo_matches)[:10]:
                print(f"    - {match}")

if __name__ == '__main__':
    analyze_matching_options()