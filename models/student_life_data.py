"""
Student Life Data Model

This module defines the data structure for university student life information
extracted from US News student-life pages.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class StudentLifeData:
    """Complete student life data structure."""
    
    university_name: str
    student_life: Optional[Dict[str, Any]] = None
    
    # Additional information
    data_year: Optional[str] = None
    source: str = "US News"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'university_name': self.university_name,
            'source': self.source
        }
        
        # Add all student life data in a single section
        if self.student_life:
            result['student_life'] = self.student_life
        
        return result
