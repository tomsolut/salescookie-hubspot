# Commission Reconciliation Tool - User Guide

## 🚀 Quick Start Guide

This guide will help you get started with the Commission Reconciliation Tool in just a few minutes.

### What This Tool Does

The Commission Reconciliation Tool helps you:
- ✅ Verify all HubSpot deals are in SalesCookie
- 💰 Check commission calculations are correct
- 📊 Identify discrepancies quickly
- 📈 Generate comprehensive reports

### 5-Minute Setup

1. **Install Python dependencies**
   ```bash
   pip3 install pandas openpyxl click
   ```

2. **Prepare your data files**
   - Export HubSpot deals (CSV format)
   - Download SalesCookie credits (manual export recommended)

3. **Run your first reconciliation**
   ```bash
   python3 reconcile_v2.py \
     --hubspot-file your_hubspot_export.csv \
     --salescookie-file your_salescookie_credits.csv
   ```

4. **Check the reports**
   - Look in the `./reports` folder
   - Open the Excel file for detailed analysis

## 📋 Step-by-Step Workflow

### Step 1: Export HubSpot Data

1. Go to HubSpot > Reports > Deals
2. Filter for "Closed & Won" deals
3. Select the time period you want
4. Export as CSV with these columns:
   - Record ID
   - Deal Name
   - Deal Stage
   - Amount in company currency
   - Close Date
   - All other standard fields

### Step 2: Export SalesCookie Data

**Option A: Manual Export (Recommended)**
1. Log into SalesCookie
2. Go to Credits section
3. Select the quarter
4. Export as CSV

**Option B: Use Scraped Data**
- Place scraped files in a directory
- Use `--salescookie-dir` option

### Step 3: Run Reconciliation

**Basic reconciliation:**
```bash
python3 reconcile_v2.py \
  --hubspot-file hubspot_deals.csv \
  --salescookie-file credits_q3_2025.csv
```

**With custom output directory:**
```bash
python3 reconcile_v2.py \
  --hubspot-file hubspot_deals.csv \
  --salescookie-file credits_q3_2025.csv \
  --output-dir ./q3_2025_reports
```

### Step 4: Review Results

The tool generates three types of reports:

1. **Excel Report** (`commission_reconciliation_*.xlsx`)
   - Summary sheet: Overall statistics
   - Discrepancies sheet: All issues found
   - All Deals sheet: Complete deal list

2. **Text Summary** (`reconciliation_summary_*.txt`)
   - Quick overview of findings
   - Top discrepancies
   - Recommendations

3. **CSV Export** (`discrepancies_*.csv`)
   - All discrepancies in CSV format
   - Easy to import into other tools

## 📊 Understanding the Results

### Match Statistics

```
✓ Matched 185 deals
ℹ️ Centrally Processed (CPI/Fix): 16 transactions
⚠️ Discrepancies: 66
💸 Total impact: €32,978.76
```

- **Matched deals**: Successfully found in both systems
- **Centrally Processed**: CPI/Fix deals handled separately
- **Discrepancies**: Issues requiring attention
- **Total impact**: Financial impact of discrepancies

### Common Discrepancy Types

1. **Missing Deal**
   - Deal in HubSpot but not in SalesCookie
   - Check if deal is eligible for commission
   - May need manual processing

2. **Wrong Commission Amount**
   - Deal found but commission differs
   - Often due to quarter splits
   - Verify commission rates and calculations

### Interpreting Match Confidence

- **100% (ID Match)**: Perfect match using Record ID
- **95% (Name+Date)**: Very likely match
- **80% (Company+Date)**: Good match, verify manually

## 🎯 Common Use Cases

### Quarterly Commission Verification

```bash
# Q3 2025 verification
python3 reconcile_v2.py \
  --hubspot-file hubspot_q3_2025.csv \
  --salescookie-file "credits q3-2025.csv" \
  --output-dir ./reports/q3_2025
```

### Year-End Reconciliation

```bash
# Analyze all quarters
python3 analyze_all_quarters.py

# Run comprehensive reconciliation
python3 reconcile_all_quarters.py
```

### Data Quality Check

```bash
# Check data quality without full reconciliation
python3 reconcile_v2.py \
  --hubspot-file hubspot.csv \
  --salescookie-file credits.csv \
  --quality-check
```

## ⚡ Tips & Tricks

### 1. Improve Match Rates

- Use manual SalesCookie exports (better data quality)
- Ensure date ranges match between systems
- Check for CPI/Fix deals (handled separately)

### 2. Handle Large Datasets

```bash
# Use verbose mode for progress updates
python3 reconcile_v2.py --verbose \
  --hubspot-file large_dataset.csv \
  --salescookie-file credits.csv
```

### 3. Debug Issues

```bash
# Enable detailed logging
python3 reconcile_v2.py --verbose \
  --hubspot-file data.csv \
  --salescookie-file credits.csv \
  --output-dir ./debug_output
```

## ❓ FAQ

### Q: Why is my match rate low?

**A:** Common reasons:
- Time period mismatch between exports
- Many CPI/Fix deals (centrally processed)
- Incomplete data export
- Using scraped data (lower quality)

### Q: What are CPI/Fix deals?

**A:** These are inflation adjustment deals processed centrally:
- CPI Increase
- Fix Increase
- Indexation deals

They appear in SalesCookie but not HubSpot.

### Q: Why do some PS deals show 50% commission?

**A:** Professional Services deals may have quarter splits:
- 50% in close quarter
- 50% in service start quarter

### Q: How often should I run reconciliation?

**A:** Recommended schedule:
- Monthly: Quick check for current quarter
- Quarterly: Full reconciliation after quarter close
- Annually: Comprehensive year-end review

### Q: What's the difference between manual and scraped data?

**Manual exports:**
- 100% data quality
- Complete deal names
- Correct ID format
- All fields included

**Scraped data:**
- May have truncated names
- Different ID format
- Missing fields
- Lower match rates

## 🛠️ Troubleshooting

### "No module named 'pandas'"

```bash
# Install required packages
pip3 install pandas openpyxl click
```

### "File not found"

- Check file paths are correct
- Use quotes for paths with spaces
- Use absolute paths if needed

### Low data quality score

- Use manual exports instead of scraped data
- Check for truncated deal names
- Verify all required columns present

### Commission discrepancies

- Check commission rate year (2024 vs 2025)
- Verify PS deal identification
- Review quarter split logic

## 📞 Getting Help

1. **Check the logs**: Use `--verbose` flag
2. **Review documentation**: See DOCUMENTATION.md
3. **Run tests**: `python3 run_tests.py`
4. **Check examples**: See test files for examples

---

*Happy reconciling! 🎉*