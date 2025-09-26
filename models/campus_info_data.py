"""
Campus Info Data Model

This module defines the data structure for university campus information
extracted from US News campus-info pages.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CampusInfoData:
    """Complete campus info data structure."""
    
    university_name: str
    campus_info: Optional[Dict[str, Any]] = None
    
    # Additional information
    data_year: Optional[str] = None
    source: str = "US News"
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.campus_info is None:
            self.campus_info = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'university_name': self.university_name,
            'source': self.source
        }
        
        # Add all campus info data in a single section
        if self.campus_info:
            result['campus_info'] = self.campus_info
        
        return result
