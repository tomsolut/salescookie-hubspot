#!/usr/bin/env python3
"""
Simple test for v3 reconciliation with regular credits only
"""
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2
from reconciliation_engine_v3 import ReconciliationEngineV3
from report_generator_v2 import ReportGeneratorV2
from dataclasses import asdict

def test_simple():
    # Load some HubSpot deals
    hs_parser = HubSpotParser("../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv")
    hubspot_deals = hs_parser.parse()[:10]  # Just 10 deals for testing
    
    # Load Q3 2025 credits (these are being detected as forecast, but let's test anyway)
    sc_parser = SalesCookieParserV2()
    transactions, quality = sc_parser.parse_file("/Users/thomasbieth/hubspot_salescookie/salescookie_manual/credits q3-2025.csv")
    
    print(f"Loaded {len(hubspot_deals)} HubSpot deals")
    print(f"Loaded {len(transactions)} SalesCookie transactions")
    print(f"Transaction types: {set(t.get('transaction_type') for t in transactions)}")
    
    # Run reconciliation
    engine = ReconciliationEngineV3(hubspot_deals, transactions)
    results = engine.reconcile(90.0)
    
    print(f"Matches: {len(results.matches)}")
    print(f"Discrepancies: {len(results.discrepancies)}")
    
    # Convert to dict properly
    results_dict = {
        'summary': results.summary,
        'discrepancies': [asdict(d) for d in results.discrepancies],  # Use asdict instead of vars
        'matched_deals': [
            {
                'hubspot_id': m.hubspot_id,
                'salescookie_id': m.salescookie_id,
                'match_type': m.match_type,
                'confidence': m.confidence,
                'hubspot_deal': m.hubspot_deal,
                'salescookie_transactions': m.salescookie_transactions,
            }
            for m in results.matches
        ],
        'unmatched_hubspot': results.unmatched_hubspot,
        'unmatched_salescookie': results.unmatched_salescookie,
    }
    
    # Generate report
    report_gen = ReportGeneratorV2("./test_reports")
    try:
        report_paths = report_gen.generate_reports(results_dict)
        print(f"Reports generated successfully: {report_paths}")
    except Exception as e:
        print(f"Error generating reports: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()