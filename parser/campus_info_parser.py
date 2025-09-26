"""
Campus Info Parser

This module parses HTML content from US News campus-info pages
and extracts structured campus information data.
"""

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from models.campus_info_data import CampusInfoData
from parser.base_parser import BaseParser


class CampusInfoParser(BaseParser):
    """Parser for university campus information HTML pages."""
    
    def parse(self, html_content: str, university_name: str) -> Optional[CampusInfoData]:
        """
        Parse HTML content and extract campus info data.
        
        Args:
            html_content: Raw HTML content from the campus-info page
            university_name: Name of the university
            
        Returns:
            CampusInfoData object or None if parsing fails
        """
        return super().parse(html_content, university_name, "campus_info", CampusInfoData)
    
    def _extract_all_campus_info_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract all campus information data from the HTML soup.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            Dictionary containing all campus info data
        """
        campus_data = {}
        
        # Extract data using data-test-id attributes (primary method)
        campus_data.update(self._extract_data_by_test_id(soup))
        
        # Extract additional DataRow data
        campus_data.update(self._extract_datarow_data(soup))
        
        # Extract campus overview information
        campus_data.update(self._extract_campus_overview(soup))
        
        # Extract campus facilities
        campus_data.update(self._extract_campus_facilities(soup))
        
        # Extract campus location and transportation
        campus_data.update(self._extract_campus_location(soup))
        
        # Extract campus housing information
        campus_data.update(self._extract_campus_housing(soup))
        
        # Extract campus dining information
        campus_data.update(self._extract_campus_dining(soup))
        
        # Extract campus safety information
        campus_data.update(self._extract_campus_safety(soup))
        
        # Extract any additional campus information
        campus_data.update(self._extract_additional_campus_info(soup))
        
        return campus_data
    
    # _extract_data_by_test_id 메서드는 BaseParser에서 상속받아 사용
    
    def _extract_group_section_data(self, soup: BeautifulSoup, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from group-section-box elements, avoiding duplicates with existing data."""
        group_data = {}
        
        # Create a set of existing label-value combinations for quick lookup
        existing_combinations = set()
        for key, value in existing_data.items():
            if isinstance(value, list):
                existing_combinations.add(tuple(sorted(value)))
            else:
                existing_combinations.add(str(value).strip().lower())
        
        # Find all group-section-box elements
        group_sections = soup.find_all('div', class_='group-section-box')
        
        for section in group_sections:
            # Get section title
            section_title = section.find('h4')
            if section_title:
                title_text = section_title.get_text(strip=True)
                
                # Find all DataRow elements within this section
                data_rows = section.find_all('div', class_=re.compile(r'DataRow', re.I))
                
                for row in data_rows:
                    # Look for label and value
                    label_elem = row.find('p', class_=re.compile(r'Paragraph', re.I))
                    
                    if label_elem:
                        label = label_elem.get_text(strip=True)
                        
                        # Check for list items first
                        list_items = row.find_all('li')
                        if list_items:
                            items = []
                            for item in list_items:
                                item_text = item.get_text(strip=True)
                                if item_text:
                                    items.append(item_text)
                            
                            if items:
                                # Check if this list content already exists
                                normalized_list = tuple(sorted(items))
                                if normalized_list not in existing_combinations:
                                    key = self._sanitize_key(f"{title_text}_{label}")
                                    group_data[key] = items
                                    existing_combinations.add(normalized_list)
                        else:
                            # Look for value in paragraph with iKkzvP class
                            value_elem = row.find('p', class_=re.compile(r'iKkzvP', re.I))
                            if value_elem:
                                value = value_elem.get_text(strip=True)
                                if value and value != label:
                                    # Check if this value already exists
                                    normalized_value = str(value).strip().lower()
                                    if normalized_value not in existing_combinations:
                                        key = self._sanitize_key(f"{title_text}_{label}")
                                        group_data[key] = value
                                        existing_combinations.add(normalized_value)
        
        return group_data
    
    def _map_test_id_to_field_name(self, test_id: str) -> str:
        """Map data-test-id values to meaningful field names."""
        mapping = {
            'env_cam_size': 'campus_size_acres',
            'reg_alc_perm_yesno': 'alcohol_permitted',
            'CAMPUS_CARRY_POLICY': 'firearm_campus_carry_policy',
            # Add more mappings as needed
        }
        return mapping.get(test_id, test_id)
    
    def _sanitize_key(self, text: str) -> str:
        """Convert text to a valid dictionary key."""
        # Convert to lowercase, replace spaces and special chars with underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '_', text.lower())
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key
    
    def _extract_campus_overview(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus overview information."""
        overview = {}
        
        # Look for campus overview sections
        overview_sections = soup.find_all(['div', 'section'], class_=re.compile(r'overview|campus.*overview', re.I))
        
        for section in overview_sections:
            # Extract text content
            text_content = section.get_text(strip=True)
            if text_content:
                overview['overview_text'] = text_content
            
            # Look for specific metrics or stats
            stats = section.find_all(['span', 'div'], class_=re.compile(r'stat|metric|number', re.I))
            for stat in stats:
                stat_text = stat.get_text(strip=True)
                if stat_text and any(char.isdigit() for char in stat_text):
                    overview['campus_stats'] = overview.get('campus_stats', [])
                    overview['campus_stats'].append(stat_text)
        
        return overview
    
    def _extract_campus_facilities(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus facilities information."""
        facilities = {}
        
        # Look for facilities sections
        facilities_sections = soup.find_all(['div', 'section'], class_=re.compile(r'facilities|amenities|campus.*facilities', re.I))
        
        for section in facilities_sections:
            # Extract facility lists
            facility_lists = section.find_all(['ul', 'ol'])
            for facility_list in facility_lists:
                facilities_items = []
                for item in facility_list.find_all('li'):
                    item_text = item.get_text(strip=True)
                    if item_text:
                        facilities_items.append(item_text)
                
                if facilities_items:
                    facilities['facilities_list'] = facilities_items
            
            # Extract facility descriptions
            facility_text = section.get_text(strip=True)
            if facility_text and len(facility_text) > 50:  # Only meaningful text
                facilities['facilities_description'] = facility_text
        
        return facilities
    
    def _extract_campus_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus location and transportation information."""
        location = {}
        
        # Look for location sections
        location_sections = soup.find_all(['div', 'section'], class_=re.compile(r'location|transportation|address', re.I))
        
        for section in location_sections:
            # Extract address information
            address_elements = section.find_all(['p', 'div'], class_=re.compile(r'address|location', re.I))
            for element in address_elements:
                address_text = element.get_text(strip=True)
                if address_text and any(char.isdigit() for char in address_text):
                    location['address'] = address_text
            
            # Extract transportation information
            transport_elements = section.find_all(['p', 'div'], class_=re.compile(r'transport|bus|train|airport', re.I))
            for element in transport_elements:
                transport_text = element.get_text(strip=True)
                if transport_text:
                    location['transportation'] = location.get('transportation', [])
                    location['transportation'].append(transport_text)
        
        return location
    
    def _extract_campus_housing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus housing information."""
        housing = {}
        
        # Look for housing sections
        housing_sections = soup.find_all(['div', 'section'], class_=re.compile(r'housing|dormitory|residence', re.I))
        
        for section in housing_sections:
            # Extract housing statistics
            housing_stats = section.find_all(['span', 'div'], class_=re.compile(r'stat|metric|number', re.I))
            for stat in housing_stats:
                stat_text = stat.get_text(strip=True)
                if stat_text and any(char.isdigit() for char in stat_text):
                    housing['housing_stats'] = housing.get('housing_stats', [])
                    housing['housing_stats'].append(stat_text)
            
            # Extract housing descriptions
            housing_text = section.get_text(strip=True)
            if housing_text and len(housing_text) > 50:
                housing['housing_description'] = housing_text
        
        return housing
    
    def _extract_campus_dining(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus dining information."""
        dining = {}
        
        # Look for dining sections
        dining_sections = soup.find_all(['div', 'section'], class_=re.compile(r'dining|food|cafeteria', re.I))
        
        for section in dining_sections:
            # Extract dining options
            dining_lists = section.find_all(['ul', 'ol'])
            for dining_list in dining_lists:
                dining_items = []
                for item in dining_list.find_all('li'):
                    item_text = item.get_text(strip=True)
                    if item_text:
                        dining_items.append(item_text)
                
                if dining_items:
                    dining['dining_options'] = dining_items
            
            # Extract dining descriptions
            dining_text = section.get_text(strip=True)
            if dining_text and len(dining_text) > 50:
                dining['dining_description'] = dining_text
        
        return dining
    
    def _extract_campus_safety(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract campus safety information."""
        safety = {}
        
        # Look for safety sections
        safety_sections = soup.find_all(['div', 'section'], class_=re.compile(r'safety|security|crime', re.I))
        
        for section in safety_sections:
            # Extract safety statistics
            safety_stats = section.find_all(['span', 'div'], class_=re.compile(r'stat|metric|number', re.I))
            for stat in safety_stats:
                stat_text = stat.get_text(strip=True)
                if stat_text and any(char.isdigit() for char in stat_text):
                    safety['safety_stats'] = safety.get('safety_stats', [])
                    safety['safety_stats'].append(stat_text)
            
            # Extract safety descriptions
            safety_text = section.get_text(strip=True)
            if safety_text and len(safety_text) > 50:
                safety['safety_description'] = safety_text
        
        return safety
    
    def _extract_additional_campus_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract any additional campus information not covered above."""
        additional = {}
        
        # Look for any remaining campus-related sections
        campus_sections = soup.find_all(['div', 'section'], class_=re.compile(r'campus|college.*info', re.I))
        
        for section in campus_sections:
            # Skip if already processed
            if any(keyword in section.get('class', []) for keyword in ['overview', 'facilities', 'location', 'housing', 'dining', 'safety']):
                continue
            
            # Extract general campus information
            campus_text = section.get_text(strip=True)
            if campus_text and len(campus_text) > 50:
                additional['additional_info'] = additional.get('additional_info', [])
                additional['additional_info'].append(campus_text)
        
        return additional
