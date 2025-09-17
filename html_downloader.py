"""
HTML Downloader

This module handles downloading HTML content from university pages.
Supports multiple page types: applying, overall-rankings, paying, academics.
Uses the university ID extracted by the UniversityIDExtractor.
"""

import time
import os
from datetime import datetime
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class HTMLDownloader:
    """Downloads HTML content from US News university pages."""
    
    def __init__(self, headless: bool = True, truncate_at_widget: bool = True):
        """
        Initialize the HTML downloader with Chrome WebDriver.
        
        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            truncate_at_widget: If True, cut HTML at the blueshift recommendations widget if present
        """
        self.headless = headless
        self.truncate_at_widget = truncate_at_widget
        self.driver = None
        self.downloads_dir = "downloads"
        # Supported page types
        self.page_types = ["applying", "overall-rankings", "paying", "academics"]
        
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # HTTP/2 and network protocol fixes
        chrome_options.add_argument("--disable-http2")  # Disable HTTP/2 to prevent protocol errors
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-extensions")
        
        # User agent to appear more like a regular browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # Automatically download and set up ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def construct_university_url_name(self, university_name: str) -> str:
        """
        Construct the university name format used in US News URLs.
        
        Args:
            university_name: Original university name
            
        Returns:
            Formatted university name for URL construction
        """
        # Convert to lowercase and replace spaces with hyphens
        formatted_name = university_name.lower().replace(' ', '-')
        
        # Add 'university' if not present
        if 'university' not in formatted_name and 'college' not in formatted_name:
            formatted_name += '-university'
            
        return formatted_name
    
    def create_downloads_directory(self):
        """Create downloads directory if it doesn't exist."""
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)
            print(f"📁 Created downloads directory: {self.downloads_dir}")
    
    def generate_filename(self, university_name: str, university_id: str, page_type: str) -> str:
        """
        Generate filename for the downloaded HTML file.
        
        Args:
            university_name: Name of the university
            university_id: University ID
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = university_name.lower().replace(' ', '_').replace('-', '_')
        safe_page_type = page_type.replace('-', '_')
        filename = f"{safe_name}_{university_id}_{safe_page_type}_{timestamp}.html"
        return filename
    
    def download_university_page(self, university_name: str, university_id: str, page_type: str) -> Optional[str]:
        """
        Download HTML content from a specific university page.
        
        Args:
            university_name: Name of the university
            university_id: University ID extracted from search results
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Path to the saved HTML file if successful, None otherwise
        """
        if page_type not in self.page_types:
            print(f"❌ Unsupported page type: {page_type}")
            print(f"Supported types: {', '.join(self.page_types)}")
            return None
            
        try:
            # Set up the driver if not already set up
            if not self.driver:
                self.setup_driver()
            
            # Construct the page URL
            formatted_name = self.construct_university_url_name(university_name)
            
            # Choose the correct base URL based on page type
            if page_type == "applying":
                base_url = "https://premium.usnews.com/best-colleges"
            else:
                base_url = "https://www.usnews.com/best-colleges"
            
            page_url = f"{base_url}/{formatted_name}-{university_id}/{page_type}"
            
            print(f"🌐 Navigating to {page_type} page...")
            print(f"📍 URL: {page_url}")
            
            # Navigate to the page
            self.driver.get(page_url)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Wait for specific content to ensure page is fully loaded
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("✅ Page loaded successfully")
            except TimeoutException:
                print("⚠️ Timeout waiting for page to load, proceeding anyway...")
            
            # Get page source
            html_content = self.driver.page_source
            
            # Optionally truncate before recommendations widget
            if self.truncate_at_widget:
                cut_index = self._find_widget_cut_index(html_content)
                if cut_index is not None and cut_index > 0:
                    print("✂️  Truncating HTML before recommendations widget")
                    html_content = html_content[:cut_index] + "\n<!-- Truncated before blueshift-recommendations-widget -->\n"
            
            # Create downloads directory
            self.create_downloads_directory()
            
            # Generate filename and path
            filename = self.generate_filename(university_name, university_id, page_type)
            file_path = os.path.join(self.downloads_dir, filename)
            
            # Save HTML content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"💾 HTML content saved successfully!")
            print(f"📄 File: {file_path}")
            print(f"📊 Size: {len(html_content):,} characters")
            
            # Get page title for additional info
            try:
                page_title = self.driver.title
                print(f"📝 Page title: {page_title}")
            except:
                pass
            
            return file_path
            
        except Exception as e:
            print(f"❌ Error downloading {page_type} page: {str(e)}")
            return None
    
    def download_applying_page(self, university_name: str, university_id: str) -> Optional[str]:
        """
        Download HTML content from the university's applying page.
        (Backward compatibility method)
        
        Args:
            university_name: Name of the university
            university_id: University ID extracted from search results
            
        Returns:
            Path to the saved HTML file if successful, None otherwise
        """
        return self.download_university_page(university_name, university_id, "applying")
    
    def download_all_pages(self, university_name: str, university_id: str) -> List[str]:
        """
        Download HTML content from all supported university pages.
        
        Args:
            university_name: Name of the university
            university_id: University ID extracted from search results
            
        Returns:
            List of paths to saved HTML files
        """
        downloaded_files = []
        
        try:
            # Set up the driver once for all downloads
            self.setup_driver()
            
            print(f"📚 Downloading all pages for {university_name} (ID: {university_id})")
            print("=" * 60)
            
            for i, page_type in enumerate(self.page_types, 1):
                print(f"\n📖 [{i}/{len(self.page_types)}] Downloading {page_type} page...")
                print("-" * 40)
                
                file_path = self.download_university_page(university_name, university_id, page_type)
                if file_path:
                    downloaded_files.append(file_path)
                    print(f"✅ {page_type} page downloaded successfully")
                else:
                    print(f"❌ Failed to download {page_type} page")
                
                # Delay between downloads to be respectful to the server
                if i < len(self.page_types):
                    print("⏳ Waiting 10 seconds before next download...")
                    time.sleep(10)
            
            print(f"\n🎉 Download Summary:")
            print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(self.page_types)} pages")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error during batch download: {str(e)}")
            return downloaded_files
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

    def _find_widget_cut_index(self, html_content: str):
        """Return the index to cut HTML before the recommendations widget, or None if not found."""
        markers = [
            '<div id="blueshift-recommendations-widget"',
            'id="blueshift-recommendations-widget"',
            'blueshift-recommendations-widget'
        ]
        for marker in markers:
            idx = html_content.find(marker)
            if idx != -1:
                return idx
        return None


# This module is designed to be imported and used by main_scraper.py
# For testing individual functionality, use main_scraper.py
