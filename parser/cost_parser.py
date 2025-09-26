"""
Cost/Paying Parser

This module parses HTML content from US News paying pages
and extracts structured cost and financial aid data.
"""

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from models.cost_data import CostData
from parser.base_parser import BaseParser


class CostParser(BaseParser):
    """Parser for university cost and paying information HTML pages."""
    
    def parse(self, html_content: str, university_name: str) -> Optional[CostData]:
        """
        Parse HTML content and extract cost and financial aid data.
        
        Args:
            html_content: Raw HTML content from the paying page
            university_name: Name of the university
            
        Returns:
            CostData object or None if parsing fails
        """
        return super().parse(html_content, university_name, "paying", CostData, "paying")
    
    def _extract_all_paying_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all paying data into a single dictionary using flexible HTML parsing."""
        
        paying_data = {}
        
        # Only extract from data-test-id attributes to avoid duplicates
        elements_with_test_id = soup.find_all(attrs={'data-test-id': True})
        for elem in elements_with_test_id:
            test_id = elem.get('data-test-id')
            if test_id:
                # Get text content, handling different element types
                text_content = self._extract_element_text(elem)
                if text_content:
                    # Skip table data that will be handled by tooltip parsing
                    if test_id in ['cs_avg_cost_income', 'cs_typical_debt_income', 'cs_loan_repayment_income']:
                        # Skip - these will be handled by tooltip parsing to avoid duplicates
                        continue
                    else:
                        paying_data[test_id] = text_content
        
        # 3. Extract tooltip data (like "Typical total federal loan debt after graduation")
        tooltip_data = self._extract_tooltip_data(soup)
        if tooltip_data:
            paying_data.update(tooltip_data)
        
        # 4. Extract list data (like "Financial Aid Statistics")
        list_data = self._extract_list_data(soup)
        if list_data:
            paying_data.update(list_data)
        
        return paying_data
    
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
    
    def _extract_table_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from tables, especially income-based cost tables."""
        table_data = {}
        
        # Look for income-based cost tables
        income_tables = soup.find_all('div', {'data-test-id': 'cs_avg_cost_income'})
        for table in income_tables:
            # Extract table rows
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    income_range = cells[0].get_text().strip()
                    cost = cells[1].get_text().strip()
                    if income_range and cost and cost.startswith('$'):
                        # Keep original text for readability
                        normalized_range = self._normalize_key_name(income_range)
                        table_data[f'income_based_costs/{normalized_range}'] = cost
        
        return table_data
    
    def _extract_list_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from complex list structures like Financial Aid Statistics."""
        print("DEBUG: _extract_list_data called")
        list_data = {}
        
        # Find all TruncatedList containers
        truncated_lists = soup.find_all('div', class_=lambda x: x and 'TruncatedList' in x)
        print(f"DEBUG: Found {len(truncated_lists)} TruncatedList containers")
        
        for list_container in truncated_lists:
            # Find the section header (h4) that precedes this list
            section_header = list_container.find_previous('h4')
            if section_header:
                section_name = section_header.get_text().strip()
                section_key = f"section_{self._normalize_key_name(section_name)}"
                print(f"Found section: {section_name}")
                
                # Extract all list items from both top and bottom lists
                list_items = list_container.find_all('li', class_=lambda x: x and 'ListItem' in x)
                print(f"Found {len(list_items)} list items")
                
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
                            print(f"Added list data: {key} = {value}")
        
        return list_data
    
    def _extract_tooltip_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from tooltip structures."""
        print("DEBUG: _extract_tooltip_data called")
        tooltip_data = {}
        
        # Find all elements with datarow-tooltip class
        tooltip_rows = soup.find_all('div', class_=lambda x: x and 'datarow-tooltip' in x)
        print(f"DEBUG: Found {len(tooltip_rows)} tooltip rows")
        
        for row in tooltip_rows:
            print(f"Processing tooltip row")
            # Find the tooltip box with the label
            tooltip_box = row.find('div', class_=lambda x: x and 'TooltipBox' in x)
            if tooltip_box:
                print("Found tooltip box")
                # Find the label span with class 'jHWBxr'
                label_span = tooltip_box.find('span', class_='jHWBxr')
                if label_span:
                    label = label_span.get_text().strip()
                    print(f"Found label: {label}")
                    
                    # Check if this is a table tooltip (has datarow-table class)
                    if 'datarow-table' in row.get('class', []):
                        print("Found table tooltip, parsing table data")
                        table_data = self._parse_table_tooltip(row, label)
                        if table_data:
                            tooltip_data.update(table_data)
                    else:
                        # Look for the value in the same row - check multiple possible locations
                        value = None
                        
                        # Method 1: Look for spans with $ values in the same row
                        spans = row.find_all('span')
                        for span in spans:
                            span_text = span.get_text().strip()
                            if span_text.startswith('$') and len(span_text) < 20:  # Reasonable length for a price
                                value = span_text
                                print(f"Found value in span: {value}")
                                break
                        
                        # Method 2: Look for paragraphs with $ values
                        if not value:
                            paragraphs = row.find_all('p')
                            for p in paragraphs:
                                p_text = p.get_text().strip()
                                if p_text.startswith('$') and len(p_text) < 20:
                                    value = p_text
                                    print(f"Found value in paragraph: {value}")
                                    break
                        
                        # Method 3: Look for any text content in the row that starts with $
                        if not value:
                            row_text = row.get_text()
                            # Use regex to find $ values
                            import re
                            dollar_matches = re.findall(r'\$[\d,]+', row_text)
                            for match in dollar_matches:
                                if len(match) < 20:  # Reasonable length for a price
                                    value = match
                                    print(f"Found value via regex: {value}")
                                    break
                        
                        if value:
                            # Create normalized key (without tooltip prefix)
                            normalized_key = self._normalize_key_name(label)
                            tooltip_data[normalized_key] = value
                            print(f"Added to tooltip_data: {normalized_key} = {value}")
                        else:
                            print(f"No value found for label: {label}")
                else:
                    print("No label span found")
            else:
                print("No tooltip box found")
        
        return tooltip_data
    
    def _parse_table_tooltip(self, row, label: str) -> Dict[str, Any]:
        """Parse table data from tooltip structures."""
        table_data = {}
        
        # Find the table container
        table_container = row.find('div', class_=lambda x: x and 'Table__Container' in x)
        if not table_container:
            print("No table container found")
            return table_data
        
        # Look for both stacked and tabular containers
        stacked_container = table_container.find('div', class_=lambda x: x and 'StackedContainer' in x)
        tabular_container = table_container.find('div', class_=lambda x: x and 'TabularContainer' in x)
        
        # Prefer tabular container as it's more structured
        container = tabular_container if tabular_container else stacked_container
        
        if not container:
            print("No table container found")
            return table_data
        
        # Find all table rows
        rows = container.find_all('tr')
        print(f"Found {len(rows)} table rows")
        
        for row_elem in rows:
            # Skip header rows
            if row_elem.find('th'):
                continue
                
            # Extract income range and debt value
            income_range = None
            debt_value = None
            
            # Look for spans with income ranges and debt values
            spans = row_elem.find_all('span', class_='jHWBxr')
            
            for span in spans:
                text = span.get_text().strip()
                if text.startswith('$'):
                    # Check if it's an income range (contains dash or plus)
                    if '-' in text or '+' in text:
                        income_range = text
                    # Otherwise it's likely a debt value
                    elif income_range and not debt_value:
                        debt_value = text
            
            if income_range and debt_value:
                # Create normalized key
                normalized_income = income_range.replace('$', '').replace(',', '').replace('-', '_').replace('+', '_plus')
                normalized_label = self._normalize_key_name(label)
                key = f"{normalized_label}/{normalized_income}"
                table_data[key] = debt_value
                print(f"Added table data: {key} = {debt_value}")
        
        return table_data
    
    def _parse_table_element(self, elem, test_id: str) -> Dict[str, Any]:
        """Parse table data from HTML element structure."""
        table_data = {}
        
        # Find all table rows in both stacked and tabular containers
        rows = elem.find_all('tr')
        
        for row in rows:
            # Look for spans with specific classes that contain income and cost data
            spans = row.find_all('span')
            
            income_range = None
            cost_value = None
            
            for span in spans:
                text = span.get_text().strip()
                if text and text.startswith('$'):
                    # Check if it's an income range (contains dash or plus)
                    if '-' in text or '+' in text:
                        income_range = text
                    # Otherwise it's likely a cost value
                    elif income_range and not cost_value:
                        cost_value = text
            
            if income_range and cost_value:
                # Create normalized key
                normalized_income = income_range.replace('$', '').replace(',', '').replace('-', '_').replace('+', '_plus')
                key = f"{test_id}/{normalized_income}"
                table_data[key] = cost_value
        
        return table_data
    
    def _parse_table_text(self, text_content: str, test_id: str) -> Dict[str, Any]:
        """Parse table text content into individual entries."""
        parsed_data = {}
        
        # Example text: "Family Income Average Cost$0-$30,000 $5,900$30,001-$48,000 $3,002..."
        # Split by $ and process each part
        parts = text_content.split('$')
        
        for part in parts[1:]:  # Skip first empty part
            part = part.strip()
            if part:
                # Look for income range pattern like "0-$30,000" or "30,001-$48,000"
                income_match = re.search(r'(\d+(?:,\d+)?(?:-\$\d+(?:,\d+)?)?)', part)
                if income_match:
                    income_range = income_match.group(1)
                    # Extract the cost value (number after income range)
                    cost_match = re.search(r'(\d+(?:,\d+)?)', part[income_match.end():])
                    if cost_match:
                        cost = cost_match.group(1)
                        clean_key = self._normalize_key_name(f"{test_id}/{income_range}")
                        parsed_data[clean_key] = f"${cost}"
        
        return parsed_data
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data from specific sections."""
        structured_data = {}
        
        # Extract net price information
        net_price_elements = soup.find_all('p', string=lambda text: text and 'Net price' in text)
        for elem in net_price_elements:
            parent = elem.parent
            if parent:
                # Look for the actual price value in nearby elements
                price_elem = parent.find_next('p')
                if price_elem and price_elem.get_text().strip().startswith('$'):
                    structured_data['net_price_federal_loan_recipients'] = price_elem.get_text().strip()
        
        # Extract section headers and their content
        section_headers = soup.find_all('h4', class_='Heading-sc-1w5xk2o-0 ldvtPE')
        for header in section_headers:
            section_name = header.get_text().strip()
            section_content = {}
            
            # Get all data rows in this section
            section_div = header.find_next('div', class_='group-section-box')
            if section_div:
                data_rows = section_div.find_all('div', class_='DataRow__Row-sc-1udybh3-0')
                for row in data_rows:
                    label_elem = row.find('p', class_='Paragraph-sc-1iyax29-0 fZPEMD')
                    value_elem = row.find('p', class_='Paragraph-sc-1iyax29-0 iKkzvP')
                    
                    if label_elem and value_elem:
                        label = label_elem.get_text().strip()
                        value = value_elem.get_text().strip()
                        section_content[label] = value
                
                if section_content:
                    structured_data[f'section_{section_name.lower().replace(" ", "_")}'] = section_content
        
        return structured_data
    
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary into single level with normalized keys."""
        flattened = {}
        
        for key, value in data.items():
            # Normalize the key name
            normalized_key = self._normalize_key_name(key)
            new_key = f"{prefix}/{normalized_key}" if prefix else normalized_key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                nested_flattened = self._flatten_dict(value, new_key)
                flattened.update(nested_flattened)
            else:
                flattened[new_key] = value
        
        return flattened
    
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
    
    def _get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description from the page."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content')
        return None
