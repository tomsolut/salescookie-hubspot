#!/usr/bin/env python3
"""
Analyze all quarterly SalesCookie credit files
"""
import pandas as pd
import os
from datetime import datetime
import glob

def analyze_all_quarters():
    """Analyze all quarterly credit files from SalesCookie"""
    print("📊 SalesCookie Quarterly Credits Analysis")
    print("=" * 70)
    
    # Find all credit files
    credit_files = glob.glob('../salescookie_manual/credits*.csv')
    credit_files.sort()
    
    print(f"\nFound {len(credit_files)} quarterly credit files:")
    for f in credit_files:
        print(f"  - {os.path.basename(f)}")
    
    # Process each file
    all_data = []
    quarterly_summary = []
    
    for file_path in credit_files:
        print(f"\n\nProcessing: {os.path.basename(file_path)}")
        print("-" * 50)
        
        try:
            # Read file
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # Extract quarter info from filename
            filename = os.path.basename(file_path)
            quarter_info = filename.replace('credits', '').replace('.csv', '').strip()
            
            # Parse commission amounts
            if 'Commission' in df.columns:
                df['Commission_Numeric'] = df['Commission'].apply(
                    lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                )
            else:
                df['Commission_Numeric'] = 0
            
            # Add quarter info
            df['Quarter'] = quarter_info
            df['Source_File'] = filename
            
            # Calculate summary statistics
            total_transactions = len(df)
            total_commission = df['Commission_Numeric'].sum()
            
            # Count CPI/Fix deals
            cpi_count = 0
            if 'Deal Name' in df.columns:
                cpi_mask = df['Deal Name'].str.lower().str.contains('cpi increase|fix increase|indexation', na=False)
                cpi_count = cpi_mask.sum()
                cpi_commission = df[cpi_mask]['Commission_Numeric'].sum()
            else:
                cpi_commission = 0
            
            regular_count = total_transactions - cpi_count
            regular_commission = total_commission - cpi_commission
            
            print(f"  Total transactions: {total_transactions}")
            print(f"  Total commission: €{total_commission:,.2f}")
            print(f"  - CPI/Fix deals: {cpi_count} (€{cpi_commission:,.2f})")
            print(f"  - Regular deals: {regular_count} (€{regular_commission:,.2f})")
            
            # Check for unique IDs
            if 'Unique ID' in df.columns:
                unique_ids = df['Unique ID'].notna().sum()
                print(f"  Records with Unique ID: {unique_ids}/{total_transactions}")
            
            # Store summary
            quarterly_summary.append({
                'Quarter': quarter_info,
                'File': filename,
                'Total_Transactions': total_transactions,
                'Total_Commission': total_commission,
                'CPI_Count': cpi_count,
                'CPI_Commission': cpi_commission,
                'Regular_Count': regular_count,
                'Regular_Commission': regular_commission
            })
            
            # Add to all data
            all_data.append(df)
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n\n📈 COMBINED STATISTICS")
        print("=" * 70)
        print(f"Total records across all quarters: {len(combined_df)}")
        print(f"Total commission: €{combined_df['Commission_Numeric'].sum():,.2f}")
        
        # Show quarterly summary
        print("\n📊 Quarterly Summary:")
        print("-" * 70)
        print(f"{'Quarter':<15} {'Transactions':>12} {'Total Comm':>15} {'CPI/Fix':>10} {'Regular':>10}")
        print("-" * 70)
        
        for qs in quarterly_summary:
            print(f"{qs['Quarter']:<15} {qs['Total_Transactions']:>12} "
                  f"€{qs['Total_Commission']:>14,.2f} {qs['CPI_Count']:>10} {qs['Regular_Count']:>10}")
        
        # Show totals
        print("-" * 70)
        total_trans = sum(qs['Total_Transactions'] for qs in quarterly_summary)
        total_comm = sum(qs['Total_Commission'] for qs in quarterly_summary)
        total_cpi = sum(qs['CPI_Count'] for qs in quarterly_summary)
        total_regular = sum(qs['Regular_Count'] for qs in quarterly_summary)
        
        print(f"{'TOTAL':<15} {total_trans:>12} €{total_comm:>14,.2f} {total_cpi:>10} {total_regular:>10}")
        
        # Analyze date ranges
        if 'Close Date' in combined_df.columns:
            combined_df['Close Date'] = pd.to_datetime(combined_df['Close Date'], errors='coerce')
            date_range = combined_df['Close Date'].dropna()
            if not date_range.empty:
                print(f"\n📅 Date Range:")
                print(f"  Earliest: {date_range.min().strftime('%Y-%m-%d')}")
                print(f"  Latest: {date_range.max().strftime('%Y-%m-%d')}")
        
        # Save combined data
        output_file = './all_salescookie_credits.csv'
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 Combined data saved to: {output_file}")
        
        return combined_df, quarterly_summary
    
    return None, None

def compare_with_hubspot():
    """Compare combined SalesCookie data with HubSpot"""
    print("\n\n🔄 Comparing with HubSpot Data")
    print("=" * 70)
    
    # Read HubSpot data
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_closed = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    hs_closed['Close Date'] = pd.to_datetime(hs_closed['Close Date'])
    
    # Group by quarter
    hs_closed['Quarter'] = hs_closed['Close Date'].dt.to_period('Q')
    hs_by_quarter = hs_closed.groupby('Quarter').agg({
        'Record ID': 'count',
        'Amount in company currency': 'sum'
    }).rename(columns={'Record ID': 'Deal_Count', 'Amount in company currency': 'Total_Amount'})
    
    print("\nHubSpot Closed & Won Deals by Quarter:")
    print("-" * 50)
    for quarter, data in hs_by_quarter.iterrows():
        print(f"{quarter}: {data['Deal_Count']} deals, €{data['Total_Amount']:,.2f}")
    
    print(f"\nTotal HubSpot Closed & Won: {len(hs_closed)} deals, €{hs_closed['Amount in company currency'].sum():,.2f}")

if __name__ == '__main__':
    combined_data, quarterly_summary = analyze_all_quarters()
    if combined_data is not None:
        compare_with_hubspot()