#!/usr/bin/env python3
"""
Enhanced Commission Reconciliation CLI Tool with dual-mode support
"""
import click
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from hubspot_parser import HubSpotParser
from salescookie_parser_v2 import SalesCookieParserV2, DataSource
from reconciliation_engine_v2 import ReconciliationEngineV2
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
    type=click.Path(exists=True),
    help='Path to SalesCookie scraped data directory'
)
@click.option(
    '--salescookie-file',
    type=click.Path(exists=True),
    help='Path to manual SalesCookie export file'
)
@click.option(
    '--data-source',
    type=click.Choice(['manual', 'scraped', 'auto']),
    default='auto',
    help='Specify data source type (default: auto-detect)'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='./reports',
    help='Directory for output reports (default: ./reports)'
)
@click.option(
    '--quality-check',
    is_flag=True,
    help='Run data quality check only (no reconciliation)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def reconcile(hubspot_file, salescookie_dir, salescookie_file, data_source, output_dir, quality_check, verbose):
    """
    Enhanced Commission Reconciliation Tool with support for both manual and scraped data.
    
    This tool will:
    - Parse HubSpot Closed & Won deals
    - Load SalesCookie data (manual export or scraped)
    - Assess data quality and provide warnings
    - Match deals using multiple strategies
    - Validate commission calculations
    - Generate comprehensive reports
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate inputs
    if not salescookie_dir and not salescookie_file:
        click.echo("❌ Error: Please provide either --salescookie-dir or --salescookie-file", err=True)
        sys.exit(1)
        
    if salescookie_dir and salescookie_file:
        click.echo("❌ Error: Please provide only one of --salescookie-dir or --salescookie-file", err=True)
        sys.exit(1)
        
    try:
        click.echo("🚀 Starting Enhanced Commission Reconciliation Process...")
        
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
        sc_parser = SalesCookieParserV2()
        all_transactions = []
        quality_reports = []
        
        if salescookie_file:
            # Manual export mode
            click.echo(f"  → Loading manual export: {os.path.basename(salescookie_file)}")
            transactions, quality = sc_parser.parse_file(
                salescookie_file, 
                DataSource.MANUAL if data_source == 'manual' else None
            )
            if quality:
                quality_reports.append(quality)
                sc_parser.data_quality_reports[salescookie_file] = quality
            all_transactions.extend(transactions)
            
        else:
            # Scraped data mode
            click.echo(f"  → Loading scraped data from: {salescookie_dir}")
            # Find all CSV files
            import glob
            csv_files = []
            for pattern in ['**/credited_transactions*.csv', '**/credits*.csv']:
                csv_files.extend(glob.glob(os.path.join(salescookie_dir, pattern), recursive=True))
                
            if not csv_files:
                click.echo("  ⚠️  No transaction CSV files found in directory", err=True)
                
            for csv_file in csv_files:
                click.echo(f"  → Processing: {os.path.basename(csv_file)}")
                transactions, quality = sc_parser.parse_file(
                    csv_file,
                    DataSource.SCRAPED if data_source == 'scraped' else None
                )
                if quality:
                    quality_reports.append(quality)
                    sc_parser.data_quality_reports[csv_file] = quality
                all_transactions.extend(transactions)
                
        click.echo(f"\n  ✓ Loaded {len(all_transactions)} transactions")
        
        # 3. Data Quality Assessment
        click.echo("\n🔍 Data Quality Assessment...")
        
        if quality_reports:
            avg_quality = sum(q.quality_score for q in quality_reports) / len(quality_reports)
            click.echo(f"  → Average quality score: {avg_quality:.1f}/100")
            
            # Show warnings
            all_warnings = []
            for report in quality_reports:
                all_warnings.extend(report.warnings)
                
            if all_warnings:
                click.echo("\n  ⚠️  Data Quality Warnings:")
                for warning in set(all_warnings):  # Unique warnings
                    click.echo(f"    - {warning}")
                    
            # Check for critical issues
            if avg_quality < 50:
                click.echo("\n  🚨 CRITICAL: Data quality is very poor!")
                click.echo("     Consider using manual exports instead of scraped data.")
                
        # If quality check only, stop here
        if quality_check:
            click.echo("\n📄 Generating data quality report...")
            quality_report = sc_parser.generate_quality_report()
            
            # Save to file
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_path, 'w') as f:
                f.write(quality_report)
                
            click.echo(f"  ✓ Quality report saved to: {report_path}")
            click.echo("\n" + quality_report)
            return
            
        # 4. Run reconciliation
        click.echo("\n🔄 Running reconciliation...")
        engine = ReconciliationEngineV2(hubspot_deals, all_transactions)
        results = engine.reconcile(avg_quality if quality_reports else 100.0)
        
        summary = results.summary
        click.echo(f"  ✓ Matched {summary['matched_deals_count']} deals")
        
        # Show centrally processed info
        if summary.get('centrally_processed_count', 0) > 0:
            click.echo(f"\n  ℹ️  Centrally Processed Transactions:")
            click.echo(f"    - Count: {summary['centrally_processed_count']}")
            click.echo(f"    - Commission: €{summary['centrally_processed_commission']:,.2f}")
            click.echo(f"    - Note: CPI/Fix Increase deals are handled centrally")
        
        if summary['matches_by_type']:
            click.echo("\n  Match types:")
            for match_type, count in summary['matches_by_type'].items():
                click.echo(f"    - {match_type}: {count}")
            click.echo(f"    - Average confidence: {summary['average_match_confidence']:.1f}%")
            
        click.echo(f"\n  ⚠️  Found {summary['total_discrepancies']} discrepancies")
        
        if summary['total_discrepancies'] > 0:
            click.echo(f"  💸 Total impact: €{summary['total_impact']:,.2f}")
            
            # Show discrepancy breakdown
            click.echo("\n  Discrepancies by type:")
            for disc_type, data in summary['discrepancies_by_type'].items():
                click.echo(f"    - {disc_type.replace('_', ' ').title()}: {data['count']} (€{data['impact']:,.2f})")
                
        # 5. Generate reports
        click.echo("\n📄 Generating reports...")
        
        # Convert enhanced results to format expected by report generator
        legacy_results = {
            'summary': summary,
            'discrepancies': results.discrepancies,
            'matched_deals': [
                {
                    'hubspot': match.hubspot_deal,
                    'salescookie': match.salescookie_transactions,
                    'confidence': match.confidence,
                    'match_type': match.match_type
                }
                for match in results.matches
            ]
        }
        
        generator = ReportGenerator(output_dir)
        report_paths = generator.generate_reports(legacy_results)
        
        click.echo("  ✓ Reports generated:")
        click.echo(f"    - Excel: {report_paths['excel']}")
        click.echo(f"    - Summary: {report_paths['text']}")
        click.echo(f"    - CSV: {report_paths['csv']}")
        
        # 6. Generate scraper requirements if using scraped data
        if salescookie_dir and avg_quality < 80:
            click.echo("\n📋 Generating scraper optimization report...")
            scraper_report_path = os.path.join(output_dir, f"scraper_requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(scraper_report_path, 'w') as f:
                f.write(generate_scraper_requirements(quality_reports, results))
                
            click.echo(f"  ✓ Scraper requirements saved to: {scraper_report_path}")
            
        # 7. Summary and recommendations
        click.echo("\n✨ Reconciliation Complete!")
        
        # Show transaction summary
        click.echo(f"\n📊 Transaction Summary:")
        click.echo(f"  - Total SalesCookie transactions: {summary.get('salescookie_total_transactions', 0)}")
        click.echo(f"  - Centrally processed (CPI/Fix): {summary.get('centrally_processed_count', 0)}")
        click.echo(f"  - Available for matching: {summary['salescookie_transactions_count']}")
        
        if summary['total_discrepancies'] > 0:
            click.echo("\n⚡ Top recommendations:")
            
            if avg_quality < 70:
                click.echo("  1. 🚨 Improve data quality - consider using manual exports")
                
            if 'missing_deal' in summary['discrepancies_by_type']:
                click.echo("  2. Check SalesCookie sync - some Closed & Won deals are missing")
                
            if 'wrong_commission_amount' in summary['discrepancies_by_type']:
                click.echo("  3. Review commission rates - some calculations don't match expected rates")
                
        else:
            click.echo("\n✅ All commissions appear to be correctly calculated and recorded!")
            
    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        logger.exception("Reconciliation failed")
        sys.exit(1)

def generate_scraper_requirements(quality_reports, results):
    """Generate scraper optimization requirements"""
    report = ["SALESCOOKIE SCRAPER OPTIMIZATION REQUIREMENTS\n" + "=" * 50 + "\n"]
    
    report.append("\nIDENTIFIED ISSUES:")
    
    # Analyze quality issues
    issues = set()
    for qr in quality_reports:
        if qr.truncated_names > 0:
            issues.add("Deal names are being truncated")
        if 'Unique ID' in qr.missing_fields:
            issues.add("Unique IDs are missing or not properly extracted")
        if qr.quality_score < 70:
            issues.add("Overall data quality is poor")
            
    for issue in issues:
        report.append(f"  - {issue}")
        
    report.append("\n\nREQUIRED FIELDS (Must match manual export exactly):")
    report.append("  1. Unique ID - Full HubSpot Deal ID (e.g., '270402053362')")
    report.append("  2. Deal Name - Complete name without truncation")
    report.append("  3. Customer - Format: 'CompanyID; Company Name'")
    report.append("  4. Close Date - Format: 'YYYY-MM-DD HH:MM:SS'")
    report.append("  5. Commission - Numeric value")
    report.append("  6. Commission Currency - e.g., 'EUR'")
    report.append("  7. Commission Rate - e.g., '7.40%'")
    report.append("  8. ACV (EUR) - Numeric value")
    report.append("  9. Deal Type - e.g., 'Upsell', 'Cross-Sell'")
    report.append("  10. All other fields as per manual export")
    
    report.append("\n\nSPECIFIC FIXES NEEDED:")
    report.append("  1. Increase field width limits to prevent truncation")
    report.append("  2. Ensure CSV export includes ALL columns")
    report.append("  3. Use UTF-8 encoding with BOM")
    report.append("  4. Set delimiter to comma (,) not semicolon")
    report.append("  5. Include header row with exact field names")
    
    report.append("\n\nTEST CASES:")
    report.append("  - Deal names longer than 50 characters")
    report.append("  - Company names with special characters")
    report.append("  - Multiple deals for same company")
    report.append("  - PS deals with 1% commission rate")
    
    report.append("\n\nVALIDATION:")
    report.append("  After fixing, the scraper output should:")
    report.append("  - Have 100% of Unique IDs matching HubSpot")
    report.append("  - Show 0 truncated deal names")
    report.append("  - Achieve >95% data quality score")
    
    return "\n".join(report)

if __name__ == '__main__':
    reconcile()