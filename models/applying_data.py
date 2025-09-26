"""
Applying Data Model

This module defines the data structure for university applying/admissions information
extracted from US News applying pages.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TestScores:
    """Test score requirements and ranges."""
    sat_range: Optional[str] = None
    act_range: Optional[str] = None
    sat_math_range: Optional[str] = None
    sat_reading_range: Optional[str] = None
    act_english_range: Optional[str] = None
    act_math_range: Optional[str] = None
    act_writing_range: Optional[str] = None


@dataclass
class ApplicationInfo:
    """Application deadlines and requirements."""
    application_deadline: Optional[str] = None
    early_decision_deadline: Optional[str] = None
    early_action_deadline: Optional[str] = None
    regular_decision_deadline: Optional[str] = None
    application_fee: Optional[str] = None
    application_fee_waiver: Optional[str] = None


@dataclass
class AdmissionStats:
    """Admission statistics."""
    acceptance_rate: Optional[str] = None
    early_acceptance_rate: Optional[str] = None
    total_applicants: Optional[str] = None
    total_admitted: Optional[str] = None
    total_enrolled: Optional[str] = None
    yield_rate: Optional[str] = None


@dataclass
class AcademicRequirements:
    """Academic requirements and factors."""
    gpa_requirement: Optional[str] = None
    gpa_importance: Optional[str] = None
    class_rank_importance: Optional[str] = None
    letters_of_recommendation: Optional[str] = None
    essay_requirement: Optional[str] = None
    interview_requirement: Optional[str] = None


@dataclass
class ApplyingData:
    """Complete applying/admissions data for a university."""
    university_name: str
    currency: str = "USD"
    
    # All applying data in a single dictionary (like paying page)
    applying: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.applying is None:
            self.applying = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "university_name": self.university_name,
            "currency": self.currency,
            "applying": self.applying
        }
