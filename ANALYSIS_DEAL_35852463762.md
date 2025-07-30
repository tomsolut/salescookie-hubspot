# Analysis: Deal 35852463762 - A360B @ KfW (Extension Bi-Direktionaler Adapter)

## Issue Summary
Deal 35852463762 exists in both HubSpot and SalesCookie but is showing as a "missing_deal" discrepancy.

## Data Presence

### HubSpot
- ✅ **Deal exists**: A360B @ KfW (Extension Bi-Direktionaler Adapter)
- **Amount**: €93,139
- **Status**: Closed Won
- **Close Date**: 2025-06-30

### SalesCookie (all_salescookie_credits.csv)
The deal appears **5 times** with different transaction types:

1. **Line 495**: Split transaction from credits q2-2025.csv
   - Type: `split`
   - Commission: €3,446.14
   - Quarter: q2-2025

2. **Lines 496, 498, 499**: Withholding transactions 
   - Type: `withholding`
   - From: q1, q2, q3 2025 withholding files
   - Amount: €6,892.29 each (50% withheld)

3. **Line 497**: Forecast transaction
   - Type: `forecast`
   - From: Estimated credits 2025.csv
   - Amount: €6,892.29

## Root Cause

The reconciliation engine categorizes transactions by type BEFORE matching:

```python
def _categorize_transactions(self):
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
```

The matching process then works in phases:
1. **Phase 1-3**: Match `regular_transactions` only
2. **Phase 4**: Match `withholding_transactions` 
3. **Phase 5**: Match `split_transactions`
4. **Phase 6**: Analyze `forecast_transactions`

## Why It's Not Matching

1. The q2-2025 entry is categorized as a **split** transaction
2. During Phase 1-3, only **regular** transactions are considered for matching
3. During Phase 5 (split matching), the code looks for EXISTING matches to append to:
   ```python
   for match in self.matches:
       if (split_transaction.get('deal_name') == match.hubspot_deal.get('deal_name') or
           split_transaction.get('salescookie_id') == match.hubspot_deal.get('hubspot_id')):
   ```
4. Since no regular transaction created a match in Phase 1-3, there's no match to append to
5. The deal is incorrectly reported as "missing" from SalesCookie

## The Real Issue

This is a **split deal** that represents the FIRST occurrence in SalesCookie. Split deals typically have:
- An initial transaction in one quarter
- Split portions in subsequent quarters

In this case, the q2-2025 split transaction appears to be the FIRST entry, but it's marked as split=Yes, preventing it from being matched as a regular deal.

## Solution Options

1. **Update matching logic**: Allow split transactions to create new matches, not just append to existing ones
2. **Data correction**: If this is actually the primary transaction, it shouldn't be marked as split=Yes
3. **Enhanced matching**: Match split transactions against HubSpot deals directly in Phase 5

## Impact

This affects any deal where:
- The first SalesCookie entry is marked as a split transaction
- There's no preceding regular transaction to create the initial match
- Multiple transaction types exist for the same deal

## Recommendation

The reconciliation engine should be updated to handle split transactions that don't have a preceding regular match. This is likely affecting other deals with similar patterns.