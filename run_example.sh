#!/bin/bash
# Example script to run the reconciliation tool

echo "Commission Reconciliation Tool - Example Run"
echo "==========================================="
echo ""
echo "This tool will help you reconcile HubSpot deals with SalesCookie commissions."
echo ""
echo "Prerequisites:"
echo "1. Install Python 3 and pip"
echo "2. Install required packages: pip3 install -r requirements.txt"
echo ""
echo "Example command:"
echo ""
echo "python3 reconcile.py \\"
echo "  --hubspot-file ../hubsport_download_20250729/hubspot-crm-exports-tb-deals-2025-07-29.csv \\"
echo "  --salescookie-dir ../sales_cookie_all_plans_20250729 \\"
echo "  --output-dir ./reports"
echo ""
echo "The tool will generate:"
echo "- Excel report with detailed analysis"
echo "- Text summary with recommendations"
echo "- CSV file with all discrepancies"
echo ""
echo "To install dependencies now, run:"
echo "pip3 install pandas openpyxl python-dateutil click tabulate colorama"