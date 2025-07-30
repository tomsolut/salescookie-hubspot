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
                # We can't know the expected commission without knowing the rate
                # So we'll use a conservative estimate or flag it differently
                
                self.discrepancies.append(Discrepancy(
                    deal_id=hs_deal['hubspot_id'],
                    deal_name=hs_deal['deal_name'],
                    discrepancy_type='missing_deal',
                    expected_value=f"Deal in SalesCookie",
                    actual_value="Not found",
                    impact_eur=0,  # Can't calculate without knowing the commission rate
                    severity='high',
                    details=f"Closed Won deal worth €{hs_deal['commission_amount']:,.2f} not found in SalesCookie"
                ))
                
    def _validate_commissions(self):
        """Validate commission calculations for matched deals using SalesCookie rates"""
        for match in self.matched_deals:
            hs_deal = match['hubspot']
            sc_transactions = match['salescookie']
            
            # For each SalesCookie transaction, validate the calculation
            for sc_tx in sc_transactions:
                sc_amount = sc_tx['commission_amount']
                sc_rate = sc_tx.get('commission_rate', 0)
                # Use ACV amount from SalesCookie itself, not HubSpot
                sc_acv = sc_tx.get('acv_eur', 0)
                is_split = sc_tx.get('has_split', False)
                
                # Skip if no rate or ACV available
                if sc_rate == 0 or sc_acv == 0:
                    continue
                    
                # Calculate what the commission should be based on SC's own ACV and rate
                expected_based_on_sc_data = sc_acv * sc_rate
                
                # For split deals, the commission is divided (usually 50/50)
                if is_split:
                    # Count how many transactions we have for this deal
                    same_deal_count = len([t for t in sc_transactions if t.get('acv_eur') == sc_acv])
                    if same_deal_count > 1:
                        expected_based_on_sc_data = expected_based_on_sc_data / same_deal_count
                
                # Check if the math is correct (allow 1 EUR tolerance for rounding)
                if abs(expected_based_on_sc_data - sc_amount) > 1.0:
                    self.discrepancies.append(Discrepancy(
                        deal_id=hs_deal['hubspot_id'],
                        deal_name=hs_deal['deal_name'],
                        discrepancy_type='calculation_error',
                        expected_value=f"€{sc_acv:,.2f} × {sc_rate*100:.2f}% = €{expected_based_on_sc_data:,.2f}{' (split)' if is_split else ''}",
                        actual_value=f"€{sc_amount:,.2f}",
                        impact_eur=abs(expected_based_on_sc_data - sc_amount),
                        severity='high' if abs(expected_based_on_sc_data - sc_amount) > 100 else 'medium',
                        details=f"SalesCookie internal calculation error: ACV × rate ≠ commission{' (split deal)' if is_split else ''}"
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