"""
Overperformance Kicker Calculator for Commission Reconciliation
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class QuotaProgress:
    """Track quota progress for kicker calculations"""
    year: int
    quarter: str
    total_acv: float
    quota_target: float
    achievement_percentage: float
    applicable_kicker: Optional[str] = None
    kicker_multiplier: float = 1.0

class KickerCalculator:
    """Calculate overperformance kickers based on quota achievement"""
    
    def __init__(self, commission_config):
        self.config = commission_config
        self.deals_by_quarter = {}
        self.quota_progress = {}
        
    def add_deal(self, deal: Dict) -> None:
        """Add a deal to track for quota calculation"""
        if not deal.get('close_date'):
            return
            
        quarter = self.config.get_quarter_from_date(deal['close_date'])
        year = deal['close_date'].year
        
        if quarter not in self.deals_by_quarter:
            self.deals_by_quarter[quarter] = []
            
        self.deals_by_quarter[quarter].append(deal)
        
    def calculate_quota_progress(self, quarter: str) -> QuotaProgress:
        """Calculate quota achievement for a specific quarter"""
        if quarter not in self.deals_by_quarter:
            return None
            
        # Extract year from quarter string (e.g., "Q1_2025" -> 2025)
        year = int(quarter.split('_')[1])
        
        # Get plan for the year
        plan = self.config.PLANS.get(year)
        if not plan:
            logger.warning(f"No commission plan found for year {year}")
            return None
            
        # Calculate total ACV for the quarter
        total_acv = sum(deal.get('commission_amount', 0) for deal in self.deals_by_quarter[quarter])
        
        # Quarterly quota is annual quota divided by 4
        quarterly_quota = plan.quota_target / 4
        
        # Calculate achievement percentage
        achievement = (total_acv / quarterly_quota * 100) if quarterly_quota > 0 else 0
        
        # Determine applicable kicker
        kicker_name, kicker_multiplier = self._get_applicable_kicker(year, quarter, achievement)
        
        return QuotaProgress(
            year=year,
            quarter=quarter,
            total_acv=total_acv,
            quota_target=quarterly_quota,
            achievement_percentage=achievement,
            applicable_kicker=kicker_name,
            kicker_multiplier=kicker_multiplier
        )
        
    def _get_applicable_kicker(self, year: int, quarter: str, achievement: float) -> Tuple[Optional[str], float]:
        """Determine which kicker applies based on achievement"""
        plan = self.config.PLANS.get(year)
        if not plan:
            return None, 1.0
            
        # Check for early bird kicker (Q1 2025 only)
        if year == 2025 and quarter == "Q1_2025":
            return 'earlybird', plan.kickers.get('earlybird', 1.2)
            
        # Check overperformance kickers based on achievement
        if year == 2024:
            if achievement >= 200:
                return 'overperformance_200', plan.kickers.get('overperformance_200', 2.0)
            elif achievement >= 120:
                return 'overperformance_120', plan.kickers.get('overperformance_120', 1.2)
        elif year == 2025:
            if achievement >= 200:
                return 'overperformance_200', plan.kickers.get('overperformance_200', 1.5)
            elif achievement >= 180:
                return 'overperformance_180', plan.kickers.get('overperformance_180', 1.4)
            elif achievement >= 160:
                return 'overperformance_160', plan.kickers.get('overperformance_160', 1.3)
            elif achievement >= 130:
                return 'overperformance_130', plan.kickers.get('overperformance_130', 1.2)
            elif achievement >= 100:
                return 'overperformance_100', plan.kickers.get('overperformance_100', 1.1)
                
        return None, 1.0
        
    def calculate_commission_with_kicker(self, base_commission: float, deal: Dict) -> Dict[str, float]:
        """Calculate commission including applicable kickers"""
        if not deal.get('close_date'):
            return {
                'base_commission': base_commission,
                'kicker_amount': 0,
                'total_commission': base_commission,
                'kicker_type': None,
                'kicker_multiplier': 1.0
            }
            
        quarter = self.config.get_quarter_from_date(deal['close_date'])
        quota_progress = self.calculate_quota_progress(quarter)
        
        if not quota_progress or not quota_progress.applicable_kicker:
            return {
                'base_commission': base_commission,
                'kicker_amount': 0,
                'total_commission': base_commission,
                'kicker_type': None,
                'kicker_multiplier': 1.0
            }
            
        # Calculate kicker amount
        kicker_amount = base_commission * (quota_progress.kicker_multiplier - 1)
        
        return {
            'base_commission': base_commission,
            'kicker_amount': kicker_amount,
            'total_commission': base_commission + kicker_amount,
            'kicker_type': quota_progress.applicable_kicker,
            'kicker_multiplier': quota_progress.kicker_multiplier,
            'achievement_percentage': quota_progress.achievement_percentage
        }
        
    def get_quarterly_summary(self) -> Dict[str, QuotaProgress]:
        """Get quota progress for all quarters"""
        summary = {}
        
        for quarter in self.deals_by_quarter:
            progress = self.calculate_quota_progress(quarter)
            if progress:
                summary[quarter] = progress
                
        return summary