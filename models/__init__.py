"""
Models package for university data structures.
"""

from .overall_rankings_data import OverallRankingsData, OverallRanking, ProgramRanking, SubProgramRanking
from .cost_data import CostData, CostMetrics, FinancialAidInfo

__all__ = [
    'OverallRankingsData',
    'OverallRanking',
    'ProgramRanking',
    'SubProgramRanking',
    'CostData',
    'CostMetrics',
    'FinancialAidInfo'
]
