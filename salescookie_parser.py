"""
SalesCookie CSV Parser for commission data
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class SalesCookieParser:
    """Parse SalesCookie quarterly transaction CSV files"""
    
    # Column mappings for SalesCookie CSV
    COLUMN_MAPPING = {
        'acv_eur': 'ACV (EUR)',
        'commission': 'Commission',
        'commission_rate': 'Commission Rate',
        'commission_details': 'Commission Details',
        'close_date': 'Close Date',
        'revenue_start_date': 'Revenue Start Date',
        'ps_start_date': 'Professional Services Start Date',
        'deal_type': 'Deal Type',
        'unique_id': 'Unique ID',
        'acv_managed_services': 'ACV Sales (Managed Services)',
        'acv_professional_services': 'ACV Sales (Professional Services)',
        'acv_software': 'ACV Sales (Software)',
        'tcv_professional_services': 'TCV (Professional Services)',
        'currency': 'Currency',
        'customer': 'Customer',
        'deal_name': 'Deal Name',
        'types_of_acv': 'Types of ACV',
        'product_name': 'Product Name',
        'split': 'Split',
        'performance_kicker': 'Performance Kicker',
        'campaign_kicker': 'Campaign Kicker',
    }
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.transactions = []
        self.quarters_data = {}
        
    def parse_all_quarters(self) -> Dict[str, List[Dict]]:
        """Parse all quarterly transaction files"""
        # Find all credited_transactions CSV files
        csv_files = self._find_transaction_files()
        
        for quarter, file_path in csv_files.items():
            logger.info(f"Parsing {quarter}: {file_path}")
            quarter_transactions = self._parse_quarter_file(file_path, quarter)
            
            if quarter_transactions:
                self.quarters_data[quarter] = quarter_transactions
                self.transactions.extend(quarter_transactions)
                
        logger.info(f"Total transactions parsed: {len(self.transactions)}")
        return self.quarters_data
        
    def _find_transaction_files(self) -> Dict[str, str]:
        """Find all credited_transactions CSV files"""
        csv_files = {}
        
        # Walk through directory structure
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.startswith('credited_transactions') and file.endswith('.csv'):
                    # Extract quarter from path
                    quarter = self._extract_quarter_from_path(root)
                    if quarter:
                        csv_files[quarter] = os.path.join(root, file)
                        
        return csv_files
        
    def _extract_quarter_from_path(self, path: str) -> Optional[str]:
        """Extract quarter from directory path"""
        # Look for Q[1-4]_YYYY pattern
        parts = path.split(os.sep)
        for part in parts:
            if re.match(r'Q[1-4]_\d{4}', part):
                return part
                
        return None
        
    def _parse_quarter_file(self, file_path: str, quarter: str) -> List[Dict]:
        """Parse a single quarter's transaction file"""
        try:
            # Read CSV with proper encoding and separator
            # First try with default settings
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig', sep=';')
            except:
                # If that fails, try with comma separator
                df = pd.read_csv(file_path, encoding='utf-8-sig', sep=',', on_bad_lines='skip')
            
            # Skip rows that don't have the expected columns
            required_columns = ['Unique ID', 'ACV (EUR)', 'Commission']
            if not all(col in df.columns for col in required_columns):
                logger.warning(f"Missing required columns in {file_path}")
                return []
            
            # Skip summary rows (those without unique IDs)
            df = df[df['Unique ID'].notna()].copy()
            
            transactions = []
            
            for idx, row in df.iterrows():
                transaction = self._process_transaction(row, quarter)
                if transaction:
                    transactions.append(transaction)
                    
            logger.info(f"Parsed {len(transactions)} transactions for {quarter}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return []
            
    def _process_transaction(self, row: pd.Series, quarter: str) -> Optional[Dict]:
        """Process a single transaction row"""
        try:
            # Parse commission amount and currency
            commission_str = str(row.get(self.COLUMN_MAPPING['commission'], '0'))
            commission_amount, commission_currency = self._parse_commission(commission_str)
            
            transaction = {
                'salescookie_id': str(row.get(self.COLUMN_MAPPING['unique_id'], '')),
                'quarter': quarter,
                'acv_eur': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_eur'])),
                'commission_amount': commission_amount,
                'commission_currency': commission_currency,
                'commission_rate': self._parse_rate(row.get(self.COLUMN_MAPPING['commission_rate'])),
                'commission_details': row.get(self.COLUMN_MAPPING['commission_details'], ''),
                'close_date': self._parse_date(row.get(self.COLUMN_MAPPING['close_date'])),
                'revenue_start_date': self._parse_date(row.get(self.COLUMN_MAPPING['revenue_start_date'])),
                'ps_start_date': self._parse_date(row.get(self.COLUMN_MAPPING['ps_start_date'])),
                'deal_type': row.get(self.COLUMN_MAPPING['deal_type'], ''),
                'currency': row.get(self.COLUMN_MAPPING['currency'], 'EUR'),
                'customer': row.get(self.COLUMN_MAPPING['customer'], ''),
                'deal_name': row.get(self.COLUMN_MAPPING['deal_name'], ''),
                'types_of_acv': row.get(self.COLUMN_MAPPING['types_of_acv'], ''),
                'product_name': row.get(self.COLUMN_MAPPING['product_name'], ''),
                'has_split': row.get(self.COLUMN_MAPPING['split'], '') == 'Yes',
                'performance_kicker': self._parse_amount(row.get(self.COLUMN_MAPPING['performance_kicker'])),
                'campaign_kicker': self._parse_amount(row.get(self.COLUMN_MAPPING['campaign_kicker'])),
            }
            
            # Extract ACV breakdown
            transaction['acv_breakdown'] = {
                'software': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_software'])),
                'managed_services': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_managed_services'])),
                'professional_services': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_professional_services'])),
            }
            
            # Determine if PS deal
            transaction['is_ps_deal'] = self._is_ps_deal(transaction)
            
            return transaction
            
        except Exception as e:
            logger.warning(f"Error processing transaction: {str(e)}")
            return None
            
    def _parse_commission(self, commission_str: str) -> Tuple[float, str]:
        """Parse commission string to extract amount and currency"""
        # Handle format like "267.96 (EUR)"
        try:
            # Remove any whitespace
            commission_str = str(commission_str).strip()
            
            # Extract number
            match = re.search(r'([\d,]+\.?\d*)', commission_str)
            if match:
                amount = float(match.group(1).replace(',', ''))
            else:
                amount = 0.0
                
            # Extract currency
            currency_match = re.search(r'\(([A-Z]{3})\)', commission_str)
            if currency_match:
                currency = currency_match.group(1)
            else:
                currency = 'EUR'
                
            return amount, currency
            
        except:
            return 0.0, 'EUR'
            
    def _parse_amount(self, amount) -> float:
        """Parse amount to float"""
        if pd.isna(amount) or amount == '' or amount is None:
            return 0.0
            
        try:
            # Handle various number formats
            amount_str = str(amount).replace(',', '').replace('€', '').replace('$', '').strip()
            return float(amount_str)
        except:
            return 0.0
            
    def _parse_rate(self, rate_str) -> float:
        """Parse commission rate percentage"""
        if pd.isna(rate_str) or not rate_str:
            return 0.0
            
        try:
            # Remove % sign and convert
            rate_clean = str(rate_str).replace('%', '').strip()
            return float(rate_clean) / 100.0
        except:
            return 0.0
            
    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if pd.isna(date_str) or not date_str:
            return None
            
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(str(date_str).strip(), fmt)
                except ValueError:
                    continue
                    
            return None
            
        except Exception:
            return None
            
    def _is_ps_deal(self, transaction: Dict) -> bool:
        """Determine if transaction is a Professional Services deal"""
        deal_type = str(transaction.get('deal_type', '')).lower()
        deal_name = str(transaction.get('deal_name', '')).lower()
        types_acv = str(transaction.get('types_of_acv', ''))
        
        indicators = [
            'professional services' in deal_type,
            'ps' in deal_name,
            transaction.get('commission_rate', 0) == 0.01,  # 1% flat rate
            'TCV' in types_acv,
        ]
        
        return any(indicators)
        
    def get_transactions_by_hubspot_id(self, hubspot_id: str) -> List[Dict]:
        """Get all transactions for a specific HubSpot deal ID"""
        return [t for t in self.transactions if t['salescookie_id'] == hubspot_id]
        
    def summary(self) -> Dict:
        """Get summary statistics"""
        total_commission = sum(t['commission_amount'] for t in self.transactions)
        
        summary = {
            'total_transactions': len(self.transactions),
            'total_commission': total_commission,
            'quarters': {},
        }
        
        # Summary by quarter
        for quarter, transactions in self.quarters_data.items():
            quarter_commission = sum(t['commission_amount'] for t in transactions)
            summary['quarters'][quarter] = {
                'count': len(transactions),
                'commission': quarter_commission,
                'ps_deals': len([t for t in transactions if t['is_ps_deal']]),
                'regular_deals': len([t for t in transactions if not t['is_ps_deal']]),
            }
            
        return summary