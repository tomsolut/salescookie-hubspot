#!/usr/bin/env python3
"""
Test exact matching with close dates and deal names
"""
import pandas as pd
from datetime import datetime
import re

def test_exact_matching():
    # Load HubSpot data
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_deals = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    
    # Parse HubSpot dates
    hs_deals['close_date_parsed'] = pd.to_datetime(hs_deals['Close Date'], errors='coerce')
    
    print(f"HubSpot Closed & Won deals: {len(hs_deals)}")
    print("\nSample HubSpot deals:")
    for idx, row in hs_deals.head(10).iterrows():
        print(f"  {row['Deal Name']} | {row['Associated Company (Primary)']} | {row['Close Date']}")
    
    # Load all SalesCookie data
    all_sc_data = []
    import os
    import glob
    
    for folder in ['Account Managers & Sales - 2024', 'Account Managers & Sales - 2025']:
        folder_path = f'../sales_cookie_all_plans_20250729/{folder}'
        if os.path.exists(folder_path):
            for quarter_folder in os.listdir(folder_path):
                if quarter_folder.startswith('Q'):
                    files = glob.glob(f'{folder_path}/{quarter_folder}/credited_transactions_*.csv')
                    if files:
                        try:
                            df = pd.read_csv(files[0], encoding='utf-8-sig', sep=';', on_bad_lines='skip')
                            if 'Unique ID' in df.columns and 'Deal Name' in df.columns:
                                df = df[df['Unique ID'].notna()].copy()
                                df['Quarter'] = quarter_folder
                                all_sc_data.append(df)
                        except Exception as e:
                            print(f"Error loading {quarter_folder}: {e}")
    
    if not all_sc_data:
        print("No SalesCookie data loaded!")
        return
    
    sc_df = pd.concat(all_sc_data, ignore_index=True)
    sc_df['close_date_parsed'] = pd.to_datetime(sc_df['Close Date'], errors='coerce')
    
    print(f"\nSalesCookie transactions: {len(sc_df)}")
    print("\nSample SalesCookie deals:")
    for idx, row in sc_df.head(10).iterrows():
        print(f"  {row.get('Deal Name', 'N/A')} | {row['Customer']} | {row['Close Date']}")
    
    # Test 1: Exact deal name match
    print("\n\n=== Test 1: Exact Deal Name Match ===")
    hs_names = set(hs_deals['Deal Name'].dropna())
    sc_names = set(sc_df['Deal Name'].dropna())
    
    exact_name_matches = hs_names.intersection(sc_names)
    print(f"Exact deal name matches: {len(exact_name_matches)}")
    
    if exact_name_matches:
        print("\nMatched deal names:")
        for name in list(exact_name_matches)[:20]:
            print(f"  - {name}")
    
    # Test 2: Deal name + Close date match
    print("\n\n=== Test 2: Deal Name + Close Date Match ===")
    matches = []
    
    for hs_idx, hs_row in hs_deals.iterrows():
        hs_name = hs_row['Deal Name']
        hs_date = hs_row['close_date_parsed']
        
        if pd.notna(hs_name) and pd.notna(hs_date):
            # Look for exact match in SalesCookie
            for sc_idx, sc_row in sc_df.iterrows():
                sc_name = sc_row.get('Deal Name')
                sc_date = sc_row['close_date_parsed']
                
                if pd.notna(sc_name) and pd.notna(sc_date):
                    # Exact name and date match
                    if hs_name == sc_name and hs_date.date() == sc_date.date():
                        matches.append({
                            'hs_idx': hs_idx,
                            'sc_idx': sc_idx,
                            'deal_name': hs_name,
                            'date': hs_date.date(),
                            'hs_company': hs_row['Associated Company (Primary)'],
                            'sc_customer': sc_row['Customer']
                        })
    
    print(f"Deal name + date matches: {len(matches)}")
    
    if matches:
        print("\nSample matches:")
        for match in matches[:10]:
            print(f"\n  Deal: {match['deal_name']}")
            print(f"  Date: {match['date']}")
            print(f"  HubSpot Company: {match['hs_company']}")
            print(f"  SalesCookie Customer: {match['sc_customer']}")
    
    # Test 3: Company extraction and normalization check
    print("\n\n=== Test 3: Company Name Extraction Test ===")
    
    # Extract company from SalesCookie customer field
    def extract_company(customer_str):
        if pd.isna(customer_str):
            return ""
        customer_str = str(customer_str)
        if ';' in customer_str:
            parts = customer_str.split(';')
            if len(parts) > 1:
                return parts[1].strip()
        return customer_str.strip()
    
    # Test extraction on samples
    print("\nSalesCookie Customer field parsing:")
    for customer in sc_df['Customer'].dropna().head(10):
        company = extract_company(customer)
        print(f"  '{customer}' → '{company}'")
    
    # Test 4: Date format analysis
    print("\n\n=== Test 4: Date Format Analysis ===")
    
    # Check date parsing success rate
    hs_dates_parsed = hs_deals['close_date_parsed'].notna().sum()
    sc_dates_parsed = sc_df['close_date_parsed'].notna().sum()
    
    print(f"HubSpot dates successfully parsed: {hs_dates_parsed}/{len(hs_deals)} ({hs_dates_parsed/len(hs_deals)*100:.1f}%)")
    print(f"SalesCookie dates successfully parsed: {sc_dates_parsed}/{len(sc_df)} ({sc_dates_parsed/len(sc_df)*100:.1f}%)")
    
    # Show date format samples
    print("\nHubSpot date formats:")
    for date in hs_deals['Close Date'].dropna().head(5):
        print(f"  {date}")
    
    print("\nSalesCookie date formats:")
    for date in sc_df['Close Date'].dropna().head(5):
        print(f"  {date}")
    
    # Test 5: Unique identifier analysis
    print("\n\n=== Test 5: Unique Identifier Patterns ===")
    
    print("\nHubSpot Record IDs (first 10):")
    for rid in hs_deals['Record ID'].head(10):
        print(f"  {rid}")
    
    print("\nSalesCookie Unique IDs (first 10):")
    for uid in sc_df['Unique ID'].dropna().head(10):
        print(f"  {uid}")
    
    # Summary
    print("\n\n=== MATCHING SUMMARY ===")
    print(f"Total HubSpot deals: {len(hs_deals)}")
    print(f"Total SalesCookie transactions: {len(sc_df)}")
    print(f"Exact deal name matches: {len(exact_name_matches)}")
    print(f"Deal name + date matches: {len(matches)}")
    print(f"Match rate: {len(matches)/len(hs_deals)*100:.1f}%")
    
    # Check for duplicate matches
    hs_matched = set(m['hs_idx'] for m in matches)
    sc_matched = set(m['sc_idx'] for m in matches)
    print(f"\nUnique HubSpot deals matched: {len(hs_matched)}")
    print(f"Unique SalesCookie transactions matched: {len(sc_matched)}")
    
    if len(matches) > len(hs_matched):
        print(f"WARNING: Some HubSpot deals have multiple matches!")

if __name__ == '__main__':
    test_exact_matching()