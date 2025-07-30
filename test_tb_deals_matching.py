#!/usr/bin/env python3
"""
Test matching with tb-deals.csv to diagnose why IDs don't match
"""
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2
from reconciliation_engine_v3 import ReconciliationEngineV3
import logging

logging.basicConfig(level=logging.DEBUG)

def test_tb_deals_matching():
    print("Testing tb-deals.csv matching...")
    
    # Load HubSpot data from tb-deals.csv
    hs_parser = HubSpotParser('/Users/thomasbieth/hubspot_salescookie/salescookie_manual/tb-deals.csv')
    hubspot_deals = hs_parser.parse()
    print(f"Loaded {len(hubspot_deals)} HubSpot deals")
    
    # Show some HubSpot IDs
    print("\nSample HubSpot deal IDs:")
    for deal in hubspot_deals[:5]:
        print(f"  - ID: {deal['hubspot_id']}, Name: {deal['deal_name']}")
    
    # Load SalesCookie Q3 2025 data
    sc_parser = SalesCookieParserV2()
    transactions, quality = sc_parser.parse_file('/Users/thomasbieth/hubspot_salescookie/salescookie_manual/credits q3-2025.csv')
    print(f"\nLoaded {len(transactions)} SalesCookie transactions")
    
    # Show transaction types
    print("\nTransaction types:")
    tx_types = {}
    for tx in transactions:
        tx_type = tx.get('transaction_type', 'unknown')
        tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
    print(tx_types)
    
    # Filter out centrally processed transactions manually
    non_central = [tx for tx in transactions if 'cpi increase' not in tx.get('deal_name', '').lower()]
    print(f"\nNon-centrally processed transactions: {len(non_central)}")
    
    # Show SalesCookie IDs for non-central transactions
    print("\nSalesCookie IDs for non-central transactions:")
    for tx in non_central:
        print(f"  - ID: {tx.get('salescookie_id')}, Name: {tx.get('deal_name')}")
    
    # Check if any HubSpot deals have matching IDs
    hs_ids = {deal['hubspot_id'] for deal in hubspot_deals}
    sc_ids = {tx.get('salescookie_id') for tx in non_central}
    
    print(f"\nHubSpot has {len(hs_ids)} unique IDs")
    print(f"SalesCookie has {len(sc_ids)} unique IDs for non-central deals")
    
    # Find matches
    matches = hs_ids.intersection(sc_ids)
    print(f"\nDirect ID matches: {len(matches)}")
    if matches:
        print("Matching IDs:")
        for match_id in list(matches)[:5]:
            print(f"  - {match_id}")
    
    # Run reconciliation
    print("\n" + "="*50)
    print("Running reconciliation...")
    engine = ReconciliationEngineV3(hubspot_deals, transactions)
    results = engine.reconcile(90.0)
    
    print(f"\nResults:")
    print(f"  - Matches: {len(results.matches)}")
    print(f"  - Centrally Processed: {results.summary['centrally_processed_count']}")
    print(f"  - Discrepancies: {len(results.discrepancies)}")
    
    # Show matched deals
    if results.matches:
        print("\nMatched deals:")
        for match in results.matches[:5]:
            print(f"  - HubSpot ID: {match.hubspot_id}, SC ID: {match.salescookie_id}")
            print(f"    Deal: {match.hubspot_deal['deal_name']}")

if __name__ == "__main__":
    test_tb_deals_matching()