#!/usr/bin/env python3
"""
Test withholding reconciliation functionality
"""
import pandas as pd
from datetime import datetime
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2
from reconciliation_engine_v3 import ReconciliationEngineV3
import os

def test_withholding_reconciliation():
    """Test reconciliation with withholding data"""
    
    # 1. Load HubSpot data
    print("📊 Loading HubSpot data...")
    hubspot_file = "../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv"
    
    if not os.path.exists(hubspot_file):
        print("❌ HubSpot file not found")
        return
        
    hs_parser = HubSpotParser(hubspot_file)
    hubspot_deals = hs_parser.parse()
    print(f"✅ Loaded {len(hubspot_deals)} HubSpot deals")
    
    # 2. Load multiple types of SalesCookie data
    print("\n💰 Loading SalesCookie data...")
    sc_parser = SalesCookieParserV2()
    all_transactions = []
    
    # Load regular Q3 2025 data
    regular_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/credits q3-2025.csv"
    if os.path.exists(regular_file):
        transactions, quality = sc_parser.parse_file(regular_file)
        all_transactions.extend(transactions)
        print(f"✅ Loaded {len(transactions)} regular transactions (Q3 2025)")
    
    # Load withholding data
    withholding_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/withholdings q3-2025.csv"
    if os.path.exists(withholding_file):
        transactions, quality = sc_parser.parse_file(withholding_file)
        all_transactions.extend(transactions)
        print(f"✅ Loaded {len(transactions)} withholding transactions")
    
    # Load forecast data
    forecast_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/Estimated credits 2025.csv"
    if os.path.exists(forecast_file):
        transactions, quality = sc_parser.parse_file(forecast_file)
        all_transactions.extend(transactions)
        print(f"✅ Loaded {len(transactions)} forecast transactions")
    
    # Load split data
    split_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/credits split 2024 q3-2025.csv"
    if os.path.exists(split_file):
        transactions, quality = sc_parser.parse_file(split_file)
        all_transactions.extend(transactions)
        print(f"✅ Loaded {len(transactions)} split transactions")
    
    # 3. Run enhanced reconciliation
    print("\n🔄 Running enhanced reconciliation...")
    engine = ReconciliationEngineV3(hubspot_deals, all_transactions)
    results = engine.reconcile(100.0)
    
    # 4. Display results
    summary = results.summary
    print(f"\n📊 RECONCILIATION RESULTS")
    print("=" * 70)
    print(f"✓ Matched {summary['matched_deals_count']} deals")
    print(f"ℹ️ Centrally Processed (CPI/Fix): {summary['centrally_processed_count']} transactions")
    print(f"⚠️ Discrepancies: {summary['total_discrepancies']}")
    print(f"💸 Total impact: €{summary['total_impact']:,.2f}")
    
    # 5. Display withholding summary
    if 'withholding_summary' in summary:
        wh_summary = summary['withholding_summary']
        print(f"\n📊 WITHHOLDING SUMMARY")
        print("=" * 70)
        print(f"💰 Total paid (50%): €{wh_summary['total_paid']:,.2f}")
        print(f"🔒 Total withheld: €{wh_summary['total_withheld']:,.2f}")
        print(f"💸 Full commission: €{wh_summary['total_full_commission']:,.2f}")
        
    # 6. Display forecast summary
    if 'forecast_summary' in summary:
        fc_summary = summary['forecast_summary']
        print(f"\n📊 FORECAST SUMMARY")
        print("=" * 70)
        print(f"📈 Total forecast: €{fc_summary['total_forecast_amount']:,.2f}")
        print(f"🎯 Total kickers: €{fc_summary['total_kickers']:,.2f}")
        print(f"🏆 Deals with kickers: {fc_summary['deals_with_kickers']}")
        
    # 7. Show top discrepancies
    if results.discrepancies:
        print(f"\n⚠️ TOP DISCREPANCIES")
        print("=" * 70)
        
        # Sort by impact
        top_discrepancies = sorted(results.discrepancies, key=lambda d: d.impact_eur, reverse=True)[:5]
        
        for disc in top_discrepancies:
            print(f"\n{disc.deal_name}")
            print(f"  Type: {disc.discrepancy_type}")
            print(f"  Expected: {disc.expected_value}")
            print(f"  Actual: {disc.actual_value}")
            print(f"  Impact: €{disc.impact_eur:,.2f}")
            print(f"  Details: {disc.details}")

if __name__ == "__main__":
    test_withholding_reconciliation()