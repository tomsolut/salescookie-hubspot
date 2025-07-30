"""
Enhanced Reconciliation Engine with withholding, forecast, and split support
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from commission_config import CommissionConfig
from reconciliation_engine_v2 import ReconciliationEngineV2, MatchResult, ReconciliationResult, Discrepancy
from kicker_calculator import KickerCalculator

logger = logging.getLogger(__name__)

class ReconciliationEngineV3(ReconciliationEngineV2):
    """Enhanced reconciliation with support for withholdings, forecasts, and splits"""
    
    def __init__(self, hubspot_deals: List[Dict], salescookie_transactions: List[Dict]):
        super().__init__(hubspot_deals, salescookie_transactions)
        
        # Separate transactions by type
        self.regular_transactions = []
        self.withholding_transactions = []
        self.forecast_transactions = []
        self.split_transactions = []
        
        # Initialize kicker calculator
        self.kicker_calculator = KickerCalculator(self.config)
        
        # Add all HubSpot deals to kicker calculator
        for deal in hubspot_deals:
            self.kicker_calculator.add_deal(deal)
        
        self._categorize_transactions()
        
    def _categorize_transactions(self):
        """Categorize SalesCookie transactions by type"""
        for transaction in self.salescookie_transactions:
            tx_type = transaction.get('transaction_type', 'regular')
            
            if tx_type == 'withholding':
                self.withholding_transactions.append(transaction)
            elif tx_type == 'forecast':
                self.forecast_transactions.append(transaction)
            elif tx_type == 'split':
                self.split_transactions.append(transaction)
            else:
                self.regular_transactions.append(transaction)
                
        logger.info(f"Categorized transactions: {len(self.regular_transactions)} regular, "
                   f"{len(self.withholding_transactions)} withholding, "
                   f"{len(self.forecast_transactions)} forecast, "
                   f"{len(self.split_transactions)} split")
    
    def reconcile(self, data_quality_score: float = 100.0) -> ReconciliationResult:
        """Run enhanced reconciliation process with withholding support"""
        logger.info(f"Starting enhanced reconciliation with data quality score: {data_quality_score:.1f}")
        
        # Phase 0: Identify centrally processed transactions
        self._identify_centrally_processed_transactions()
        
        # Phase 1: Match regular transactions first
        self.salescookie_transactions = self.regular_transactions
        self._match_by_id()
        self._match_by_name_and_date()
        self._match_by_company_and_date()
        
        # Phase 2: Match withholding transactions
        self._match_withholdings()
        
        # Phase 3: Match split transactions
        self._match_splits()
        
        # Phase 4: Validate matched deals
        self._validate_matches()
        
        # Phase 5: Check for missing deals
        self._check_unmatched_deals()
        
        # Phase 6: Generate forecast analysis
        self._analyze_forecasts()
        
        # Phase 7: Generate summary
        result = self._generate_enhanced_result(data_quality_score)
        
        logger.info(f"Enhanced reconciliation complete: {len(self.matches)} matches, "
                   f"{len(self.discrepancies)} discrepancies")
        
        return result
        
    def _match_withholdings(self):
        """Match withholding transactions to existing matches"""
        logger.info(f"Matching {len(self.withholding_transactions)} withholding transactions...")
        
        withholding_matches = 0
        
        for match in self.matches:
            hs_deal = match.hubspot_deal
            
            # Skip centrally processed deals - they don't have traditional withholding
            if hs_deal.get('is_centrally_processed', False):
                continue
            
            # Look for corresponding withholding transaction
            for wh_transaction in self.withholding_transactions:
                # Match by ID or name+date
                if (wh_transaction.get('salescookie_id') == hs_deal.get('hubspot_id') or
                    (wh_transaction.get('deal_name') == hs_deal.get('deal_name') and
                     self._dates_match(wh_transaction.get('close_date'), hs_deal.get('close_date'), 1))):
                    
                    # Add withholding info to match
                    match.salescookie_transactions.append(wh_transaction)
                    withholding_matches += 1
                    
                    # Create discrepancy if commission doesn't match withholding pattern
                    expected_withholding = match.salescookie_transactions[0].get('commission_amount', 0) * 2
                    est_commission = wh_transaction.get('est_commission', 0)
                    
                    if abs(expected_withholding - est_commission) > 0.01:
                        self.discrepancies.append(Discrepancy(
                            deal_id=hs_deal['hubspot_id'],
                            deal_name=hs_deal['deal_name'],
                            discrepancy_type='withholding_mismatch',
                            expected_value=f"€{expected_withholding:,.2f}",
                            actual_value=f"€{est_commission:,.2f}",
                            impact_eur=abs(expected_withholding - est_commission),
                            severity='medium',
                            details=f"Withholding calculation mismatch. Expected 50% withholding.",
                            match_confidence=match.confidence,
                            data_source='withholding'
                        ))
                    
                    break
                    
        logger.info(f"Matched {withholding_matches} withholding transactions")
        
    def _match_splits(self):
        """Match split transactions (cross-year deals)"""
        logger.info(f"Matching {len(self.split_transactions)} split transactions...")
        
        split_matches = 0
        new_matches_created = 0
        
        # Split transactions might not have direct matches in current period HubSpot data
        # They represent future portions of deals closed in previous periods
        # However, some split transactions are the FIRST entry for a deal
        for split_transaction in self.split_transactions:
            matched = False
            
            # Try to find in existing matches
            for match in self.matches:
                if (split_transaction.get('deal_name') == match.hubspot_deal.get('deal_name') or
                    split_transaction.get('salescookie_id') == match.hubspot_deal.get('hubspot_id')):
                    match.salescookie_transactions.append(split_transaction)
                    split_matches += 1
                    matched = True
                    break
            
            if not matched:
                # NEW: Try to match directly against HubSpot deals
                for hs_deal in self.hubspot_deals:
                    # Skip if already matched
                    if any(m.hubspot_id == hs_deal['hubspot_id'] for m in self.matches):
                        continue
                    
                    # Try matching by ID first (highest confidence)
                    if split_transaction.get('salescookie_id') == hs_deal.get('hubspot_id'):
                        new_match = MatchResult(
                            hubspot_id=hs_deal['hubspot_id'],
                            salescookie_id=split_transaction.get('salescookie_id'),
                            confidence=100.0,
                            match_type='id_match',
                            hubspot_deal=hs_deal,
                            salescookie_transactions=[split_transaction]
                        )
                        self.matches.append(new_match)
                        new_matches_created += 1
                        split_matches += 1
                        matched = True
                        break
                    
                    # Try matching by name and date (lower confidence)
                    elif (split_transaction.get('deal_name') == hs_deal.get('deal_name') and
                          self._dates_match(split_transaction.get('close_date'), 
                                           hs_deal.get('close_date'), 
                                           1)):
                        new_match = MatchResult(
                            hubspot_id=hs_deal['hubspot_id'],
                            salescookie_id=split_transaction.get('salescookie_id'),
                            confidence=85.0,
                            match_type='name_date_match',
                            hubspot_deal=hs_deal,
                            salescookie_transactions=[split_transaction]
                        )
                        self.matches.append(new_match)
                        new_matches_created += 1
                        split_matches += 1
                        matched = True
                        break
                    
            if not matched:
                # Create a standalone entry for split transactions without current period match
                self.split_transactions_unmatched = getattr(self, 'split_transactions_unmatched', [])
                self.split_transactions_unmatched.append(split_transaction)
                
        logger.info(f"Matched {split_matches} split transactions ({new_matches_created} new matches created)")
        
    def _analyze_forecasts(self):
        """Analyze forecast transactions for future planning"""
        logger.info(f"Analyzing {len(self.forecast_transactions)} forecast transactions...")
        
        # Group forecasts by deal and calculate totals
        forecast_summary = {
            'total_forecast_amount': 0,
            'total_kickers': 0,
            'deals_with_kickers': 0,
            'forecast_deals': [],
            'quarterly_quota_progress': {}
        }
        
        for forecast in self.forecast_transactions:
            base_commission = forecast.get('commission_amount', 0) or forecast.get('est_commission', 0)
            
            # Calculate kickers based on quota achievement
            kicker_info = self.kicker_calculator.calculate_commission_with_kicker(
                base_commission, 
                {'close_date': forecast.get('close_date'), 'commission_amount': base_commission}
            )
            
            # Also check if transaction has explicit kicker values
            early_bird = forecast.get('early_bird_kicker', 0)
            performance = forecast.get('performance_kicker', 0)
            campaign = forecast.get('campaign_kicker', 0)
            explicit_kickers = early_bird + performance + campaign
            
            # Use the higher of calculated or explicit kickers
            total_kickers = max(kicker_info['kicker_amount'], explicit_kickers)
            
            forecast_summary['total_forecast_amount'] += base_commission
            forecast_summary['total_kickers'] += total_kickers
            
            if total_kickers > 0:
                forecast_summary['deals_with_kickers'] += 1
                
            forecast_summary['forecast_deals'].append({
                'deal_name': forecast.get('deal_name'),
                'commission': base_commission,
                'kickers': total_kickers,
                'kicker_type': kicker_info.get('kicker_type'),
                'kicker_multiplier': kicker_info.get('kicker_multiplier', 1.0),
                'revenue_start': forecast.get('revenue_start_date')
            })
        
        # Add quarterly quota progress
        forecast_summary['quarterly_quota_progress'] = self.kicker_calculator.get_quarterly_summary()
            
        self.forecast_summary = forecast_summary
        
    def _validate_matches(self):
        """Enhanced validation using SalesCookie rates"""
        # First validate CPI/FP increase revenue dates
        self._validate_increase_revenue_dates()
        
        for match in self.matches:
            hs_deal = match.hubspot_deal
            sc_transactions = match.salescookie_transactions
            
            # Skip validation for centrally processed deals
            if hs_deal.get('is_centrally_processed', False):
                continue
            
            # Separate transaction types
            regular_txs = [tx for tx in sc_transactions if tx.get('transaction_type', 'regular') == 'regular']
            withholding_txs = [tx for tx in sc_transactions if tx.get('transaction_type') == 'withholding']
            
            # Validate each transaction's calculation using its own data
            for sc_tx in regular_txs:
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
                    same_deal_count = len([t for t in sc_transactions if t.get('acv_eur') == sc_acv and t.get('transaction_type', 'regular') == 'regular'])
                    if same_deal_count > 1:
                        expected_based_on_sc_data = expected_based_on_sc_data / same_deal_count
                
                # For withholding deals, the paid amount should be 50% of full commission
                if withholding_txs:
                    # This is the 50% payment, so the full commission would be double
                    expected_based_on_sc_data = expected_based_on_sc_data / 2
                
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
                        details=f"SalesCookie internal calculation error: ACV × rate ≠ commission"
                                f"{' (split deal)' if is_split else ''}"
                                f"{' (withholding: 50% payment)' if withholding_txs else ''}",
                        match_confidence=match.confidence,
                        data_source=sc_tx.get('data_source', 'unknown')
                    ))
    
    def _generate_enhanced_result(self, data_quality_score: float) -> ReconciliationResult:
        """Generate enhanced result with withholding and forecast info"""
        # Get base result
        result = self._generate_result(data_quality_score)
        
        # Add enhanced summary info
        result.summary['withholding_transactions'] = len(self.withholding_transactions)
        result.summary['forecast_transactions'] = len(self.forecast_transactions)
        result.summary['split_transactions'] = len(self.split_transactions)
        
        # Add withholding summary
        # For withholding transactions:
        # - commission_amount is the 50% that was paid
        # - est_commission should be the full 100% commission
        # - If est_commission is 0 or missing, calculate it as commission_amount * 2
        
        total_paid = 0
        total_withheld = 0
        
        for tx in self.withholding_transactions:
            paid = tx.get('commission_amount', 0)
            est_full = tx.get('est_commission', 0)
            
            # If est_commission is missing or zero, assume 50% withholding
            if est_full == 0 and paid > 0:
                est_full = paid * 2
                
            withheld = est_full - paid if est_full > paid else paid
            
            total_paid += paid
            total_withheld += withheld
        
        result.summary['withholding_summary'] = {
            'total_paid': total_paid,
            'total_withheld': total_withheld,
            'total_full_commission': total_paid + total_withheld
        }
        
        # Add forecast summary
        if hasattr(self, 'forecast_summary'):
            result.summary['forecast_summary'] = self.forecast_summary
            
        # Add centrally processed summary
        centrally_processed_total = sum(
            t.get('commission_amount', 0) for t in self.centrally_processed_transactions
        )
        
        result.summary['centrally_processed'] = {
            'count': len(self.centrally_processed_transactions),
            'total_commission': centrally_processed_total,
            'types': {
                'cpi_increase': len([t for t in self.centrally_processed_transactions 
                                   if 'cpi increase' in t.get('deal_name', '').lower()]),
                'fp_increase': len([t for t in self.centrally_processed_transactions 
                                  if 'fp increase' in t.get('deal_name', '').lower()]),
                'fixed_price_increase': len([t for t in self.centrally_processed_transactions 
                                           if 'fixed price increase' in t.get('deal_name', '').lower()]),
                'indexation': len([t for t in self.centrally_processed_transactions 
                                 if 'indexation' in t.get('deal_name', '').lower()])
            },
            'note': 'These deals are processed by SalesOps team and do not appear in HubSpot'
        }
            
        # Return result as is - we'll add all_deals when converting to dict
        return result
        
    def _dates_match(self, date1: datetime, date2: datetime, tolerance_days: int) -> bool:
        """Check if two dates match within tolerance"""
        if not date1 or not date2:
            return False
        return abs((date1 - date2).days) <= tolerance_days
    
    def _validate_increase_revenue_dates(self):
        """Validate that CPI/FP increase deals have revenue start on January 1st of following year"""
        for match in self.matches:
            # Skip non-increase deals
            deal_name = match.hubspot_deal.get('deal_name', '').lower()
            if not any(pattern in deal_name for pattern in ['cpi increase', 'fp increase', 'fixed price increase']):
                continue
                
            # Check each SalesCookie transaction
            for sc_tx in match.salescookie_transactions:
                sc_deal_name = sc_tx.get('deal_name', '').lower()
                if any(pattern in sc_deal_name for pattern in ['cpi increase', 'fp increase', 'fixed price increase']):
                    close_date = sc_tx.get('close_date')
                    revenue_start = sc_tx.get('revenue_start_date')
                    
                    if close_date and revenue_start:
                        # Expected revenue start is January 1st of following year
                        expected_year = close_date.year + 1
                        expected_revenue = datetime(expected_year, 1, 1)
                        
                        # Check if revenue start matches expected
                        if revenue_start.month != 1 or revenue_start.day != 1 or revenue_start.year != expected_year:
                            self.discrepancies.append(Discrepancy(
                                deal_id=match.hubspot_id,
                                deal_name=sc_tx.get('deal_name'),
                                discrepancy_type='incorrect_revenue_date',
                                expected_value=f"{expected_revenue.strftime('%Y-%m-%d')} (January following close)",
                                actual_value=revenue_start.strftime('%Y-%m-%d'),
                                impact_eur=0,  # No financial impact, just date issue
                                severity='medium',
                                details=f"CPI/FP increase deals must start January 1st of year after close. "
                                       f"Close: {close_date.strftime('%Y-%m-%d')}",
                                match_confidence=match.confidence,
                                data_source=sc_tx.get('data_source', 'unknown')
                            ))