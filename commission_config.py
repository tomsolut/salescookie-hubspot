"""
Commission Configuration based on Thomas Bieth's commission plans
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import date

@dataclass
class CommissionPlan:
    year: int
    quota_target: float
    commission_rates: Dict[str, float]
    quota_factors: Dict[float, float]
    kickers: Dict[str, float]
    ps_flat_rate: float = 0.01  # 1% for Professional Services
    
class CommissionConfig:
    """Commission configuration for Thomas Bieth"""
    
    PLANS = {
        2023: CommissionPlan(
            year=2023,
            quota_target=1_500_000,  # Using 2024 values as default
            commission_rates={
                'software': 0.073,  # 7.3%
                'managed_services_public': 0.059,  # 5.9%
                'managed_services_private': 0.044,  # 4.4%
                'recurring_professional_services': 0.029,  # 2.9%
                'indexations_parameter': 0.044,  # 4.4%
                'churn': 0.044,  # 4.4%
            },
            quota_factors={
                1.00: 0.073,
                0.80: 0.059,
                0.60: 0.044,
                0.40: 0.029,
            },
            kickers={
                'overperformance_120': 1.2,
                'overperformance_200': 2.0,
            }
        ),
        2024: CommissionPlan(
            year=2024,
            quota_target=1_500_000,
            commission_rates={
                'software': 0.073,  # 7.3%
                'managed_services_public': 0.059,  # 5.9%
                'managed_services_private': 0.073,  # 7.3% (corrected from 4.4%)
                'recurring_professional_services': 0.029,  # 2.9%
                'indexations_parameter': 0.088,  # 8.8% (corrected from 4.4%)
                'churn': 0.044,  # 4.4%
            },
            quota_factors={
                1.00: 0.073,
                0.80: 0.059,
                0.60: 0.044,
                0.40: 0.029,
            },
            kickers={
                'overperformance_120': 1.2,  # 120-200% achievement
                'overperformance_200': 2.0,  # >200% achievement
            }
        ),
        2025: CommissionPlan(
            year=2025,
            quota_target=1_700_000,
            commission_rates={
                'software': 0.07,  # 7%
                'managed_services_public': 0.074,  # 7.4%
                'managed_services_private': 0.084,  # 8.4% (corrected from 7.4%)
                'recurring_professional_services': 0.031,  # 3.1% (corrected from 7.4%)
                'indexations_parameter': 0.093,  # 9.3% (corrected from 4.4%)
                'churn': 0.044,  # 4.4%
            },
            quota_factors={
                1.00: 0.07,  # Base rate varies by type
            },
            kickers={
                'overperformance_100': 1.1,  # 100-130% achievement
                'overperformance_130': 1.2,  # 130-160% achievement
                'overperformance_160': 1.3,  # 160-180% achievement
                'overperformance_180': 1.4,  # 180-200% achievement
                'overperformance_200': 1.5,  # >200% achievement
                'earlybird': 1.2,  # Q1 2025 deals
            }
        )
    }
    
    # Quarter split rules
    QUARTER_SPLIT = {
        'close_quarter': 0.5,  # 50% in closing quarter
        'service_start_quarter': 0.5,  # 50% in service start quarter
    }
    
    # Deal type mappings
    DEAL_TYPE_MAPPING = {
        'software': ['software', 'sw'],
        'managed_services': ['managed services', 'managed software', 'ms'],
        'professional_services': ['professional services', 'ps', 'abp'],
        'indexations': ['indexations', 'parameter', 'balance sheet'],
        'churn': ['churn'],
    }
    
    @classmethod
    def get_commission_rate(cls, year: int, deal_type: str, is_ps: bool = False) -> float:
        """Get commission rate for a specific deal type and year"""
        if is_ps:
            return cls.PLANS[year].ps_flat_rate
            
        plan = cls.PLANS.get(year)
        if not plan:
            raise ValueError(f"No commission plan found for year {year}")
            
        # Normalize deal type
        normalized_type = cls._normalize_deal_type(deal_type)
        
        # Get rate from plan
        rate = plan.commission_rates.get(normalized_type, 0.0)
        return rate
    
    @classmethod
    def _normalize_deal_type(cls, deal_type: str) -> str:
        """Normalize deal type to match commission plan categories"""
        deal_type_lower = deal_type.lower()
        
        # Check mappings
        for category, keywords in cls.DEAL_TYPE_MAPPING.items():
            if any(keyword in deal_type_lower for keyword in keywords):
                if category == 'managed_services':
                    # Determine public vs private cloud
                    if 'public' in deal_type_lower or 'rcloud' in deal_type_lower:
                        return 'managed_services_public'
                    else:
                        return 'managed_services_private'
                elif category == 'professional_services':
                    return 'recurring_professional_services'
                elif category == 'indexations':
                    return 'indexations_parameter'
                else:
                    return category
                    
        # Default to software if no match
        return 'software'
    
    @classmethod
    def get_quarter_from_date(cls, date_obj: date) -> str:
        """Get quarter string from date"""
        month = date_obj.month
        year = date_obj.year
        
        if month <= 3:
            return f"Q1_{year}"
        elif month <= 6:
            return f"Q2_{year}"
        elif month <= 9:
            return f"Q3_{year}"
        else:
            return f"Q4_{year}"
    
    @classmethod
    def calculate_split_quarters(cls, close_date: date, service_start_date: Optional[date] = None) -> Dict[str, float]:
        """Calculate commission split between quarters"""
        close_quarter = cls.get_quarter_from_date(close_date)
        
        if service_start_date:
            service_quarter = cls.get_quarter_from_date(service_start_date)
        else:
            # If no service start date, assume same quarter
            service_quarter = close_quarter
            
        if close_quarter == service_quarter:
            # All commission in same quarter
            return {close_quarter: 1.0}
        else:
            # Split 50/50
            return {
                close_quarter: cls.QUARTER_SPLIT['close_quarter'],
                service_quarter: cls.QUARTER_SPLIT['service_start_quarter']
            }