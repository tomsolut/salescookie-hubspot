#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced reconciliation tool
Tests all transaction types and matching scenarios
"""
import unittest
import pandas as pd
from datetime import datetime
from salescookie_parser_v2 import SalesCookieParserV2, TransactionType
from reconciliation_engine_v3 import ReconciliationEngineV3
from hubspot_parser import HubSpotParser
import tempfile
import os


class TestTransactionTypeDetection(unittest.TestCase):
    """Test transaction type detection logic"""
    
    def setUp(self):
        self.parser = SalesCookieParserV2()
    
    def test_regular_transaction_detection(self):
        """Test that regular transactions are correctly identified"""
        # Create test data with Performance Kicker
        data = {
            'Deal Name': ['Test Deal'],
            'Performance Kicker': [1.10],
            'Commission': [100],
            'Unique ID': ['12345']
        }
        df = pd.DataFrame(data)
        
        # Should be REGULAR, not FORECAST (Performance Kicker alone doesn't mean forecast)
        tx_type = self.parser.detect_transaction_type(df, 'credits_q3.csv')
        self.assertEqual(tx_type, TransactionType.REGULAR)
    
    def test_forecast_transaction_detection(self):
        """Test that forecast transactions are correctly identified by filename"""
        df = pd.DataFrame({'Deal Name': ['Test']})
        
        # Test various forecast filenames
        self.assertEqual(
            self.parser.detect_transaction_type(df, 'Estimated credits 2025.csv'),
            TransactionType.FORECAST
        )
        self.assertEqual(
            self.parser.detect_transaction_type(df, 'forecast_q4.csv'),
            TransactionType.FORECAST
        )
    
    def test_withholding_transaction_detection(self):
        """Test withholding transaction detection"""
        df = pd.DataFrame({'Deal Name': ['Test']})
        
        self.assertEqual(
            self.parser.detect_transaction_type(df, 'withholdings q1-2025.csv'),
            TransactionType.WITHHOLDING
        )
    
    def test_split_transaction_detection(self):
        """Test split transaction detection"""
        df = pd.DataFrame({'Deal Name': ['Test']})
        
        self.assertEqual(
            self.parser.detect_transaction_type(df, 'credits split 2024 q3-2025.csv'),
            TransactionType.SPLIT
        )


class TestCentrallyProcessedDetection(unittest.TestCase):
    """Test centrally processed transaction detection"""
    
    def test_cpi_detection(self):
        """Test CPI Increase deals are marked as centrally processed"""
        transactions = [
            {'deal_name': 'CPI Increase 2025@Test Bank', 'commission_amount': 100},
            {'deal_name': 'Regular Deal@Test Bank', 'commission_amount': 200}
        ]
        
        engine = ReconciliationEngineV3([], transactions)
        engine._identify_centrally_processed_transactions()
        
        self.assertEqual(len(engine.centrally_processed_transactions), 1)
        self.assertEqual(len(engine.salescookie_transactions), 1)
        self.assertEqual(
            engine.centrally_processed_transactions[0]['deal_name'],
            'CPI Increase 2025@Test Bank'
        )
    
    def test_fixed_price_detection(self):
        """Test Fixed Price Increase deals are marked as centrally processed"""
        transactions = [
            {'deal_name': 'Fixed Price Increase@Test Bank', 'commission_amount': 100},
            {'deal_name': 'Regular Upsell@Test Bank', 'commission_amount': 200}
        ]
        
        engine = ReconciliationEngineV3([], transactions)
        engine._identify_centrally_processed_transactions()
        
        self.assertEqual(len(engine.centrally_processed_transactions), 1)
        self.assertEqual(
            engine.centrally_processed_transactions[0]['deal_name'],
            'Fixed Price Increase@Test Bank'
        )


class TestIDMatching(unittest.TestCase):
    """Test ID matching functionality"""
    
    def test_direct_id_matching(self):
        """Test that deals with matching IDs are properly matched"""
        hubspot_deals = [
            {
                'hubspot_id': '12345',
                'deal_name': 'Test Deal',
                'close_date': datetime(2025, 7, 1),
                'commission_amount': 1000
            }
        ]
        
        salescookie_transactions = [
            {
                'salescookie_id': '12345',
                'deal_name': 'Test Deal',
                'close_date': datetime(2025, 7, 1),
                'commission_amount': 1000
            }
        ]
        
        engine = ReconciliationEngineV3(hubspot_deals, salescookie_transactions)
        results = engine.reconcile(90.0)
        
        self.assertEqual(len(results.matches), 1)
        self.assertEqual(results.matches[0].hubspot_id, '12345')
        self.assertEqual(results.matches[0].match_type, 'id')
        self.assertEqual(results.matches[0].confidence, 100.0)


class TestReconciliationScenarios(unittest.TestCase):
    """Test complete reconciliation scenarios"""
    
    def test_q3_2025_scenario(self):
        """Test Q3 2025 scenario: 16 CPI + 7 regular deals"""
        # Create test data mimicking Q3 2025
        salescookie_transactions = []
        
        # Add 16 CPI deals (should be centrally processed)
        for i in range(16):
            salescookie_transactions.append({
                'salescookie_id': f'cpi_{i}',
                'deal_name': f'CPI Increase 2025@Bank {i}',
                'commission_amount': 100,
                'transaction_type': 'regular'
            })
        
        # Add 7 regular deals (should match)
        regular_ids = ['270402053362', '234824647884', '250563139790', 
                      '34505378614', '34130746030', '15493853990', '28296679471']
        
        hubspot_deals = []
        for i, deal_id in enumerate(regular_ids):
            deal = {
                'hubspot_id': deal_id,
                'deal_name': f'Regular Deal {i}',
                'close_date': datetime(2025, 7, 1),
                'commission_amount': 1000
            }
            hubspot_deals.append(deal)
            
            salescookie_transactions.append({
                'salescookie_id': deal_id,
                'deal_name': f'Regular Deal {i}',
                'close_date': datetime(2025, 7, 1),
                'commission_amount': 1000,
                'transaction_type': 'regular'
            })
        
        # Run reconciliation
        engine = ReconciliationEngineV3(hubspot_deals, salescookie_transactions)
        results = engine.reconcile(90.0)
        
        # Verify results
        self.assertEqual(results.summary['centrally_processed_count'], 16)
        self.assertEqual(len(results.matches), 7)
        self.assertEqual(results.summary['match_rate'], 100.0)  # 7 out of 7 matchable deals


class TestWithholdingTransactions(unittest.TestCase):
    """Test withholding transaction handling"""
    
    def test_withholding_calculation(self):
        """Test withholding ratio calculation"""
        transactions = [{
            'salescookie_id': '123',
            'deal_name': 'Test Withholding',
            'commission_amount': 500,  # 50% paid
            'est_commission': 1000,    # Full amount
            'transaction_type': 'withholding',
            'withholding_ratio': 0.5
        }]
        
        engine = ReconciliationEngineV3([], transactions)
        results = engine.reconcile(90.0)
        
        # Check withholding summary
        wh_summary = results.summary['withholding_summary']
        self.assertEqual(wh_summary['total_paid'], 500)
        self.assertEqual(wh_summary['total_withheld'], 500)
        self.assertEqual(wh_summary['total_full_commission'], 1000)


class TestForecastTransactions(unittest.TestCase):
    """Test forecast transaction handling"""
    
    def test_forecast_with_kickers(self):
        """Test forecast transactions with kickers"""
        transactions = [{
            'salescookie_id': '123',
            'deal_name': 'Forecast Deal',
            'commission_amount': 1000,
            'early_bird_kicker': 100,
            'performance_kicker': 50,
            'campaign_kicker': 25,
            'transaction_type': 'forecast'
        }]
        
        engine = ReconciliationEngineV3([], transactions)
        results = engine.reconcile(90.0)
        
        # Check forecast summary
        fc_summary = results.summary['forecast_summary']
        self.assertEqual(fc_summary['total_forecast_amount'], 1000)
        self.assertEqual(fc_summary['total_kickers'], 175)
        self.assertEqual(fc_summary['deals_with_kickers'], 1)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()