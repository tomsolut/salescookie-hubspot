# Commission Reconciliation Tool - Version 3 Enhancements

## Overview

Version 3 of the Commission Reconciliation Tool adds comprehensive support for advanced SalesCookie transaction types, including withholdings, forecasts, and split credits. The tool now correctly handles centrally processed deals and achieves 100% matching accuracy for regular transactions.

## New Features

### 1. Transaction Type Classification

The tool now automatically detects and classifies four types of transactions:

- **Regular**: Standard commission transactions
- **Withholding**: Partial commission payments (typically 50%)
- **Forecast**: Estimated future commissions with kickers
- **Split**: Cross-year/quarter commission splits

### 2. Enhanced Parser (SalesCookieParserV2)

```python
class TransactionType(Enum):
    REGULAR = "regular"
    WITHHOLDING = "withholding"
    FORECAST = "forecast"
    SPLIT = "split"
```

- Automatic detection based on filename patterns and content
- Support for new fields:
  - `est_commission`, `est_commission_currency`, `est_commission_rate`
  - `early_bird_kicker`, `performance_kicker`, `campaign_kicker`
  - `withholding_ratio` (calculated automatically)

### 3. Enhanced Reconciliation Engine (ReconciliationEngineV3)

- Separate processing pipelines for different transaction types
- Withholding validation (ensures 50% standard rate)
- Forecast analysis with kicker summaries
- Split transaction tracking across fiscal boundaries

### 4. Enhanced Reports (ReportGeneratorV2)

New report sections:
- **Withholding Analysis**: Shows paid vs. withheld amounts
- **Forecast Analysis**: Future commission projections with kickers
- **Enhanced Summary**: Transaction type breakdown

### 5. Enhanced CLI (reconcile_v3.py)

New command-line flags:
- `--include-withholdings`: Process withholding transactions
- `--include-forecasts`: Process forecast/estimated transactions
- `--include-splits`: Process split credit transactions
- `--all-types`: Process all transaction types

## Usage Examples

### Basic Q3 2025 Reconciliation
```bash
python3 reconcile_v3.py \
  --hubspot-file hubspot_export.csv \
  --salescookie-file "credits q3-2025.csv"
```

### Include Withholdings
```bash
python3 reconcile_v3.py \
  --hubspot-file hubspot_export.csv \
  --salescookie-dir ./salescookie_manual \
  --include-withholdings
```

### Process All Transaction Types
```bash
python3 reconcile_v3.py \
  --hubspot-file hubspot_export.csv \
  --salescookie-dir ./salescookie_manual \
  --all-types \
  --output-dir ./comprehensive_reports
```

## Data Quality Improvements

- Enhanced detection of data source (manual vs. scraped)
- Quality scoring with detailed warnings
- Support for multiple file formats and encodings

## Key Benefits

1. **Complete Commission Visibility**: Track commissions from forecast to final payment
2. **Withholding Management**: Understand partial payments and future receivables
3. **Forecast Accuracy**: Compare estimated vs. actual commissions
4. **Cross-Period Tracking**: Handle deals that span multiple quarters/years

## Technical Details

### Withholding Calculation
```python
if transaction_type == TransactionType.WITHHOLDING:
    withholding_ratio = commission_amount / est_commission
    # Typically 0.5 (50%)
```

### Forecast Kickers
- Early Bird Kicker: Bonus for early closure
- Performance Kicker: Achievement-based bonus
- Campaign Kicker: Special promotion bonus

## Important Notes

### Centrally Processed Deals

CPI (Consumer Price Index) Increase and Fixed Price Increase deals are handled centrally and do not appear in HubSpot. This is by design:

- **CPI Increase deals**: Automatic price adjustments based on inflation
- **Fixed Price Increase deals**: Negotiated price increases outside regular sales process
- These are correctly excluded from matching and marked as "centrally processed"

### Using the Correct HubSpot Export

For optimal results, use `tb-deals.csv` export format which includes:
- SalesCookie Unique ID as "Record ID"
- Enables direct ID matching with 100% accuracy
- Standard HubSpot exports lack this critical field

## Performance Results

- **Q3 2025**: 100% match rate (7/7 regular deals matched, 16 CPI deals correctly excluded)
- **Q2 2025**: 100% match rate (10/10 regular deals matched, 30 Fixed Price deals correctly excluded)
- **Transaction type detection**: Fixed to correctly identify regular vs forecast transactions
- **Centrally processed detection**: Enhanced to include both CPI and Fixed Price Increase deals

## Future Enhancements

1. Automated scraper optimization based on data quality analysis
2. Machine learning for improved matching algorithms
3. Real-time integration with SalesCookie API
4. Dashboard visualization of commission trends
5. Automatic detection of new centrally processed deal types

---

*Version 3.0 - Released July 2025*