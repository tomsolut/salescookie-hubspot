# Commission Reconciliation Tool v3.0

A comprehensive tool for reconciling HubSpot deals with SalesCookie commission data, designed to automate quarterly commission verification processes.

## 🚀 Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Combine all SalesCookie files
python combine_salescookie_files.py

# Run reconciliation
python reconcile_v3.py \
  --hubspot-file ../salescookie_manual/tb-deals.csv \
  --salescookie-file all_salescookie_credits.csv \
  --output-dir reports_v3
```

## 📋 Features

### Core Capabilities
- ✅ **Multi-source data parsing**: HubSpot CSV exports and SalesCookie data (manual/scraped)
- 🎯 **Intelligent matching**: Multiple strategies with confidence scoring
- 💰 **Commission validation**: Uses SalesCookie rates as source of truth
- 📊 **Comprehensive reporting**: Excel with discrepancy percentages, CSV, and text summaries

### v3.0 Enhancements
- 💳 **Withholding transactions**: Handles 50% paid/50% withheld CPI increases
- 📈 **Forecast transactions**: Supports future quarter projections with kickers
- 🔄 **Split deal recognition**: Properly handles deals split across quarters
- 💡 **FP/CPI deal handling**: Identifies centrally processed transactions (308 total)
- 📊 **Discrepancy percentage**: New column showing variance percentages with color coding

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Quick start guide for business users
- **[Complete Documentation](DOCUMENTATION.md)** - Full system documentation
- **[Technical Reference](TECHNICAL_REFERENCE.md)** - Developer documentation
- **[FP/CPI Analysis](ANALYSIS_FP_CPI_DEALS.md)** - Centrally processed deals analysis

## 🛠️ Installation

1. **Prerequisites**: Python 3.8+
2. **Clone repository**: `git clone [repository-url]`
3. **Create virtual environment**: 
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. **Install dependencies**: `pip install -r requirements.txt`

## 💻 Usage Examples

### Combine SalesCookie Files
```bash
# Combines all CSV files including withholdings and splits
python combine_salescookie_files.py
```

### Basic Reconciliation (v3)
```bash
python reconcile_v3.py \
  --hubspot-file ../salescookie_manual/tb-deals.csv \
  --salescookie-file all_salescookie_credits.csv \
  --output-dir reports_v3
```

### Legacy Version (v2)
```bash
python reconcile_v2.py \
  --hubspot-file hubspot_export.csv \
  --salescookie-file salescookie_credits.csv
```

## 📊 Current Results (July 2025)

- **Total SalesCookie transactions**: 580
  - Regular: 130
  - Withholding: 135 (€32,917 withheld)
  - Forecast: 86
  - Split: 229
- **Centrally processed**: 308 (FP/CPI increases)
- **Match rate**: 59.5% (113 matched deals)
- **Discrepancies**: 99 (€311,745 impact)

## 🏗️ Architecture

```
commission_reconciliation/
├── reconcile_v3.py              # Main CLI interface (enhanced)
├── combine_salescookie_files.py # Merges all SalesCookie CSVs
├── hubspot_parser.py            # HubSpot data parser
├── salescookie_parser_v2.py     # Enhanced parser with transaction types
├── reconciliation_engine_v3.py  # Advanced matching with withholding/forecast
├── report_generator_v3.py       # Enhanced reports with discrepancy %
└── commission_config.py         # Rate configuration (deprecated)
```

## 📈 Key Improvements

### Commission Calculation
- Now uses SalesCookie's own commission rates as source of truth
- No longer relies on pre-configured rates in commission_config.py
- Validates: SalesCookie ACV × SalesCookie Rate = SalesCookie Commission

### Transaction Types
- **Regular**: Standard commission transactions
- **Withholding**: 50% paid immediately, 50% withheld (CPI increases)
- **Forecast**: Future quarter projections with kicker calculations
- **Split**: Deals divided across multiple quarters

### Centrally Processed Deals
Automatically identifies and excludes from matching:
- CPI Increase deals
- FP Increase deals  
- Fixed Price Increase deals
- Indexation deals

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Run specific test suites
python -m pytest tests/test_reconciliation_suite.py
```

## 🐛 Known Issues

1. **HubSpot data quality**: 32 FP/CPI deals exist in HubSpot but shouldn't (centrally managed)
2. **Match rate**: Lower match rate due to withholding/forecast transactions for future quarters
3. **Data format**: Some SalesCookie exports have inconsistent formats

## 🤝 Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Run tests before submitting
5. Use virtual environment

## 📝 Version History

- **v3.0** (July 2025): Withholding/forecast support, discrepancy percentages
- **v2.0** (June 2025): Enhanced matching, data quality assessment
- **v1.0** (May 2025): Initial release

## 📝 License

Proprietary - Internal use only

---

*For detailed information, see the [complete documentation](DOCUMENTATION.md).*