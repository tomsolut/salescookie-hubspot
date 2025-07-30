# Fixing Commission % Column in Excel

## The Issue
The `#VALUE!` error occurs when Excel can't perform the calculation, usually because:
1. The values in columns E or F are formatted as text
2. The values contain currency symbols (€)
3. The values contain thousand separators (,)

## Solution 1: Manual Fix in Excel

### Step 1: Clean the Amount column (E)
1. Select column E (Amount EUR)
2. Find & Replace (Ctrl+H or Cmd+H):
   - Find: €
   - Replace: (leave empty)
   - Click "Replace All"
3. Find & Replace again:
   - Find: ,
   - Replace: (leave empty)
   - Click "Replace All"
4. Select column E again
5. Right-click → Format Cells → Number → Currency

### Step 2: Clean the SC Total Commission column (F)
1. Repeat the same process for column F

### Step 3: Update the Formula
In cell H2, use this formula:
```
=IFERROR(F2/E2,0)
```

Then copy down to all rows.

## Solution 2: Alternative Formula
If the above doesn't work, try this formula that handles text:
```
=IFERROR(VALUE(SUBSTITUTE(SUBSTITUTE(F2,"€",""),",",""))/VALUE(SUBSTITUTE(SUBSTITUTE(E2,"€",""),",","")),0)
```

## Solution 3: Power Query (Best for recurring use)
1. Data → From Table/Range
2. Transform the data:
   - Change Amount and SC Total Commission to decimal number type
   - Add custom column with formula: [SC Total Commission] / [Amount (EUR)]
3. Close & Load

## Expected Results
After fixing, you should see:
- PS deals: 1.00%
- Software deals: 7.00-7.30%
- Managed Services: 5.90-8.40%
- Professional Services: 2.90-3.10%
- Indexations: 8.80-9.30%

## Identifying Issues
Look for:
- PS deals not at 1% (indicates wrong calculation)
- Very high percentages (>15%)
- Very low percentages (<0.5%)
- Zero percentages (missing commission data)