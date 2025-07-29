# Commission Reconciliation Tool

Automated reconciliation tool for validating HubSpot deals against SalesCookie commission data.

## Features

- **Automated Matching**: Matches HubSpot Closed & Won deals with SalesCookie transactions
- **Commission Validation**: Verifies commission calculations based on your commission plans
- **Quarter Split Validation**: Checks 50/50 split between closing and service start quarters
- **PS Deal Handling**: Correctly applies 1% flat rate for Professional Services deals
- **Currency Conversion**: Validates company currency amounts for international deals
- **Comprehensive Reporting**: Excel, text summary, and CSV discrepancy reports

## Installation

```bash
# Navigate to the project directory
cd /Users/thomasbieth/hubspot_salescookie/commission_reconciliation

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python reconcile.py \
  --hubspot-file ../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv \
  --salescookie-dir ../sales_cookie_all_plans_20250729 \
  --output-dir ./reports
```

### Command Options

- `--hubspot-file`: Path to HubSpot CSV export (required)
- `--salescookie-dir`: Path to SalesCookie data directory (required)
- `--output-dir`: Directory for output reports (default: ./reports)
- `--verbose`: Enable detailed logging

## Commission Rules

Based on your commission plans:

### 2024 Commission Rates
- **Software**: 7.3%
- **Managed Services (Public Cloud)**: 5.9%
- **Managed Services (Private Cloud)**: 4.4%
- **Recurring Professional Services**: 2.9%
- **Indexations/Parameter**: 4.4%
- **Professional Services (PS)**: 1.0% flat rate

### 2025 Commission Rates
- **Software**: 7.0%
- **Managed Services (Public/Private Cloud)**: 7.4%
- **Recurring Professional Services**: 7.4%
- **Indexations/Parameter**: 4.4%
- **Professional Services (PS)**: 1.0% flat rate

### Quarter Split Rules
- 50% commission in closing quarter
- 50% commission in service start quarter
- If no service start date, 100% in closing quarter

## Output Reports

### 1. Excel Report
Comprehensive workbook with:
- **Summary**: Overall statistics and discrepancy breakdown
- **Discrepancies**: Detailed list of all issues found
- **Matched Deals**: Successfully matched deals between systems

### 2. Text Summary
Quick overview with:
- Overall statistics
- Discrepancy counts by type
- High severity issues
- Actionable recommendations

### 3. Discrepancy CSV
Machine-readable format for further analysis or integration

## Common Discrepancy Types

- **missing_deal**: HubSpot deal not found in SalesCookie
- **wrong_commission_amount**: Commission calculation doesn't match expected rate
- **missing_quarter_split**: Expected quarter allocation not found
- **missing_currency_conversion**: International deal missing EUR conversion

## Automation Tips

1. **Schedule quarterly runs**: Add to cron for automatic execution after quarter close
2. **Email notifications**: Pipe output or parse reports for email alerts
3. **Integration**: Use CSV output for integration with other systems

## Troubleshooting

- Ensure HubSpot export includes all required columns
- Verify SalesCookie directory structure matches expected format
- Check that all CSV files are properly encoded (UTF-8)

## Future Enhancements

- Direct HubSpot API integration
- Real-time monitoring dashboard
- Automated discrepancy resolution suggestions
- Historical trend analysis