#!/usr/bin/env python3
"""
Combine all SalesCookie CSV files into a single comprehensive file
Handles regular credits, withholdings, splits, and estimates
"""
import pandas as pd
import os
import sys
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_quarter_from_filename(filename):
    """Extract quarter information from filename"""
    filename_lower = filename.lower()
    
    # Handle split files like "credits split 2024 q1-2025.csv"
    if 'split' in filename_lower:
        if 'q1-2025' in filename_lower:
            return 'q1-2025-split'
        elif 'q2-2025' in filename_lower:
            return 'q2-2025-split'
        elif 'q3-2025' in filename_lower:
            return 'q3-2025-split'
    
    # Handle withholding files
    if 'withholding' in filename_lower:
        if 'q1-2025' in filename_lower:
            return 'q1-2025-withholding'
        elif 'q2-2025' in filename_lower:
            return 'q2-2025-withholding'
        elif 'q3-2025' in filename_lower:
            return 'q3-2025-withholding'
    
    # Handle estimated/forecast files
    if 'estimated' in filename_lower:
        return '2025-forecast'
    
    # Regular credit files
    quarters = ['q1-2023', 'q2-2023', 'q3-2023', 'q4-2023',
                'q1-2024', 'q2-2024', 'q3-2024', 'q4-2024',
                'q1-2025', 'q2-2025', 'q3-2025', 'q4-2025']
    
    for quarter in quarters:
        if quarter in filename_lower:
            return quarter
    
    return 'unknown'

def determine_transaction_type(filename, row=None):
    """Determine transaction type based on filename and row data"""
    filename_lower = filename.lower()
    
    if 'withholding' in filename_lower:
        return 'withholding'
    elif 'split' in filename_lower:
        return 'split'
    elif 'estimated' in filename_lower or 'forecast' in filename_lower:
        return 'forecast'
    else:
        # Check if row has split indicator
        if row is not None and pd.notna(row.get('Split')) and str(row.get('Split')).lower() in ['yes', 'true', '1']:
            return 'split'
        return 'regular'

def normalize_columns(df, source_file):
    """Normalize column names across different file formats"""
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Remove BOM if present
    if df.columns[0].startswith('\ufeff'):
        df.columns = [col.replace('\ufeff', '') for col in df.columns]
    
    # Standard column mapping
    column_mapping = {
        'ACV (EUR)': 'ACV (EUR)',
        'ACV Sales (Managed Services)': 'ACV Sales (Managed Services)',
        'ACV Sales (Professional Services) ': 'ACV Sales (Professional Services)',
        'ACV Sales (Software)': 'ACV Sales (Software)',
        'Commission': 'Commission',
        'Est. Commission': 'Est_Commission',
        'Commission Currency': 'Commission Currency',
        'Commission Rate': 'Commission Rate',
        'Deal Name': 'Deal Name',
        'Unique ID': 'Unique ID',
        'Close Date': 'Close Date',
        'Revenue Start Date': 'Revenue Start Date',
        'Customer': 'Customer',
        'Deal owner - Name': 'Deal owner - Name',
        'Deal owner - Email': 'Deal owner - Email',
        'Product Name': 'Product Name',
        'Split': 'Split',
        'Performance Kicker': 'Performance Kicker',
        'Campaign Kicker': 'Campaign Kicker',
        'Summer Kicker': 'Summer Kicker',
        'Early Bird Kicker': 'Early Bird Kicker',
        'Earlybird Kicker': 'Earlybird Kicker',
        'TCV Accelerator': 'TCV Accelerator'
    }
    
    # Apply mapping
    df.columns = [column_mapping.get(col.strip(), col.strip()) for col in df.columns]
    
    # Add source metadata
    df['Source_File'] = source_file
    df['Quarter'] = extract_quarter_from_filename(source_file)
    
    # Add transaction type for each row
    df['Transaction_Type'] = df.apply(lambda row: determine_transaction_type(source_file, row), axis=1)
    
    # Handle withholding files (they have both Commission and Est. Commission)
    if 'withholding' in source_file.lower() and 'Est_Commission' in df.columns:
        # Convert to numeric first
        df['Commission'] = pd.to_numeric(
            df['Commission'].astype(str).str.replace('€', '').str.replace(',', ''), 
            errors='coerce'
        )
        df['Est_Commission'] = pd.to_numeric(
            df['Est_Commission'].astype(str).str.replace('€', '').str.replace(',', ''), 
            errors='coerce'
        )
        # For withholding files, Commission is 50% paid, Est_Commission is 100%
        df['Withheld_Amount'] = df['Est_Commission'] - df['Commission']
        df['Full_Commission'] = df['Est_Commission']
    
    # Convert Commission to numeric, handling various formats
    if 'Commission' in df.columns:
        df['Commission_Numeric'] = pd.to_numeric(
            df['Commission'].astype(str).str.replace('€', '').str.replace(',', ''), 
            errors='coerce'
        )
    
    return df

def combine_all_files(directory_path):
    """Combine all SalesCookie CSV files from directory"""
    all_dataframes = []
    files_processed = []
    
    # Get all CSV files except tb-deals.csv (that's HubSpot data)
    csv_files = [f for f in os.listdir(directory_path) 
                 if f.endswith('.csv') and f != 'tb-deals.csv']
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    for filename in sorted(csv_files):
        filepath = os.path.join(directory_path, filename)
        logger.info(f"Processing: {filename}")
        
        try:
            # Read CSV with multiple encoding attempts
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            # Skip empty files
            if df.empty:
                logger.warning(f"Skipping empty file: {filename}")
                continue
            
            # Normalize columns
            df = normalize_columns(df, filename)
            
            all_dataframes.append(df)
            files_processed.append(filename)
            
            logger.info(f"  - Loaded {len(df)} rows")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            continue
    
    # Combine all dataframes
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
        logger.info(f"\nCombined {len(combined_df)} total rows from {len(files_processed)} files")
        
        # Sort by Close Date
        if 'Close Date' in combined_df.columns:
            combined_df['Close Date'] = pd.to_datetime(combined_df['Close Date'], errors='coerce')
            combined_df = combined_df.sort_values('Close Date', na_position='last')
        
        return combined_df, files_processed
    else:
        logger.error("No data to combine!")
        return None, []

def main():
    # Directory containing SalesCookie files
    salescookie_dir = os.path.join(os.path.dirname(__file__), '..', 'salescookie_manual')
    
    if not os.path.exists(salescookie_dir):
        logger.error(f"Directory not found: {salescookie_dir}")
        sys.exit(1)
    
    logger.info(f"Combining SalesCookie files from: {salescookie_dir}")
    
    # Combine all files
    combined_df, files_processed = combine_all_files(salescookie_dir)
    
    if combined_df is not None:
        # Save combined file
        output_file = os.path.join(os.path.dirname(__file__), 'all_salescookie_credits.csv')
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\nSaved combined file to: {output_file}")
        
        # Print summary
        logger.info("\n=== SUMMARY ===")
        logger.info(f"Files processed: {len(files_processed)}")
        logger.info(f"Total rows: {len(combined_df)}")
        
        # Transaction type breakdown
        if 'Transaction_Type' in combined_df.columns:
            type_counts = combined_df['Transaction_Type'].value_counts()
            logger.info("\nTransaction Types:")
            for tx_type, count in type_counts.items():
                logger.info(f"  - {tx_type}: {count}")
        
        # Quarter breakdown
        if 'Quarter' in combined_df.columns:
            quarter_counts = combined_df['Quarter'].value_counts().sort_index()
            logger.info("\nQuarters:")
            for quarter, count in quarter_counts.items():
                logger.info(f"  - {quarter}: {count}")
        
        # Commission totals
        if 'Commission_Numeric' in combined_df.columns:
            total_commission = combined_df['Commission_Numeric'].sum()
            logger.info(f"\nTotal Commission: €{total_commission:,.2f}")
            
            if 'Withheld_Amount' in combined_df.columns:
                total_withheld = combined_df['Withheld_Amount'].sum()
                logger.info(f"Total Withheld: €{total_withheld:,.2f}")
    else:
        logger.error("Failed to combine files")
        sys.exit(1)

if __name__ == '__main__':
    main()