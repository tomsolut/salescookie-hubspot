#!/usr/bin/env python3
"""
Direct reconciliation runner for manual exports
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2, DataSource
from reconciliation_engine_v2 import ReconciliationEngineV2
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run reconciliation with manual SalesCookie export"""
    # File paths
    hubspot_file = '../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv'
    salescookie_file = '../salescookie_manual/credits (7).csv'
    output_dir = './reports'
    
    print("🚀 Starting Commission Reconciliation with Manual Export...")
    
    try:
        # 1. Parse HubSpot data
        print("\n📊 Parsing HubSpot data...")
        hs_parser = HubSpotParser(hubspot_file)
        hubspot_deals = hs_parser.parse()
        hs_summary = hs_parser.summary()
        
        print(f"  ✓ Found {hs_summary['total_deals']} Closed & Won deals")
        print(f"  ✓ Total amount: €{hs_summary['total_amount']:,.2f}")
        print(f"  ✓ PS deals: {hs_summary['ps_deals_count']}")
        
        # 2. Parse SalesCookie manual export
        print("\n💰 Parsing SalesCookie manual export...")
        sc_parser = SalesCookieParserV2()
        transactions, quality = sc_parser.parse_file(salescookie_file, DataSource.MANUAL)
        
        print(f"  ✓ Loaded {len(transactions)} transactions")
        print(f"  ✓ Data quality score: {quality.quality_score:.1f}/100")
        
        if quality.warnings:
            print("\n  ⚠️  Data Quality Warnings:")
            for warning in quality.warnings:
                print(f"    - {warning}")
        
        # 3. Run reconciliation
        print("\n🔄 Running reconciliation...")
        engine = ReconciliationEngineV2(hubspot_deals, transactions)
        results = engine.reconcile(quality.quality_score)
        
        summary = results.summary
        print(f"  ✓ Matched {summary['matched_deals_count']} deals")
        
        if summary['matches_by_type']:
            print("\n  Match types:")
            for match_type, count in summary['matches_by_type'].items():
                print(f"    - {match_type}: {count}")
            print(f"    - Average confidence: {summary['average_match_confidence']:.1f}%")
        
        print(f"\n  ⚠️  Found {summary['total_discrepancies']} discrepancies")
        
        if summary['total_discrepancies'] > 0:
            print(f"  💸 Total impact: €{summary['total_impact']:,.2f}")
            
            # Show discrepancy breakdown
            print("\n  Discrepancies by type:")
            for disc_type, data in summary['discrepancies_by_type'].items():
                print(f"    - {disc_type.replace('_', ' ').title()}: {data['count']} (€{data['impact']:,.2f})")
        
        # 4. Generate reports
        print("\n📄 Generating reports...")
        
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
        
        # 5. Show detailed discrepancies
        if results.discrepancies:
            print("\n🔍 Detailed Discrepancies:")
            for i, disc in enumerate(results.discrepancies[:10], 1):  # Show first 10
                print(f"\n  {i}. {disc.deal_name}")
                print(f"     Type: {disc.discrepancy_type}")
                print(f"     Expected: {disc.expected_value}")
                print(f"     Actual: {disc.actual_value}")
                print(f"     Impact: €{disc.impact_eur:,.2f}")
                print(f"     Confidence: {disc.match_confidence:.0f}%")
        
        # 6. Summary
        print("\n✨ Reconciliation Complete!")
        
        if summary['total_discrepancies'] == 0:
            print("\n✅ All commissions are correctly calculated and recorded!")
        else:
            print(f"\n⚠️  Found {summary['total_discrepancies']} issues requiring attention")
            print(f"   Total financial impact: €{summary['total_impact']:,.2f}")
        
        # Show match statistics
        match_rate = (summary['matched_deals_count'] / summary['hubspot_deals_count']) * 100
        print(f"\n📊 Match Statistics:")
        print(f"   - Match rate: {match_rate:.1f}%")
        print(f"   - Unmatched HubSpot deals: {summary['unmatched_hubspot_count']}")
        print(f"   - Unmatched SalesCookie transactions: {summary['unmatched_salescookie_count']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Reconciliation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()