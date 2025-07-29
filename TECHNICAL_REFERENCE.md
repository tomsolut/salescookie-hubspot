# Technical Reference - Commission Reconciliation Tool

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI Interface Layer                         │
│                    (reconcile_v2.py)                            │
└─────────────┬───────────────────────────────────┬──────────────┘
              │                                   │
┌─────────────▼─────────────┐       ┌────────────▼──────────────┐
│     Data Input Layer      │       │   Business Logic Layer     │
├───────────────────────────┤       ├────────────────────────────┤
│ • HubSpotParser          │       │ • ReconciliationEngineV2   │
│ • SalesCookieParserV2    │       │ • CommissionConfig         │
│ • DataQualityReport      │       │ • Matching Strategies      │
└─────────────┬─────────────┘       └────────────┬──────────────┘
              │                                   │
              └──────────────┬────────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │    Output Layer           │
              ├───────────────────────────┤
              │ • ReportGenerator         │
              │ • Excel/CSV/Text formats  │
              └───────────────────────────┘
```

## Core Components

### 1. HubSpotParser

**Purpose**: Parse and validate HubSpot deal exports

```python
class HubSpotParser:
    """
    Parses HubSpot CSV exports and extracts Closed & Won deals.
    
    Key responsibilities:
    - CSV loading with encoding detection
    - Deal filtering (Closed & Won only)
    - Data normalization
    - PS deal identification
    - Currency handling
    """
    
    def __init__(self, file_path: str):
        """Initialize with CSV file path"""
        
    def parse(self) -> List[Dict]:
        """
        Parse deals and return normalized format.
        
        Returns:
            List of deal dictionaries with keys:
            - hubspot_id: str
            - deal_name: str
            - close_date: datetime
            - commission_amount: float (EUR)
            - is_ps_deal: bool
            - company: str
            - deal_type: str
        """
        
    def summary(self) -> Dict:
        """Generate summary statistics"""
```

**Key Features**:
- Automatic PS deal detection (prefix "PS @")
- Multi-currency support with EUR conversion
- Date parsing and validation
- Deal type classification

### 2. SalesCookieParserV2

**Purpose**: Dual-mode parser for manual and scraped SalesCookie data

```python
class SalesCookieParserV2:
    """
    Enhanced parser supporting both manual exports and scraped data.
    
    Features:
    - Automatic data source detection
    - Quality assessment and scoring
    - Multiple CSV format support
    - Truncation detection
    """
    
    def parse_file(self, file_path: str, source: DataSource = None) -> Tuple[List[Dict], DataQualityReport]:
        """
        Parse SalesCookie file with quality assessment.
        
        Args:
            file_path: Path to CSV file
            source: Force specific source type (manual/scraped/auto)
            
        Returns:
            Tuple of (transactions, quality_report)
        """
        
    def detect_data_source(self, df: pd.DataFrame, file_path: str) -> DataSource:
        """Automatically detect if data is manual export or scraped"""
        
    def assess_data_quality(self, df: pd.DataFrame, source: DataSource) -> DataQualityReport:
        """
        Assess data quality with scoring.
        
        Quality factors:
        - Unique ID presence (30% weight)
        - Non-truncated names (20% weight)
        - Field completeness (10% per field)
        """
```

**Data Quality Scoring**:
```python
@dataclass
class DataQualityReport:
    source_type: DataSource
    total_records: int
    valid_ids: int
    valid_names: int
    truncated_names: int
    missing_fields: Dict[str, int]
    quality_score: float  # 0-100
    warnings: List[str]
```

### 3. ReconciliationEngineV2

**Purpose**: Core matching and validation engine

```python
class ReconciliationEngineV2:
    """
    Multi-strategy reconciliation engine with CPI handling.
    
    Matching strategies:
    1. ID match (100% confidence)
    2. Name + Date match (95% confidence)
    3. Company + Date match (80% confidence)
    """
    
    def reconcile(self, data_quality_score: float = 100.0) -> ReconciliationResult:
        """
        Run reconciliation process:
        1. Identify centrally processed transactions
        2. Execute matching strategies
        3. Validate commission amounts
        4. Generate discrepancies
        """
        
    def _identify_centrally_processed_transactions(self):
        """
        Identify CPI/Fix deals:
        - Keywords: 'cpi increase', 'fix increase', 'indexation'
        - Exclude from matching requirements
        """
```

**Matching Algorithm**:
```python
def _match_by_id(self):
    """Direct ID matching - O(n) complexity using hash lookup"""
    
def _match_by_name_and_date(self):
    """
    Name + Date matching:
    - Exact name match required
    - Date tolerance: ±1 day
    - Skip already matched deals
    """
    
def _match_by_company_and_date(self):
    """
    Company + Date matching:
    - Normalized company name
    - Date tolerance: ±7 days
    - Amount similarity boosts confidence
    """
```

### 4. CommissionConfig

**Purpose**: Commission rate configuration by year and type

```python
@dataclass
class CommissionPlan:
    commission_rates: Dict[str, float]
    ps_flat_rate: float = 0.01
    effective_date: datetime = None

PLANS = {
    2024: CommissionPlan(
        commission_rates={
            'software': 0.073,
            'managed_services_public': 0.059,
            'managed_services_private': 0.073,
            'professional_services': 0.029,
            'indexations_parameter': 0.088,
        }
    ),
    2025: CommissionPlan(
        commission_rates={
            'software': 0.07,
            'managed_services_public': 0.074,
            'managed_services_private': 0.084,
            'professional_services': 0.031,
            'indexations_parameter': 0.093,
        }
    )
}
```

### 5. ReportGenerator

**Purpose**: Multi-format report generation

```python
class ReportGenerator:
    """
    Generate Excel, CSV, and text reports.
    
    Excel structure:
    - Summary sheet: Statistics and metrics
    - Discrepancies sheet: Detailed issues
    - All Deals sheet: Complete deal list
    """
    
    def generate_excel_report(self, results: Dict, timestamp: datetime) -> str:
        """
        Create multi-sheet Excel workbook.
        Uses openpyxl for formatting and styling.
        """
        
    def generate_text_summary(self, results: Dict, timestamp: datetime) -> str:
        """Human-readable summary with recommendations"""
        
    def generate_discrepancy_csv(self, results: Dict, timestamp: datetime) -> str:
        """CSV export for further analysis"""
```

## Data Models

### Deal Structure

```python
# HubSpot Deal
{
    'hubspot_id': str,              # e.g., '270402053362'
    'deal_name': str,               # e.g., 'Software License@Aktia Bank'
    'close_date': datetime,
    'commission_amount': float,      # EUR normalized
    'original_amount': float,        # Original currency
    'currency': str,                # Original currency code
    'company': str,
    'company_id': str,
    'deal_type': str,               # New Business, Upsell, etc.
    'revenue_start_date': datetime,
    'is_ps_deal': bool,
    'types_of_acv': str,
    'product_name': str,
}

# SalesCookie Transaction
{
    'salescookie_id': str,          # Should match hubspot_id
    'deal_name': str,
    'customer': str,                # Format: 'ID; Company Name'
    'company_id': str,              # Extracted from customer
    'company_name': str,            # Extracted from customer
    'close_date': datetime,
    'revenue_start_date': datetime,
    'commission_amount': float,
    'commission_currency': str,
    'commission_rate': float,       # As decimal (0.073 = 7.3%)
    'commission_details': str,
    'deal_type': str,
    'acv_eur': float,
    'has_split': bool,
    'is_ps_deal': bool,
    'data_source': str,             # 'manual' or 'scraped'
}
```

### Reconciliation Results

```python
@dataclass
class ReconciliationResult:
    matches: List[MatchResult]
    unmatched_hubspot: List[Dict]
    unmatched_salescookie: List[Dict]
    discrepancies: List[Discrepancy]
    summary: Dict
    data_quality_score: float

@dataclass
class MatchResult:
    hubspot_id: str
    salescookie_id: str
    match_type: str              # 'id', 'name_date', 'company_date'
    confidence: float            # 0-100
    hubspot_deal: Dict
    salescookie_transactions: List[Dict]

@dataclass
class Discrepancy:
    deal_id: str
    deal_name: str
    discrepancy_type: str        # 'missing_deal', 'wrong_commission_amount'
    expected_value: str
    actual_value: str
    impact_eur: float
    severity: str                # 'high', 'medium', 'low'
    details: str
    match_confidence: float
    data_source: str
```

## Algorithms

### Company Name Normalization

```python
def _normalize_company(self, company_name: str) -> str:
    """
    Normalize company names for matching:
    1. Convert to lowercase
    2. Remove common suffixes (GmbH, AG, Ltd, etc.)
    3. Remove special characters
    4. Normalize whitespace
    """
    name = company_name.lower().strip()
    
    # Remove legal entity suffixes
    suffixes = [
        r'\s*\(.*\)$',  # Remove parentheses
        r'\s*(gmbh|ag|bank|ltd|limited|plc|s\.a\.|sa).*$',
        r'\s*&\s*co\.?.*$',
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
        
    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)
    name = ' '.join(name.split())
    
    return name
```

### Commission Calculation

```python
def _calculate_expected_commission(self, deal: Dict, year: int) -> float:
    """
    Calculate expected commission:
    
    1. PS deals: flat 1% rate
    2. Other deals: based on type and year
    3. Handle quarter splits if applicable
    """
    base_amount = deal['commission_amount']
    
    if deal.get('is_ps_deal', False):
        return base_amount * 0.01
    else:
        deal_type = self._determine_deal_type(deal)
        rate = self.config.get_commission_rate(year, deal_type, False)
        return base_amount * rate
```

### Data Quality Scoring

```python
def calculate_quality_score(df: pd.DataFrame) -> float:
    """
    Score calculation:
    - Base: 100 points
    - Deduct 30 points for missing IDs
    - Deduct 20 points for truncated names
    - Deduct 10 points per missing critical field
    """
    score = 100.0
    total = len(df)
    
    if total > 0:
        # ID completeness (30% weight)
        id_missing = (total - df['Unique ID'].notna().sum())
        score -= (id_missing / total) * 30
        
        # Name truncation (20% weight)
        truncated = df['Deal Name'].str.endswith('…').sum()
        score -= (truncated / total) * 20
        
        # Field completeness (10% per field)
        critical_fields = ['Customer', 'Close Date', 'Commission']
        for field in critical_fields:
            if field not in df.columns:
                score -= 10
                
    return max(0, score)
```

## Performance Optimization

### Memory Management

```python
# Chunked reading for large files
def read_large_csv(file_path: str, chunk_size: int = 10000):
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        processed_chunk = process_chunk(chunk)
        chunks.append(processed_chunk)
    return pd.concat(chunks, ignore_index=True)
```

### Matching Optimization

```python
# Use hash tables for O(1) lookups
sc_by_id = {deal['salescookie_id']: deal for deal in salescookie_transactions}

# Skip already matched deals
matched_ids = set()
for hs_deal in hubspot_deals:
    if hs_deal['hubspot_id'] in matched_ids:
        continue
```

### Parallel Processing

```python
# For multi-quarter analysis
from concurrent.futures import ProcessPoolExecutor

def process_quarter_parallel(quarter_files: List[str]):
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_single_quarter, quarter_files))
    return combine_results(results)
```

## Error Handling

### Input Validation

```python
def validate_hubspot_csv(df: pd.DataFrame) -> None:
    """Validate required columns exist"""
    required_columns = [
        'Record ID', 'Deal Name', 'Deal Stage',
        'Amount in company currency', 'Close Date'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
```

### Graceful Degradation

```python
def parse_date_safe(date_str: str) -> Optional[datetime]:
    """Try multiple date formats"""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%m/%d/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date: {date_str}")
    return None
```

## Testing

### Unit Test Structure

```python
class TestReconciliation(unittest.TestCase):
    def setUp(self):
        """Create test data"""
        self.test_hubspot_deals = [
            {
                'hubspot_id': '123',
                'deal_name': 'Test Deal',
                'commission_amount': 10000,
                'close_date': datetime(2025, 7, 1),
                'is_ps_deal': False,
            }
        ]
        
    def test_id_matching(self):
        """Test exact ID matching"""
        engine = ReconciliationEngineV2(
            self.test_hubspot_deals,
            self.test_salescookie_transactions
        )
        results = engine.reconcile()
        self.assertEqual(len(results.matches), 1)
        self.assertEqual(results.matches[0].confidence, 100.0)
```

### Integration Testing

```python
def test_end_to_end_workflow():
    """Test complete reconciliation workflow"""
    # Create test files
    create_test_hubspot_csv()
    create_test_salescookie_csv()
    
    # Run reconciliation
    result = subprocess.run([
        'python3', 'reconcile_v2.py',
        '--hubspot-file', 'test_hubspot.csv',
        '--salescookie-file', 'test_salescookie.csv'
    ], capture_output=True)
    
    assert result.returncode == 0
    assert os.path.exists('./reports/')
```

## Configuration

### Environment Variables

```bash
# Optional configuration
export COMMISSION_RECONCILIATION_LOG_LEVEL=DEBUG
export COMMISSION_RECONCILIATION_OUTPUT_DIR=/custom/path
export COMMISSION_RECONCILIATION_DATE_FORMAT="%Y-%m-%d"
```

### Settings File (Optional)

```json
{
  "matching": {
    "id_confidence": 100,
    "name_date_confidence": 95,
    "company_date_confidence": 80,
    "date_tolerance_days": {
      "name_match": 1,
      "company_match": 7
    }
  },
  "quality_thresholds": {
    "excellent": 90,
    "good": 70,
    "poor": 50,
    "critical": 30
  },
  "output": {
    "excel_formatting": true,
    "include_all_deals": true,
    "max_discrepancies_shown": 10
  }
}
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_reconciliation():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run reconciliation
    engine = ReconciliationEngineV2(hubspot_deals, sc_transactions)
    results = engine.reconcile()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_operation():
    # This will show line-by-line memory usage
    large_df = pd.read_csv('large_file.csv')
    processed = process_dataframe(large_df)
    return processed
```

## Security Considerations

### Input Sanitization

```python
def sanitize_file_path(file_path: str) -> str:
    """Prevent path traversal attacks"""
    # Remove any parent directory references
    safe_path = os.path.normpath(file_path)
    if '..' in safe_path:
        raise ValueError("Invalid file path")
    return safe_path
```

### Sensitive Data Handling

```python
# Never log sensitive commission data
logger.info(f"Processing deal {deal_id}")  # Good
logger.info(f"Commission: {amount}")       # Bad

# Mask sensitive information in reports
def mask_deal_name(name: str) -> str:
    """Mask customer name for privacy"""
    if '@' in name:
        parts = name.split('@')
        customer = parts[1]
        masked = customer[:3] + '*' * (len(customer) - 3)
        return f"{parts[0]}@{masked}"
    return name
```

---

*For additional technical details, see the source code documentation and inline comments.*