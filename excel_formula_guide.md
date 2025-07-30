# Adding Commission Percentage Column to Excel

## Manual Method

1. **Insert New Column**
   - Right-click on column H
   - Select "Insert Column"

2. **Add Header**
   - In cell H1, type: `Commission %`

3. **Add Formula**
   - In cell H2, enter this formula:
   ```
   =IF(E2>0, F2/E2, 0)
   ```
   
4. **Copy Formula Down**
   - Select cell H2
   - Copy (Ctrl+C or Cmd+C)
   - Select range H3 to last row with data
   - Paste (Ctrl+V or Cmd+V)

5. **Format as Percentage**
   - Select all cells in column H with data
   - Right-click → Format Cells
   - Choose "Percentage" with 2 decimal places

## Excel Formula Explanation

The formula `=IF(E2>0, F2/E2, 0)` does the following:
- `IF(E2>0, ...)` - Checks if Amount (column E) is greater than 0
- `F2/E2` - Divides SC Total Commission (F) by Amount (E)
- `0` - Returns 0 if Amount is 0 (to avoid division by zero)

Excel automatically converts to percentage when you apply percentage formatting.

## Expected Commission Rates

Based on the commission plans:

### 2024 Rates
- Software: 7.3%
- Managed Services Public: 5.9%
- Managed Services Private: 7.3%
- Professional Services (Recurring): 2.9%
- Indexations & Parameter: 8.8%
- PS Deals (Flat): 1.0%

### 2025 Rates
- Software: 7.0%
- Managed Services Public: 7.4%
- Managed Services Private: 8.4%
- Professional Services (Recurring): 3.1%
- Indexations & Parameter: 9.3%
- PS Deals (Flat): 1.0%

## Identifying Issues

Look for deals where the commission percentage doesn't match expected rates:
- PS deals should be exactly 1.0%
- Software deals should be 7.0-7.3%
- Managed Services should be 5.9-8.4%
- Very high or very low percentages indicate calculation errors