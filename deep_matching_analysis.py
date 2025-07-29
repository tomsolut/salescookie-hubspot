#!/usr/bin/env python3
"""
Deep analysis of matching strategies with actual results
"""
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict

def normalize_company_name(name):
    """Normalize company names for matching"""
    if pd.isna(name):
        return ""
    
    name = str(name).lower().strip()
    
    # Remove common suffixes
    suffixes = [
        r'\s*\(.*\)$',  # Remove anything in parentheses
        r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc|ltd|limited|plc|s\.a\.|sa).*$',
        r'\s*&\s*co.*$',
        r'\s*kommanditgesellschaft.*$',
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    
    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)
    name = ' '.join(name.split())  # Normalize whitespace
    
    return name

def extract_company_from_customer(customer_str):
    """Extract company name from SalesCookie customer field"""
    if pd.isna(customer_str):
        return ""
    
    customer_str = str(customer_str)
    if ';' in customer_str:
        parts = customer_str.split(';')
        if len(parts) > 1:
            return parts[1].strip()
    
    return customer_str.strip()

def test_matching_strategies():
    # Load data
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_deals = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    
    # Load all SalesCookie data
    all_sc_data = []
    base_path = '../sales_cookie_all_plans_20250729/Account Managers & Sales - 2024'
    
    # Also check 2025 folder
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
                            if 'Unique ID' in df.columns:
                                df = df[df['Unique ID'].notna()].copy()
                                df['Quarter'] = quarter_folder
                                df['Source_Folder'] = folder
                                all_sc_data.append(df)
                        except:
                            pass
    
    if not all_sc_data:
        print("No SalesCookie data loaded!")
        return
    
    sc_df = pd.concat(all_sc_data, ignore_index=True)
    
    print(f"Loaded {len(hs_deals)} HubSpot deals and {len(sc_df)} SalesCookie transactions")
    
    # Prepare matching data
    hs_deals['normalized_company'] = hs_deals['Associated Company (Primary)'].apply(normalize_company_name)
    hs_deals['close_date_parsed'] = pd.to_datetime(hs_deals['Close Date'], errors='coerce')
    
    sc_df['company_extracted'] = sc_df['Customer'].apply(extract_company_from_customer)
    sc_df['normalized_company'] = sc_df['company_extracted'].apply(normalize_company_name)
    sc_df['close_date_parsed'] = pd.to_datetime(sc_df['Close Date'], errors='coerce')
    
    # Test different matching strategies
    results = {}
    
    # Strategy 1: Company name only
    print("\n=== Strategy 1: Company Name Only ===")
    matches = defaultdict(list)
    
    for hs_idx, hs_row in hs_deals.iterrows():
        hs_company = hs_row['normalized_company']
        if hs_company:
            for sc_idx, sc_row in sc_df.iterrows():
                sc_company = sc_row['normalized_company']
                if sc_company and hs_company == sc_company:
                    matches[hs_idx].append(sc_idx)
    
    results['company_only'] = len(matches)
    print(f"Matched deals: {len(matches)}")
    print(f"Multiple matches: {sum(1 for m in matches.values() if len(m) > 1)}")
    
    # Show sample matches
    print("\nSample matches:")
    for hs_idx, sc_indices in list(matches.items())[:5]:
        hs_deal = hs_deals.loc[hs_idx]
        print(f"\nHubSpot: {hs_deal['Deal Name']} | {hs_deal['Associated Company (Primary)']} | {hs_deal['Close Date']}")
        for sc_idx in sc_indices:
            sc_deal = sc_df.loc[sc_idx]
            print(f"  → SC: {sc_deal.get('Deal Name', 'N/A')} | {sc_deal['Customer']} | {sc_deal['Close Date']}")
    
    # Strategy 2: Company + Date
    print("\n\n=== Strategy 2: Company + Date ===")
    matches = defaultdict(list)
    
    for hs_idx, hs_row in hs_deals.iterrows():
        hs_company = hs_row['normalized_company']
        hs_date = hs_row['close_date_parsed']
        
        if hs_company and pd.notna(hs_date):
            for sc_idx, sc_row in sc_df.iterrows():
                sc_company = sc_row['normalized_company']
                sc_date = sc_row['close_date_parsed']
                
                if sc_company and pd.notna(sc_date):
                    # Check if company matches and dates are within 7 days
                    if hs_company == sc_company and abs((hs_date - sc_date).days) <= 7:
                        matches[hs_idx].append((sc_idx, (hs_date - sc_date).days))
    
    results['company_date'] = len(matches)
    print(f"Matched deals: {len(matches)}")
    print(f"Multiple matches: {sum(1 for m in matches.values() if len(m) > 1)}")
    
    # Show sample matches with date differences
    print("\nSample matches:")
    for hs_idx, sc_matches in list(matches.items())[:5]:
        hs_deal = hs_deals.loc[hs_idx]
        print(f"\nHubSpot: {hs_deal['Deal Name']} | {hs_deal['Associated Company (Primary)']} | {hs_deal['Close Date']}")
        for sc_idx, date_diff in sc_matches:
            sc_deal = sc_df.loc[sc_idx]
            print(f"  → SC: {sc_deal.get('Deal Name', 'N/A')} | {sc_deal['Customer']} | {sc_deal['Close Date']} (diff: {date_diff} days)")
    
    # Strategy 3: Deal name partial matching
    print("\n\n=== Strategy 3: Deal Name Partial Matching ===")
    matches = defaultdict(list)
    
    for hs_idx, hs_row in hs_deals.iterrows():
        hs_name = str(hs_row['Deal Name']).lower()
        hs_company = hs_row['normalized_company']
        
        # Extract key parts from deal name
        # Look for patterns like "Product @ Company"
        parts = hs_name.split('@')
        if len(parts) >= 2:
            product = parts[0].strip()
            company_in_name = normalize_company_name(parts[1])
            
            for sc_idx, sc_row in sc_df.iterrows():
                sc_name = str(sc_row.get('Deal Name', '')).lower()
                sc_company = sc_row['normalized_company']
                
                # Check if product matches and company matches
                if product in sc_name and (hs_company == sc_company or company_in_name == sc_company):
                    matches[hs_idx].append(sc_idx)
    
    results['deal_name_partial'] = len(matches)
    print(f"Matched deals: {len(matches)}")
    
    # Strategy 4: Company + Amount (for PS deals)
    print("\n\n=== Strategy 4: Company + Amount (PS Deals) ===")
    matches = defaultdict(list)
    
    # Focus on PS deals
    ps_deals = hs_deals[hs_deals['Deal Name'].str.contains('PS @', case=False, na=False)]
    
    for hs_idx, hs_row in ps_deals.iterrows():
        hs_company = hs_row['normalized_company']
        hs_amount = hs_row['Amount']
        hs_tcv = hs_row['Weigh. ACV product & MS & TCV advisory']
        
        if hs_company:
            for sc_idx, sc_row in sc_df.iterrows():
                sc_company = sc_row['normalized_company']
                sc_tcv = sc_row.get('TCV (Professional Services)', 0)
                
                if sc_company and hs_company == sc_company:
                    # Check if amounts match (with 1% tolerance)
                    if hs_tcv > 0 and abs(hs_tcv - sc_tcv) / hs_tcv < 0.01:
                        matches[hs_idx].append(sc_idx)
    
    results['ps_company_amount'] = len(matches)
    print(f"Matched PS deals: {len(matches)}")
    
    # Summary
    print("\n\n=== SUMMARY OF MATCHING STRATEGIES ===")
    print(f"Total HubSpot deals to match: {len(hs_deals)}")
    print(f"\nMatching results:")
    print(f"1. Company only: {results['company_only']} matches ({results['company_only']/len(hs_deals)*100:.1f}%)")
    print(f"2. Company + Date (±7 days): {results['company_date']} matches ({results['company_date']/len(hs_deals)*100:.1f}%)")
    print(f"3. Deal name partial: {results['deal_name_partial']} matches ({results['deal_name_partial']/len(hs_deals)*100:.1f}%)")
    print(f"4. PS deals (company + amount): {results['ps_company_amount']} matches ({results['ps_company_amount']/len(ps_deals)*100:.1f}% of PS deals)")
    
    # Best strategy recommendation
    print("\n\n=== RECOMMENDATION ===")
    print("Best matching strategy: Company + Date (±7 days)")
    print("This provides a good balance between match rate and accuracy.")
    print("\nImplementation approach:")
    print("1. Primary match: Company name + Close date (±7 days)")
    print("2. Secondary match: Company name only (for deals without date matches)")
    print("3. Manual review: Remaining unmatched deals")
    
    # Additional insights
    print("\n\n=== Additional Insights ===")
    
    # Check date formats
    print("\nDate format analysis:")
    hs_date_sample = hs_deals['Close Date'].dropna().head()
    sc_date_sample = sc_df['Close Date'].dropna().head()
    print("HubSpot date samples:", list(hs_date_sample))
    print("SalesCookie date samples:", list(sc_date_sample))
    
    # Company name variations
    print("\n\nCompany name variations to handle:")
    company_variations = {
        'OP Cooperative': ['OP', 'OP Financial Group'],
        'Kreditanstalt für Wiederaufbau': ['KfW'],
        'Deutsche Kreditbank Aktiengesellschaft': ['DKB', 'Deutsche Kreditbank'],
        'Investitionsbank': ['ILB', 'IBB', 'IBSH'],
    }
    
    for full_name, variations in company_variations.items():
        print(f"  {full_name}: {', '.join(variations)}")

if __name__ == '__main__':
    test_matching_strategies()