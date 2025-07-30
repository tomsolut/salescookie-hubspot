#!/usr/bin/env python3
"""
Analyze ID mismatch between HubSpot and SalesCookie withholding data
"""
import pandas as pd
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2

def analyze_id_mismatch():
    """Check ID formats and matching"""
    
    # Load HubSpot data
    hs_parser = HubSpotParser("../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv")
    hubspot_deals = hs_parser.parse()
    
    # Load withholding data
    sc_parser = SalesCookieParserV2()
    withholding_txs, _ = sc_parser.parse_file("/Users/thomasbieth/hubspot_salescookie/salescookie_manual/withholdings q3-2025.csv")
    
    # Check ID formats
    print("📊 Sample HubSpot IDs:")
    for deal in hubspot_deals[:5]:
        print(f"  - {deal['hubspot_id']} : {deal['deal_name']}")
        
    print("\n📊 Sample Withholding IDs:")
    for tx in withholding_txs[:5]:
        print(f"  - {tx['salescookie_id']} : {tx['deal_name']}")
        
    # Try matching by deal name
    print("\n🔍 Checking deal name matches...")
    hs_names = {deal['deal_name'] for deal in hubspot_deals}
    wh_names = {tx['deal_name'] for tx in withholding_txs}
    
    matches = hs_names.intersection(wh_names)
    print(f"✅ Found {len(matches)} matching deal names")
    
    if matches:
        print("\nSample matches:")
        for name in list(matches)[:5]:
            print(f"  - {name}")

if __name__ == "__main__":
    analyze_id_mismatch()