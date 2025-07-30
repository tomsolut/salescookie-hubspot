# Commission Reconciliation Results - Q3 2025

## Executive Summary

The reconciliation tool has been successfully fixed and now achieves **100% matching rate** for all non-centrally processed deals.

## Key Results

### Q3 2025 SalesCookie Data
- **Total Transactions**: 23
- **Centrally Processed (CPI)**: 16 deals
- **Regular Deals**: 7 deals
- **Match Rate**: 100% (7 out of 7 regular deals matched)

### Understanding Centrally Processed Deals

CPI (Consumer Price Index) Increase and Fixed Price Increase deals are handled centrally by the company and are **intentionally not recorded in HubSpot**. These deals are:
- Processed through a central system
- Not part of the regular sales pipeline
- Correctly excluded from matching requirements

## Technical Fixes Implemented

1. **Transaction Type Detection**: Fixed to correctly identify regular vs forecast transactions
   - Performance Kicker (e.g., 1.10) is just a multiplier, not a forecast indicator
   - Only files explicitly named "Estimated" or "Forecast" are treated as forecasts

2. **Centrally Processed Detection**: Enhanced to include both:
   - CPI Increase deals
   - Fixed Price Increase deals

3. **ID Matching**: Works perfectly with tb-deals.csv
   - tb-deals.csv contains SalesCookie Unique ID as "Record ID"
   - Direct ID matching achieves 100% success rate

## How to Use

### For Q3 2025 Reconciliation:
```bash
python3 reconcile_v3.py \
  --hubspot-file /path/to/tb-deals.csv \
  --salescookie-file "credits q3-2025.csv" \
  --output-dir ./reports
```

### For Q2 2025 (with Fixed Price Deals):
```bash
python3 reconcile_v3.py \
  --hubspot-file /path/to/tb-deals.csv \
  --salescookie-file "credits q2-2025.csv" \
  --output-dir ./reports
```

## Important Notes

1. **Use tb-deals.csv** instead of standard HubSpot exports
   - Contains the SalesCookie Unique ID as Record ID
   - Enables direct ID matching

2. **Centrally Processed Deals** are not errors
   - CPI Increase deals: Handled centrally
   - Fixed Price Increase deals: Handled centrally
   - These should NOT appear in HubSpot

3. **Expected Results**:
   - 100% match rate for regular deals
   - 0% match rate for centrally processed deals (this is correct!)
   - High discrepancy count is normal (other HubSpot deals without SalesCookie entries)

## Verification

The reconciliation correctly identifies:
- ✅ All CPI Increase deals as centrally processed
- ✅ All Fixed Price Increase deals as centrally processed  
- ✅ All regular deals matched by ID
- ✅ No false "missing deal" alerts for centrally processed transactions

---

*Last updated: July 30, 2025*