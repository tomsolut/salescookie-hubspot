#!/usr/bin/env python3
"""
Integration tests for the complete reconciliation workflow
"""
import unittest
import tempfile
import os
import sys
import subprocess
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.create_integration_test_data()
        
    def create_integration_test_data(self):
        """Create realistic test data for integration testing"""
        # Comprehensive HubSpot test data
        hubspot_data = {
            'Record ID': [
                '270402053362', '270402053363', '270402053364', '270402053365',
                '270402053366', '270402053367', '270402053368', '270402053369'
            ],
            'Deal Name': [
                'Software License@Aktia Bank Abp',
                'PS @ Tieto (Additional PS Support Rcloud 54 MD - 88.560 EUR)',
                'Managed Services@State Bank of India',
                'CPI Increase 2025@Kreditanstalt für Wiederaufbau',
                'Upsell@Nordea Bank',
                'Cross-Sell@Swedbank',
                'PS @ Bank of Ireland (Migration Support)',
                'Parameter & Indexation@Santander'
            ],
            'Deal Stage': ['Closed & Won'] * 8,
            'Amount in company currency': [50000, 88560, 120000, 5000, 75000, 45000, 125000, 30000],
            'Close Date': [
                '2025-07-15', '2025-07-20', '2025-07-25', '2025-07-28',
                '2025-08-01', '2025-08-05', '2025-08-10', '2025-08-15'
            ],
            'Currency in company currency': ['EUR'] * 8,
            'Deal Type': [
                'New Business', 'Expansion', 'Renewal', 'Renewal',
                'Upsell', 'Cross-Sell', 'New Business', 'Renewal'
            ],
            'Associated Company IDs (Primary)': [
                '100123', '100456', '100733', '100556',
                '100789', '100890', '100901', '100234'
            ],
            'Associated Company Names (Primary)': [
                'Aktia Bank Abp', 'Tieto', 'State Bank of India', 'Kreditanstalt für Wiederaufbau',
                'Nordea Bank', 'Swedbank', 'Bank of Ireland', 'Santander'
            ],
            'Revenue start date': [
                '2025-08-01', '2025-08-01', '2025-09-01', '2026-01-01',
                '2025-09-01', '2025-09-01', '2025-09-01', '2025-10-01'
            ],
            'Types of ACV': [
                'Software', 'Professional Services', 'Managed Services', 'Software',
                'Software', 'Software', 'Professional Services', 'Software'
            ],
            'Product Name': [
                'Regnology Regulatory Reporting', 'Professional Services', 'RCloud Public', 'Regnology Transactions',
                'Regnology Regulatory Reporting', 'Regnology Analytics', 'Professional Services', 'Parameter Management'
            ],
            'Regnology -  Managed Services | 1 | Deployment Type': [
                '', '', 'Public RCloud', '',
                '', '', '', ''
            ],
            'ACV PS': ['', '88560', '', '', '', '', '125000', ''],
            'Weigh. ACV product & MS & TCV advisory': [
                '50000', '88560', '120000', '5000',
                '75000', '45000', '125000', '30000'
            ]
        }
        
        self.hubspot_file = os.path.join(self.temp_dir, 'hubspot_integration_test.csv')
        pd.DataFrame(hubspot_data).to_csv(self.hubspot_file, index=False)
        
        # Create corresponding SalesCookie data with some discrepancies
        salescookie_data = {
            'Unique ID': [
                '270402053362', '270402053363', '270402053364', '270402053365',
                '270402053366', '270402053367', '270402053369'  # Missing 270402053368
            ],
            'Deal Name': [
                'Software License@Aktia Bank Abp',
                'PS @ Tieto (Additional PS Support Rcloud 54 MD - 88.560 EUR)',
                'Managed Services@State Bank of India',
                'CPI Increase 2025@Kreditanstalt für Wiederaufbau',
                'Upsell@Nordea Bank',
                'Cross-Sell@Swedbank',
                'Parameter & Indexation@Santander'
            ],
            'Customer': [
                '100123; Aktia Bank Abp',
                '100456; Tieto',
                '100733; State Bank of India',
                '100556; Kreditanstalt für Wiederaufbau',
                '100789; Nordea Bank',
                '100890; Swedbank',
                '100234; Santander'
            ],
            'Close Date': [
                '2025-07-15 00:00:00', '2025-07-20 00:00:00', '2025-07-25 00:00:00', '2025-07-28 00:00:00',
                '2025-08-01 00:00:00', '2025-08-05 00:00:00', '2025-08-15 00:00:00'
            ],
            'Commission': [
                3650, 885.60, 8880, 440,  # CPI wrong: should be 350 (7% of 5000)
                5250, 3150, 2400  # Parameter wrong: should be 2790 (9.3% of 30000)
            ],
            'Commission Currency': ['EUR'] * 7,
            'Commission Rate': ['7.30%', '1.00%', '7.40%', '8.80%', '7.00%', '7.00%', '8.00%'],
            'Commission Details': [
                'Tier 2 - Software',
                'Professional Services',
                'Tier 2 - Managed Services Public',
                'Tier 3 - Indexation',
                'Tier 2 - Software',
                'Tier 2 - Software',
                'Tier 3 - Parameter'
            ],
            'Revenue Start Date': [
                '2025-08-01 00:00:00', '2025-08-01 00:00:00', '2025-09-01 00:00:00', '2026-01-01 00:00:00',
                '2025-09-01 00:00:00', '2025-09-01 00:00:00', '2025-10-01 00:00:00'
            ],
            'Deal Type': [
                'New Business', 'Expansion', 'Renewal', 'Renewal',
                'Upsell', 'Cross-Sell', 'Renewal'
            ],
            'ACV (EUR)': [50000, 0, 120000, 5000, 75000, 45000, 30000],
            'ACV Sales (Software)': [50000, 0, 0, 5000, 75000, 45000, 30000],
            'ACV Sales (Managed Services)': [0, 0, 120000, 0, 0, 0, 0],
            'ACV Sales (Professional Services) ': [0, 0, 0, 0, 0, 0, 0],
            'TCV (Professional Services)': [0, 88560, 0, 0, 0, 0, 0],
            'Currency': ['EUR'] * 7,
            'Create Date': [
                '2025-07-15 00:00:00', '2025-07-20 00:00:00', '2025-07-25 00:00:00', '2025-07-28 00:00:00',
                '2025-08-01 00:00:00', '2025-08-05 00:00:00', '2025-08-15 00:00:00'
            ],
            'Deal owner - Email': ['test@example.com'] * 7,
            'Deal owner - Name': ['Test User'] * 7,
            'Is Closed Won': ['true'] * 7,
            'Split': ['No'] * 7,
            'Types of ACV': [
                'Software', 'Professional Services', 'Managed Services', 'Software',
                'Software', 'Software', 'Software'
            ],
            'Product Name': [
                'Regnology Regulatory Reporting', 'Professional Services', 'RCloud Public', 'Regnology Transactions',
                'Regnology Regulatory Reporting', 'Regnology Analytics', 'Parameter Management'
            ]
        }
        
        self.salescookie_file = os.path.join(self.temp_dir, 'salescookie_integration_test.csv')
        pd.DataFrame(salescookie_data).to_csv(self.salescookie_file, index=False, encoding='utf-8-sig')
        
    def test_cli_execution(self):
        """Test CLI execution with test data"""
        output_dir = os.path.join(self.temp_dir, 'reports')
        
        # Build command
        cmd = [
            sys.executable,
            'reconcile_v2.py',
            '--hubspot-file', self.hubspot_file,
            '--salescookie-file', self.salescookie_file,
            '--output-dir', output_dir,
            '--verbose'
        ]
        
        # Run reconciliation
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Check execution
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        
        # Verify output files created
        self.assertTrue(os.path.exists(output_dir))
        
        # Check for report files
        files = os.listdir(output_dir)
        xlsx_files = [f for f in files if f.endswith('.xlsx')]
        txt_files = [f for f in files if f.endswith('.txt')]
        csv_files = [f for f in files if f.endswith('.csv')]
        
        self.assertGreater(len(xlsx_files), 0, "No Excel report generated")
        self.assertGreater(len(txt_files), 0, "No text report generated")
        self.assertGreater(len(csv_files), 0, "No CSV report generated")
        
    def test_data_quality_check_only(self):
        """Test data quality check mode"""
        output_dir = os.path.join(self.temp_dir, 'quality_reports')
        
        # Build command for quality check only
        cmd = [
            sys.executable,
            'reconcile_v2.py',
            '--hubspot-file', self.hubspot_file,
            '--salescookie-file', self.salescookie_file,
            '--output-dir', output_dir,
            '--quality-check'
        ]
        
        # Run quality check
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.assertEqual(result.returncode, 0, f"Quality check failed: {result.stderr}")
        self.assertIn("Data Quality Assessment", result.stdout)
        
    def test_expected_discrepancies(self):
        """Test that expected discrepancies are detected"""
        from hubspot_parser import HubSpotParser
        from salescookie_parser_v2 import SalesCookieParserV2, DataSource
        from reconciliation_engine_v2 import ReconciliationEngineV2
        
        # Parse data
        hs_parser = HubSpotParser(self.hubspot_file)
        hubspot_deals = hs_parser.parse()
        
        sc_parser = SalesCookieParserV2()
        sc_transactions, _ = sc_parser.parse_file(self.salescookie_file, DataSource.MANUAL)
        
        # Run reconciliation
        engine = ReconciliationEngineV2(hubspot_deals, sc_transactions)
        results = engine.reconcile(100.0)
        
        # Check expected discrepancies
        self.assertGreater(len(results.discrepancies), 0, "No discrepancies detected")
        
        # Check for missing deal (PS @ Bank of Ireland)
        missing_deals = [d for d in results.discrepancies if d.discrepancy_type == 'missing_deal']
        self.assertGreater(len(missing_deals), 0, "Missing deal not detected")
        
        # Check for wrong commission amounts
        wrong_amounts = [d for d in results.discrepancies if d.discrepancy_type == 'wrong_commission_amount']
        self.assertGreater(len(wrong_amounts), 0, "Wrong commission amounts not detected")
        
    def test_report_content(self):
        """Test report content accuracy"""
        from report_generator import ReportGenerator
        from hubspot_parser import HubSpotParser
        from salescookie_parser_v2 import SalesCookieParserV2, DataSource
        from reconciliation_engine_v2 import ReconciliationEngineV2
        
        # Run full reconciliation
        hs_parser = HubSpotParser(self.hubspot_file)
        hubspot_deals = hs_parser.parse()
        
        sc_parser = SalesCookieParserV2()
        sc_transactions, _ = sc_parser.parse_file(self.salescookie_file, DataSource.MANUAL)
        
        engine = ReconciliationEngineV2(hubspot_deals, sc_transactions)
        results = engine.reconcile(100.0)
        
        # Generate reports
        output_dir = os.path.join(self.temp_dir, 'test_reports')
        generator = ReportGenerator(output_dir)
        
        # Convert results for report generator
        legacy_results = {
            'summary': results.summary,
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
        
        report_paths = generator.generate_reports(legacy_results)
        
        # Verify Excel report
        self.assertTrue(os.path.exists(report_paths['excel']))
        
        # Read Excel and check sheets
        xl = pd.ExcelFile(report_paths['excel'])
        self.assertIn('Summary', xl.sheet_names)
        self.assertIn('Discrepancies', xl.sheet_names)
        self.assertIn('All Deals', xl.sheet_names)
        
        # Check summary content
        summary_df = pd.read_excel(xl, 'Summary')
        self.assertGreater(len(summary_df), 0)
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()