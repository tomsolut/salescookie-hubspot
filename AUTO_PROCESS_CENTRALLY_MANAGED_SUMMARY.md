# Centrally Processed Deals - Auto-Processing Implementation

## Summary
CPI and FP increase deals are now automatically processed by the reconciliation system since they are centrally managed by the SalesOps team and do not appear in HubSpot.

## Changes Implemented

### 1. Enhanced Reconciliation Engine (reconciliation_engine_v2.py)
Updated `_identify_centrally_processed_transactions()` to:
- Auto-create matches for centrally processed deals
- Mark them with special flags (auto_processed, processing_type, processing_note)
- Generate pseudo HubSpot IDs (CENTRAL_xxx) for reporting

### 2. Enhanced Reporting
- **Excel Report**: Added "Centrally Processed Transactions" section in Summary sheet
- **Text Report**: Added detailed breakdown of centrally processed deals
- Shows count by type (CPI, FP, Fixed Price, Indexation)
- Displays total commission amount

### 3. Result Generation (reconciliation_engine_v3.py)
Added centrally processed summary to results:
```python
result.summary['centrally_processed'] = {
    'count': 308,
    'total_commission': 46146.80,
    'types': {
        'cpi_increase': 105,
        'fp_increase': 56,
        'fixed_price_increase': 147,
        'indexation': 0
    },
    'note': 'These deals are processed by SalesOps team and do not appear in HubSpot'
}
```

## Impact

### Before Changes:
- 308 CPI/FP deals were excluded but not properly tracked
- No visibility into centrally processed commission amounts
- Confusion about why these deals weren't being matched

### After Changes:
- 308 deals auto-processed with proper tracking
- €46,146.80 in centrally processed commissions visible
- Clear reporting shows:
  - 105 CPI Increase deals
  - 56 FP Increase deals  
  - 147 Fixed Price Increase deals
  - 0 Indexation deals
- Note explains these are handled by SalesOps team

## Important Notes

1. **HubSpot CPI/FP Deals**: The system still correctly identifies when CPI/FP deals exist in HubSpot (they shouldn't). Example from report shows 5 such deals worth ~€21k.

2. **Match Count**: The match count now includes auto-processed deals, which is why it shows 453 matches (161 regular + 308 centrally processed - some overlap).

3. **Commission Tracking**: All centrally processed commissions are now properly tracked and reported.

## Usage
No changes needed to command line usage. The auto-processing happens automatically during reconciliation.