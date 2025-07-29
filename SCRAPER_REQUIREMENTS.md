# SalesCookie Scraper Requirements & Specifications

## Overview

This document provides detailed requirements for the SalesCookie scraper to ensure data quality matches manual exports.

## Current Issues with Scraped Data

Based on analysis comparing scraped vs. manual exports:

1. **Truncated Deal Names**: Deal names are cut off with "..." (e.g., "FP Increase@Aktia Bank ...")
2. **Missing/Incorrect Unique IDs**: HubSpot Deal IDs not properly captured
3. **Data Format Issues**: Different CSV structure than manual exports
4. **Poor Data Quality**: Average quality score <50% vs. 100% for manual exports

## Required CSV Format

The scraper must produce CSV files matching the exact format of manual SalesCookie exports:

### Required Columns (in order)

```csv
ACV (EUR),Performance Kicker,Split,Commission,Commission Currency,Commission Rate,Commission Details,Close Date,Revenue Start Date,Professional Services Start Date,Deal Type,Unique ID,ACV Sales (Managed Services),ACV Sales (Professional Services) ,ACV Sales (Software),TCV (Professional Services),Currency,Create Date,Customer,Deal owner - Email,Deal owner - Name,Deal Stage,Is Closed Won,Deal Name,Imported Date,Edited Date,Added By,Types of ACV,Product Name
```

### Critical Fields

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| **Unique ID** | Numeric string | `270402053362` | Must match HubSpot Record ID exactly |
| **Deal Name** | Full text, no truncation | `PS @ Tieto (Additional PS Support Rcloud 54 MD - 88.560 EUR)` | Complete name required |
| **Customer** | `ID; Company Name` | `100556; Kreditanstalt für Wiederaufbau` | Semicolon separator |
| **Close Date** | `YYYY-MM-DD HH:MM:SS` | `2025-07-24 14:09:22` | ISO format |
| **Commission** | Numeric | `885.60` | No currency symbols |
| **Commission Currency** | ISO code | `EUR` | Three-letter code |
| **Commission Rate** | Percentage | `7.40%` | Include % symbol |

## Scraper Implementation Requirements

### 1. Field Width Handling
```python
# DO NOT truncate fields
# Set maximum field width to at least 500 characters
# Example: pandas to_csv with no truncation
df.to_csv(filename, index=False, encoding='utf-8-sig', 
          float_format='%.2f', quoting=csv.QUOTE_MINIMAL)
```

### 2. CSV Export Settings
- **Encoding**: UTF-8 with BOM (`utf-8-sig`)
- **Delimiter**: Comma (`,`)
- **Quote Character**: Double quote (`"`)
- **Line Terminator**: `\r\n` (Windows style)
- **Header**: Required, exact field names as shown above

### 3. Data Extraction Rules

#### Deal Name Extraction
- Extract complete deal name without truncation
- Preserve special characters and parentheses
- No ellipsis (...) truncation

#### Unique ID Extraction
- Must capture the full HubSpot Deal ID
- This is the primary key for matching
- Format: Numeric string (e.g., `270402053362`)

#### Customer Field Format
- Format: `CompanyID; CompanyName`
- Preserve the semicolon separator
- Include both ID and name

#### Date Formatting
- Convert all dates to `YYYY-MM-DD HH:MM:SS`
- Use 24-hour format
- Include seconds even if 00

## Validation Tests

The scraper output must pass these tests:

### 1. Data Completeness Test
```python
def validate_completeness(df):
    required_columns = [
        'Unique ID', 'Deal Name', 'Customer', 'Close Date',
        'Commission', 'Commission Currency', 'Commission Rate'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
        assert df[col].notna().all(), f"Null values in {col}"
```

### 2. Deal Name Truncation Test
```python
def check_truncation(df):
    truncated = df['Deal Name'].str.endswith('…').sum()
    assert truncated == 0, f"{truncated} deal names are truncated"
```

### 3. Unique ID Format Test
```python
def validate_unique_ids(df):
    # All IDs should be numeric strings
    assert df['Unique ID'].str.match(r'^\d+$').all(), "Invalid ID format"
    
    # IDs should match HubSpot format (10-12 digits)
    assert df['Unique ID'].str.len().between(10, 15).all(), "ID length mismatch"
```

### 4. Customer Format Test
```python
def validate_customer_format(df):
    # Should contain semicolon separator
    assert df['Customer'].str.contains(';').all(), "Customer format incorrect"
    
    # Should have format: "ID; Name"
    pattern = r'^\d+;\s*.+$'
    assert df['Customer'].str.match(pattern).all(), "Customer format invalid"
```

## Quality Metrics

The scraper should achieve:
- **Data Quality Score**: >95%
- **Unique ID Match Rate**: 100%
- **Deal Name Completeness**: 100% (no truncation)
- **Field Completeness**: 100% for required fields

## Testing Checklist

Before deployment, verify:

- [ ] All required columns present
- [ ] No truncated deal names
- [ ] Unique IDs match HubSpot format
- [ ] Customer field has correct format
- [ ] Dates in ISO format
- [ ] Commission values are numeric
- [ ] UTF-8 BOM encoding used
- [ ] Quality score >95%

## Example Output (First Row)

```csv
ACV (EUR),Performance Kicker,Split,Commission,Commission Currency,Commission Rate,Commission Details,Close Date,Revenue Start Date,Professional Services Start Date,Deal Type,Unique ID,ACV Sales (Managed Services),ACV Sales (Professional Services) ,ACV Sales (Software),TCV (Professional Services),Currency,Create Date,Customer,Deal owner - Email,Deal owner - Name,Deal Stage,Is Closed Won,Deal Name,Imported Date,Edited Date,Added By,Types of ACV,Product Name
104,1.10,Yes,2.5168,EUR,4.40%,Tier 2 - Indexation and Parameter,2025-07-24 16:17:48,2026-01-01 01:00:00,,CPI Increase,270564406496,0,0,104,0,EUR,2025-07-24 16:17:48,100733; State Bank of India,thomas.bieth@regnology.net,Thomas Bieth,Closed & Won,true,CPI Increase 2025@State Bank of India,2025-07-24 16:38:40,2025-07-28 15:10:28,david.leather@regnology.net,Software,Regnology Transactions
```

## Support

For questions about these requirements, please refer to the manual export format as the gold standard.

## Implementation Strategy

### Phase 1: Critical Field Fixes (Priority: HIGH)
1. **Unique ID Extraction**
   - Ensure full HubSpot Deal ID is captured
   - No truncation or transformation
   - This is the primary matching key

2. **Deal Name Completeness**
   - Increase field buffer to handle long names
   - Remove any character limits that cause truncation
   - Preserve all special characters

3. **Customer Format**
   - Maintain "ID; Company Name" format
   - This enables company-based matching as fallback

### Phase 2: Data Format Standardization (Priority: MEDIUM)
1. **CSV Structure**
   - Match exact column order of manual exports
   - Use UTF-8 with BOM encoding
   - Implement proper quoting for fields with commas

2. **Date Formatting**
   - Convert all dates to ISO format
   - Include time component even if 00:00:00
   - Ensure timezone consistency

### Phase 3: Validation & Testing (Priority: HIGH)
1. **Automated Tests**
   - Run validation suite on each scrape
   - Compare sample against manual export
   - Alert on quality degradation

2. **Performance Metrics**
   - Track data quality score over time
   - Monitor truncation rates
   - Measure ID match rates

## Common Scraper Issues & Solutions

### Issue: Field Truncation
**Symptom**: Deal names ending with "..."
**Root Cause**: HTML element width limits or CSS text-overflow
**Solution**:
```python
# Instead of visible text
element.text  # May be truncated

# Use full attribute value
element.get_attribute('title')  # Often contains full text
element.get_attribute('data-full-text')  # Custom attributes
```

### Issue: Missing Unique IDs
**Symptom**: Unique ID field empty or wrong format
**Root Cause**: ID might be in different element or attribute
**Solution**:
```python
# Check multiple sources
id_sources = [
    element.get_attribute('data-deal-id'),
    element.get_attribute('href').split('/')[-1],  # From URL
    element.find_element_by_class_name('deal-id').text
]
```

### Issue: Incorrect CSV Encoding
**Symptom**: Special characters corrupted
**Root Cause**: Wrong encoding on write
**Solution**:
```python
# Always use UTF-8 with BOM
with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(data)
```

## Monitoring & Alerts

### Quality Metrics to Track
1. **Data Completeness**
   - % of records with Unique ID
   - % of non-truncated deal names
   - Field fill rates

2. **Match Rates**
   - ID match rate with HubSpot
   - Successful reconciliation rate
   - Commission accuracy

3. **Performance**
   - Scraping duration
   - Error rates
   - Retry counts

### Alert Thresholds
- Data quality score < 80%: Warning
- Data quality score < 60%: Critical
- Truncation rate > 5%: Warning
- Missing IDs > 1%: Critical