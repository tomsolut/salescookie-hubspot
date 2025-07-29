#!/usr/bin/env python3
"""
Quick analysis tool to understand data structure
"""
import pandas as pd
import sys

def analyze_hubspot(file_path):
    print("\n=== HubSpot Data Analysis ===")
    df = pd.read_csv(file_path)
    
    # Filter Closed & Won
    df_cw = df[df['Deal Stage'] == 'Closed & Won']
    
    print(f"Total Closed & Won deals: {len(df_cw)}")
    print(f"\nSample Deal IDs:")
    for idx, row in df_cw.head(5).iterrows():
        print(f"  - {row['Record ID']}: {row['Deal Name']}")
    
    print(f"\nDeal Types:")
    print(df_cw['Deal Type'].value_counts().head())
    
    return df_cw

def analyze_salescookie(file_path):
    print("\n=== SalesCookie Data Analysis ===")
    
    # Try different separators
    for sep in [';', ',']:
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig', sep=sep, on_bad_lines='skip')
            print(f"Successfully read with separator: '{sep}'")
            break
        except:
            continue
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)[:10]}...")
    
    # Look for Unique ID column
    if 'Unique ID' in df.columns:
        df_with_id = df[df['Unique ID'].notna()]
        print(f"\nRows with Unique ID: {len(df_with_id)}")
        print(f"\nSample Unique IDs:")
        for idx, row in df_with_id.head(5).iterrows():
            print(f"  - {row['Unique ID']}: {row.get('Deal Name', 'N/A')}")
    
    return df

if __name__ == '__main__':
    # Analyze HubSpot
    hs_df = analyze_hubspot('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    
    # Analyze SalesCookie Q4 2024
    sc_df = analyze_salescookie('../sales_cookie_all_plans_20250729/Account Managers & Sales - 2024/Q4_2024/credited_transactions_20250729_155838.csv')
    
    # Try to find matching pattern
    print("\n=== Matching Analysis ===")
    hs_ids = set(hs_df['Record ID'].astype(str))
    
    if 'Unique ID' in sc_df.columns:
        sc_ids = set(sc_df[sc_df['Unique ID'].notna()]['Unique ID'].astype(str))
        
        # Check direct matches
        matches = hs_ids.intersection(sc_ids)
        print(f"Direct ID matches: {len(matches)}")
        
        # Check if names match
        print("\nChecking name-based matching...")
        hs_names = {row['Deal Name'].lower() for _, row in hs_df.iterrows() if pd.notna(row['Deal Name'])}
        sc_names = {row['Deal Name'].lower() for _, row in sc_df.iterrows() if 'Deal Name' in sc_df.columns and pd.notna(row.get('Deal Name'))}
        
        name_matches = hs_names.intersection(sc_names)
        print(f"Name matches: {len(name_matches)}")
        if name_matches:
            print("Sample matched names:")
            for name in list(name_matches)[:5]:
                print(f"  - {name}")