#!/usr/bin/env python3
"""
Commission Reconciliation CLI Tool
Main entry point for reconciling HubSpot deals with SalesCookie commissions
"""
import click
import logging
import sys
from datetime import datetime
from pathlib import Path
from hubspot_parser import HubSpotParser
from salescookie_parser import SalesCookieParser
from reconciliation_engine import ReconciliationEngine
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    '--hubspot-file', 
    required=True,
    type=click.Path(exists=True),
    help='Path to HubSpot CSV export file'
)
@click.option(
    '--salescookie-dir',
    required=True,
    type=click.Path(exists=True),
    help='Path to SalesCookie data directory'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='./reports',
    help='Directory for output reports (default: ./reports)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def reconcile(hubspot_file, salescookie_dir, output_dir, verbose):
    """
    Reconcile HubSpot deals with SalesCookie commission data.
    
    This tool will:
    - Parse all Closed & Won deals from HubSpot
    - Load all quarterly commission data from SalesCookie
    - Match deals between systems
    - Validate commission calculations
    - Generate detailed reports with discrepancies
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        click.echo("🚀 Starting Commission Reconciliation Process...")
        
        # 1. Parse HubSpot data
        click.echo("\n📊 Parsing HubSpot data...")
        hs_parser = HubSpotParser(hubspot_file)
        hubspot_deals = hs_parser.parse()
        hs_summary = hs_parser.summary()
        
        click.echo(f"  ✓ Found {hs_summary['total_deals']} Closed & Won deals")
        click.echo(f"  ✓ Total amount: €{hs_summary['total_amount']:,.2f}")
        click.echo(f"  ✓ PS deals: {hs_summary['ps_deals_count']}")
        
        # 2. Parse SalesCookie data
        click.echo("\n💰 Parsing SalesCookie data...")
        sc_parser = SalesCookieParser(salescookie_dir)
        quarters_data = sc_parser.parse_all_quarters()
        sc_summary = sc_parser.summary()
        
        click.echo(f"  ✓ Found {sc_summary['total_transactions']} transactions")
        click.echo(f"  ✓ Total commission: €{sc_summary['total_commission']:,.2f}")
        click.echo(f"  ✓ Quarters: {', '.join(sorted(sc_summary['quarters'].keys()))}")
        
        # 3. Run reconciliation
        click.echo("\n🔍 Running reconciliation...")
        engine = ReconciliationEngine(hubspot_deals, sc_parser.transactions)
        results = engine.reconcile()
        
        summary = results['summary']
        click.echo(f"  ✓ Matched {summary['matched_deals_count']} deals")
        click.echo(f"  ⚠️  Found {summary['total_discrepancies']} discrepancies")
        
        if summary['total_discrepancies'] > 0:
            click.echo(f"  💸 Total impact: €{summary['total_impact']:,.2f}")
            
            # Show discrepancy breakdown
            click.echo("\n  Discrepancies by type:")
            for disc_type, data in summary['discrepancies_by_type'].items():
                click.echo(f"    - {disc_type.replace('_', ' ').title()}: {data['count']} (€{data['impact']:,.2f})")
                
        # 4. Generate reports
        click.echo("\n📄 Generating reports...")
        generator = ReportGenerator(output_dir)
        report_paths = generator.generate_reports(results)
        
        click.echo("  ✓ Reports generated:")
        click.echo(f"    - Excel: {report_paths['excel']}")
        click.echo(f"    - Summary: {report_paths['text']}")
        click.echo(f"    - CSV: {report_paths['csv']}")
        
        # 5. Summary and recommendations
        click.echo("\n✨ Reconciliation Complete!")
        
        if summary['total_discrepancies'] > 0:
            click.echo("\n⚡ Top recommendations:")
            
            if 'missing_deal' in summary['discrepancies_by_type']:
                click.echo("  1. Check SalesCookie sync - some Closed & Won deals are missing")
                
            if 'wrong_commission_amount' in summary['discrepancies_by_type']:
                click.echo("  2. Review commission rates - some calculations don't match expected rates")
                
            if 'missing_quarter_split' in summary['discrepancies_by_type']:
                click.echo("  3. Verify quarter splits - some deals missing 50/50 allocation")
                
            if 'missing_currency_conversion' in summary['discrepancies_by_type']:
                click.echo("  4. Check currency conversions - ensure company currency is recorded")
        else:
            click.echo("\n✅ All commissions appear to be correctly calculated and recorded!")
            
    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        logger.exception("Reconciliation failed")
        sys.exit(1)

if __name__ == '__main__':
    reconcile()