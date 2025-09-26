"""
Overall Rankings Parser

This module parses HTML content from US News overall rankings pages
and extracts structured ranking data.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

from models.overall_rankings_data import OverallRankingsData, OverallRanking, ProgramRanking, SubProgramRanking


class OverallRankingsParser:
    """Parser for overall university rankings HTML pages."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html_content: str, university_name: str) -> Optional[OverallRankingsData]:
        """
        Parse HTML content and extract overall rankings data.
        
        Args:
            html_content: Raw HTML content from the rankings page
            university_name: Name of the university
            
        Returns:
            OverallRankingsData object or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract overall ranking information
            overall_ranking = self._extract_overall_ranking(soup)
            
            # Extract program-specific rankings
            program_rankings = self._extract_program_rankings(soup)
            if program_rankings:
                overall_ranking.rankings = program_rankings
            
            # Extract metrics from Box sections
            metrics = self._extract_metrics_from_boxes(soup)
            if metrics:
                # Convert program rankings to dict if it's a list
                if isinstance(overall_ranking.rankings, list):
                    rankings_dict = {}
                    for ranking in overall_ranking.rankings:
                        category_key = self._sanitize_key(ranking.category)
                        rankings_dict[category_key] = ranking.rank
                        
                        # Add sub_programs if they exist
                        if ranking.sub_programs:
                            for sub in ranking.sub_programs:
                                sub_key = f"{category_key}/{self._sanitize_key(sub.sub_program_name)}"
                                rankings_dict[sub_key] = sub.rank
                    overall_ranking.rankings = rankings_dict
                
                # Add metrics to the rankings dict
                overall_ranking.rankings.update(metrics)
            
            # Create the data structure
            rankings_data = OverallRankingsData(
                university_name=university_name,
                overall_ranking=overall_ranking
            )
            
            self.logger.info(f"Successfully parsed rankings for {university_name}")
            return rankings_data
            
        except Exception as e:
            self.logger.error(f"Error parsing rankings for {university_name}: {e}")
            return None
    
    def _extract_metrics_from_boxes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metrics from Box sections with DataRow pattern."""
        metrics = {}
        
        # Find all Box sections with the specific class pattern
        box_sections = soup.find_all('div', class_=lambda x: x and 'Box-w0dun1-0' in x and 'bcZeaE' in x and 'pt5' in x)
        
        for box_section in box_sections:
            # Find all DataRow elements within this box
            data_rows = box_section.find_all('div', class_=lambda x: x and 'DataRow__Row-sc-1udybh3-0' in x)
            
            for data_row in data_rows:
                # Find the two p tags within the DataRow
                p_tags = data_row.find_all('p')
                
                if len(p_tags) >= 2:
                    # First p tag is the label (key)
                    label = p_tags[0].get_text(strip=True)
                    # Second p tag is the value
                    value = p_tags[1].get_text(strip=True)
                    
                    if label and value:
                        # Clean the key
                        clean_key = self._sanitize_key(label)
                        # Clean the value
                        clean_value = self._clean_value(value)
                        metrics[clean_key] = clean_value
        
        return metrics
    
    def _clean_value(self, value: str) -> Any:
        """Clean and convert value to appropriate type."""
        if not value:
            return None
        
        # Remove common prefixes/suffixes
        cleaned = value.replace('$', '').replace(',', '').strip()
        
        # Handle percentage values
        if '%' in cleaned:
            match = re.search(r'([0-9.]+)', cleaned)
            if match:
                return float(match.group(1))
        
        # Handle numeric values
        if cleaned.replace('.', '').replace('-', '').isdigit():
            try:
                return float(cleaned)
            except ValueError:
                return cleaned
        
        # Return as string if not numeric
        return cleaned
    
    def _sanitize_key(self, text: str) -> str:
        """Convert text to a valid dictionary key."""
        # Convert to lowercase, replace spaces and special chars with underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '_', text.lower())
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key
    
    def _extract_overall_ranking(self, soup: BeautifulSoup) -> OverallRanking:
        """Extract overall ranking information from the HTML."""
        
        return OverallRanking(
            raw_data={
                'page_title': soup.title.string if soup.title else None,
                'meta_description': self._get_meta_description(soup),
                'page_text_sample': soup.get_text()[:500] if soup.get_text() else None
            }
        )
    
    
    def _extract_program_rankings(self, soup: BeautifulSoup) -> Optional[List[ProgramRanking]]:
        """Extract program-specific rankings from the HTML with hierarchical structure."""
        
        program_rankings = []
        processed_urls = set()  # To avoid duplicates
        sub_program_urls = set()  # Track URLs that are sub-programs
        
        # First pass: collect all sub-program URLs to avoid duplicates
        main_badge_list = soup.find('ul', class_=lambda x: x and 'BadgeList' in x and 'fBykJl' in x)
        if main_badge_list:
            program_items = main_badge_list.find_all('li', class_=lambda x: x and 'BadgeList__ListItem' in x)
            
            for item in program_items:
                # Check if this item has nested sub-programs
                nested_badge_lists = item.find_all('ul', class_=lambda x: x and 'BadgeList' in x)
                for nested_list in nested_badge_lists:
                    nested_items = nested_list.find_all('li', class_=lambda x: x and 'BadgeList__ListItem' in x)
                    for nested_item in nested_items:
                        nested_link = nested_item.find('a', href=True)
                        if nested_link:
                            sub_program_urls.add(nested_link.get('href', ''))
        
        # Second pass: extract main programs
        if main_badge_list:
            program_items = main_badge_list.find_all('li', class_=lambda x: x and 'BadgeList__ListItem' in x)
            
            for item in program_items:
                # Look for the main program link
                main_program_link = item.find('a', href=True)
                if not main_program_link:
                    continue
                    
                href = main_program_link.get('href', '')
                text = main_program_link.get_text()
                
                # Skip if already processed or is a sub-program
                if href in processed_urls or href in sub_program_urls:
                    continue
                
                
                # Check if this is a rankings link
                if 'rankings' in href:
                    # Extract main program ranking
                    main_rank_match = re.search(r'#(\d{1,4})', text)
                    if main_rank_match:
                        try:
                            main_rank = int(main_rank_match.group(1))
                            main_program_name = self._extract_program_name(text)
                            
                            if main_program_name:
                                # Look for sub-programs within this item
                                sub_programs = self._extract_sub_programs(item)
                                
                                program_ranking = ProgramRanking(
                                    category=main_program_name,
                                    rank=main_rank,
                                    url=href,
                                    sub_programs=sub_programs
                                )
                                program_rankings.append(program_ranking)
                                processed_urls.add(href)
                                
                        except ValueError:
                            continue
        
        return program_rankings if program_rankings else None
    
    def _extract_sub_programs(self, item) -> Optional[List[SubProgramRanking]]:
        """Extract sub-program rankings from a program item."""
        
        sub_programs = []
        
        # Look for nested BadgeList items (sub-programs)
        # Pattern: <ul class="BadgeList-wn7t98-1 fBykJl pl0 ml3 mt4">
        nested_badge_lists = item.find_all('ul', class_=lambda x: x and 'BadgeList' in x)
        
        for badge_list in nested_badge_lists:
            # Pattern: <li class="BadgeList__ListItem-wn7t98-0 iBRHgY">
            list_items = badge_list.find_all('li', class_=lambda x: x and 'BadgeList__ListItem' in x)
            
            for sub_item in list_items:
                # Pattern: <div><div><a href="...">#X in Sub Program Name</a></div></div>
                sub_link = sub_item.find('a', href=True)
                if not sub_link:
                    continue
                
                href = sub_link.get('href', '')
                text = sub_link.get_text()
                
                # Extract sub-program ranking
                sub_rank_match = re.search(r'#(\d{1,4})', text)
                if sub_rank_match:
                    try:
                        sub_rank = int(sub_rank_match.group(1))
                        sub_program_name = self._extract_sub_program_name(text)
                        
                        if sub_program_name:
                            sub_program = SubProgramRanking(
                                sub_program_name=sub_program_name,
                                rank=sub_rank,
                                url=href
                            )
                            sub_programs.append(sub_program)
                            
                    except ValueError:
                        continue
        
        return sub_programs if sub_programs else None
    
    def _extract_sub_program_name(self, text: str) -> Optional[str]:
        """Extract sub-program name from ranking text."""
        
        # Try to extract program name from "in" pattern
        # e.g., "#13 in Artificial Intelligence", "#4 in Biocomputing/Bioinformatics/Biotechnology"
        match = re.search(r'in\s+(.+?)$', text, re.IGNORECASE)
        if match:
            program_name = match.group(1).strip()
            # Remove "(tie)" from the end
            program_name = re.sub(r'\s*\(tie\)\s*$', '', program_name, flags=re.IGNORECASE)
            if program_name:
                return program_name
        
        return None
    
    def _extract_program_name(self, text: str) -> Optional[str]:
        """Extract program name from ranking text."""
        
        # Try to extract program name from "in" pattern
        # e.g., "#5 in Computer Science", "#11 in Best Undergraduate Engineering Programs"
        match = re.search(r'in\s+(.+?)$', text, re.IGNORECASE)
        if match:
            program_name = match.group(1).strip()
            # Remove "(tie)" from the end
            program_name = re.sub(r'\s*\(tie\)\s*$', '', program_name, flags=re.IGNORECASE)
            if program_name:
                return program_name
        
        return None
    
    
    
    def _get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description from the page."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content')
        return None
    
    
    

