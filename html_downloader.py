"""
HTML Downloader

This module handles downloading HTML content from university pages.
Supports multiple page types: applying, overall-rankings, paying, academics.
Loads university information from universities.json file.
"""

import time
import os
import json
import re
from datetime import datetime
from typing import Optional, List, Dict
from selenium_base import SeleniumBase


class HTMLDownloader(SeleniumBase):
    """Downloads HTML content from US News university pages."""
    
    def __init__(self, headless: bool = True, truncate_at_widget: bool = True, universities_json: str = "universities.json"):
        """
        Initialize the HTML downloader with Chrome WebDriver.
        
        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            truncate_at_widget: If True, cut HTML at the blueshift recommendations widget if present
            universities_json: Path to the JSON file containing university information
        """
        super().__init__(headless=headless)
        self.truncate_at_widget = truncate_at_widget
        self.downloads_dir = "downloads"
        self.universities_json = universities_json
        self.universities = []
        # Supported page types
        self.page_types = ["applying", "overall-rankings", "paying", "academics"]
        
        # Load universities from JSON file
        self.load_universities()
    
    def load_universities(self):
        """Load university information from JSON file."""
        try:
            with open(self.universities_json, 'r', encoding='utf-8') as f:
                self.universities = json.load(f)
            print(f"✅ Loaded {len(self.universities)} universities from {self.universities_json}")
        except FileNotFoundError:
            print(f"❌ Universities JSON file not found: {self.universities_json}")
            self.universities = []
        except Exception as e:
            print(f"❌ Error loading universities JSON: {e}")
            self.universities = []
    
    def extract_university_id_from_link(self, link: str) -> Optional[str]:
        """
        Extract university ID from US News link.
        
        Args:
            link: University link (e.g., "/best-colleges/princeton-university-2627")
            
        Returns:
            University ID as string, or None if not found
        """
        # Pattern to match university ID at the end of the link
        pattern = r'-(\d+)$'
        match = re.search(pattern, link)
        if match:
            return match.group(1)
        return None
    
    def find_university_by_name(self, university_name: str) -> Optional[Dict]:
        """
        Find university information by name.
        
        Args:
            university_name: Name of the university to search for
            
        Returns:
            Dictionary with university info (name, link, id) or None if not found
        """
        university_name_lower = university_name.lower()
        
        for university in self.universities:
            if university_name_lower in university['name'].lower():
                university_id = self.extract_university_id_from_link(university['link'])
                return {
                    'name': university['name'],
                    'link': university['link'],
                    'id': university_id
                }
        
        print(f"❌ University '{university_name}' not found in the universities list")
        return None
    
    def list_all_universities(self) -> List[str]:
        """Return a list of all university names."""
        return [university['name'] for university in self.universities]
        
    def construct_url_from_link(self, link: str, page_type: str) -> str:
        """
        Construct full URL from university link and page type.
        
        Args:
            link: University link from JSON (e.g., "/best-colleges/princeton-university-2627")
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Full URL for the requested page
        """
        # Choose the correct base URL based on page type
        if page_type == "applying":
            base_url = "https://premium.usnews.com"
        else:
            base_url = "https://www.usnews.com"
        
        return f"{base_url}{link}/{page_type}"
    
    def create_downloads_directory(self):
        """Create downloads directory if it doesn't exist."""
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)
    
    def generate_filename_and_path(self, university_name: str, page_type: str) -> tuple:
        """
        Generate filename and directory path for the downloaded HTML file.
        
        Args:
            university_name: Name of the university
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Tuple of (directory_path, filename)
        """
        # Create safe directory name
        safe_name = university_name.replace(' ', '_').replace('&', 'and').replace(',', '').replace('.', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
        
        # Create university directory
        university_dir = os.path.join(self.downloads_dir, safe_name)
        
        # Simple filename based on page type
        filename = f"{page_type.replace('-', '_')}.html"
        
        return university_dir, filename
    
    def download_university_page(self, university_name: str, page_type: str) -> Optional[str]:
        """
        Download HTML content from a specific university page.
        
        Args:
            university_name: Name of the university (will be searched in universities.json)
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Path to the saved HTML file if successful, None otherwise
        """
        if page_type not in self.page_types:
            print(f"❌ Unsupported page type: {page_type}")
            print(f"Supported types: {', '.join(self.page_types)}")
            return None
        
        # Find university information
        university_info = self.find_university_by_name(university_name)
        if not university_info:
            return None
        
        university_id = university_info['id']
        university_link = university_info['link']
        actual_name = university_info['name']
        
        try:
            # Set up the driver if not already set up
            if not self.driver:
                self.setup_driver()
            
            # Construct the page URL using the link from JSON
            page_url = self.construct_url_from_link(university_link, page_type)
            
            print(f"📥 {page_type} 페이지 다운로드 중...")
            if not self.navigate_to(page_url, wait_time=1):
                return None
            
            # Get page source after stopping
            html_content = self.get_page_source()
            if not html_content:
                return None
            
            # Check for recommendations widget and handle accordingly
            if self.truncate_at_widget:
                cut_index = self._find_widget_cut_index(html_content)
                if cut_index is not None and cut_index > 0:
                    html_content = html_content[:cut_index] + "\n<!-- Truncated before recommendations widget -->\n"
            
            # Create downloads directory
            self.create_downloads_directory()
            
            # Generate directory and filename
            university_dir, filename = self.generate_filename_and_path(actual_name, page_type)
            
            # Create university directory if it doesn't exist
            if not os.path.exists(university_dir):
                os.makedirs(university_dir)
            
            file_path = os.path.join(university_dir, filename)
            
            # Save HTML content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ 저장됨: {filename} ({len(html_content):,}자)")
            
            return file_path
            
        except Exception as e:
            print(f"❌ Error downloading {page_type} page: {str(e)}")
            return None
    
    def download_all_pages(self, university_name: str) -> List[str]:
        """
        Download HTML content from all supported university pages.
        
        Args:
            university_name: Name of the university (will be searched in universities.json)
            
        Returns:
            List of paths to saved HTML files
        """
        downloaded_files = []
        
        # Find university information first
        university_info = self.find_university_by_name(university_name)
        if not university_info:
            return downloaded_files
        
        university_id = university_info['id']
        actual_name = university_info['name']
        
        try:
            print(f"📚 Downloading all pages for {actual_name} (ID: {university_id})")
            print("=" * 60)
            
            for i, page_type in enumerate(self.page_types, 1):
                print(f"\n📖 [{i}/{len(self.page_types)}] Downloading {page_type} page...")
                print("-" * 40)
                
                # 각 페이지마다 새로운 드라이버 시작
                self.setup_driver()
                
                file_path = self.download_university_page(university_name, page_type)
                if file_path:
                    downloaded_files.append(file_path)
                else:
                    print(f"❌ {page_type} 페이지 다운로드 실패")
                
                # 페이지 다운로드 후 드라이버 종료
                self.close()
                
                # Delay between downloads to be respectful to the server
                if i < len(self.page_types):
                    print("⏳ Waiting 5 seconds before next download...")
                    time.sleep(5)
            
            print(f"\n🎉 Download Summary:")
            print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(self.page_types)} pages")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error during batch download: {str(e)}")
            return downloaded_files
            
        finally:
            self.close()

    def _find_widget_cut_index(self, html_content: str):
        """Return the index to cut HTML before the recommendations widget, or None if not found."""
        # 여러 종류의 추천 위젯을 찾아서 가장 먼저 나타나는 것 선택
        markers = [
            '<div id="blueshift-recommendations-widget"',
            'id="blueshift-recommendations-widget"',
            'blueshift-recommendations-widget',
            '<div id="null-recommendations-widget"',
            'id="null-recommendations-widget"',
            'null-recommendations-widget',
            'SailthruRecommend__Container'
        ]
        
        earliest_index = None
        for marker in markers:
            idx = html_content.find(marker)
            if idx != -1:
                if earliest_index is None or idx < earliest_index:
                    earliest_index = idx
        
        return earliest_index
    
    

# This module is designed to be imported and used by main_scraper.py
# For testing individual functionality, use main_scraper.py
