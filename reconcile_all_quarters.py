#!/usr/bin/env python3
"""
Reconcile all quarterly SalesCookie data with HubSpot
"""
import pandas as pd
from datetime import datetime
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2, DataSource
from reconciliation_engine_v2 import ReconciliationEngineV2
from report_generator import ReportGenerator
import os

def main():
    print("🚀 Comprehensive Commission Reconciliation - All Quarters")
    print("=" * 70)
    
    # 1. Load HubSpot data
    print("\n📊 Loading HubSpot data...")
    hs_parser = HubSpotParser('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hubspot_deals = hs_parser.parse()
    hs_summary = hs_parser.summary()
    
    print(f"  ✓ Found {hs_summary['total_deals']} Closed & Won deals")
    print(f"  ✓ Total amount: €{hs_summary['total_amount']:,.2f}")
    
    # 2. Load all SalesCookie data
    print("\n💰 Loading all SalesCookie quarterly data...")
    
    # Read the combined file we just created
    all_sc_data = pd.read_csv('./all_salescookie_credits.csv', encoding='utf-8-sig')
    
    # Convert to format expected by reconciliation engine
    sc_parser = SalesCookieParserV2()
    all_transactions = []
    
    for idx, row in all_sc_data.iterrows():
        # Parse each row as a transaction
        transaction = {
            'salescookie_id': str(row.get('Unique ID', '')),
            'deal_name': row.get('Deal Name', ''),
            'customer': row.get('Customer', ''),
            'close_date': pd.to_datetime(row.get('Close Date'), errors='coerce'),
            'revenue_start_date': pd.to_datetime(row.get('Revenue Start Date'), errors='coerce'),
            'commission_amount': float(row.get('Commission_Numeric', 0)),
            'commission_currency': row.get('Commission Currency', 'EUR'),
            'commission_rate': sc_parser._parse_rate(row.get('Commission Rate')),
            'commission_details': row.get('Commission Details', ''),
            'deal_type': row.get('Deal Type', ''),
            'acv_eur': sc_parser._parse_amount(row.get('ACV (EUR)')),
            'currency': row.get('Currency', 'EUR'),
            'types_of_acv': row.get('Types of ACV', ''),
            'product_name': row.get('Product Name', ''),
            'has_split': str(row.get('Split', '')).lower() == 'yes',
            'is_ps_deal': sc_parser._is_ps_deal(row),
            'data_source': 'manual',
            'quarter': row.get('Quarter', ''),
        }
        
        # Extract company info
        transaction['company_id'], transaction['company_name'] = sc_parser._extract_customer_info(transaction['customer'])
        
        all_transactions.append(transaction)
    
    print(f"  ✓ Loaded {len(all_transactions)} total transactions")
    
    # 3. Run reconciliation
    print("\n🔄 Running comprehensive reconciliation...")
    engine = ReconciliationEngineV2(hubspot_deals, all_transactions)
    results = engine.reconcile(100.0)
    
    summary = results.summary
    
    # 4. Display results
    print(f"\n📊 RECONCILIATION RESULTS")
    print("=" * 70)
    print(f"  ✓ Matched {summary['matched_deals_count']} deals")
    print(f"  ℹ️  Centrally Processed (CPI/Fix): {summary['centrally_processed_count']} transactions")
    print(f"  ⚠️  Discrepancies: {summary['total_discrepancies']}")
    print(f"  💸 Total impact: €{summary['total_impact']:,.2f}")
    
    if summary['matches_by_type']:
        print("\n  Match types:")
        for match_type, count in summary['matches_by_type'].items():
            print(f"    - {match_type}: {count}")
        print(f"    - Average confidence: {summary['average_match_confidence']:.1f}%")
    
    # 5. Analyze by quarter
    print("\n📅 Quarterly Analysis:")
    print("-" * 70)
    
    # Group matches by quarter
    quarter_analysis = {}
    
    for match in results.matches:
        hs_deal = match.hubspot_deal
        close_date = hs_deal.get('close_date')
        if close_date:
            quarter = f"{close_date.year}Q{(close_date.month-1)//3 + 1}"
            if quarter not in quarter_analysis:
                quarter_analysis[quarter] = {
                    'matched': 0,
                    'commission': 0,
                    'hubspot_amount': 0
                }
            quarter_analysis[quarter]['matched'] += 1
            quarter_analysis[quarter]['hubspot_amount'] += hs_deal.get('commission_amount', 0)
            # Sum commission from SC transactions
            for sc_trans in match.salescookie_transactions:
                quarter_analysis[quarter]['commission'] += sc_trans.get('commission_amount', 0)
    
    # Display quarterly results
    print(f"{'Quarter':<10} {'Matched':>10} {'HS Amount':>15} {'SC Commission':>15}")
    print("-" * 70)
    
    for quarter in sorted(quarter_analysis.keys()):
        data = quarter_analysis[quarter]
        print(f"{quarter:<10} {data['matched']:>10} "
              f"€{data['hubspot_amount']:>14,.2f} €{data['commission']:>14,.2f}")
    
    # 6. Generate comprehensive report
    print("\n📄 Generating comprehensive reports...")
    
    output_dir = './reports_all_quarters'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert results for report generator
    legacy_results = {
        'summary': summary,
        'discrepancies': results.discrepancies,
        'matched_deals': [
            {
                'hubspot': match.hubspot_deal,
                'salescookie': match.salescookie_transactions,
                'confidence': match.confidence,
                'match_type': match.match_type
            }
            for match in results.matches
        ]
    }
    
    generator = ReportGenerator(output_dir)
    report_paths = generator.generate_reports(legacy_results)
    
    print("  ✓ Reports generated:")
    print(f"    - Excel: {report_paths['excel']}")
    print(f"    - Summary: {report_paths['text']}")
    print(f"    - CSV: {report_paths['csv']}")
    
    # 7. Summary statistics
    print("\n✨ Summary:")
    match_rate = (summary['matched_deals_count'] / summary['hubspot_deals_count']) * 100
    print(f"  - Overall match rate: {match_rate:.1f}%")
    print(f"  - Unmatched HubSpot deals: {summary['unmatched_hubspot_count']}")
    print(f"  - Unmatched SalesCookie: {summary['unmatched_salescookie_count']} (excl. CPI/Fix)")
    
    if summary['total_discrepancies'] > 0:
        print("\n  Discrepancy breakdown:")
        for disc_type, data in summary['discrepancies_by_type'].items():
            print(f"    - {disc_type.replace('_', ' ').title()}: {data['count']} (€{data['impact']:,.2f})")

if __name__ == '__main__':
    main()