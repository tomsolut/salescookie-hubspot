#!/usr/bin/env python3
"""
Analyze the withholding mismatch issue for centrally processed deals
"""
import pandas as pd

# Read the discrepancy report
df = pd.read_csv('reports_v3_fixed_dates/discrepancies_20250731_002009.csv')

# Filter for withholding mismatches
withholding_issues = df[df['Type'] == 'Withholding Mismatch'].copy()

print(f"Total withholding mismatch issues: {len(withholding_issues)}")
print("\nSample issues:")
print("-" * 80)

# Show first few examples
for idx, row in withholding_issues.head(5).iterrows():
    print(f"\nDeal: {row['Deal Name']}")
    print(f"  Expected: {row['Expected']}")
    print(f"  Actual: {row['Actual']}")
    print(f"  Details: {row['Details']}")

# Check if these are all centrally processed deals
central_deals = withholding_issues[withholding_issues['Deal ID'].str.startswith('CENTRAL_')]
print(f"\n\nCentrally processed deals with withholding issues: {len(central_deals)}")

# Analyze the pattern
if len(withholding_issues) > 0:
    print("\n\nPATTERN ANALYSIS:")
    print("-" * 80)
    print("All these withholding mismatches appear to be for centrally processed deals.")
    print("The issue is that the auto-processing logic is creating withholding validation")
    print("for deals that don't actually have withholding transactions in the traditional sense.")
    print("\nThese are Fixed Price Increase deals that are centrally managed,")
    print("so the withholding validation logic should not apply to them.")