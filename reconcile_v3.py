#!/usr/bin/env python3
"""
Enhanced Commission Reconciliation Tool v3
Supports withholding, forecast, and split transaction analysis
"""
import click
import pandas as pd
from datetime import datetime
import os
import sys
import logging
from dataclasses import asdict
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2, DataSource
from reconciliation_engine_v3 import ReconciliationEngineV3
from report_generator_v3 import ReportGeneratorV3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--hubspot-file', required=True, help='Path to HubSpot CSV export')
@click.option('--salescookie-file', help='Path to manual SalesCookie CSV export')
@click.option('--salescookie-dir', help='Directory containing SalesCookie files')
@click.option('--output-dir', default='./reports', help='Directory for output reports')
@click.option('--data-source', type=click.Choice(['manual', 'scraped', 'auto']), 
              default='auto', help='Specify data source type')
@click.option('--quality-check', is_flag=True, help='Run data quality check only')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--include-withholdings', is_flag=True, help='Include withholding transactions')
@click.option('--include-forecasts', is_flag=True, help='Include forecast/estimated transactions')
@click.option('--include-splits', is_flag=True, help='Include split credit transactions')
@click.option('--all-types', is_flag=True, help='Include all transaction types')
def reconcile(hubspot_file, salescookie_file, salescookie_dir, output_dir, 
              data_source, quality_check, verbose, include_withholdings, 
              include_forecasts, include_splits, all_types):
    """
    Enhanced Commission Reconciliation Tool v3
    
    Reconciles HubSpot deals with SalesCookie commission data including
    withholdings, forecasts, and split transactions.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    click.echo("🚀 Commission Reconciliation Tool v3.0")
    click.echo("=" * 70)
    
    # Validate inputs
    if not salescookie_file and not salescookie_dir:
        click.echo("❌ Error: Either --salescookie-file or --salescookie-dir must be provided")
        sys.exit(1)
        
    if salescookie_file and salescookie_dir:
        click.echo("❌ Error: Cannot specify both --salescookie-file and --salescookie-dir")
        sys.exit(1)
        
    # 1. Load HubSpot data
    click.echo("\n📊 Loading HubSpot data...")
    try:
        hs_parser = HubSpotParser(hubspot_file)
        hubspot_deals = hs_parser.parse()
        summary = hs_parser.summary()
        
        click.echo(f"  ✓ Found {summary['total_deals']} Closed & Won deals")
        click.echo(f"  ✓ Total amount: €{summary['total_amount']:,.2f}")
        
    except Exception as e:
        click.echo(f"❌ Error loading HubSpot data: {str(e)}")
        sys.exit(1)
        
    # 2. Load SalesCookie data
    click.echo("\n💰 Loading SalesCookie data...")
    sc_parser = SalesCookieParserV2()
    all_transactions = []
    quality_reports = []
    
    try:
        if salescookie_file:
            # Single file mode
            source = DataSource.MANUAL if data_source == 'manual' else DataSource.SCRAPED if data_source == 'scraped' else None
            transactions, quality = sc_parser.parse_file(salescookie_file, source)
            all_transactions.extend(transactions)
            if quality:
                quality_reports.append((salescookie_file, quality))
                
        else:
            # Directory mode - load multiple files
            files_to_load = []
            
            # Determine which files to load based on flags
            if all_types or (not include_withholdings and not include_forecasts and not include_splits):
                # Load all files if --all-types or no specific flags
                files_to_load = [f for f in os.listdir(salescookie_dir) if f.endswith('.csv')]
            else:
                # Load specific file types
                for file in os.listdir(salescookie_dir):
                    if file.endswith('.csv'):
                        file_lower = file.lower()
                        
                        # Regular credit files
                        if 'credits' in file_lower and 'withholding' not in file_lower and 'split' not in file_lower and 'estimated' not in file_lower:
                            files_to_load.append(file)
                            
                        # Withholding files
                        elif include_withholdings and 'withholding' in file_lower:
                            files_to_load.append(file)
                            
                        # Forecast files
                        elif include_forecasts and ('estimated' in file_lower or 'forecast' in file_lower):
                            files_to_load.append(file)
                            
                        # Split files
                        elif include_splits and 'split' in file_lower:
                            files_to_load.append(file)
                            
            # Load selected files
            click.echo(f"  Loading {len(files_to_load)} files from {salescookie_dir}")
            
            for file in sorted(files_to_load):
                filepath = os.path.join(salescookie_dir, file)
                click.echo(f"  - {file}...", nl=False)
                
                try:
                    transactions, quality = sc_parser.parse_file(filepath)
                    if transactions:
                        all_transactions.extend(transactions)
                        click.echo(f" ✓ ({len(transactions)} transactions)")
                    else:
                        click.echo(" ⚠️  (no data)")
                        
                    if quality:
                        quality_reports.append((file, quality))
                        
                except Exception as e:
                    click.echo(f" ❌ (error: {str(e)})")
                    
        click.echo(f"\n  ✓ Total transactions loaded: {len(all_transactions)}")
        
        # Show transaction type breakdown
        tx_types = {}
        for tx in all_transactions:
            tx_type = tx.get('transaction_type', 'regular')
            tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
            
        if len(tx_types) > 1:
            click.echo("\n  Transaction types:")
            for tx_type, count in sorted(tx_types.items()):
                click.echo(f"    - {tx_type}: {count}")
        
    except Exception as e:
        click.echo(f"❌ Error loading SalesCookie data: {str(e)}")
        sys.exit(1)
        
    # 3. Data Quality Check
    if quality_reports:
        click.echo("\n📊 Data Quality Summary:")
        for filename, quality in quality_reports:
            click.echo(f"  {os.path.basename(filename)}: {quality.quality_score:.1f}/100 "
                      f"({quality.source_type.value})")
            
    if quality_check:
        # Only show quality report and exit
        click.echo("\n" + sc_parser.generate_quality_report())
        return
        
    # 4. Run Reconciliation
    click.echo("\n🔄 Running enhanced reconciliation...")
    try:
        engine = ReconciliationEngineV3(hubspot_deals, all_transactions)
        
        # Calculate average quality score
        avg_quality = sum(q.quality_score for _, q in quality_reports) / len(quality_reports) if quality_reports else 100.0
        
        results = engine.reconcile(avg_quality)
        
        # Convert result object to dict for report generator
        results_dict = {
            'summary': results.summary,
            'discrepancies': [asdict(d) for d in results.discrepancies],
            'matched_deals': [
                {
                    'hubspot_id': m.hubspot_id,
                    'salescookie_id': m.salescookie_id,
                    'match_type': m.match_type,
                    'confidence': m.confidence,
                    'hubspot_deal': m.hubspot_deal,
                    'salescookie_transactions': m.salescookie_transactions,
                    # Include additional fields for reporting
                    'deal_name': m.hubspot_deal.get('deal_name'),
                    'close_date': m.hubspot_deal.get('close_date'),
                    'service_start_date': m.hubspot_deal.get('service_start_date'),
                    'revenue_start_date': m.hubspot_deal.get('service_start_date'),  # Alias for compatibility
                    'hubspot_amount': m.hubspot_deal.get('commission_amount', 0),
                    'salescookie_amount': sum(t.get('commission_amount', 0) for t in m.salescookie_transactions),
                }
                for m in results.matches
            ],
            'unmatched_hubspot': results.unmatched_hubspot,
            'unmatched_salescookie': results.unmatched_salescookie,
            'all_deals': hubspot_deals,  # Include all HubSpot deals for complete reporting
        }
        
    except Exception as e:
        click.echo(f"❌ Error during reconciliation: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
        
    # 5. Display Results
    summary = results.summary
    click.echo(f"\n📊 RECONCILIATION RESULTS")
    click.echo("=" * 70)
    click.echo(f"  ✓ Matched {summary['matched_deals_count']} deals "
              f"({summary['match_rate']:.1f}%)")
    click.echo(f"  ℹ️  Centrally Processed (CPI/Fix): {summary['centrally_processed_count']} transactions")
    click.echo(f"  ⚠️  Discrepancies: {summary['total_discrepancies']}")
    click.echo(f"  💸 Total impact: €{summary['total_impact']:,.2f}")
    
    # Show withholding summary if applicable
    if 'withholding_summary' in summary and summary['withholding_transactions'] > 0:
        wh = summary['withholding_summary']
        click.echo(f"\n  💰 Withholding Summary:")
        click.echo(f"     - Paid (50%): €{wh['total_paid']:,.2f}")
        click.echo(f"     - Withheld: €{wh['total_withheld']:,.2f}")
        click.echo(f"     - Full value: €{wh['total_full_commission']:,.2f}")
        
    # Show forecast summary if applicable
    if 'forecast_summary' in summary and summary['forecast_transactions'] > 0:
        fc = summary['forecast_summary']
        click.echo(f"\n  📈 Forecast Summary:")
        click.echo(f"     - Total forecast: €{fc['total_forecast_amount']:,.2f}")
        click.echo(f"     - Total kickers: €{fc['total_kickers']:,.2f}")
        click.echo(f"     - Deals with kickers: {fc['deals_with_kickers']}")
    
    # 6. Generate Reports
    click.echo("\n📄 Generating reports...")
    try:
        report_gen = ReportGeneratorV3(output_dir)
        report_paths = report_gen.generate_reports(results_dict)
        
        click.echo(f"  ✓ Excel report: {report_paths['excel']}")
        click.echo(f"  ✓ Text summary: {report_paths['text']}")
        click.echo(f"  ✓ Discrepancy CSV: {report_paths['csv']}")
        
    except Exception as e:
        click.echo(f"❌ Error generating reports: {str(e)}")
        
    # 7. Recommendations
    if summary['total_discrepancies'] > 0:
        click.echo("\n💡 RECOMMENDATIONS:")
        click.echo("-" * 40)
        
        disc_types = summary.get('discrepancies_by_type', {})
        
        if disc_types.get('missing_deal', {}).get('count', 0) > 0:
            click.echo("  1. Review missing deals - ensure all eligible deals are in SalesCookie")
            
        if disc_types.get('wrong_commission_amount', {}).get('count', 0) > 0:
            click.echo("  2. Check commission calculations - verify rates and amounts")
            
        if disc_types.get('withholding_mismatch', {}).get('count', 0) > 0:
            click.echo("  3. Verify withholding calculations - should be 50% standard rate")
            
        if summary.get('data_quality_score', 100) < 80:
            click.echo("  4. Improve data quality - check for truncated names and missing IDs")
            
    else:
        click.echo("\n✅ No discrepancies found - all commissions reconciled successfully!")
        
    click.echo("\n✨ Reconciliation complete!")

if __name__ == '__main__':
    reconcile()