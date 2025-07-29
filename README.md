# Commission Reconciliation Tool

A comprehensive tool for reconciling HubSpot deals with SalesCookie commission data, designed to automate quarterly commission verification processes.

## 🚀 Quick Start

```bash
# Install dependencies
pip3 install pandas openpyxl click

# Run reconciliation
python3 reconcile_v2.py \
  --hubspot-file hubspot_export.csv \
  --salescookie-file salescookie_credits.csv
```

## 📋 Features

- ✅ **Multi-source data parsing**: HubSpot CSV exports and SalesCookie data (manual/scraped)
- 🎯 **Intelligent matching**: Multiple strategies with confidence scoring
- 💡 **CPI/Fix deal handling**: Automatic identification of centrally processed transactions
- 💰 **Commission validation**: Verification against configured commission plans
- 📊 **Comprehensive reporting**: Excel, CSV, and text summary outputs
- 🔍 **Data quality assessment**: Automatic detection and scoring of data issues
- 📅 **Multi-quarter support**: Process multiple quarters simultaneously

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Quick start guide for business users
- **[Complete Documentation](DOCUMENTATION.md)** - Full system documentation
- **[Technical Reference](TECHNICAL_REFERENCE.md)** - Developer documentation
- **[Test Guide](TEST_GUIDE.md)** - Testing documentation

## 🛠️ Installation

1. **Prerequisites**: Python 3.8+
2. **Clone repository**: `git clone [repository-url]`
3. **Install dependencies**: `pip3 install -r requirements.txt`

## 💻 Usage Examples

### Basic Reconciliation
```bash
python3 reconcile_v2.py \
  --hubspot-file hubspot_q3_2025.csv \
  --salescookie-file "credits q3-2025.csv"
```

### Multi-Quarter Analysis
```bash
python3 reconcile_all_quarters.py
```

### Data Quality Check
```bash
python3 reconcile_v2.py \
  --hubspot-file data.csv \
  --salescookie-file credits.csv \
  --quality-check
```

## 📊 Results

The tool generates:
- **Excel Report**: Multi-sheet workbook with summary, discrepancies, and all deals
- **Text Summary**: Human-readable overview with recommendations
- **CSV Export**: Detailed discrepancy data for further analysis

## 🏗️ Architecture

```
commission_reconciliation/
├── reconcile_v2.py              # Main CLI interface
├── hubspot_parser.py            # HubSpot data parser
├── salescookie_parser_v2.py     # Dual-mode parser
├── reconciliation_engine_v2.py  # Matching engine
├── report_generator.py          # Report generation
└── commission_config.py         # Rate configuration
```

## 🧪 Testing

```bash
python3 run_tests.py
```

## 📈 Performance

- Processes 2+ years of data in seconds
- 73.7% match rate across all quarters
- Handles 300+ transactions efficiently

## 🤝 Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Run tests before submitting

## 📝 License

Proprietary - Internal use only

---

*For detailed information, see the [complete documentation](DOCUMENTATION.md).*