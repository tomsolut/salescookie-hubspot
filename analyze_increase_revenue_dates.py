#!/usr/bin/env python3
"""
Analyze revenue start dates for CPI/FP increase deals
"""
import pandas as pd
from datetime import datetime
from collections import Counter

# Read the data
df = pd.read_csv('all_salescookie_credits.csv', encoding='utf-8-sig')

# Filter for CPI/FP increase deals
increase_deals = df[
    df['Deal Name'].str.contains('CPI Increase|FP Increase|Fixed Price Increase', 
                                case=False, na=False)
].copy()

print(f"Total CPI/FP Increase deals found: {len(increase_deals)}")
print("\n" + "="*80 + "\n")

# Parse dates
increase_deals['Close Date'] = pd.to_datetime(increase_deals['Close Date'], errors='coerce')
increase_deals['Revenue Start Date'] = pd.to_datetime(increase_deals['Revenue Start Date'], errors='coerce')

# Extract year and month
increase_deals['Close Year'] = increase_deals['Close Date'].dt.year
increase_deals['Close Month'] = increase_deals['Close Date'].dt.month
increase_deals['Revenue Year'] = increase_deals['Revenue Start Date'].dt.year
increase_deals['Revenue Month'] = increase_deals['Revenue Start Date'].dt.month
increase_deals['Revenue Day'] = increase_deals['Revenue Start Date'].dt.day

# Analyze revenue start patterns
print("REVENUE START DATE PATTERNS:")
print("-" * 40)
revenue_patterns = increase_deals.groupby(['Revenue Year', 'Revenue Month', 'Revenue Day']).size()
for (year, month, day), count in revenue_patterns.items():
    if pd.notna(year):
        print(f"{int(year):4d}-{int(month):02d}-{int(day):02d}: {count} deals")

print("\n" + "="*80 + "\n")

# Find deals NOT starting in January
non_january = increase_deals[increase_deals['Revenue Month'] != 1]
print(f"DEALS NOT STARTING IN JANUARY: {len(non_january)}")
print("-" * 40)
if len(non_january) > 0:
    for idx, row in non_january.iterrows():
        print(f"\nDeal: {row['Deal Name']}")
        print(f"  Close Date: {row['Close Date'].strftime('%Y-%m-%d') if pd.notna(row['Close Date']) else 'N/A'}")
        print(f"  Revenue Start: {row['Revenue Start Date'].strftime('%Y-%m-%d') if pd.notna(row['Revenue Start Date']) else 'N/A'}")
        acv = str(row['ACV (EUR)']).replace(',', '')
        try:
            acv_float = float(acv) if acv and acv != 'nan' else 0
            print(f"  ACV: €{acv_float:,.2f}")
        except:
            print(f"  ACV: {row['ACV (EUR)']}")
        
        commission = row.get('Commission', 0)
        if pd.notna(commission) and commission != 0:
            try:
                commission_float = float(str(commission).replace(',', ''))
                print(f"  Commission: €{commission_float:,.2f}")
            except:
                print(f"  Commission: {commission}")

print("\n" + "="*80 + "\n")

# Analyze close date to revenue start patterns
print("CLOSE DATE TO REVENUE START PATTERNS:")
print("-" * 40)
increase_deals['Revenue Delay'] = (
    increase_deals['Revenue Start Date'] - increase_deals['Close Date']
).dt.days

# Group by close month and show typical revenue start
close_to_revenue = increase_deals.groupby(['Close Month']).agg({
    'Revenue Month': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
    'Revenue Year': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
    'Deal Name': 'count'
}).rename(columns={'Deal Name': 'Count'})

print("Close Month → Typical Revenue Start")
for month in range(1, 13):
    if month in close_to_revenue.index:
        row = close_to_revenue.loc[month]
        if pd.notna(row['Revenue Month']):
            print(f"  Month {month:2d} → {int(row['Revenue Year'])}-{int(row['Revenue Month']):02d} ({row['Count']} deals)")

print("\n" + "="*80 + "\n")

# Expected pattern analysis
print("EXPECTED PATTERN ANALYSIS:")
print("-" * 40)
print("According to business rules:")
print("- CPI/FP increases are set twice per year")
print("- Revenue start should be January of the following year")
print("\nChecking compliance...")

# For each deal, check if revenue start is January of year after close
increase_deals['Expected Revenue Year'] = increase_deals['Close Year'] + 1
increase_deals['Is Compliant'] = (
    (increase_deals['Revenue Month'] == 1) & 
    (increase_deals['Revenue Year'] == increase_deals['Expected Revenue Year'])
)

compliant = increase_deals[increase_deals['Is Compliant']]
non_compliant = increase_deals[~increase_deals['Is Compliant']]

print(f"\nCompliant deals (January of following year): {len(compliant)} ({len(compliant)/len(increase_deals)*100:.1f}%)")
print(f"Non-compliant deals: {len(non_compliant)} ({len(non_compliant)/len(increase_deals)*100:.1f}%)")

if len(non_compliant) > 0:
    print("\nNON-COMPLIANT DEALS:")
    print("-" * 40)
    for idx, row in non_compliant.head(10).iterrows():
        print(f"\nDeal: {row['Deal Name']}")
        print(f"  Close: {row['Close Date'].strftime('%Y-%m-%d') if pd.notna(row['Close Date']) else 'N/A'}")
        print(f"  Revenue Start: {row['Revenue Start Date'].strftime('%Y-%m-%d') if pd.notna(row['Revenue Start Date']) else 'N/A'}")
        print(f"  Expected: {int(row['Expected Revenue Year'])}-01-01")
        print(f"  Issue: ", end="")
        if row['Revenue Month'] != 1:
            print(f"Wrong month ({int(row['Revenue Month'])})", end="")
        if row['Revenue Year'] != row['Expected Revenue Year']:
            print(f" Wrong year ({int(row['Revenue Year'])} vs {int(row['Expected Revenue Year'])})", end="")
        print()

# Save non-compliant deals for fixing
if len(non_compliant) > 0:
    non_compliant.to_csv('non_compliant_increase_deals.csv', index=False)
    print(f"\nSaved {len(non_compliant)} non-compliant deals to non_compliant_increase_deals.csv")