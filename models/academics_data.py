"""
Academics Data Model

This module defines the data structure for university academics information
extracted from US News academics pages.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AcademicsData:
    """Complete academics data for a university."""
    university_name: str
    currency: str = "USD"
    
    # All academics data in a single dictionary (like paying and applying pages)
    academics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.academics is None:
            self.academics = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "university_name": self.university_name,
            "currency": self.currency,
            "academics": self.academics
        }
