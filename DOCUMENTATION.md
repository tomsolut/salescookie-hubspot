# Commission Reconciliation Tool v3.0 - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Usage Guide](#usage-guide)
5. [Data Formats](#data-formats)
6. [Business Logic](#business-logic)
7. [Technical Architecture](#technical-architecture)
8. [Transaction Types](#transaction-types)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Overview

The Commission Reconciliation Tool automates the quarterly process of verifying that all "Closed & Won" deals in HubSpot are properly recorded in SalesCookie with correct commission calculations.

### Key Benefits

- **Time Savings**: Reduces manual reconciliation from hours to minutes
- **Accuracy**: Automated calculation verification using SalesCookie rates
- **Visibility**: Comprehensive reports with discrepancy percentages
- **Flexibility**: Supports multiple transaction types and data sources

### v3.0 Features

- Multi-source data parsing (HubSpot CSV, SalesCookie manual/scraped)
- Intelligent deal matching with confidence scoring
- Automatic handling of centrally processed deals (FP/CPI)
- Support for withholding, forecast, and split transactions
- Discrepancy percentage calculations with color coding
- Enhanced reporting with transaction type breakdowns

## Quick Start

### 1. Combine SalesCookie Files

```bash
# First, combine all SalesCookie CSV files
python combine_salescookie_files.py
```

This will merge:
- Regular credit files (q1-q4 for each year)
- Withholding files (50% paid/50% withheld)
- Split credit files (deals across quarters)
- Forecast/estimated files

### 2. Run Reconciliation

```bash
# Use v3 for enhanced features
python reconcile_v3.py \
  --hubspot-file ../salescookie_manual/tb-deals.csv \
  --salescookie-file all_salescookie_credits.csv \
  --output-dir reports_v3
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Clone the repository
git clone [repository-url]
cd commission_reconciliation

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Dependencies

- `pandas>=1.5.0` - Data manipulation
- `openpyxl>=3.0.0` - Excel file generation
- `click>=8.0.0` - Command-line interface

## Usage Guide

### Command Line Options

#### reconcile_v3.py

```bash
python reconcile_v3.py [OPTIONS]

Options:
  --hubspot-file PATH      Path to HubSpot CSV export file [required]
  --salescookie-file PATH  Path to combined SalesCookie CSV file [required]
  --output-dir PATH        Directory for output reports (default: ./reports_v3)
  --verbose               Enable verbose logging
  --help                  Show this message and exit
```

#### combine_salescookie_files.py

```bash
python combine_salescookie_files.py

# Automatically processes all files in ../salescookie_manual/
# Creates: all_salescookie_credits.csv
```

### Output Files

1. **Excel Report** (`commission_reconciliation_YYYYMMDD_HHMMSS.xlsx`)
   - Summary sheet with overall statistics
   - Discrepancies sheet with percentage column
   - Matched deals sheet with commission details

2. **Text Summary** (`reconciliation_summary_YYYYMMDD_HHMMSS.txt`)
   - High-level overview
   - Transaction type breakdown
   - Top discrepancies
   - Recommendations

3. **CSV Export** (`discrepancies_YYYYMMDD_HHMMSS.csv`)
   - Detailed discrepancy data for analysis

## Data Formats

### HubSpot Export Format

Required columns:
- `Deal ID` - Unique identifier
- `Deal Name` - Full deal name
- `Close Date` - When deal was closed
- `Amount in company currency` - Deal value in EUR
- `Deal Stage` - Must be "Closed Won"

### SalesCookie Format

The tool handles multiple formats:

#### Regular Credits
- `Unique ID` - Maps to HubSpot Deal ID
- `Deal Name` - Deal description
- `Commission` - Commission amount
- `Commission Rate` - Percentage rate
- `ACV (EUR)` - Annual contract value

#### Withholding Transactions
- `Commission` - 50% paid amount
- `Est. Commission` - 100% full amount
- `Withheld_Amount` - Calculated 50% withheld

#### Split Transactions
- `Split` - "Yes" indicator
- Deals divided across multiple quarters

## Business Logic

### Commission Validation

**v3.0 Change**: The system now uses SalesCookie's own commission rates as the source of truth:

```
Expected Commission = SalesCookie ACV × SalesCookie Rate
```

No longer uses pre-configured rates from commission_config.py.

### Centrally Processed Deals

The following deal types are handled centrally and excluded from matching:
- **CPI Increase** - Consumer Price Index adjustments
- **FP Increase** - Fixed Price increases
- **Fixed Price Increase** - Alternative naming
- **Indexation** - General price indexation

Total identified: **308 transactions** (as of July 2025)

### Matching Algorithm

1. **Phase 0**: Identify and exclude centrally processed transactions
2. **Phase 1**: Match by unique ID (100% confidence)
3. **Phase 2**: Match by name and date (85% confidence)
4. **Phase 3**: Match by company and date (70% confidence)
5. **Phase 4**: Match withholding transactions
6. **Phase 5**: Match split transactions
7. **Phase 6**: Analyze forecast transactions

### Discrepancy Types

- **missing_deal**: Deal in HubSpot but not in SalesCookie
- **calculation_error**: Commission amount doesn't match expected
- **wrong_rate**: Applied rate differs from expected
- **data_quality**: Issues with data format or completeness

### Discrepancy Percentage

New in v3.0 - Color-coded percentages:
- 🔴 **Red**: >50% variance
- 🟠 **Orange**: 20-50% variance  
- ⚫ **Black**: ≤20% variance

## Technical Architecture

### Core Components

```
commission_reconciliation/
│
├── Entry Points
│   ├── reconcile_v3.py          # Main CLI with enhanced features
│   └── combine_salescookie_files.py # File merger utility
│
├── Data Parsers
│   ├── hubspot_parser.py        # HubSpot CSV parser
│   └── salescookie_parser_v2.py # Enhanced multi-format parser
│
├── Processing Engine
│   ├── reconciliation_engine_v3.py # Advanced matching logic
│   └── reconciliation_engine_v2.py # Base engine (inherited)
│
├── Report Generation
│   ├── report_generator_v3.py   # Enhanced reports with %
│   └── report_generator.py      # Base report generator
│
└── Configuration
    └── commission_config.py     # Rate config (deprecated)
```

### Data Flow

1. **Input**: HubSpot and SalesCookie CSV files
2. **Parsing**: Extract and normalize data
3. **Combination**: Merge all SalesCookie sources
4. **Processing**: Match deals and validate commissions
5. **Analysis**: Calculate discrepancies and percentages
6. **Output**: Generate multi-format reports

## Transaction Types

### Regular Transactions
- Standard commission entries
- Direct ACV × Rate calculation
- Most common type (~130 transactions)

### Withholding Transactions
- CPI increases with 50/50 split
- Shows both paid and withheld amounts
- ~135 transactions with €32,917 withheld

### Forecast Transactions
- Future quarter projections
- May include kicker calculations
- ~86 transactions for planning

### Split Transactions
- Deals divided across quarters
- Requires special validation logic
- ~229 transactions identified

## Troubleshooting

### Common Issues

1. **Low Match Rate**
   - Check if withholding/forecast transactions are for future quarters
   - Verify HubSpot Deal IDs are complete
   - Review data quality score in output

2. **#VALUE! Errors in Excel**
   - Fixed in v3.0 - percentages now calculate correctly
   - Ensure using latest report_generator_v3.py

3. **Missing Transactions**
   - Run combine_salescookie_files.py to include all sources
   - Check for new file formats in salescookie_manual/

4. **FP/CPI Deals Showing as Missing**
   - These are centrally processed - not an error
   - Consider removing from HubSpot export

### Data Quality Indicators

- **Quality Score**: 70/100 or higher is good
- **Centrally Processed**: Should be 300+ transactions
- **Match Rate**: Expected 60-80% with all transaction types

## Best Practices

### Data Preparation

1. **HubSpot Export**
   - Filter for Closed Won deals only
   - Include all required columns
   - Export in CSV format

2. **SalesCookie Files**
   - Place all files in salescookie_manual/
   - Don't modify file names
   - Run combine script before reconciliation

### Regular Workflow

1. Export fresh data from both systems
2. Run combine_salescookie_files.py
3. Run reconciliation with v3
4. Review discrepancy report
5. Focus on high-impact discrepancies (>€1000)
6. Check discrepancy percentages for patterns

### Maintenance

- Keep virtual environment updated
- Monitor for new transaction types
- Document any manual adjustments
- Archive reports quarterly

---

*Last updated: July 2025 - Version 3.0*