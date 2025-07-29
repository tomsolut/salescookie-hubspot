"""
Enhanced Reconciliation Engine with improved matching and quality awareness
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from commission_config import CommissionConfig

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Represents a match between HubSpot and SalesCookie"""
    hubspot_id: str
    salescookie_id: str
    match_type: str  # 'id', 'name_date', 'company_date', 'fuzzy'
    confidence: float  # 0-100
    hubspot_deal: Dict
    salescookie_transactions: List[Dict]
    
@dataclass
class ReconciliationResult:
    """Complete reconciliation results"""
    matches: List[MatchResult]
    unmatched_hubspot: List[Dict]
    unmatched_salescookie: List[Dict]
    discrepancies: List['Discrepancy']
    summary: Dict
    data_quality_score: float

@dataclass
class Discrepancy:
    """Enhanced discrepancy with confidence and match information"""
    deal_id: str
    deal_name: str
    discrepancy_type: str
    expected_value: str
    actual_value: str
    impact_eur: float
    severity: str
    details: str
    match_confidence: float = 0.0
    data_source: str = "unknown"
    
class ReconciliationEngineV2:
    """Enhanced reconciliation with multiple matching strategies"""
    
    def __init__(self, hubspot_deals: List[Dict], salescookie_transactions: List[Dict]):
        self.hubspot_deals = hubspot_deals
        self.salescookie_transactions = salescookie_transactions
        self.matches = []
        self.discrepancies = []
        self.config = CommissionConfig()
        self.centrally_processed_transactions = []
        
    def reconcile(self, data_quality_score: float = 100.0) -> ReconciliationResult:
        """Run enhanced reconciliation process"""
        logger.info(f"Starting reconciliation with data quality score: {data_quality_score:.1f}")
        
        # Phase 0: Identify centrally processed transactions
        self._identify_centrally_processed_transactions()
        
        # Phase 1: Try different matching strategies
        self._match_by_id()
        self._match_by_name_and_date()
        self._match_by_company_and_date()
        
        # Phase 2: Validate matched deals
        self._validate_matches()
        
        # Phase 3: Check for missing deals
        self._check_unmatched_deals()
        
        # Phase 4: Generate summary
        result = self._generate_result(data_quality_score)
        
        logger.info(f"Reconciliation complete: {len(self.matches)} matches, {len(self.discrepancies)} discrepancies")
        
        return result
        
    def _match_by_id(self):
        """Match deals by Unique ID (highest confidence)"""
        logger.info("Matching by Unique ID...")
        
        # Create lookup for SalesCookie by ID
        sc_by_id = {}
        for sc_deal in self.salescookie_transactions:
            deal_id = sc_deal.get('salescookie_id', '')
            if deal_id:
                if deal_id not in sc_by_id:
                    sc_by_id[deal_id] = []
                sc_by_id[deal_id].append(sc_deal)
                
        # Match HubSpot deals
        matched_hs_ids = set()
        for hs_deal in self.hubspot_deals:
            hs_id = str(hs_deal['hubspot_id'])
            
            if hs_id in sc_by_id:
                self.matches.append(MatchResult(
                    hubspot_id=hs_id,
                    salescookie_id=hs_id,
                    match_type='id',
                    confidence=100.0,
                    hubspot_deal=hs_deal,
                    salescookie_transactions=sc_by_id[hs_id]
                ))
                matched_hs_ids.add(hs_id)
                
        logger.info(f"Matched {len(matched_hs_ids)} deals by ID")
        
    def _match_by_name_and_date(self):
        """Match by deal name and close date (high confidence)"""
        logger.info("Matching by name and date...")
        
        # Skip already matched deals
        matched_hs_ids = {m.hubspot_id for m in self.matches}
        matched_sc_ids = {sc.get('salescookie_id') for m in self.matches for sc in m.salescookie_transactions}
        
        matches_found = 0
        
        for hs_deal in self.hubspot_deals:
            if hs_deal['hubspot_id'] in matched_hs_ids:
                continue
                
            hs_name = hs_deal.get('deal_name', '')
            hs_date = hs_deal.get('close_date')
            
            if hs_name and hs_date:
                for sc_deal in self.salescookie_transactions:
                    if sc_deal.get('salescookie_id') in matched_sc_ids:
                        continue
                        
                    sc_name = sc_deal.get('deal_name', '')
                    sc_date = sc_deal.get('close_date')
                    
                    # Check exact name match and date within 1 day
                    if (hs_name == sc_name and 
                        sc_date and 
                        abs((hs_date - sc_date).days) <= 1):
                        
                        self.matches.append(MatchResult(
                            hubspot_id=hs_deal['hubspot_id'],
                            salescookie_id=sc_deal.get('salescookie_id', ''),
                            match_type='name_date',
                            confidence=95.0,
                            hubspot_deal=hs_deal,
                            salescookie_transactions=[sc_deal]
                        ))
                        matched_hs_ids.add(hs_deal['hubspot_id'])
                        matched_sc_ids.add(sc_deal.get('salescookie_id'))
                        matches_found += 1
                        break
                        
        logger.info(f"Matched {matches_found} additional deals by name and date")
        
    def _match_by_company_and_date(self):
        """Match by company and close date (medium confidence)"""
        logger.info("Matching by company and date...")
        
        # Skip already matched deals
        matched_hs_ids = {m.hubspot_id for m in self.matches}
        matched_sc_ids = {sc.get('salescookie_id') for m in self.matches for sc in m.salescookie_transactions}
        
        matches_found = 0
        
        for hs_deal in self.hubspot_deals:
            if hs_deal['hubspot_id'] in matched_hs_ids:
                continue
                
            hs_company = self._normalize_company(hs_deal.get('company', ''))
            hs_date = hs_deal.get('close_date')
            hs_amount = hs_deal.get('commission_amount', 0)
            
            if hs_company and hs_date:
                potential_matches = []
                
                for sc_deal in self.salescookie_transactions:
                    if sc_deal.get('salescookie_id') in matched_sc_ids:
                        continue
                        
                    sc_company = self._normalize_company(sc_deal.get('company_name', ''))
                    sc_date = sc_deal.get('close_date')
                    
                    if (hs_company == sc_company and 
                        sc_date and 
                        abs((hs_date - sc_date).days) <= 7):
                        
                        # Calculate confidence based on date difference and amount
                        date_diff = abs((hs_date - sc_date).days)
                        confidence = 80.0 - (date_diff * 5)  # Reduce confidence by 5% per day
                        
                        # Check if amounts are similar (within 10%)
                        sc_acv = sc_deal.get('acv_eur', 0)
                        if sc_acv > 0 and abs(hs_amount - sc_acv) / sc_acv < 0.1:
                            confidence += 10  # Boost confidence for matching amounts
                            
                        potential_matches.append((sc_deal, confidence))
                        
                # Take the best match if found
                if potential_matches:
                    best_match = max(potential_matches, key=lambda x: x[1])
                    sc_deal, confidence = best_match
                    
                    self.matches.append(MatchResult(
                        hubspot_id=hs_deal['hubspot_id'],
                        salescookie_id=sc_deal.get('salescookie_id', ''),
                        match_type='company_date',
                        confidence=confidence,
                        hubspot_deal=hs_deal,
                        salescookie_transactions=[sc_deal]
                    ))
                    matched_hs_ids.add(hs_deal['hubspot_id'])
                    matched_sc_ids.add(sc_deal.get('salescookie_id'))
                    matches_found += 1
                    
        logger.info(f"Matched {matches_found} additional deals by company and date")
        
    def _normalize_company(self, company_name: str) -> str:
        """Normalize company name for matching"""
        if not company_name:
            return ""
            
        import re
        name = company_name.lower().strip()
        
        # Remove common suffixes
        suffixes = [
            r'\s*\(.*\)$',  # Remove anything in parentheses
            r'\s*(gmbh|ag|bank|aktiengesellschaft|abp|oyj|inc\.|inc|ltd|limited|plc|s\.a\.|sa).*$',
            r'\s*&\s*co\.?.*$',
            r'\s*kommanditgesellschaft.*$',
        ]
        
        for suffix in suffixes:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)
            
        # Remove special characters and normalize whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name
        
    def _validate_matches(self):
        """Validate commission calculations for matched deals"""
        for match in self.matches:
            hs_deal = match.hubspot_deal
            sc_transactions = match.salescookie_transactions
            
            # Calculate expected commission
            year = hs_deal['close_date'].year if hs_deal['close_date'] else datetime.now().year
            expected_commission = self._calculate_expected_commission(hs_deal, year)
            
            # Sum actual commissions
            actual_commission = sum(t.get('commission_amount', 0) for t in sc_transactions)
            
            # Check for discrepancy (allow 1 EUR tolerance)
            if abs(expected_commission - actual_commission) > 1.0:
                severity = 'high' if abs(expected_commission - actual_commission) > 100 else 'medium'
                
                self.discrepancies.append(Discrepancy(
                    deal_id=hs_deal['hubspot_id'],
                    deal_name=hs_deal['deal_name'],
                    discrepancy_type='wrong_commission_amount',
                    expected_value=f"€{expected_commission:,.2f}",
                    actual_value=f"€{actual_commission:,.2f}",
                    impact_eur=abs(expected_commission - actual_commission),
                    severity=severity,
                    details=f"Match confidence: {match.confidence:.0f}%",
                    match_confidence=match.confidence,
                    data_source=sc_transactions[0].get('data_source', 'unknown') if sc_transactions else 'unknown'
                ))
                
    def _check_unmatched_deals(self):
        """Check for HubSpot deals not found in SalesCookie"""
        matched_hs_ids = {m.hubspot_id for m in self.matches}
        
        for hs_deal in self.hubspot_deals:
            if hs_deal['hubspot_id'] not in matched_hs_ids:
                year = hs_deal['close_date'].year if hs_deal['close_date'] else datetime.now().year
                expected_commission = self._calculate_expected_commission(hs_deal, year)
                
                self.discrepancies.append(Discrepancy(
                    deal_id=hs_deal['hubspot_id'],
                    deal_name=hs_deal['deal_name'],
                    discrepancy_type='missing_deal',
                    expected_value="Deal in SalesCookie",
                    actual_value="Not found",
                    impact_eur=expected_commission,
                    severity='high',
                    details=f"Closed Won deal worth €{hs_deal['commission_amount']:,.2f} not found in SalesCookie",
                    match_confidence=0.0,
                    data_source='none'
                ))
                
    def _calculate_expected_commission(self, deal: Dict, year: int) -> float:
        """Calculate expected commission for a deal"""
        base_amount = deal['commission_amount']
        
        if deal.get('is_ps_deal', False):
            # PS deals get flat 1%
            return base_amount * 0.01
        else:
            # Regular deals - determine type and rate
            deal_type = self._determine_deal_type(deal)
            rate = self.config.get_commission_rate(year, deal_type, deal.get('is_ps_deal', False))
            
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
        elif 'professional services' in acv_types and not deal.get('is_ps_deal', False):
            return 'recurring_professional_services'
        else:
            return 'software'
            
    def _identify_centrally_processed_transactions(self):
        """Identify CPI and Fix Increase deals that are centrally processed"""
        logger.info("Identifying centrally processed transactions...")
        
        centrally_processed_count = 0
        remaining_transactions = []
        
        for transaction in self.salescookie_transactions:
            deal_name = transaction.get('deal_name', '').lower()
            
            # Check if this is a centrally processed deal
            if any(indicator in deal_name for indicator in ['cpi increase', 'fix increase', 'indexation']):
                self.centrally_processed_transactions.append(transaction)
                centrally_processed_count += 1
                logger.debug(f"Marked as centrally processed: {transaction.get('deal_name')}")
            else:
                remaining_transactions.append(transaction)
        
        # Update the transactions list to exclude centrally processed ones
        self.salescookie_transactions = remaining_transactions
        
        logger.info(f"Identified {centrally_processed_count} centrally processed transactions")
        logger.info(f"Remaining transactions for matching: {len(self.salescookie_transactions)}")
    
    def _generate_result(self, data_quality_score: float) -> ReconciliationResult:
        """Generate comprehensive reconciliation result"""
        # Separate matched and unmatched
        matched_hs_ids = {m.hubspot_id for m in self.matches}
        matched_sc_ids = {sc.get('salescookie_id') for m in self.matches for sc in m.salescookie_transactions}
        
        unmatched_hubspot = [d for d in self.hubspot_deals if d['hubspot_id'] not in matched_hs_ids]
        unmatched_salescookie = [t for t in self.salescookie_transactions 
                               if t.get('salescookie_id') not in matched_sc_ids]
        
        # Calculate summary statistics
        total_hs_amount = sum(d['commission_amount'] for d in self.hubspot_deals)
        total_sc_commission = sum(t.get('commission_amount', 0) for t in self.salescookie_transactions)
        
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
            
        # Match confidence statistics
        match_by_type = {}
        for match in self.matches:
            if match.match_type not in match_by_type:
                match_by_type[match.match_type] = 0
            match_by_type[match.match_type] += 1
            
        # Calculate totals including centrally processed
        total_sc_transactions_original = len(self.salescookie_transactions) + len(self.centrally_processed_transactions)
        centrally_processed_commission = sum(t.get('commission_amount', 0) for t in self.centrally_processed_transactions)
        
        summary = {
            'hubspot_deals_count': len(self.hubspot_deals),
            'hubspot_total_amount': total_hs_amount,
            'salescookie_transactions_count': len(self.salescookie_transactions),
            'salescookie_total_transactions': total_sc_transactions_original,
            'centrally_processed_count': len(self.centrally_processed_transactions),
            'centrally_processed_commission': centrally_processed_commission,
            'salescookie_total_commission': total_sc_commission,
            'matched_deals_count': len(self.matches),
            'unmatched_hubspot_count': len(unmatched_hubspot),
            'unmatched_salescookie_count': len(unmatched_salescookie),
            'total_discrepancies': len(self.discrepancies),
            'discrepancies_by_type': disc_by_type,
            'matches_by_type': match_by_type,
            'total_impact': sum(d.impact_eur for d in self.discrepancies),
            'average_match_confidence': sum(m.confidence for m in self.matches) / len(self.matches) if self.matches else 0,
            'data_quality_score': data_quality_score,
        }
        
        return ReconciliationResult(
            matches=self.matches,
            unmatched_hubspot=unmatched_hubspot,
            unmatched_salescookie=unmatched_salescookie,
            discrepancies=self.discrepancies,
            summary=summary,
            data_quality_score=data_quality_score
        )