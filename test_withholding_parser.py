#!/usr/bin/env python3
"""
Test script for withholding and forecast parser functionality
"""
from salescookie_parser_v2 import SalesCookieParserV2, TransactionType
import os

def test_withholding_detection():
    """Test detection and parsing of withholding files"""
    parser = SalesCookieParserV2()
    
    # Test withholding file
    withholding_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/withholdings q3-2025.csv"
    
    if os.path.exists(withholding_file):
        print(f"\n🔍 Testing withholding file: {os.path.basename(withholding_file)}")
        transactions, quality = parser.parse_file(withholding_file)
        
        if transactions:
            print(f"✅ Parsed {len(transactions)} transactions")
            print(f"📊 Data quality score: {quality.quality_score:.1f}/100")
            
            # Check first transaction
            if len(transactions) > 0:
                t = transactions[0]
                print(f"\n📄 First transaction details:")
                print(f"  - Deal: {t.get('deal_name')}")
                print(f"  - Type: {t.get('transaction_type')}")
                print(f"  - Commission: €{t.get('commission_amount', 0):,.2f}")
                print(f"  - Est. Commission: €{t.get('est_commission', 0):,.2f}")
                print(f"  - Withholding Ratio: {t.get('withholding_ratio', 1.0):.2%}")
                
    # Test forecast file
    forecast_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/Estimated credits 2025.csv"
    
    if os.path.exists(forecast_file):
        print(f"\n🔍 Testing forecast file: {os.path.basename(forecast_file)}")
        transactions, quality = parser.parse_file(forecast_file)
        
        if transactions:
            print(f"✅ Parsed {len(transactions)} transactions")
            print(f"📊 Data quality score: {quality.quality_score:.1f}/100")
            
            # Check first transaction with kickers
            for t in transactions[:5]:
                if any(t.get(k, 0) > 0 for k in ['early_bird_kicker', 'performance_kicker', 'campaign_kicker']):
                    print(f"\n📄 Transaction with kickers:")
                    print(f"  - Deal: {t.get('deal_name')}")
                    print(f"  - Type: {t.get('transaction_type')}")
                    print(f"  - Early Bird: {t.get('early_bird_kicker', 0)}")
                    print(f"  - Performance: {t.get('performance_kicker', 0)}")
                    print(f"  - Campaign: {t.get('campaign_kicker', 0)}")
                    break
                    
    # Test split file
    split_file = "/Users/thomasbieth/hubspot_salescookie/salescookie_manual/credits split 2024 q3-2025.csv"
    
    if os.path.exists(split_file):
        print(f"\n🔍 Testing split file: {os.path.basename(split_file)}")
        transactions, quality = parser.parse_file(split_file)
        
        if transactions:
            print(f"✅ Parsed {len(transactions)} transactions")
            print(f"📊 Data quality score: {quality.quality_score:.1f}/100")
            print(f"📄 Transaction type: {transactions[0].get('transaction_type')}")

if __name__ == "__main__":
    test_withholding_detection()