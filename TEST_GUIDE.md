# Commission Reconciliation Tool - Testing Guide

## Overview

This document provides instructions for running the automated test suite for the Commission Reconciliation Tool.

## Prerequisites

Before running tests, ensure you have the required dependencies installed:

```bash
pip install pandas openpyxl click
```

## Test Structure

The test suite includes:

### 1. Unit Tests (`tests/test_reconciliation.py`)
- **HubSpot Parser Tests**: Validates CSV parsing and deal classification
- **SalesCookie Parser Tests**: Tests both manual and scraped data parsing
- **Data Quality Detection**: Verifies automatic quality assessment
- **Commission Validation**: Tests commission rate calculations
- **Edge Cases**: Tests error handling and missing fields

### 2. Integration Tests (`tests/test_integration.py`)
- **End-to-End Workflow**: Tests complete reconciliation process
- **CLI Testing**: Validates command-line interface
- **Report Generation**: Verifies all output formats
- **Discrepancy Detection**: Ensures issues are properly identified

## Running Tests

### Run All Tests
```bash
python3 run_tests.py
```

### Run Specific Test Module
```bash
python3 -m unittest tests.test_reconciliation
python3 -m unittest tests.test_integration
```

### Run with Coverage
```bash
pip install coverage
coverage run --source=. run_tests.py
coverage report
coverage html  # Creates htmlcov/index.html
```

## Test Data

The tests use synthetic data that simulates:
- Various deal types (Software, Managed Services, Professional Services)
- Different commission rates and calculations
- Data quality issues (truncation, missing IDs)
- Currency conversions
- Edge cases and errors

## Expected Test Results

### Successful Run
- All tests should pass with no errors
- Output shows: `✅ All tests passed!`
- Exit code: 0

### Test Failures
- Failed tests will show detailed error messages
- Output shows: `❌ Some tests failed!`
- Exit code: 1

## Test Coverage Areas

1. **Data Parsing**
   - HubSpot CSV format variations
   - Manual vs scraped SalesCookie data
   - Missing fields and bad data

2. **Matching Algorithms**
   - ID-based matching (100% confidence)
   - Name+date matching (95% confidence)
   - Company+date matching (80% confidence)

3. **Commission Calculations**
   - 2024 vs 2025 rate differences
   - PS deals (1% flat rate)
   - Deal type classification

4. **Data Quality**
   - Truncation detection
   - Missing field identification
   - Quality scoring algorithm

5. **Report Generation**
   - Excel with multiple sheets
   - Summary text reports
   - CSV discrepancy exports

## Adding New Tests

To add new test cases:

1. Create test methods in appropriate test file
2. Follow naming convention: `test_description_of_test`
3. Use setUp/tearDown for test data management
4. Include assertions to verify expected behavior

Example:
```python
def test_new_feature(self):
    """Test description"""
    # Arrange
    test_data = create_test_data()
    
    # Act
    result = function_under_test(test_data)
    
    # Assert
    self.assertEqual(result.expected, actual)
```

## Troubleshooting

### Import Errors
Ensure all dependencies are installed and you're running from the correct directory.

### File Not Found
Tests create temporary files. Ensure you have write permissions in the temp directory.

### Assertion Failures
Check test expectations against actual implementation. Tests may need updates if business logic changes.

## Continuous Integration

For CI/CD pipelines, use:
```bash
python3 run_tests.py
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Tests failed"
    exit 1
fi
```