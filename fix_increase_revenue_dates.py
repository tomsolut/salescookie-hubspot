#!/usr/bin/env python3
"""
Fix revenue start dates for CPI/FP increase deals.
According to business rules:
- CPI/FP increases are set twice per year
- Revenue start should be January 1st of the following year
"""
import pandas as pd
from datetime import datetime
import sys

def fix_revenue_dates(input_file='all_salescookie_credits.csv', output_file='all_salescookie_credits_fixed.csv'):
    """Fix revenue start dates for CPI/FP increase deals"""
    
    print("Loading data...")
    # Read the data
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    # Create a copy for modifications
    df_fixed = df.copy()
    
    # Track changes
    changes_made = 0
    changes_log = []
    
    # Process each row
    for idx, row in df_fixed.iterrows():
        deal_name = str(row.get('Deal Name', ''))
        
        # Check if this is a CPI/FP increase deal
        if any(pattern in deal_name.lower() for pattern in ['cpi increase', 'fp increase', 'fixed price increase']):
            # Parse dates
            try:
                close_date = pd.to_datetime(row['Close Date'])
                revenue_start = pd.to_datetime(row['Revenue Start Date'])
                
                # Calculate expected revenue start date
                # Should be January 1st of the year following the close date
                expected_year = close_date.year + 1
                expected_revenue_start = pd.Timestamp(year=expected_year, month=1, day=1)
                
                # Check if correction is needed
                if revenue_start != expected_revenue_start:
                    # Log the change
                    changes_log.append({
                        'Deal': deal_name,
                        'Close Date': close_date.strftime('%Y-%m-%d'),
                        'Old Revenue Start': revenue_start.strftime('%Y-%m-%d'),
                        'New Revenue Start': expected_revenue_start.strftime('%Y-%m-%d'),
                        'ACV': row.get('ACV (EUR)', ''),
                        'Commission': row.get('Commission', '')
                    })
                    
                    # Make the correction
                    df_fixed.at[idx, 'Revenue Start Date'] = expected_revenue_start.strftime('%Y-%m-%d %H:%M:%S')
                    changes_made += 1
                    
            except Exception as e:
                print(f"Warning: Could not process dates for row {idx}: {deal_name}")
                print(f"  Error: {e}")
                continue
    
    print(f"\nProcessed {len(df_fixed)} rows")
    print(f"Found {changes_made} CPI/FP increase deals with incorrect revenue start dates")
    
    if changes_made > 0:
        # Save the fixed file
        df_fixed.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nFixed data saved to: {output_file}")
        
        # Save change log
        change_log_df = pd.DataFrame(changes_log)
        change_log_file = 'revenue_date_fixes.csv'
        change_log_df.to_csv(change_log_file, index=False)
        print(f"Change log saved to: {change_log_file}")
        
        # Print summary of changes
        print("\nSUMMARY OF CHANGES:")
        print("-" * 80)
        print(f"{'Deal':<60} {'Old Date':<12} {'New Date':<12}")
        print("-" * 80)
        
        for change in changes_log[:10]:  # Show first 10
            deal_short = change['Deal'][:58] + '..' if len(change['Deal']) > 60 else change['Deal']
            print(f"{deal_short:<60} {change['Old Revenue Start']:<12} {change['New Revenue Start']:<12}")
        
        if len(changes_log) > 10:
            print(f"\n... and {len(changes_log) - 10} more changes")
        
        # Group changes by old revenue start pattern
        print("\nCHANGES BY PATTERN:")
        print("-" * 40)
        pattern_counts = {}
        for change in changes_log:
            old_date = change['Old Revenue Start']
            pattern_counts[old_date] = pattern_counts.get(old_date, 0) + 1
        
        for date, count in sorted(pattern_counts.items()):
            print(f"  {date}: {count} deals")
            
    else:
        print("\nNo changes needed - all CPI/FP increase deals have correct revenue start dates!")
    
    return changes_made

if __name__ == "__main__":
    # Allow custom input/output files
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'all_salescookie_credits.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'all_salescookie_credits_fixed.csv'
    
    fix_revenue_dates(input_file, output_file)