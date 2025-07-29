"""
Commission Reconciliation Engine
Validates HubSpot deals against SalesCookie commission data
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from commission_config import CommissionConfig

logger = logging.getLogger(__name__)

@dataclass
class Discrepancy:
    """Represents a discrepancy between HubSpot and SalesCookie"""
    deal_id: str
    deal_name: str
    discrepancy_type: str  # missing_deal, wrong_amount, wrong_rate, wrong_quarter, etc.
    expected_value: str
    actual_value: str
    impact_eur: float
    severity: str  # high, medium, low
    details: str
    
class ReconciliationEngine:
    """Core reconciliation logic"""
    
    def __init__(self, hubspot_deals: List[Dict], salescookie_transactions: List[Dict]):
        self.hubspot_deals = hubspot_deals
        self.salescookie_transactions = salescookie_transactions
        self.discrepancies = []
        self.matched_deals = []
        self.config = CommissionConfig()
        
    def reconcile(self) -> Dict:
        """Run full reconciliation process"""
        logger.info("Starting reconciliation process...")
        
        # 1. Match deals between systems
        self._match_deals()
        
        # 2. Check for missing deals
        self._check_missing_deals()
        
        # 3. Validate commission calculations
        self._validate_commissions()
        
        # 4. Validate quarter allocations
        self._validate_quarter_splits()
        
        # 5. Validate currency handling
        self._validate_currency_conversions()
        
        # Generate summary
        summary = self._generate_summary()
        
        logger.info(f"Reconciliation complete. Found {len(self.discrepancies)} discrepancies")
        
        return {
            'summary': summary,
            'discrepancies': self.discrepancies,
            'matched_deals': self.matched_deals,
        }
        
    def _match_deals(self):
        """Match HubSpot deals with SalesCookie transactions"""
        # Create lookup dictionary for SalesCookie transactions
        sc_by_id = {}
        for transaction in self.salescookie_transactions:
            deal_id = transaction['salescookie_id']
            if deal_id not in sc_by_id:
                sc_by_id[deal_id] = []
            sc_by_id[deal_id].append(transaction)
            
        # Match deals
        for hs_deal in self.hubspot_deals:
            deal_id = hs_deal['hubspot_id']
            sc_transactions = sc_by_id.get(deal_id, [])
            
            if sc_transactions:
                self.matched_deals.append({
                    'hubspot': hs_deal,
                    'salescookie': sc_transactions,
                })
                
    def _check_missing_deals(self):
        """Check for HubSpot deals missing in SalesCookie"""
        matched_ids = {m['hubspot']['hubspot_id'] for m in self.matched_deals}
        
        for hs_deal in self.hubspot_deals:
            if hs_deal['hubspot_id'] not in matched_ids:
                # Deal is missing in SalesCookie
                year = hs_deal['close_date'].year if hs_deal['close_date'] else datetime.now().year
                
                # Calculate expected commission
                expected_commission = self._calculate_expected_commission(hs_deal, year)
                
                self.discrepancies.append(Discrepancy(
                    deal_id=hs_deal['hubspot_id'],
                    deal_name=hs_deal['deal_name'],
                    discrepancy_type='missing_deal',
                    expected_value=f"Deal in SalesCookie",
                    actual_value="Not found",
                    impact_eur=expected_commission,
                    severity='high',
                    details=f"Closed Won deal worth €{hs_deal['commission_amount']:,.2f} not found in SalesCookie"
                ))
                
    def _validate_commissions(self):
        """Validate commission calculations for matched deals"""
        for match in self.matched_deals:
            hs_deal = match['hubspot']
            sc_transactions = match['salescookie']
            
            # Calculate expected commission
            year = hs_deal['close_date'].year if hs_deal['close_date'] else datetime.now().year
            expected_commission = self._calculate_expected_commission(hs_deal, year)
            
            # Sum actual commissions from SalesCookie
            actual_commission = sum(t['commission_amount'] for t in sc_transactions)
            
            # Check for discrepancy (allow 1 EUR tolerance for rounding)
            if abs(expected_commission - actual_commission) > 1.0:
                # Determine the issue
                if hs_deal['is_ps_deal']:
                    expected_rate = "1.0%"
                    actual_rates = [f"{t['commission_rate']*100:.1f}%" for t in sc_transactions]
                else:
                    expected_rate = self._get_expected_rate(hs_deal, year)
                    actual_rates = [f"{t['commission_rate']*100:.1f}%" for t in sc_transactions]
                    
                self.discrepancies.append(Discrepancy(
                    deal_id=hs_deal['hubspot_id'],
                    deal_name=hs_deal['deal_name'],
                    discrepancy_type='wrong_commission_amount',
                    expected_value=f"€{expected_commission:,.2f}",
                    actual_value=f"€{actual_commission:,.2f}",
                    impact_eur=abs(expected_commission - actual_commission),
                    severity='high' if abs(expected_commission - actual_commission) > 100 else 'medium',
                    details=f"Expected rate: {expected_rate}, Actual rates: {', '.join(actual_rates)}"
                ))
                
    def _validate_quarter_splits(self):
        """Validate quarter allocation for split deals"""
        for match in self.matched_deals:
            hs_deal = match['hubspot']
            sc_transactions = match['salescookie']
            
            # Skip if no service start date (no split expected)
            if not hs_deal['service_start_date']:
                continue
                
            # Calculate expected quarters
            expected_quarters = self.config.calculate_split_quarters(
                hs_deal['close_date'],
                hs_deal['service_start_date']
            )
            
            # Get actual quarters from SalesCookie
            actual_quarters = {t['quarter']: t['commission_amount'] for t in sc_transactions}
            
            # Check if quarters match
            for expected_q, expected_split in expected_quarters.items():
                if expected_q not in actual_quarters:
                    self.discrepancies.append(Discrepancy(
                        deal_id=hs_deal['hubspot_id'],
                        deal_name=hs_deal['deal_name'],
                        discrepancy_type='missing_quarter_split',
                        expected_value=f"{expected_q} ({expected_split*100}%)",
                        actual_value="Not found",
                        impact_eur=hs_deal['commission_amount'] * expected_split * 0.073,  # Approximate
                        severity='medium',
                        details=f"Expected commission split in {expected_q} not found"
                    ))
                    
    def _validate_currency_conversions(self):
        """Validate currency handling for international deals"""
        for match in self.matched_deals:
            hs_deal = match['hubspot']
            
            # Check if deal has currency conversion (non-EUR original currency)
            if hs_deal['currency'] != 'EUR' and hs_deal['amount_company_currency'] != hs_deal['amount']:
                # This is an international deal with currency conversion
                if hs_deal['amount_company_currency'] == 0:
                    self.discrepancies.append(Discrepancy(
                        deal_id=hs_deal['hubspot_id'],
                        deal_name=hs_deal['deal_name'],
                        discrepancy_type='missing_currency_conversion',
                        expected_value=f"Company currency amount for {hs_deal['currency']} deal",
                        actual_value="€0.00",
                        impact_eur=0,  # Can't calculate without conversion rate
                        severity='high',
                        details=f"Deal in {hs_deal['currency']} missing company currency (EUR) amount"
                    ))
                    
    def _calculate_expected_commission(self, deal: Dict, year: int) -> float:
        """Calculate expected commission for a deal"""
        base_amount = deal['commission_amount']
        
        if deal['is_ps_deal']:
            # PS deals get flat 1%
            return base_amount * 0.01
        else:
            # Regular deals - determine type and rate
            deal_type = self._determine_deal_type(deal)
            rate = self.config.get_commission_rate(year, deal_type, deal['is_ps_deal'])
            
            return base_amount * rate
            
    def _determine_deal_type(self, deal: Dict) -> str:
        """Determine deal type for commission calculation"""
        # Check product name and types of ACV
        product = str(deal.get('product_name', '')).lower()
        acv_types = str(deal.get('types_of_acv', '')).lower()
        deployment = str(deal.get('deployment_type', '')).lower()
        
        # Priority order for type detection
        if 'indexation' in product or 'parameter' in product:
            return 'indexations_parameter'
        elif 'managed' in acv_types or 'managed' in product:
            if 'public' in deployment or 'rcloud' in deployment:
                return 'managed_services_public'
            else:
                return 'managed_services_private'
        elif 'professional services' in acv_types and not deal['is_ps_deal']:
            return 'recurring_professional_services'
        else:
            return 'software'
            
    def _get_expected_rate(self, deal: Dict, year: int) -> str:
        """Get expected commission rate as string"""
        deal_type = self._determine_deal_type(deal)
        rate = self.config.get_commission_rate(year, deal_type, deal['is_ps_deal'])
        return f"{rate*100:.1f}%"
        
    def _generate_summary(self) -> Dict:
        """Generate reconciliation summary"""
        total_hubspot_amount = sum(d['commission_amount'] for d in self.hubspot_deals)
        total_sc_commission = sum(t['commission_amount'] for t in self.salescookie_transactions)
        
        # Group discrepancies by type
        disc_by_type = {}
        for disc in self.discrepancies:
            if disc.discrepancy_type not in disc_by_type:
                disc_by_type[disc.discrepancy_type] = {
                    'count': 0,
                    'impact': 0.0,
                }
            disc_by_type[disc.discrepancy_type]['count'] += 1
            disc_by_type[disc.discrepancy_type]['impact'] += disc.impact_eur
            
        return {
            'hubspot_deals_count': len(self.hubspot_deals),
            'hubspot_total_amount': total_hubspot_amount,
            'salescookie_transactions_count': len(self.salescookie_transactions),
            'salescookie_total_commission': total_sc_commission,
            'matched_deals_count': len(self.matched_deals),
            'total_discrepancies': len(self.discrepancies),
            'discrepancies_by_type': disc_by_type,
            'total_impact': sum(d.impact_eur for d in self.discrepancies),
        }