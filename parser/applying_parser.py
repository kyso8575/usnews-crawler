"""
Applying Parser

This module parses HTML content from US News applying pages
and extracts structured admissions and application data.
"""

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from models.applying_data import ApplyingData
from parser.base_parser import BaseParser


class ApplyingParser(BaseParser):
    """Parser for university applying/admissions information HTML pages."""
    
    def parse(self, html_content: str, university_name: str) -> Optional[ApplyingData]:
        """
        Parse HTML content and extract applying/admissions data.
        
        Args:
            html_content: Raw HTML content from the applying page
            university_name: Name of the university
            
        Returns:
            ApplyingData object or None if parsing fails
        """
        return super().parse(html_content, university_name, "applying", ApplyingData)
    
    def _extract_all_applying_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all applying data into a single dictionary using flexible HTML parsing."""
        
        applying_data = {}
        
        # 1. Extract QuickStat data (dl/dt/dd structure)
        quick_stats = self._extract_quick_stats(soup)
        if quick_stats:
            applying_data.update(quick_stats)
        
        # 2. Extract data-test-id attributes
        elements_with_test_id = soup.find_all(attrs={'data-test-id': True})
        for elem in elements_with_test_id:
            test_id = elem.get('data-test-id')
            if test_id:
                text_content = self._extract_element_text(elem)
                if text_content:
                    applying_data[test_id] = text_content
        
        # 3. Extract structured sections
        structured_data = self._extract_structured_sections(soup)
        if structured_data:
            applying_data.update(structured_data)
        
        # 4. Extract additional admission data from text patterns
        additional_data = self._extract_admission_patterns(soup)
        if additional_data:
            applying_data.update(additional_data)
        
        return applying_data
    
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
    
    def _extract_admission_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract admission data using text patterns."""
        admission_data = {}
        page_text = soup.get_text()
        
        # Application deadline patterns
        deadline_patterns = [
            r'application deadline.*?(\w+\.?\s+\d+)',
            r'deadline.*?(\w+\.?\s+\d+)',
            r'(\w+\.?\s+\d+).*?deadline'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['application_deadline'] = match.group(1)
                break
        
        # Application fee patterns
        fee_patterns = [
            r'application fee.*?(\$\d+)',
            r'fee.*?(\$\d+)'
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['application_fee'] = match.group(1)
                break
        
        # Acceptance rate patterns
        acceptance_patterns = [
            r'acceptance rate.*?(\d+\.?\d*%)',
            r'(\d+\.?\d*%).*?acceptance rate',
            r'admitted.*?(\d+\.?\d*%)'
        ]
        
        for pattern in acceptance_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['acceptance_rate'] = match.group(1)
                break
        
        # Early acceptance rate patterns
        early_patterns = [
            r'early.*?acceptance.*?rate.*?(\d+\.?\d*%)',
            r'early.*?decision.*?(\d+\.?\d*%)',
            r'early.*?action.*?(\d+\.?\d*%)'
        ]
        
        for pattern in early_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['early_acceptance_rate'] = match.group(1)
                break
        
        # SAT score ranges
        sat_patterns = [
            r'SAT.*?score.*?between.*?(\d+).*?and.*?(\d+)',
            r'SAT.*?(\d+).*?to.*?(\d+)',
            r'SAT.*?(\d+)-(\d+)'
        ]
        
        for pattern in sat_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['sat_range'] = f"{match.group(1)}-{match.group(2)}"
                break
        
        # ACT score ranges
        act_patterns = [
            r'ACT.*?score.*?between.*?(\d+).*?and.*?(\d+)',
            r'ACT.*?(\d+).*?to.*?(\d+)',
            r'ACT.*?(\d+)-(\d+)'
        ]
        
        for pattern in act_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['act_range'] = f"{match.group(1)}-{match.group(2)}"
                break
        
        # GPA importance
        gpa_patterns = [
            r'GPA.*?(very important|important|considered)',
            r'(very important|important).*?GPA'
        ]
        
        for pattern in gpa_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['gpa_importance'] = match.group(1)
                break
        
        # Class rank importance
        class_rank_patterns = [
            r'class rank.*?(very important|important|considered)',
            r'(very important|important).*?class rank'
        ]
        
        for pattern in class_rank_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                admission_data['class_rank_importance'] = match.group(1)
                break
        
        return admission_data
    
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
    
    def _create_category_key(self, category: str) -> str:
        """Create a meaningful key from category text."""
        # Convert to lowercase and replace spaces/special chars
        key = category.lower()
        
        # Handle specific patterns for class standing breakdown
        if 'top 10%' in key:
            return 'top_10_percent'
        elif 'top 25%' in key:
            return 'top_25_percent'
        elif 'top 50%' in key:
            return 'top_50_percent'
        elif 'bottom 25%' in key:
            return 'bottom_25_percent'
        elif 'bottom 50%' in key:
            return 'bottom_50_percent'
        elif 'bottom 10%' in key:
            return 'bottom_10_percent'
        
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
