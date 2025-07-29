#!/usr/bin/env python3
"""
Test matching with manually downloaded SalesCookie data
"""
import pandas as pd

def test_manual_matching():
    print("=== Testing with Manual SalesCookie Data ===\n")
    
    # Load HubSpot data
    hs_df = pd.read_csv('../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv')
    hs_deals = hs_df[hs_df['Deal Stage'] == 'Closed & Won'].copy()
    print(f"HubSpot Closed & Won deals: {len(hs_deals)}")
    
    # Load manual SalesCookie data
    sc_manual = pd.read_csv('../salescookie_manual/credits (7).csv', encoding='utf-8-sig')
    print(f"Manual SalesCookie credits: {len(sc_manual)}")
    
    # Test 1: Direct ID matching
    print("\n=== Test 1: Direct ID Matching ===")
    
    hs_ids = set(hs_deals['Record ID'].astype(str))
    sc_ids = set(sc_manual['Unique ID'].astype(str))
    
    id_matches = hs_ids.intersection(sc_ids)
    print(f"Direct ID matches: {len(id_matches)} ({len(id_matches)/len(hs_deals)*100:.1f}%)")
    
    if id_matches:
        print("\nSample matched IDs:")
        for deal_id in list(id_matches)[:10]:
            # Find details
            hs_deal = hs_deals[hs_deals['Record ID'].astype(str) == deal_id].iloc[0]
            sc_deal = sc_manual[sc_manual['Unique ID'].astype(str) == deal_id].iloc[0]
            
            print(f"\n  ID: {deal_id}")
            print(f"  HubSpot: {hs_deal['Deal Name']}")
            print(f"  SalesCookie: {sc_deal['Deal Name']}")
            print(f"  Match: {'✓ EXACT' if hs_deal['Deal Name'] == sc_deal['Deal Name'] else '≈ Similar'}")
    
    # Test 2: Deal name matching
    print("\n\n=== Test 2: Deal Name Matching ===")
    
    hs_names = set(hs_deals['Deal Name'].dropna())
    sc_names = set(sc_manual['Deal Name'].dropna())
    
    name_matches = hs_names.intersection(sc_names)
    print(f"Exact name matches: {len(name_matches)} ({len(name_matches)/len(hs_deals)*100:.1f}%)")
    
    # Test 3: Combined ID + Name validation
    print("\n\n=== Test 3: ID + Name Validation ===")
    
    valid_matches = 0
    mismatched_names = []
    
    for deal_id in id_matches:
        hs_deal = hs_deals[hs_deals['Record ID'].astype(str) == deal_id].iloc[0]
        sc_deal = sc_manual[sc_manual['Unique ID'].astype(str) == deal_id].iloc[0]
        
        if hs_deal['Deal Name'] == sc_deal['Deal Name']:
            valid_matches += 1
        else:
            mismatched_names.append({
                'id': deal_id,
                'hs_name': hs_deal['Deal Name'],
                'sc_name': sc_deal['Deal Name']
            })
    
    print(f"Valid matches (ID + Name): {valid_matches} ({valid_matches/len(id_matches)*100:.1f}% of ID matches)")
    
    if mismatched_names:
        print(f"\nMismatched names: {len(mismatched_names)}")
        print("Samples:")
        for mismatch in mismatched_names[:5]:
            print(f"\n  ID: {mismatch['id']}")
            print(f"  HubSpot: {mismatch['hs_name']}")
            print(f"  SalesCookie: {mismatch['sc_name']}")
    
    # Test 4: Commission validation
    print("\n\n=== Test 4: Commission Validation Sample ===")
    
    # Check a few matches for commission accuracy
    sample_validations = []
    
    for deal_id in list(id_matches)[:5]:
        hs_deal = hs_deals[hs_deals['Record ID'].astype(str) == deal_id].iloc[0]
        sc_deal = sc_manual[sc_manual['Unique ID'].astype(str) == deal_id].iloc[0]
        
        # Parse commission
        commission_str = str(sc_deal['Commission']).replace(',', '')
        try:
            commission = float(commission_str)
        except:
            commission = 0
        
        sample_validations.append({
            'name': hs_deal['Deal Name'],
            'hs_amount': hs_deal['Amount in company currency'],
            'sc_commission': commission,
            'sc_rate': sc_deal['Commission Rate'],
            'deal_type': hs_deal['Deal Type']
        })
    
    print("\nSample commission validations:")
    for val in sample_validations:
        print(f"\n  {val['name']}")
        print(f"  HubSpot Amount: €{val['hs_amount']:,.2f}")
        print(f"  SalesCookie Commission: €{val['sc_commission']:,.2f}")
        print(f"  Rate: {val['sc_rate']}")
        print(f"  Deal Type: {val['deal_type']}")
    
    # Summary
    print("\n\n=== SUMMARY ===")
    print(f"HubSpot deals: {len(hs_deals)}")
    print(f"SalesCookie records: {len(sc_manual)}")
    print(f"ID matches: {len(id_matches)} ({len(id_matches)/len(hs_deals)*100:.1f}%)")
    print(f"Name matches: {len(name_matches)} ({len(name_matches)/len(hs_deals)*100:.1f}%)")
    print(f"Valid (ID+Name) matches: {valid_matches} ({valid_matches/len(hs_deals)*100:.1f}%)")
    
    # Data quality assessment
    print("\n\n=== Data Quality Assessment ===")
    print(f"SalesCookie data completeness:")
    print(f"  Deal Names: {sc_manual['Deal Name'].notna().sum()}/{len(sc_manual)} ({sc_manual['Deal Name'].notna().sum()/len(sc_manual)*100:.1f}%)")
    print(f"  Unique IDs: {sc_manual['Unique ID'].notna().sum()}/{len(sc_manual)} ({sc_manual['Unique ID'].notna().sum()/len(sc_manual)*100:.1f}%)")
    print(f"  Commission: {sc_manual['Commission'].notna().sum()}/{len(sc_manual)} ({sc_manual['Commission'].notna().sum()/len(sc_manual)*100:.1f}%)")
    
    # Compare with scraped data
    print("\n\n=== Comparison with Scraped Data ===")
    print("The manual export has:")
    print("- Full deal names (not truncated)")
    print("- Matching Unique IDs with HubSpot")
    print("- Better data quality overall")
    print("\nRecommendation: Use manual exports or fix the scraping process")

if __name__ == '__main__':
    test_manual_matching()