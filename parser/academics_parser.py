"""
Academics Parser

This module parses HTML content from US News academics pages
and extracts structured academic information.
"""

import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from models.academics_data import AcademicsData
from parser.base_parser import BaseParser


class AcademicsParser(BaseParser):
    """Parser for university academics information HTML pages."""
    
    def parse(self, html_content: str, university_name: str) -> Optional[AcademicsData]:
        """
        Parse HTML content and extract academics data.
        
        Args:
            html_content: Raw HTML content from the academics page
            university_name: Name of the university
            
        Returns:
            AcademicsData object or None if parsing fails
        """
        return super().parse(html_content, university_name, "academics", AcademicsData)
    
    def _convert_to_flat_structure(self, academics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert nested academics structure to flat key-value pairs."""
        
        flat_data = {}
        
        for section_key, section_data in academics_data.items():
            if isinstance(section_data, dict):
                # Handle section data
                if 'data' in section_data:
                    data_dict = section_data['data']
                    for data_key, data_value in data_dict.items():
                        # Create flat key
                        flat_key = self._sanitize_key(f"{section_key}_{data_key}")
                        
                        if isinstance(data_value, list):
                            # Handle list data
                            flat_data[flat_key] = data_value
                        elif isinstance(data_value, dict):
                            # Handle nested dict data
                            for nested_key, nested_value in data_value.items():
                                nested_flat_key = self._sanitize_key(f"{section_key}_{data_key}_{nested_key}")
                                flat_data[nested_flat_key] = nested_value
                        else:
                            # Handle simple values
                            flat_data[flat_key] = data_value
                else:
                    # Handle direct section data
                    flat_key = self._sanitize_key(section_key)
                    flat_data[flat_key] = section_data
            else:
                # Handle simple values
                flat_key = self._sanitize_key(section_key)
                flat_data[flat_key] = section_data
        
        return flat_data
    
    def _sanitize_key(self, text: str) -> str:
        """Convert text to a valid dictionary key."""
        # Convert to lowercase, replace spaces and special chars with underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '_', text.lower())
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key
    
    def _extract_all_academics_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all academics data into a single dictionary using priority-based parsing."""
        
        academics_data = {}
        extracted_values = set()  # Track extracted values to avoid duplicates
        
        # 1. Extract structured group sections first (highest priority)
        group_sections = self._extract_group_sections(soup)
        if group_sections:
            academics_data.update(group_sections)
            # Track values from group sections
            self._track_extracted_values(group_sections, extracted_values)
        
        # 2. Extract QuickStat data (high priority)
        quick_stats = self._extract_quick_stats(soup)
        if quick_stats:
            filtered_quick_stats = self._filter_duplicates(quick_stats, extracted_values)
            if filtered_quick_stats:
                academics_data.update(filtered_quick_stats)
                self._track_extracted_values(filtered_quick_stats, extracted_values)
        
        # 3. Extract data-test-id attributes (medium priority, skip if already extracted)
        elements_with_test_id = soup.find_all(attrs={'data-test-id': True})
        for elem in elements_with_test_id:
            test_id = elem.get('data-test-id')
            if test_id:
                # Check if this element is inside a group-section-box (already extracted)
                parent_group_box = elem.find_parent('div', class_='group-section-box')
                if parent_group_box:
                    continue
                
                text_content = self._extract_element_text(elem)
                if text_content and text_content not in extracted_values:
                    academics_data[test_id] = text_content
                    extracted_values.add(text_content)
        
        # 4. Extract structured sections (medium priority)
        structured_data = self._extract_structured_sections(soup)
        if structured_data:
            filtered_structured = self._filter_duplicates(structured_data, extracted_values)
            if filtered_structured:
                academics_data.update(filtered_structured)
                self._track_extracted_values(filtered_structured, extracted_values)
        
        # 5. Extract additional academic data from text patterns (low priority)
        additional_data = self._extract_academic_patterns(soup)
        if additional_data:
            filtered_additional = self._filter_duplicates(additional_data, extracted_values)
            if filtered_additional:
                academics_data.update(filtered_additional)
                self._track_extracted_values(filtered_additional, extracted_values)
        
        # 6. Extract list data (low priority)
        list_data = self._extract_list_data(soup)
        if list_data:
            filtered_list_data = self._filter_duplicates(list_data, extracted_values)
            if filtered_list_data:
                academics_data.update(filtered_list_data)
        
        return academics_data
    
    def _extract_quick_stats(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from QuickStat boxes (dl/dt/dd structure)."""
        quick_stats = {}
        
        # Find all QuickStat containers
        quick_stat_containers = soup.find_all('div', class_=lambda x: x and 'QuickStat' in x)
        
        for container in quick_stat_containers:
            # Find dl elements within the container
            dl_elements = container.find_all('dl')
            
            for dl in dl_elements:
                dt_elem = dl.find('dt')
                dd_elem = dl.find('dd')
                
                if dt_elem and dd_elem:
                    label = dt_elem.get_text().strip()
                    value = dd_elem.get_text().strip()
                    
                    if label and value:
                        normalized_key = self._normalize_key_name(label)
                        quick_stats[normalized_key] = value
        
        return quick_stats
    
    def _extract_academic_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract academic data using text patterns."""
        academic_data = {}
        page_text = soup.get_text()
        
        # Student-faculty ratio patterns
        ratio_patterns = [
            r'student-faculty ratio.*?(\d+:\d+)',
            r'(\d+:\d+).*?student-faculty ratio',
            r'student to faculty ratio.*?(\d+:\d+)',
            r'(\d+:\d+).*?student to faculty ratio'
        ]
        
        for pattern in ratio_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                academic_data['student_faculty_ratio'] = match.group(1)
                break
        
        # Class size patterns
        class_size_patterns = [
            r'class size.*?(\d+\.?\d*)',
            r'(\d+\.?\d*).*?class size',
            r'average class size.*?(\d+\.?\d*)',
            r'(\d+\.?\d*).*?average class size'
        ]
        
        for pattern in class_size_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                academic_data['average_class_size'] = match.group(1)
                break
        
        # Graduation rate patterns
        graduation_patterns = [
            r'graduation rate.*?(\d+\.?\d*%)',
            r'(\d+\.?\d*%).*?graduation rate',
            r'four-year graduation rate.*?(\d+\.?\d*%)',
            r'(\d+\.?\d*%).*?four-year graduation rate'
        ]
        
        for pattern in graduation_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                academic_data['graduation_rate'] = match.group(1)
                break
        
        # Retention rate patterns
        retention_patterns = [
            r'retention rate.*?(\d+\.?\d*%)',
            r'(\d+\.?\d*%).*?retention rate',
            r'first-year retention rate.*?(\d+\.?\d*%)',
            r'(\d+\.?\d*%).*?first-year retention rate'
        ]
        
        for pattern in retention_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                academic_data['retention_rate'] = match.group(1)
                break
        
        # Academic calendar patterns
        calendar_patterns = [
            r'academic calendar.*?(semester|quarter|trimester)',
            r'(semester|quarter|trimester).*?academic calendar'
        ]
        
        for pattern in calendar_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                academic_data['academic_calendar'] = match.group(1)
                break
        
        # Degree programs patterns
        degree_patterns = [
            r'(\d+).*?bachelor.*?degree',
            r'(\d+).*?master.*?degree',
            r'(\d+).*?doctoral.*?degree',
            r'(\d+).*?associate.*?degree'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                degree_type = pattern.split('.*?')[1].replace('.*?', '').replace('degree', '').strip()
                academic_data[f'{degree_type}_degrees'] = match.group(1)
        
        return academic_data
    
    def _extract_structured_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from structured sections."""
        structured_data = {}
        
        # Extract section headers and their content
        section_headers = soup.find_all('h3', class_=lambda x: x and 'Heading' in x)
        for header in section_headers:
            section_name = header.get_text().strip()
            section_content = {}
            
            # Get all data in this section
            section_div = header.find_next('div')
            if section_div:
                # Look for various data patterns
                data_elements = section_div.find_all(['p', 'div', 'span'])
                for elem in data_elements:
                    text = elem.get_text().strip()
                    if text and len(text) > 10:  # Filter out short text
                        # Try to extract key-value pairs
                        if ':' in text:
                            parts = text.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                if key and value:
                                    normalized_key = self._normalize_key_name(key)
                                    section_content[normalized_key] = value
                
                if section_content:
                    normalized_section = self._normalize_key_name(section_name)
                    structured_data[f'section_{normalized_section}'] = section_content
        
        # Extract all DataRow sections with TruncatedList structure
        data_row_sections = self._extract_data_row_sections(soup)
        if data_row_sections:
            structured_data.update(data_row_sections)
        
        return structured_data
    
    def _extract_data_row_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all DataRow sections with TruncatedList structure."""
        data_row_sections = {}
        
        # Look for divs with DataRow__Row class that contain TruncatedList structure
        data_rows = soup.find_all('div', class_=lambda x: x and 'DataRow__Row' in x)
        
        for row in data_rows:
            # Check if this row has a paragraph with a label
            paragraph = row.find('p', class_=lambda x: x and 'Paragraph' in x)
            if paragraph:
                section_label = paragraph.get_text().strip()
                
                # Look for the TruncatedList wrapper
                truncated_wrapper = row.find('div', class_=lambda x: x and 'TruncatedList' in x)
                if truncated_wrapper:
                    # Find all list items
                    list_items = truncated_wrapper.find_all('li')
                    
                    # Check if there are multiple list items
                    if len(list_items) > 1:
                        # Multiple items - store as individual flat keys
                        normalized_section_key = self._normalize_key_name(section_label)
                        
                        for li in list_items:
                            inner_div = li.find('div', class_=lambda x: x and 'DataRow__Row' in x)
                            if inner_div:
                                paragraphs = inner_div.find_all('p', class_=lambda x: x and 'Paragraph' in x)
                                if len(paragraphs) >= 2:
                                    category = paragraphs[0].get_text().strip()
                                    value = paragraphs[1].get_text().strip()
                                    
                                    # Create a meaningful key from the category
                                    category_key = self._create_category_key(category)
                                    
                                    # Create flat key: section_category
                                    flat_key = f"{normalized_section_key}_{category_key}"
                                    data_row_sections[flat_key] = value
                    else:
                        # Single item - store as simple string value
                        first_li = list_items[0]
                        inner_div = first_li.find('div', class_=lambda x: x and 'DataRow__Row' in x)
                        if inner_div:
                            paragraphs = inner_div.find_all('p', class_=lambda x: x and 'Paragraph' in x)
                            if len(paragraphs) >= 2:
                                # Use the second paragraph as the primary value
                                primary_value = paragraphs[1].get_text().strip()
                            elif len(paragraphs) == 1:
                                # Handle single paragraph case
                                primary_value = paragraphs[0].get_text().strip()
                            else:
                                continue
                            
                            # Normalize the section label to create a key
                            normalized_key = self._normalize_key_name(section_label)
                            data_row_sections[normalized_key] = primary_value
        
        return data_row_sections
    
    def _extract_list_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from complex list structures like Most Popular Majors."""
        list_data = {}
        
        # Extract majors and minors data specifically
        majors_data = self._extract_majors_data(soup)
        if majors_data:
            list_data.update(majors_data)
        
        # Find all TruncatedList containers for other data
        truncated_lists = soup.find_all('div', class_=lambda x: x and 'TruncatedList' in x)
        
        for list_container in truncated_lists:
            # Find the section header (h4) that precedes this list
            section_header = list_container.find_previous('h4')
            if section_header:
                section_name = section_header.get_text().strip()
                section_key = f"section_{self._normalize_key_name(section_name)}"
                
                # Skip if this is already handled by majors extraction
                if 'majors' in section_name.lower() or 'minors' in section_name.lower():
                    continue
                
                # Extract all list items from both top and bottom lists
                list_items = list_container.find_all('li', class_=lambda x: x and 'ListItem' in x)
                
                for item in list_items:
                    # Find all paragraphs in this item
                    paragraphs = item.find_all('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                    
                    if len(paragraphs) >= 2:
                        label = paragraphs[0].get_text().strip()
                        value = paragraphs[1].get_text().strip()
                        
                        if label and value:
                            normalized_label = self._normalize_key_name(label)
                            key = f"{section_key}/{normalized_label}"
                            list_data[key] = value
        
        return list_data
    
    def _extract_majors_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract majors and minors data specifically."""
        majors_data = {}
        
        # Find the MajorsDegrees section
        majors_section = soup.find('div', id='MajorsDegrees')
        if not majors_section:
            return majors_data
        
        # Extract Popular Majors
        popular_majors = self._extract_popular_majors(majors_section)
        if popular_majors:
            majors_data['popular_majors'] = popular_majors
        
        # Extract Alumni Salaries by Major
        alumni_salaries = self._extract_alumni_salaries(majors_section)
        if alumni_salaries:
            majors_data['alumni_salaries_by_major'] = alumni_salaries
        
        # Extract All Majors Offered
        all_majors = self._extract_all_majors(majors_section)
        if all_majors:
            majors_data['majors_offered'] = all_majors
        
        # Extract Minors
        minors = self._extract_minors(majors_section)
        if minors:
            majors_data['minors_offered'] = minors
        
        # Extract Study Abroad information (search in entire HTML, not just majors section)
        study_abroad = self._extract_study_abroad(soup)
        if study_abroad:
            majors_data['study_abroad'] = study_abroad
        
        return majors_data
    
    def _extract_popular_majors(self, majors_section: BeautifulSoup) -> Dict[str, str]:
        """Extract popular majors with percentages."""
        popular_majors = {}
        
        # Find the "Ten Most Popular Majors" section
        popular_section = majors_section.find('h4', string=lambda text: text and 'Most Popular Majors' in text)
        if not popular_section:
            return popular_majors
        
        # Find the TruncatedList container
        truncated_list = popular_section.find_next('div', class_=lambda x: x and 'TruncatedList' in x)
        if not truncated_list:
            return popular_majors
        
        # Extract from both top and bottom lists
        list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
        
        for item in list_items:
            paragraphs = item.find_all('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
            if len(paragraphs) >= 2:
                major_name = paragraphs[0].get_text().strip()
                percentage = paragraphs[1].get_text().strip()
                if major_name and percentage:
                    popular_majors[major_name] = percentage
        
        return popular_majors
    
    def _extract_alumni_salaries(self, majors_section: BeautifulSoup) -> Dict[str, str]:
        """Extract alumni starting salaries by major."""
        alumni_salaries = {}
        
        # Find the "Alumni Starting Salaries by Major" section
        salary_section = majors_section.find('h4', string=lambda text: text and 'Alumni Starting Salaries' in text)
        if not salary_section:
            return alumni_salaries
        
        # Find the TruncatedList container
        truncated_list = salary_section.find_next('div', class_=lambda x: x and 'TruncatedList' in x)
        if not truncated_list:
            return alumni_salaries
        
        # Extract from both top and bottom lists
        list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
        
        for item in list_items:
            paragraphs = item.find_all('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
            if len(paragraphs) >= 2:
                major_name = paragraphs[0].get_text().strip()
                salary = paragraphs[1].get_text().strip()
                if major_name and salary:
                    alumni_salaries[major_name] = salary
        
        return alumni_salaries
    
    def _extract_all_majors(self, majors_section: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all majors offered, organized by category."""
        all_majors = {}
        
        # Find the "Majors Offered at This School" section
        majors_offered_section = majors_section.find('h4', string=lambda text: text and 'Majors Offered' in text)
        if not majors_offered_section:
            return all_majors
        
        # Find all DataRow sections after this header
        current_element = majors_offered_section.find_next()
        while current_element:
            # Check if this is a DataRow with datarow-list class
            if (current_element.name == 'div' and 
                current_element.get('class') and 
                any('DataRow__Row' in cls for cls in current_element.get('class', [])) and
                any('datarow-list' in cls for cls in current_element.get('class', []))):
                
                # Extract category name
                category_paragraph = current_element.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
                if category_paragraph:
                    category_name = category_paragraph.get_text().strip()
                    
                    # Extract majors in this category
                    majors_in_category = []
                    truncated_list = current_element.find('div', class_=lambda x: x and 'TruncatedList' in x)
                    if truncated_list:
                        list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                        for item in list_items:
                            span = item.find('span', class_='undefined')
                            if span:
                                major_name = span.get_text().strip()
                                if major_name:
                                    majors_in_category.append(major_name)
                    
                    if majors_in_category:
                        all_majors[category_name] = majors_in_category
            
            # Move to next sibling
            current_element = current_element.find_next_sibling()
            
            # Stop if we hit the Minors section
            if (current_element and current_element.name == 'div' and 
                current_element.find('h4', string=lambda text: text and 'Minors' in text)):
                break
        
        return all_majors
    
    def _extract_minors(self, majors_section: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all minors offered, organized by category."""
        minors = {}
        
        # Find the "Minors" section
        minors_section = majors_section.find('h4', string=lambda text: text and 'Minors' in text)
        if not minors_section:
            return minors
        
        # Find all DataRow sections after this header
        current_element = minors_section.find_next()
        while current_element:
            # Check if this is a DataRow with datarow-list class
            if (current_element.name == 'div' and 
                current_element.get('class') and 
                any('DataRow__Row' in cls for cls in current_element.get('class', [])) and
                any('datarow-list' in cls for cls in current_element.get('class', []))):
                
                # Extract category name
                category_paragraph = current_element.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
                if category_paragraph:
                    category_name = category_paragraph.get_text().strip()
                    
                    # Extract minors in this category
                    minors_in_category = []
                    truncated_list = current_element.find('div', class_=lambda x: x and 'TruncatedList' in x)
                    if truncated_list:
                        list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                        for item in list_items:
                            span = item.find('span', class_='undefined')
                            if span:
                                minor_name = span.get_text().strip()
                                if minor_name:
                                    minors_in_category.append(minor_name)
                    
                    if minors_in_category:
                        minors[category_name] = minors_in_category
            
            # Move to next sibling
            current_element = current_element.find_next_sibling()
        
        return minors
    
    def _extract_study_abroad(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract study abroad information including countries and participation rates."""
        study_abroad_data = {}
        
        # Find the "Study Abroad" section by looking for the jump-link with International_study_away ID
        study_abroad_link = soup.find('span', class_='jump-link', id='International_study_away')
        if not study_abroad_link:
            # Fallback: try to find by h4 text
            study_abroad_section = soup.find('h4', string=lambda text: text and 'Study Abroad' in text)
            if not study_abroad_section:
                return study_abroad_data
        else:
            # Find the h4 that follows this jump-link
            study_abroad_section = study_abroad_link.find_next('h4')
            if not study_abroad_section:
                return study_abroad_data
        
        # Extract countries where study abroad opportunities are available
        countries_section = study_abroad_section.find_next('div', class_=lambda x: x and 'DataRow__Row' in x)
        if countries_section:
            # Check if this is the countries section
            countries_paragraph = countries_section.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
            if countries_paragraph and 'Countries where study abroad opportunities are available' in countries_paragraph.get_text():
                countries = []
                truncated_list = countries_section.find('div', class_=lambda x: x and 'TruncatedList' in x)
                if truncated_list:
                    # Extract from both top and bottom lists
                    list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                    for item in list_items:
                        span = item.find('span', class_='undefined')
                        if span:
                            country = span.get_text().strip()
                            if country:
                                countries.append(country)
                
                if countries:
                    study_abroad_data['countries_available'] = countries
        
        # Extract study abroad participation rate
        participation_section = countries_section.find_next('div', class_=lambda x: x and 'DataRow__Row' in x)
        if participation_section:
            participation_paragraph = participation_section.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
            if participation_paragraph and 'Graduates Participating in Study Abroad Programs' in participation_paragraph.get_text():
                # Find the data-test-id element for participation rate
                participation_element = participation_section.find(attrs={'data-test-id': 'aca_off_study_abroad'})
                if participation_element:
                    participation_rate = participation_element.get_text().strip()
                    if participation_rate and participation_rate != 'N/A':
                        study_abroad_data['participation_rate'] = participation_rate
        
        return study_abroad_data
    
    def _create_category_key(self, category: str) -> str:
        """Create a meaningful key from category text."""
        # Convert to lowercase and replace spaces/special chars
        key = category.lower()
        
        # Handle specific patterns for academic categories
        if 'most popular' in key:
            return 'most_popular'
        elif 'top' in key and 'percent' in key:
            return 'top_percent'
        elif 'bachelor' in key:
            return 'bachelor'
        elif 'master' in key:
            return 'master'
        elif 'doctoral' in key:
            return 'doctoral'
        elif 'associate' in key:
            return 'associate'
        
        # General case - normalize the text
        key = re.sub(r'[^\w\s]', '', key)  # Remove special characters
        key = re.sub(r'\s+', '_', key)    # Replace spaces with underscores
        key = key.strip('_')               # Remove leading/trailing underscores
        
        return key
    
    def _extract_element_text(self, elem) -> Optional[str]:
        """Extract text content from various element types."""
        if elem.name == 'a':  # Links
            return elem.get_text().strip()
        elif elem.name == 'span':  # Spans
            return elem.get_text().strip()
        elif elem.name == 'p':  # Paragraphs
            return elem.get_text().strip()
        else:
            return elem.get_text().strip() if elem.get_text() else None
    
    def _normalize_key_name(self, key: str) -> str:
        """Normalize key names to be more website-like while keeping them programming-safe."""
        # Keep the original text but make it programming-safe
        normalized = key
        
        # Replace spaces with underscores
        normalized = normalized.replace(' ', '_')
        
        # Replace special characters that might cause issues
        normalized = re.sub(r'[^\w\-_()&]', '_', normalized)
        
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Keep original case for better readability (don't convert to lowercase)
        return normalized
    
    def _track_extracted_values(self, data: Dict[str, Any], extracted_values: set):
        """Track extracted values to avoid duplicates."""
        for key, value in data.items():
            if isinstance(value, str):
                extracted_values.add(value)
            elif isinstance(value, dict):
                # Recursively track values in nested dictionaries
                self._track_extracted_values(value, extracted_values)
            elif isinstance(value, list):
                # Track string values in lists
                for item in value:
                    if isinstance(item, str):
                        extracted_values.add(item)
    
    def _filter_duplicates(self, data: Dict[str, Any], extracted_values: set) -> Dict[str, Any]:
        """Filter out data that has already been extracted."""
        filtered_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                if value not in extracted_values:
                    filtered_data[key] = value
            elif isinstance(value, dict):
                # Recursively filter nested dictionaries
                filtered_nested = self._filter_duplicates(value, extracted_values)
                if filtered_nested:
                    filtered_data[key] = filtered_nested
            elif isinstance(value, list):
                # Filter lists
                filtered_list = []
                for item in value:
                    if isinstance(item, str) and item not in extracted_values:
                        filtered_list.append(item)
                    elif not isinstance(item, str):
                        filtered_list.append(item)
                if filtered_list:
                    filtered_data[key] = filtered_list
            else:
                # Keep non-string values
                filtered_data[key] = value
        return filtered_data
    
    def _extract_group_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all group-section-box sections automatically."""
        group_sections = {}
        
        # Find all group-section-box containers
        group_boxes = soup.find_all('div', class_='group-section-box')
        
        for group_box in group_boxes:
            # Find the jump-link to get the section ID
            jump_link = group_box.find('span', class_='jump-link')
            if not jump_link:
                continue
            
            section_id = jump_link.get('id')
            if not section_id:
                continue
            
            # Find the h4 header to get the section title
            header = group_box.find('h4', class_=lambda x: x and 'Heading' in x)
            if not header:
                continue
            
            section_title = header.get_text().strip()
            
            # Extract all data rows within this group section
            section_data = {}
            data_rows = group_box.find_all('div', class_=lambda x: x and 'DataRow__Row' in x)
            
            for data_row in data_rows:
                # Find the label paragraph
                label_paragraph = data_row.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
                if not label_paragraph:
                    continue
                
                label = label_paragraph.get_text().strip()
                
                # Check if this is a list type (datarow-list or datarow-table with TruncatedList)
                is_list_type = ('datarow-list' in data_row.get('class', []) or 
                              ('datarow-table' in data_row.get('class', []) and 
                               data_row.find('div', class_=lambda x: x and 'TruncatedList' in x)))
                
                if is_list_type:
                    # Extract list items
                    truncated_list = data_row.find('div', class_=lambda x: x and 'TruncatedList' in x)
                    if truncated_list:
                        items = []
                        list_items = truncated_list.find_all('li', class_=lambda x: x and 'ListItem' in x)
                        
                        for item in list_items:
                            # Try multiple ways to extract text from list items
                            item_text = None
                            
                            # Method 1: Direct span with undefined class
                            span = item.find('span', class_='undefined')
                            if span:
                                item_text = span.get_text().strip()
                            
                            # Method 2: Look for nested p tag inside span > div
                            if not item_text:
                                nested_p = item.find('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                                if nested_p:
                                    item_text = nested_p.get_text().strip()
                            
                            # Method 3: Fallback to any p tag
                            if not item_text:
                                any_p = item.find('p')
                                if any_p:
                                    item_text = any_p.get_text().strip()
                            
                            # Method 4: Fallback to direct text
                            if not item_text:
                                item_text = item.get_text().strip()
                            
                            if item_text:
                                items.append(item_text)
                        
                        if items:
                            normalized_label = self._normalize_key_name(label)
                            section_data[normalized_label] = items
                
                else:
                    # Regular data row - find the value
                    value_paragraph = data_row.find('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                    if value_paragraph:
                        value = value_paragraph.get_text().strip()
                        if value:
                            normalized_label = self._normalize_key_name(label)
                            section_data[normalized_label] = value
            
            if section_data:
                # Create a normalized key from the section title
                normalized_section_key = self._normalize_key_name(section_title)
                group_sections[normalized_section_key] = {
                    'title': section_title,
                    'section_id': section_id,
                    'data': section_data
                }
        
        return group_sections
