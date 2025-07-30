#!/usr/bin/env python3
"""
Fix for split transaction matching issue in reconciliation engine.
Allows split transactions to create new matches, not just append to existing ones.
"""

def enhanced_match_splits(self):
    """Enhanced split transaction matching that can create new matches"""
    logger.info(f"Matching {len(self.split_transactions)} split transactions...")
    
    split_matches = 0
    new_matches_created = 0
    
    for split_transaction in self.split_transactions:
        matched = False
        
        # First, try to find in existing matches (current behavior)
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
                        salescookie_ids=[split_transaction.get('salescookie_id')],
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
                                       self.DATE_TOLERANCE_DAYS)):
                    new_match = MatchResult(
                        hubspot_id=hs_deal['hubspot_id'],
                        salescookie_ids=[split_transaction.get('salescookie_id')],
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
            # Still no match - add to unmatched list
            self.split_transactions_unmatched = getattr(self, 'split_transactions_unmatched', [])
            self.split_transactions_unmatched.append(split_transaction)
    
    logger.info(f"Matched {split_matches} split transactions ({new_matches_created} new matches created)")


# Implementation instructions:
# Replace the _match_splits method in reconciliation_engine_v3.py with this enhanced version
# This will allow split transactions to create new matches when they are the first entry for a deal