"""
HubSpot CSV Parser for Closed & Won deals
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class HubSpotParser:
    """Parse HubSpot CSV exports for Closed & Won deals"""
    
    # Column mappings
    COLUMN_MAPPING = {
        'record_id': 'Record ID',
        'deal_name': 'Deal Name',
        'deal_stage': 'Deal Stage',
        'close_date': 'Close Date',
        'amount': 'Amount',
        'amount_company_currency': 'Amount in company currency',
        'currency': 'Currency',
        'deal_type': 'Deal Type',
        'product_name': 'Product Name',
        'types_of_acv': 'Types of ACV',
        'company': 'Associated Company (Primary)',
        'owner': 'Deal owner',
        'service_start_date': 'Revenue Start Date',
        'ps_start_date': 'Professional Services Start Date',
        'acv_software': 'ACV Sales (Software)',
        'acv_managed_services': 'ACV Sales (Managed Services)',
        'acv_professional_services': 'ACV Sales (Professional Services) ',
        'deployment_type': 'Deployment Type',
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.deals = []
        
    def parse(self) -> List[Dict]:
        """Parse HubSpot CSV file and return Closed & Won deals"""
        try:
            # Read CSV
            df = pd.read_csv(self.file_path)
            logger.info(f"Loaded {len(df)} deals from HubSpot export")
            
            # Filter for Closed & Won deals
            closed_won_df = df[df['Deal Stage'] == 'Closed & Won'].copy()
            logger.info(f"Found {len(closed_won_df)} Closed & Won deals")
            
            # Process each deal
            for idx, row in closed_won_df.iterrows():
                deal = self._process_deal(row)
                if deal:
                    self.deals.append(deal)
                    
            logger.info(f"Successfully processed {len(self.deals)} deals")
            return self.deals
            
        except Exception as e:
            logger.error(f"Error parsing HubSpot CSV: {str(e)}")
            raise
            
    def _process_deal(self, row: pd.Series) -> Optional[Dict]:
        """Process a single deal row"""
        try:
            # Extract basic information
            deal = {
                'hubspot_id': str(row.get(self.COLUMN_MAPPING['record_id'], '')),
                'deal_name': row.get(self.COLUMN_MAPPING['deal_name'], ''),
                'close_date': self._parse_date(row.get(self.COLUMN_MAPPING['close_date'])),
                'service_start_date': self._parse_date(row.get(self.COLUMN_MAPPING['service_start_date'])),
                'ps_start_date': self._parse_date(row.get(self.COLUMN_MAPPING['ps_start_date'])),
                'amount': self._parse_amount(row.get(self.COLUMN_MAPPING['amount'])),
                'amount_company_currency': self._parse_amount(row.get(self.COLUMN_MAPPING['amount_company_currency'])),
                'currency': row.get(self.COLUMN_MAPPING['currency'], 'EUR'),
                'deal_type': row.get(self.COLUMN_MAPPING['deal_type'], ''),
                'product_name': row.get(self.COLUMN_MAPPING['product_name'], ''),
                'types_of_acv': row.get(self.COLUMN_MAPPING['types_of_acv'], ''),
                'company': row.get(self.COLUMN_MAPPING['company'], ''),
                'owner': row.get(self.COLUMN_MAPPING['owner'], ''),
                'deployment_type': row.get(self.COLUMN_MAPPING['deployment_type'], ''),
            }
            
            # Determine if this is a PS deal
            deal['is_ps_deal'] = self._is_ps_deal(deal)
            
            # Extract ACV breakdown
            deal['acv_breakdown'] = {
                'software': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_software'])),
                'managed_services': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_managed_services'])),
                'professional_services': self._parse_amount(row.get(self.COLUMN_MAPPING['acv_professional_services'])),
            }
            
            # Use company currency amount for commission calculation
            deal['commission_amount'] = deal['amount_company_currency'] or deal['amount']
            
            return deal
            
        except Exception as e:
            logger.warning(f"Error processing deal: {str(e)}")
            return None
            
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if pd.isna(date_str) or not date_str:
            return None
            
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(str(date_str).strip(), fmt)
                except ValueError:
                    continue
                    
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {str(e)}")
            return None
            
    def _parse_amount(self, amount) -> float:
        """Parse amount to float"""
        if pd.isna(amount) or amount == '' or amount is None:
            return 0.0
            
        try:
            # Remove currency symbols and convert
            amount_str = str(amount).replace('€', '').replace('$', '').replace(',', '').strip()
            return float(amount_str)
        except:
            return 0.0
            
    def _is_ps_deal(self, deal: Dict) -> bool:
        """Determine if deal is a Professional Services deal"""
        # Check various indicators
        indicators = [
            'PS @' in deal.get('deal_name', ''),
            'professional services' in deal.get('deal_type', '').lower(),
            'ps deal' in deal.get('deal_name', '').lower(),
            deal.get('acv_breakdown', {}).get('professional_services', 0) > 0 and
            deal.get('acv_breakdown', {}).get('software', 0) == 0 and
            deal.get('acv_breakdown', {}).get('managed_services', 0) == 0,
        ]
        
        return any(indicators)
    
    def get_deals_by_quarter(self, quarter: str) -> List[Dict]:
        """Get deals for a specific quarter"""
        quarter_deals = []
        
        for deal in self.deals:
            if not deal['close_date']:
                continue
                
            deal_quarter = self._get_quarter_from_date(deal['close_date'])
            if deal_quarter == quarter:
                quarter_deals.append(deal)
                
        return quarter_deals
    
    def _get_quarter_from_date(self, date_obj: datetime) -> str:
        """Get quarter string from date"""
        month = date_obj.month
        year = date_obj.year
        
        if month <= 3:
            return f"Q1_{year}"
        elif month <= 6:
            return f"Q2_{year}"
        elif month <= 9:
            return f"Q3_{year}"
        else:
            return f"Q4_{year}"
            
    def summary(self) -> Dict:
        """Get summary statistics"""
        total_amount = sum(deal['commission_amount'] for deal in self.deals)
        ps_deals = [d for d in self.deals if d['is_ps_deal']]
        regular_deals = [d for d in self.deals if not d['is_ps_deal']]
        
        return {
            'total_deals': len(self.deals),
            'total_amount': total_amount,
            'ps_deals_count': len(ps_deals),
            'ps_deals_amount': sum(d['commission_amount'] for d in ps_deals),
            'regular_deals_count': len(regular_deals),
            'regular_deals_amount': sum(d['commission_amount'] for d in regular_deals),
            'deals_by_currency': self._group_by_currency(),
        }
        
    def _group_by_currency(self) -> Dict:
        """Group deals by currency"""
        currency_groups = {}
        
        for deal in self.deals:
            currency = deal['currency']
            if currency not in currency_groups:
                currency_groups[currency] = {
                    'count': 0,
                    'amount': 0,
                    'amount_company_currency': 0,
                }
                
            currency_groups[currency]['count'] += 1
            currency_groups[currency]['amount'] += deal['amount']
            currency_groups[currency]['amount_company_currency'] += deal['amount_company_currency']
            
        return currency_groups