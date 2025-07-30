# Analysis: FP Increase and CPI Increase Deals

## Summary
Based on the documentation provided, **FP Increase and CPI Increase deals are centrally managed and processed**, meaning they should NOT appear in HubSpot. However, the reconciliation found significant discrepancies.

## Current Situation

### SalesCookie Data
- **308 centrally processed transactions** identified correctly
- These include deals with names containing:
  - "CPI Increase"
  - "FP Increase" 
  - "Fixed Price Increase"
  - "Indexation"

### HubSpot Data  
- **32 FP/CPI deals found in HubSpot** that shouldn't be there
- Total value: **€311,067.84**
- These are being reported as "missing_deal" discrepancies

## Key Findings

1. **System correctly identifies centrally processed deals** in SalesCookie
   - Updated detection logic now includes "fp increase" pattern
   - 308 transactions properly categorized as centrally processed

2. **HubSpot contains deals that shouldn't exist**
   - 25 FP Increase deals (2024-2025)
   - 7 CPI Increase deals
   - These are centrally managed and should not be in HubSpot CRM

3. **Impact on reconciliation**
   - These deals inflate HubSpot's deal count
   - They appear as "missing" because SalesCookie correctly excludes them from matching
   - Total discrepancy impact from these deals: ~€280,000

## Recommendations

1. **Remove FP/CPI deals from HubSpot**
   - These 32 deals should be deleted or marked differently in HubSpot
   - They are handled through a central process, not through sales

2. **Update HubSpot export filters**
   - Exclude deals with names containing "FP Increase", "CPI Increase", etc.
   - Or add a custom field to mark centrally processed deals

3. **Reconciliation logic is correct**
   - The system properly identifies and excludes these from matching
   - No changes needed to the reconciliation engine

## Technical Implementation
The reconciliation engine now correctly identifies centrally processed deals using:
```python
if any(indicator in deal_name for indicator in ['cpi increase', 'fp increase', 'fixed price increase', 'indexation']):
    # Mark as centrally processed
```

This ensures these deals are excluded from the matching process as they are managed outside the normal sales commission workflow.