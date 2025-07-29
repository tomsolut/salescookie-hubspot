"""
Enhanced SalesCookie CSV Parser with dual-mode support
Supports both manual exports and scraped data
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    MANUAL = "manual"
    SCRAPED = "scraped"
    UNKNOWN = "unknown"

@dataclass
class DataQualityReport:
    """Data quality assessment for loaded data"""
    source_type: DataSource
    total_records: int
    valid_ids: int
    valid_names: int
    truncated_names: int
    missing_fields: Dict[str, int]
    quality_score: float  # 0-100
    warnings: List[str]
    
class SalesCookieParserV2:
    """Enhanced parser supporting both manual and scraped SalesCookie data"""
    
    # Expected columns in manual export
    MANUAL_COLUMNS = {
        'unique_id': 'Unique ID',
        'deal_name': 'Deal Name',
        'customer': 'Customer',
        'close_date': 'Close Date',
        'commission': 'Commission',
        'commission_currency': 'Commission Currency',
        'commission_rate': 'Commission Rate',
        'commission_details': 'Commission Details',
        'revenue_start_date': 'Revenue Start Date',
        'deal_type': 'Deal Type',
        'acv_eur': 'ACV (EUR)',
        'acv_software': 'ACV Sales (Software)',
        'acv_managed_services': 'ACV Sales (Managed Services)',
        'acv_professional_services': 'ACV Sales (Professional Services) ',
        'tcv_professional_services': 'TCV (Professional Services)',
        'split': 'Split',
        'types_of_acv': 'Types of ACV',
        'product_name': 'Product Name',
    }
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path
        self.transactions = []
        self.data_quality_reports = {}
        
    def detect_data_source(self, df: pd.DataFrame, file_path: str) -> DataSource:
        """Detect if data is from manual export or scraped"""
        # Check for key indicators
        if 'Commission Currency' in df.columns and 'Is Closed Won' in df.columns:
            return DataSource.MANUAL
        elif all(col in df.columns for col in ['Commission', 'Commission Rate', 'Unique ID']):
            # Check if Deal Names are truncated (ending with …)
            if 'Deal Name' in df.columns:
                truncated = df['Deal Name'].fillna('').str.endswith('…').sum()
                if truncated > len(df) * 0.1:  # More than 10% truncated
                    return DataSource.SCRAPED
            return DataSource.MANUAL
        else:
            return DataSource.SCRAPED
            
    def assess_data_quality(self, df: pd.DataFrame, source: DataSource) -> DataQualityReport:
        """Assess the quality of loaded data"""
        total = len(df)
        warnings = []
        missing_fields = {}
        
        # Check Unique IDs
        valid_ids = 0
        if 'Unique ID' in df.columns:
            valid_ids = df['Unique ID'].notna().sum()
            if valid_ids < total:
                warnings.append(f"{total - valid_ids} records missing Unique ID")
        else:
            missing_fields['Unique ID'] = total
            warnings.append("Critical: Unique ID column missing")
            
        # Check Deal Names
        valid_names = 0
        truncated_names = 0
        if 'Deal Name' in df.columns:
            valid_names = df['Deal Name'].notna().sum()
            truncated_names = df['Deal Name'].fillna('').str.endswith('…').sum()
            if truncated_names > 0:
                warnings.append(f"{truncated_names} deal names are truncated")
        else:
            missing_fields['Deal Name'] = total
            warnings.append("Critical: Deal Name column missing")
            
        # Check other critical fields
        critical_fields = ['Customer', 'Close Date', 'Commission', 'Commission Rate']
        for field in critical_fields:
            if field not in df.columns:
                missing_fields[field] = total
                warnings.append(f"Missing field: {field}")
            else:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    missing_fields[field] = missing_count
                    
        # Calculate quality score
        score = 100.0
        if total > 0:
            # Deduct points for issues
            score -= (total - valid_ids) / total * 30  # 30 points for missing IDs
            score -= truncated_names / total * 20  # 20 points for truncated names
            score -= len(missing_fields) * 10  # 10 points per missing field
            score = max(0, score)
            
        return DataQualityReport(
            source_type=source,
            total_records=total,
            valid_ids=valid_ids,
            valid_names=valid_names,
            truncated_names=truncated_names,
            missing_fields=missing_fields,
            quality_score=score,
            warnings=warnings
        )
        
    def parse_file(self, file_path: str, source: DataSource = None) -> Tuple[List[Dict], DataQualityReport]:
        """Parse a single SalesCookie file with quality assessment"""
        try:
            # Read CSV with automatic delimiter detection
            df = self._read_csv_safe(file_path)
            
            if df is None or len(df) == 0:
                logger.warning(f"No data loaded from {file_path}")
                return [], None
                
            # Detect source if not specified
            if source is None:
                source = self.detect_data_source(df, file_path)
                logger.info(f"Detected data source: {source.value}")
                
            # Assess data quality
            quality_report = self.assess_data_quality(df, source)
            logger.info(f"Data quality score: {quality_report.quality_score:.1f}/100")
            
            # Parse based on source type
            if source == DataSource.MANUAL:
                transactions = self._parse_manual_format(df)
            else:
                transactions = self._parse_scraped_format(df)
                
            return transactions, quality_report
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return [], None
            
    def _read_csv_safe(self, file_path: str) -> Optional[pd.DataFrame]:
        """Safely read CSV with multiple encoding and separator attempts"""
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for separator in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=separator, 
                                   on_bad_lines='skip', low_memory=False)
                    # Check if we got meaningful data
                    if len(df.columns) > 1 and len(df) > 0:
                        logger.info(f"Successfully read {file_path} with {encoding} encoding and '{separator}' separator")
                        return df
                except:
                    continue
                    
        logger.error(f"Failed to read {file_path} with any encoding/separator combination")
        return None
        
    def _parse_manual_format(self, df: pd.DataFrame) -> List[Dict]:
        """Parse manual export format (high quality)"""
        transactions = []
        
        # Filter out rows without Unique ID
        if 'Unique ID' in df.columns:
            df = df[df['Unique ID'].notna()].copy()
            
        for idx, row in df.iterrows():
            try:
                transaction = {
                    'salescookie_id': str(row.get('Unique ID', '')),
                    'deal_name': row.get('Deal Name', ''),
                    'customer': row.get('Customer', ''),
                    'close_date': self._parse_date(row.get('Close Date')),
                    'revenue_start_date': self._parse_date(row.get('Revenue Start Date')),
                    'commission_amount': self._parse_amount(row.get('Commission')),
                    'commission_currency': row.get('Commission Currency', 'EUR'),
                    'commission_rate': self._parse_rate(row.get('Commission Rate')),
                    'commission_details': row.get('Commission Details', ''),
                    'deal_type': row.get('Deal Type', ''),
                    'acv_eur': self._parse_amount(row.get('ACV (EUR)')),
                    'currency': row.get('Currency', 'EUR'),
                    'types_of_acv': row.get('Types of ACV', ''),
                    'product_name': row.get('Product Name', ''),
                    'has_split': str(row.get('Split', '')).lower() == 'yes',
                    'acv_breakdown': {
                        'software': self._parse_amount(row.get('ACV Sales (Software)', 0)),
                        'managed_services': self._parse_amount(row.get('ACV Sales (Managed Services)', 0)),
                        'professional_services': self._parse_amount(row.get('ACV Sales (Professional Services) ', 0)),
                    },
                    'tcv_professional_services': self._parse_amount(row.get('TCV (Professional Services)', 0)),
                    'is_ps_deal': self._is_ps_deal(row),
                    'data_source': 'manual'
                }
                
                # Extract company info
                transaction['company_id'], transaction['company_name'] = self._extract_customer_info(transaction['customer'])
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {str(e)}")
                
        return transactions
        
    def _parse_scraped_format(self, df: pd.DataFrame) -> List[Dict]:
        """Parse scraped format (lower quality, may have issues)"""
        transactions = []
        
        # Map potentially different column names
        column_mapping = {
            'ACV (EUR)': ['ACV (EUR)', 'ACV EUR', 'ACV'],
            'Unique ID': ['Unique ID', 'Unique_ID', 'ID'],
            'Deal Name': ['Deal Name', 'Deal_Name', 'Name'],
            'Customer': ['Customer', 'Company', 'Client'],
        }
        
        # Normalize column names
        for standard, variations in column_mapping.items():
            for var in variations:
                if var in df.columns and standard not in df.columns:
                    df[standard] = df[var]
                    
        # Filter rows with Unique ID if available
        if 'Unique ID' in df.columns:
            df = df[df['Unique ID'].notna()].copy()
            
        for idx, row in df.iterrows():
            try:
                transaction = self._parse_scraped_row(row)
                transaction['data_source'] = 'scraped'
                transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Error processing scraped row {idx}: {str(e)}")
                
        return transactions
        
    def _parse_scraped_row(self, row: pd.Series) -> Dict:
        """Parse a single row from scraped data"""
        # Similar to original parser but with more error handling
        deal_name = str(row.get('Deal Name', ''))
        
        # Check if deal name is truncated and add warning
        if deal_name.endswith('…'):
            logger.warning(f"Truncated deal name detected: {deal_name}")
            
        transaction = {
            'salescookie_id': str(row.get('Unique ID', '')),
            'deal_name': deal_name,
            'customer': row.get('Customer', ''),
            'close_date': self._parse_date(row.get('Close Date')),
            'revenue_start_date': self._parse_date(row.get('Revenue Start Date')),
            'commission_amount': self._parse_commission_amount(row.get('Commission', '')),
            'commission_currency': 'EUR',  # Often missing in scraped data
            'commission_rate': self._parse_rate(row.get('Commission Rate')),
            'deal_type': row.get('Deal Type', ''),
            'acv_eur': self._parse_amount(row.get('ACV (EUR)')),
            'currency': row.get('Currency', 'EUR'),
            'types_of_acv': str(row.get('Types of ACV', '')),
            'product_name': row.get('Product Name', ''),
            'has_split': str(row.get('Split', '')).lower() == 'yes',
            'is_ps_deal': self._is_ps_deal(row),
        }
        
        # Extract company info
        transaction['company_id'], transaction['company_name'] = self._extract_customer_info(transaction['customer'])
        
        return transaction
        
    def _extract_customer_info(self, customer_str: str) -> Tuple[str, str]:
        """Extract company ID and name from customer field"""
        if pd.isna(customer_str):
            return '', ''
            
        customer_str = str(customer_str)
        if ';' in customer_str:
            parts = customer_str.split(';', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
                
        return '', customer_str.strip()
        
    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if pd.isna(date_str) or not date_str:
            return None
            
        # Try multiple date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]
        
        date_str = str(date_str).strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    def _parse_amount(self, amount) -> float:
        """Parse amount to float"""
        if pd.isna(amount) or amount == '' or amount is None:
            return 0.0
            
        try:
            # Remove currency symbols and thousands separators
            amount_str = str(amount).replace('€', '').replace('$', '').replace(',', '').strip()
            return float(amount_str)
        except:
            return 0.0
            
    def _parse_commission_amount(self, commission_str) -> float:
        """Parse commission from various formats"""
        if pd.isna(commission_str):
            return 0.0
            
        commission_str = str(commission_str)
        
        # Handle format like "267.96 (EUR)"
        match = re.search(r'([\d,]+\.?\d*)', commission_str)
        if match:
            return float(match.group(1).replace(',', ''))
            
        return self._parse_amount(commission_str)
        
    def _parse_rate(self, rate_str) -> float:
        """Parse commission rate percentage"""
        if pd.isna(rate_str) or not rate_str:
            return 0.0
            
        try:
            rate_clean = str(rate_str).replace('%', '').strip()
            return float(rate_clean) / 100.0
        except:
            return 0.0
            
    def _is_ps_deal(self, row) -> bool:
        """Determine if this is a Professional Services deal"""
        indicators = [
            str(row.get('Deal Name', '')).upper().startswith('PS @'),
            str(row.get('Deal Type', '')).lower() == 'professional services',
            self._parse_rate(row.get('Commission Rate')) == 0.01,  # 1% rate
            self._parse_amount(row.get('TCV (Professional Services)', 0)) > 0,
        ]
        
        return any(indicators)
        
    def generate_quality_report(self) -> str:
        """Generate a comprehensive data quality report"""
        report = ["=== SalesCookie Data Quality Report ===\n"]
        
        for file_path, quality in self.data_quality_reports.items():
            report.append(f"\nFile: {os.path.basename(file_path)}")
            report.append(f"Source Type: {quality.source_type.value}")
            report.append(f"Quality Score: {quality.quality_score:.1f}/100")
            report.append(f"Total Records: {quality.total_records}")
            report.append(f"Valid IDs: {quality.valid_ids} ({quality.valid_ids/quality.total_records*100:.1f}%)")
            report.append(f"Valid Names: {quality.valid_names} ({quality.valid_names/quality.total_records*100:.1f}%)")
            
            if quality.truncated_names > 0:
                report.append(f"⚠️  Truncated Names: {quality.truncated_names}")
                
            if quality.missing_fields:
                report.append("\nMissing Fields:")
                for field, count in quality.missing_fields.items():
                    report.append(f"  - {field}: {count} records")
                    
            if quality.warnings:
                report.append("\nWarnings:")
                for warning in quality.warnings:
                    report.append(f"  ⚠️  {warning}")
                    
        return "\n".join(report)