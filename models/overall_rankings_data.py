"""
Overall Rankings Data Model

This module defines the data structure for overall university rankings
extracted from US News HTML pages.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SubProgramRanking:
    """Data model for sub-program rankings within a main program."""
    
    sub_program_name: str
    rank: Optional[int] = None
    url: Optional[str] = None


@dataclass
class ProgramRanking:
    """Data model for specific program rankings."""
    
    category: str
    rank: Optional[int] = None
    url: Optional[str] = None
    sub_programs: Optional[List[SubProgramRanking]] = None


@dataclass
class OverallRanking:
    """Data model for overall university ranking information."""
    
    # Rankings by category
    rankings: Optional[List[ProgramRanking]] = None
    
    # Metadata
    ranking_year: Optional[str] = None
    ranking_methodology: Optional[str] = None
    
    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = None






@dataclass
class OverallRankingsData:
    """Complete overall rankings data structure."""
    
    university_name: str
    overall_ranking: OverallRanking
    
    # Additional information
    ranking_history: Optional[List[Dict[str, Any]]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'university_name': self.university_name,
            'rankings': {}
        }
        
        # Check if we have flat rankings data stored in overall_ranking.rankings
        if hasattr(self.overall_ranking, 'rankings') and isinstance(self.overall_ranking.rankings, dict):
            # Flat structure - use directly
            result['rankings'] = self.overall_ranking.rankings
        elif self.overall_ranking and self.overall_ranking.rankings:
            # Nested structure - convert to flat
            for pr in self.overall_ranking.rankings:
                category_key = self._sanitize_key(pr.category)
                result['rankings'][category_key] = pr.rank
                
                # Add sub_programs if they exist
                if pr.sub_programs:
                    for sp in pr.sub_programs:
                        sub_key = f"{category_key}/{self._sanitize_key(sp.sub_program_name)}"
                        result['rankings'][sub_key] = sp.rank
        
        return result
    
    def _sanitize_key(self, text: str) -> str:
        """Convert text to a valid dictionary key."""
        import re
        # Convert to lowercase, replace spaces and special chars with underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '_', text.lower())
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key
