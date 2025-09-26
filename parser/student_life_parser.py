"""
Student Life Parser

This module parses HTML content from US News student-life pages
and extracts structured student life data.
"""

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from models.student_life_data import StudentLifeData
from parser.base_parser import BaseParser


class StudentLifeParser(BaseParser):
    """Parser for university student life information HTML pages."""
    
    def parse(self, html_content: str, university_name: str) -> Optional[StudentLifeData]:
        """
        Parse HTML content and extract student life data.
        
        Args:
            html_content: Raw HTML content from the student-life page
            university_name: Name of the university
            
        Returns:
            StudentLifeData object or None if parsing fails
        """
        return super().parse(html_content, university_name, "student_life", StudentLifeData)
    
    def _extract_all_student_life_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all student life data into a single dictionary using flexible HTML parsing."""
        
        student_life_data = {}
        
        # 1. Extract DataRow elements with data-test-id attributes (most reliable)
        datarow_data = self._extract_datarow_data(soup)
        if datarow_data:
            student_life_data.update(datarow_data)
        
        # 2. Extract TruncatedList demographic data
        demographic_data = self._extract_demographic_data(soup)
        if demographic_data:
            student_life_data.update(demographic_data)
        
        # 3. Extract QuickStat data (like total enrollment, live on-campus, etc.)
        quickstat_data = self._extract_quickstat_data(soup)
        if quickstat_data:
            student_life_data.update(quickstat_data)
        
        # 4. Extract general descriptive text
        description_data = self._extract_description_data(soup)
        if description_data:
            student_life_data.update(description_data)
        
        # 5. Extract any other structured data
        structured_data = self._extract_structured_data(soup)
        if structured_data:
            student_life_data.update(structured_data)
        
        # 6. Parse and structure sports data
        sports_data = self._parse_sports_data(student_life_data)
        if sports_data:
            # Remove raw sports data and add structured version
            for key in ['v_ncaa_sports', 'v_club_sports', 'v_intr_sports']:
                if key in student_life_data:
                    del student_life_data[key]
            student_life_data.update(sports_data)
        
        return student_life_data
    
    # _extract_datarow_data 메서드는 BaseParser에서 상속받아 사용
    
    def _extract_demographic_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract demographic data from TruncatedList structures."""
        print("DEBUG: _extract_demographic_data called")
        demographic_data = {}
        
        # Find TruncatedList containers
        truncated_lists = soup.find_all('div', class_=lambda x: x and 'TruncatedList' in x)
        print(f"DEBUG: Found {len(truncated_lists)} TruncatedList containers")
        
        # Track processed sections to avoid duplicates
        processed_sections = set()
        
        for list_container in truncated_lists:
            # Find the section header (h4) that precedes this list
            section_header = list_container.find_previous('h4')
            if section_header:
                section_name = section_header.get_text().strip()
                section_key = f"demographics_{self._sanitize_key(section_name)}"
                
                # Skip if we've already processed this section
                if section_key in processed_sections:
                    continue
                    
                processed_sections.add(section_key)
                print(f"Found demographic section: {section_name}")
                
                # Extract all list items from both top and bottom lists
                list_items = list_container.find_all('li', class_=lambda x: x and 'ListItem' in x)
                print(f"Found {len(list_items)} demographic items")
                
                # Check if this is a simple list (like student activities) or label-value pairs
                if list_items:
                    first_item = list_items[0]
                    paragraphs = first_item.find_all('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                    
                    if len(paragraphs) >= 2:
                        # This is label-value pairs (demographics)
                        for item in list_items:
                            paragraphs = item.find_all('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                            
                            if len(paragraphs) >= 2:
                                label = paragraphs[0].get_text().strip()
                                value = paragraphs[1].get_text().strip()
                                
                                if label and value:
                                    normalized_label = self._sanitize_key(label)
                                    key = f"{section_key}/{normalized_label}"
                                    demographic_data[key] = value
                                    print(f"Added demographic data: {key} = {value}")
                    else:
                        # This is a simple list (like student activities)
                        activities = []
                        
                        # Extract from both TopList and BottomList
                        top_list = list_container.find('ul', class_=lambda x: x and 'TopList' in x)
                        bottom_list_wrapper = list_container.find('div', class_=lambda x: x and 'BottomListWrapper' in x)
                        bottom_list = None
                        if bottom_list_wrapper:
                            bottom_list = bottom_list_wrapper.find('ul')
                        
                        # Extract from TopList first
                        if top_list:
                            top_items = top_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                            for item in top_items:
                                span = item.find('span')
                                if span:
                                    activity = span.get_text().strip()
                                else:
                                    activity = item.get_text().strip()
                                
                                if activity:
                                    activities.append(activity)
                                    print(f"Added top activity: {activity}")
                        
                        # Extract from BottomList second
                        if bottom_list:
                            bottom_items = bottom_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                            for item in bottom_items:
                                span = item.find('span')
                                if span:
                                    activity = span.get_text().strip()
                                else:
                                    activity = item.get_text().strip()
                                
                                if activity:
                                    activities.append(activity)
                                    print(f"Added bottom activity: {activity}")
                        
                        # Fallback: extract from all list items if the above doesn't work
                        if not activities:
                            for item in list_items:
                                span = item.find('span')
                                if span:
                                    activity = span.get_text().strip()
                                else:
                                    activity = item.get_text().strip()
                                
                                if activity:
                                    activities.append(activity)
                                    print(f"Added fallback activity: {activity}")
                        
                        if activities:
                            key = f"{section_key}/activities_list"
                            demographic_data[key] = activities
                            print(f"Added activities list: {key} = {len(activities)} activities")
        
        return demographic_data
    
    def _parse_sports_data(self, student_life_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure sports data from raw strings."""
        print("DEBUG: _parse_sports_data called")
        sports_data = {}
        
        # Parse NCAA sports
        if 'v_ncaa_sports' in student_life_data:
            ncaa_sports = self._parse_sports_string(student_life_data['v_ncaa_sports'])
            if ncaa_sports:
                sports_data['ncaa_sports'] = ncaa_sports
                print(f"Parsed {len(ncaa_sports)} NCAA sports")
        
        # Parse Club sports
        if 'v_club_sports' in student_life_data:
            club_sports = self._parse_sports_string(student_life_data['v_club_sports'])
            if club_sports:
                sports_data['club_sports'] = club_sports
                print(f"Parsed {len(club_sports)} club sports")
        
        # Parse Intramural sports
        if 'v_intr_sports' in student_life_data:
            intramural_sports = self._parse_sports_string(student_life_data['v_intr_sports'])
            if intramural_sports:
                sports_data['intramural_sports'] = intramural_sports
                print(f"Parsed {len(intramural_sports)} intramural sports")
        
        return sports_data
    
    def _parse_sports_string(self, sports_string: str) -> Dict[str, Dict[str, str]]:
        """Parse a sports string into structured data."""
        if not sports_string or sports_string == "N/A":
            return {}
        
        # Remove repeated headers like "Sports Men's Women's"
        cleaned_string = sports_string
        cleaned_string = re.sub(r'Sports\s+Men\'s\s+Women\'s', '', cleaned_string)
        cleaned_string = re.sub(r'^Sports\s+Men\'s\s+Women\'s', '', cleaned_string)
        
        # Split by sport names (capitalized words followed by data)
        sports = {}
        
        # Common sport names to look for
        sport_names = [
            'Baseball', 'Basketball', 'Crew (heavyweight)', 'Crew (lightweight)', 
            'Cross country', 'Fencing', 'Field hockey', 'Football', 'Golf', 
            'Ice hockey', 'Lacrosse', 'Rugby', 'Skiing (alpine)', 'Skiing (nordic)',
            'Soccer', 'Softball', 'Squash', 'Swimming', 'Tennis', 
            'Track and field (indoor)', 'Track and field (outdoor)', 
            'Volleyball', 'Water polo', 'Wrestling', 'Archery', 'Badminton',
            'Bowling', 'Cheerleading', 'Curling', 'Figure skating', 'Gymnastics',
            'Martial arts', 'Team handball', 'Ultimate frisbee'
        ]
        
        for sport in sport_names:
            # Look for sport name followed by Yes/No for Men's and Women's
            pattern = rf'{re.escape(sport)}\s+(Yes|No)\s+(Yes|No)'
            match = re.search(pattern, cleaned_string)
            
            if match:
                mens_team = match.group(1)
                womens_team = match.group(2)
                
                sports[sport] = {
                    'mens_team': mens_team,
                    'womens_team': womens_team
                }
                print(f"Parsed sport: {sport} - Men's: {mens_team}, Women's: {womens_team}")
        
        return sports
    
    def _extract_quickstat_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from QuickStat boxes."""
        print("DEBUG: _extract_quickstat_data called")
        quickstat_data = {}
        
        # Find all QuickStat containers
        quickstat_containers = soup.find_all('div', class_=lambda x: x and 'QuickStat__Container' in x)
        print(f"DEBUG: Found {len(quickstat_containers)} QuickStat containers")
        
        for container in quickstat_containers:
            # Find the dt (definition term) and dd (definition description)
            dt = container.find('dt')
            dd = container.find('dd')
            
            if dt and dd:
                label = dt.get_text().strip()
                value_elem = dd.find(class_=lambda x: x and 'QuickStat__Description' in x)
                
                if value_elem:
                    value = value_elem.get_text().strip()
                    
                    # Also look for subtext (like "(fall 2024)")
                    subtext_elem = dd.find(class_=lambda x: x and 'QuickStat__Subtext' in x)
                    if subtext_elem:
                        subtext = subtext_elem.get_text().strip()
                        value = f"{value} {subtext}"
                    
                    if label and value:
                        normalized_label = self._sanitize_key(label)
                        quickstat_data[normalized_label] = value
                        print(f"Added QuickStat: {normalized_label} = {value}")
        
        return quickstat_data
    
    def _extract_description_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract general descriptive text about student life."""
        print("DEBUG: _extract_description_data called")
        description_data = {}
        
        # Look for paragraphs that contain student life information
        paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 50:  # Only longer descriptive text
                # Check if this paragraph contains student life information
                if any(keyword in text.lower() for keyword in ['student', 'campus', 'housing', 'sports', 'gender', 'enrollment']):
                    # Extract key information using regex patterns
                    extracted_info = self._extract_info_from_text(text)
                    if extracted_info:
                        description_data.update(extracted_info)
        
        return description_data
    
    def _extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract specific information from descriptive text using regex patterns."""
        extracted = {}
        
        # Gender distribution pattern
        gender_match = re.search(r'(\d+\.?\d*)%\s*(male|female)', text, re.IGNORECASE)
        if gender_match:
            percentage = gender_match.group(1)
            gender = gender_match.group(2).lower()
            extracted[f'gender_distribution_{gender}'] = f"{percentage}%"
        
        # Housing pattern
        housing_match = re.search(r'(\d+)%\s*of\s*the\s*students\s*live\s*(?:in\s*college-owned|on\s*campus)', text, re.IGNORECASE)
        if housing_match:
            percentage = housing_match.group(1)
            extracted['students_live_on_campus'] = f"{percentage}%"
        
        # Sports pattern
        sports_match = re.search(r'NCAA\s*([IVX]+)', text, re.IGNORECASE)
        if sports_match:
            division = sports_match.group(1)
            extracted['athletic_division'] = f"NCAA {division}"
        
        return extracted
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract any other structured data from the page."""
        structured_data = {}
        
        # Look for any remaining data-test-id attributes
        elements_with_test_id = soup.find_all(attrs={'data-test-id': True})
        for elem in elements_with_test_id:
            test_id = elem.get('data-test-id')
            if test_id and 'student' in test_id.lower():
                text_content = self._extract_text_from_element(elem)
                if text_content:
                    structured_data[test_id] = text_content
        
        return structured_data
    
    # _extract_element_text 메서드는 BaseParser의 _extract_text_from_element로 대체
    
    # _normalize_key_name 메서드는 BaseParser의 _sanitize_key로 대체
