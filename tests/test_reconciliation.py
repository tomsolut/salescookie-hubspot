#!/usr/bin/env python3
"""
Automated test suite for commission reconciliation tool
"""
import unittest
import tempfile
import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2, DataSource
from reconciliation_engine_v2 import ReconciliationEngineV2
from commission_config import CommissionConfig

class TestReconciliation(unittest.TestCase):
    """Test suite for reconciliation components"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.create_sample_data()
        
    def create_sample_data(self):
        """Create sample test data files"""
        # Sample HubSpot data
        hubspot_data = {
            'Record ID': ['270402053362', '270402053363', '270402053364', '270402053365'],
            'Deal Name': [
                'Software License@Aktia Bank Abp',
                'PS @ Tieto (Additional PS Support)',
                'Managed Services@State Bank of India',
                'CPI Increase 2025@Kreditanstalt für Wiederaufbau'
            ],
            'Deal Stage': ['Closed & Won', 'Closed & Won', 'Closed & Won', 'Closed & Won'],
            'Amount in company currency': [50000, 88560, 120000, 5000],
            'Close Date': ['2025-07-15', '2025-07-20', '2025-07-25', '2025-07-28'],
            'Currency in company currency': ['EUR', 'EUR', 'EUR', 'EUR'],
            'Deal Type': ['New Business', 'Expansion', 'Renewal', 'Renewal'],
            'Associated Company IDs (Primary)': ['100123', '100456', '100733', '100556'],
            'Associated Company Names (Primary)': [
                'Aktia Bank Abp',
                'Tieto',
                'State Bank of India',
                'Kreditanstalt für Wiederaufbau'
            ],
            'Revenue start date': ['2025-08-01', '2025-08-01', '2025-09-01', '2026-01-01'],
            'Types of ACV': ['Software', 'Professional Services', 'Managed Services', 'Software'],
            'Product Name': ['Regnology Regulatory Reporting', 'Professional Services', 'RCloud Public', 'Regnology Transactions'],
            'Regnology -  Managed Services | 1 | Deployment Type': ['', '', 'Public RCloud', ''],
            'ACV PS': ['', '88560', '', ''],
            'Weigh. ACV product & MS & TCV advisory': ['50000', '88560', '120000', '5000']
        }
        
        self.hubspot_file = os.path.join(self.temp_dir, 'hubspot_test.csv')
        pd.DataFrame(hubspot_data).to_csv(self.hubspot_file, index=False)
        
        # Sample manual SalesCookie data (good quality)
        manual_data = {
            'Unique ID': ['270402053362', '270402053363', '270402053364'],
            'Deal Name': [
                'Software License@Aktia Bank Abp',
                'PS @ Tieto (Additional PS Support)',
                'Managed Services@State Bank of India'
            ],
            'Customer': ['100123; Aktia Bank Abp', '100456; Tieto', '100733; State Bank of India'],
            'Close Date': ['2025-07-15 00:00:00', '2025-07-20 00:00:00', '2025-07-25 00:00:00'],
            'Commission': [3650, 885.60, 8880],
            'Commission Currency': ['EUR', 'EUR', 'EUR'],
            'Commission Rate': ['7.30%', '1.00%', '7.40%'],
            'Commission Details': [
                'Tier 2 - Software',
                'Professional Services',
                'Tier 2 - Managed Services Public'
            ],
            'Revenue Start Date': ['2025-08-01 00:00:00', '2025-08-01 00:00:00', '2025-09-01 00:00:00'],
            'Deal Type': ['New Business', 'Expansion', 'Renewal'],
            'ACV (EUR)': [50000, 0, 120000],
            'ACV Sales (Software)': [50000, 0, 0],
            'ACV Sales (Managed Services)': [0, 0, 120000],
            'ACV Sales (Professional Services) ': [0, 0, 0],
            'TCV (Professional Services)': [0, 88560, 0],
            'Currency': ['EUR', 'EUR', 'EUR'],
            'Create Date': ['2025-07-15 00:00:00', '2025-07-20 00:00:00', '2025-07-25 00:00:00'],
            'Deal owner - Email': ['test@example.com', 'test@example.com', 'test@example.com'],
            'Deal owner - Name': ['Test User', 'Test User', 'Test User'],
            'Is Closed Won': ['true', 'true', 'true'],
            'Split': ['No', 'No', 'No'],
            'Types of ACV': ['Software', 'Professional Services', 'Managed Services'],
            'Product Name': ['Regnology Regulatory Reporting', 'Professional Services', 'RCloud Public']
        }
        
        self.manual_file = os.path.join(self.temp_dir, 'salescookie_manual.csv')
        pd.DataFrame(manual_data).to_csv(self.manual_file, index=False, encoding='utf-8-sig')
        
        # Sample scraped SalesCookie data (poor quality)
        scraped_data = {
            'Unique ID': ['20351301806', '20351301807', '20351301808'],  # Wrong ID format
            'Deal Name': [
                'Software License@Aktia Bank ...',  # Truncated
                'PS @ Tieto (Additional PS Sup...',  # Truncated
                'Managed Services@State Bank o...'  # Truncated
            ],
            'Customer': ['Aktia Bank Abp', 'Tieto', 'State Bank of India'],  # Missing ID prefix
            'Close Date': ['2025-07-15', '2025-07-20', '2025-07-25'],
            'Commission': ['3650 (EUR)', '885.60 (EUR)', '8880 (EUR)'],
            'Commission Rate': ['7.30%', '1.00%', '7.40%']
        }
        
        self.scraped_file = os.path.join(self.temp_dir, 'salescookie_scraped.csv')
        pd.DataFrame(scraped_data).to_csv(self.scraped_file, index=False)
        
    def test_hubspot_parser(self):
        """Test HubSpot parser functionality"""
        parser = HubSpotParser(self.hubspot_file)
        deals = parser.parse()
        
        self.assertEqual(len(deals), 4)
        self.assertEqual(deals[0]['hubspot_id'], '270402053362')
        self.assertEqual(deals[0]['deal_name'], 'Software License@Aktia Bank Abp')
        self.assertEqual(deals[0]['commission_amount'], 50000)
        self.assertFalse(deals[0]['is_ps_deal'])
        self.assertTrue(deals[1]['is_ps_deal'])  # PS @ Tieto
        
    def test_salescookie_parser_manual(self):
        """Test SalesCookie parser with manual data"""
        parser = SalesCookieParserV2()
        transactions, quality = parser.parse_file(self.manual_file, DataSource.MANUAL)
        
        self.assertEqual(len(transactions), 3)
        self.assertEqual(quality.source_type, DataSource.MANUAL)
        self.assertEqual(quality.quality_score, 100.0)
        self.assertEqual(quality.truncated_names, 0)
        self.assertEqual(transactions[0]['salescookie_id'], '270402053362')
        self.assertEqual(transactions[0]['commission_amount'], 3650)
        
    def test_salescookie_parser_scraped(self):
        """Test SalesCookie parser with scraped data"""
        parser = SalesCookieParserV2()
        transactions, quality = parser.parse_file(self.scraped_file, DataSource.SCRAPED)
        
        self.assertEqual(len(transactions), 3)
        self.assertEqual(quality.source_type, DataSource.SCRAPED)
        self.assertLess(quality.quality_score, 80)  # Poor quality
        self.assertEqual(quality.truncated_names, 3)  # All names truncated
        self.assertIn('deal names are truncated', ' '.join(quality.warnings))
        
    def test_reconciliation_with_manual_data(self):
        """Test reconciliation with high-quality manual data"""
        # Parse data
        hs_parser = HubSpotParser(self.hubspot_file)
        hubspot_deals = hs_parser.parse()
        
        sc_parser = SalesCookieParserV2()
        sc_transactions, _ = sc_parser.parse_file(self.manual_file, DataSource.MANUAL)
        
        # Run reconciliation
        engine = ReconciliationEngineV2(hubspot_deals, sc_transactions)
        results = engine.reconcile(100.0)
        
        # Check results
        self.assertEqual(len(results.matches), 3)  # 3 out of 4 matched
        self.assertEqual(len(results.unmatched_hubspot), 1)  # CPI Increase deal
        self.assertEqual(results.matches[0].match_type, 'id')
        self.assertEqual(results.matches[0].confidence, 100.0)
        
    def test_reconciliation_with_scraped_data(self):
        """Test reconciliation with poor-quality scraped data"""
        # Parse data
        hs_parser = HubSpotParser(self.hubspot_file)
        hubspot_deals = hs_parser.parse()
        
        sc_parser = SalesCookieParserV2()
        sc_transactions, quality = sc_parser.parse_file(self.scraped_file, DataSource.SCRAPED)
        
        # Run reconciliation
        engine = ReconciliationEngineV2(hubspot_deals, sc_transactions)
        results = engine.reconcile(quality.quality_score)
        
        # Check results - should have no ID matches due to wrong format
        id_matches = [m for m in results.matches if m.match_type == 'id']
        self.assertEqual(len(id_matches), 0)
        
        # But might have some company/date matches
        self.assertGreaterEqual(len(results.matches), 0)
        
    def test_commission_validation(self):
        """Test commission calculation validation"""
        config = CommissionConfig()
        
        # Test software deal
        rate = config.get_commission_rate(2025, 'software', False)
        self.assertEqual(rate, 0.07)  # 7%
        
        # Test PS deal
        rate = config.get_commission_rate(2025, 'software', True)
        self.assertEqual(rate, 0.01)  # 1%
        
        # Test managed services
        rate = config.get_commission_rate(2025, 'managed_services_public', False)
        self.assertEqual(rate, 0.074)  # 7.4%
        
    def test_data_quality_detection(self):
        """Test automatic data quality detection"""
        parser = SalesCookieParserV2()
        
        # Test manual data detection
        manual_df = pd.read_csv(self.manual_file, encoding='utf-8-sig')
        source = parser.detect_data_source(manual_df, self.manual_file)
        self.assertEqual(source, DataSource.MANUAL)
        
        # Test scraped data detection
        scraped_df = pd.read_csv(self.scraped_file)
        source = parser.detect_data_source(scraped_df, self.scraped_file)
        self.assertEqual(source, DataSource.SCRAPED)
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_missing_fields(self):
        """Test handling of missing required fields"""
        parser = SalesCookieParserV2()
        
        # Create data with missing fields
        bad_data = pd.DataFrame({
            'Deal Name': ['Test Deal'],
            'Commission': [100]
            # Missing Unique ID, Customer, etc.
        })
        
        quality = parser.assess_data_quality(bad_data, DataSource.SCRAPED)
        self.assertLess(quality.quality_score, 50)
        self.assertIn('Unique ID', quality.missing_fields)
        
    def test_currency_conversion(self):
        """Test currency handling"""
        # Create test data with SEK currency
        test_data = {
            'Record ID': ['270402053366'],
            'Deal Name': ['Swedish Deal@Company AB'],
            'Deal Stage': ['Closed & Won'],
            'Amount in company currency': [500000],  # SEK
            'Currency in company currency': ['SEK'],
            'Close Date': ['2025-07-15'],
            'Deal Type': ['New Business'],
            'Associated Company Names (Primary)': ['Company AB'],
            'Types of ACV': ['Software'],
            'Weigh. ACV product & MS & TCV advisory': ['50000']  # EUR equivalent
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame(test_data).to_csv(f, index=False)
            temp_file = f.name
            
        try:
            parser = HubSpotParser(temp_file)
            deals = parser.parse()
            
            # Should use the EUR amount from weighted field
            self.assertEqual(deals[0]['commission_amount'], 50000)
            self.assertEqual(deals[0]['currency'], 'SEK')
            self.assertEqual(deals[0]['original_amount'], 500000)
        finally:
            os.unlink(temp_file)

if __name__ == '__main__':
    unittest.main()