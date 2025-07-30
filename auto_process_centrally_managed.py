#!/usr/bin/env python3
"""
Enhancement to automatically process centrally managed CPI/FP deals
without flagging them as discrepancies.
"""

def enhanced_identify_centrally_processed_transactions(self):
    """
    Identify and auto-process CPI and FP Increase deals that are centrally processed.
    These are handled by SalesOps team and should not appear in HubSpot.
    """
    logger.info("Identifying and processing centrally managed transactions...")
    
    centrally_processed_count = 0
    remaining_transactions = []
    
    for transaction in self.salescookie_transactions:
        deal_name = transaction.get('deal_name', '').lower()
        
        # Check if this is a centrally processed deal
        # CPI Increase, FP Increase, and Fixed Price Increase deals are handled centrally
        if any(indicator in deal_name for indicator in ['cpi increase', 'fp increase', 'fixed price increase', 'indexation']):
            # Auto-process these transactions
            transaction['auto_processed'] = True
            transaction['processing_type'] = 'centrally_managed'
            transaction['processing_note'] = 'Processed by SalesOps team - not in HubSpot'
            
            self.centrally_processed_transactions.append(transaction)
            
            # Create an auto-match for reporting purposes
            auto_match = MatchResult(
                hubspot_id=f"CENTRAL_{transaction.get('salescookie_id', centrally_processed_count)}",
                salescookie_id=transaction.get('salescookie_id', ''),
                match_type='centrally_processed',
                confidence=100.0,
                hubspot_deal={
                    'hubspot_id': f"CENTRAL_{transaction.get('salescookie_id', centrally_processed_count)}",
                    'deal_name': transaction.get('deal_name'),
                    'close_date': transaction.get('close_date'),
                    'commission_amount': 0,  # No HubSpot amount
                    'company_name': transaction.get('company_name', ''),
                    'is_centrally_processed': True
                },
                salescookie_transactions=[transaction]
            )
            self.matches.append(auto_match)
            
            centrally_processed_count += 1
            logger.debug(f"Auto-processed centrally managed deal: {transaction.get('deal_name')}")
        else:
            remaining_transactions.append(transaction)
    
    # Update the transactions list to exclude centrally processed ones
    self.salescookie_transactions = remaining_transactions
    
    logger.info(f"Auto-processed {centrally_processed_count} centrally managed transactions")
    logger.info(f"Remaining transactions for matching: {len(remaining_transactions)}")


def enhanced_generate_result(self, data_quality_score: float) -> ReconciliationResult:
    """Generate result with proper centrally processed handling"""
    # Get base result
    result = self._generate_enhanced_result(data_quality_score)
    
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
    
    return result


# Implementation note:
# Replace the _identify_centrally_processed_transactions method in reconciliation_engine_v2.py
# This will auto-process CPI/FP deals and prevent them from being flagged as discrepancies