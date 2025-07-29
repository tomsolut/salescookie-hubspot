#!/usr/bin/env python3
"""
Analyze Q3 2025 data specifically
"""
import pandas as pd
from datetime import datetime

def analyze_q3_2025():
    print("📊 Q3 2025 Commission Reconciliation Analysis")
    print("=" * 60)
    
    # Read HubSpot data
    print("\n1. HubSpot Q3 2025 Deals:")
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_deals = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    
    # Parse dates
    hs_deals['Close Date'] = pd.to_datetime(hs_deals['Close Date'])
    
    # Filter for Q3 2025 (July-September 2025)
    q3_2025_deals = hs_deals[
        (hs_deals['Close Date'] >= '2025-07-01') & 
        (hs_deals['Close Date'] <= '2025-09-30')
    ]
    
    print(f"   Total deals: {len(q3_2025_deals)}")
    print(f"   Total amount: €{q3_2025_deals['Amount in company currency'].sum():,.2f}")
    
    # Show deal details
    print("\n   Deal Details:")
    for idx, deal in q3_2025_deals.iterrows():
        print(f"   - {deal['Deal Name']}")
        print(f"     ID: {deal['Record ID']}")
        print(f"     Amount: €{deal['Amount in company currency']:,.2f}")
        print(f"     Close Date: {deal['Close Date'].strftime('%Y-%m-%d')}")
        print(f"     Type: {deal.get('Deal Type', 'N/A')}")
        print()
    
    # Read SalesCookie data
    print("\n2. SalesCookie Q3 2025 Credits:")
    sc_df = pd.read_csv('../salescookie_manual/credits (7).csv', encoding='utf-8-sig')
    
    # Parse commission amounts
    sc_df['Commission_Numeric'] = sc_df['Commission'].apply(
        lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
    )
    
    print(f"   Total transactions: {len(sc_df)}")
    print(f"   Total commission: €{sc_df['Commission_Numeric'].sum():,.2f}")
    
    # Parse dates in SalesCookie
    sc_df['Close Date'] = pd.to_datetime(sc_df['Close Date'], errors='coerce')
    
    # Group by month
    if 'Close Date' in sc_df.columns:
        sc_by_month = sc_df.groupby(sc_df['Close Date'].dt.to_period('M'))['Commission_Numeric'].agg(['count', 'sum'])
        print("\n   Transactions by month:")
        for month, data in sc_by_month.iterrows():
            print(f"   - {month}: {data['count']} transactions, €{data['sum']:,.2f} commission")
    
    # Check for matching IDs
    print("\n3. Matching Analysis:")
    hs_ids = set(str(id) for id in q3_2025_deals['Record ID'])
    sc_ids = set(str(id) for id in sc_df['Unique ID'] if pd.notna(id))
    
    matches = hs_ids.intersection(sc_ids)
    print(f"   HubSpot Q3 2025 deal IDs: {hs_ids}")
    print(f"   SalesCookie IDs in export: {len(sc_ids)} unique IDs")
    print(f"   Matching IDs: {matches if matches else 'None'}")
    
    # Show some SalesCookie records
    print("\n   Sample SalesCookie records:")
    for idx, row in sc_df.head(5).iterrows():
        print(f"   - {row['Deal Name']}")
        print(f"     ID: {row['Unique ID']}")
        print(f"     Commission: €{row['Commission_Numeric']:,.2f}")
        if pd.notna(row['Close Date']):
            print(f"     Close Date: {row['Close Date'].strftime('%Y-%m-%d')}")
        print()
    
    print("\n4. Summary:")
    print(f"   - HubSpot has {len(q3_2025_deals)} Q3 2025 deals")
    print(f"   - SalesCookie export has {len(sc_df)} transactions")
    print(f"   - Only {len(matches)} direct ID matches found")
    print("\n   This suggests the SalesCookie export contains:")
    print("   - Deals from different periods (not just Q3 2025)")
    print("   - Or uses different criteria for including deals")
    print("   - Or there's a timing difference in when deals appear")

if __name__ == '__main__':
    analyze_q3_2025()