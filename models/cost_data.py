"""
Cost/Paying Data Model

This module defines the data structure for university cost and paying information
extracted from US News paying pages.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class CostMetrics:
    """Data model for cost metrics - flexible dictionary-based approach."""
    
    # Store all cost metrics as a flexible dictionary
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a cost metric value by key."""
        return self.metrics.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a cost metric value by key."""
        self.metrics[key] = value
    
    def has(self, key: str) -> bool:
        """Check if a cost metric exists."""
        return key in self.metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, only including non-None values."""
        return {k: v for k, v in self.metrics.items() if v is not None}


@dataclass
class FinancialAidInfo:
    """Data model for financial aid information."""
    
    # Financial aid metrics
    aid_metrics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.aid_metrics is None:
            self.aid_metrics = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a financial aid metric value by key."""
        return self.aid_metrics.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a financial aid metric value by key."""
        self.aid_metrics[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, only including non-None values."""
        return {k: v for k, v in self.aid_metrics.items() if v is not None}


@dataclass
class CostData:
    """Complete cost/paying data structure."""
    
    university_name: str
    paying: Optional[Dict[str, Any]] = None
    
    # Additional information
    cost_year: Optional[str] = None
    currency: str = "USD"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'university_name': self.university_name,
            'currency': self.currency
        }
        
        # Add all paying data in a single section
        if self.paying:
            result['paying'] = self.paying
        
        return result
