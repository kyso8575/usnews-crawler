"""
University ID Extractor

This module handles extracting university IDs from US News search results.
Separated for better code organization and reusability.
"""

import time
import re
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class UniversityIDExtractor:
    """Extracts university IDs from US News search results."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the ID extractor with Chrome WebDriver.
        
        Args:
            headless: Whether to run Chrome in headless mode (default: True)
        """
        self.headless = headless
        self.driver = None
        self.base_search_url = "https://www.usnews.com/search/education"
        
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
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Automatically download and set up ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def build_search_url(self, university_name: str) -> str:
        """
        Build the search URL for a university.
        
        Args:
            university_name: Name of the university to search for
            
        Returns:
            The constructed search URL
        """
        search_url = f"{self.base_search_url}?q={university_name}#gsc.tab=0&gsc.q={university_name}&gsc.page=1"
        return search_url
        
    def extract_university_links(self) -> List[str]:
        """
        Extract all university links from the current search results page.
        
        Returns:
            List of URLs pointing to university pages
        """
        university_links = []
        
        try:
            # Wait for search results to load
            wait = WebDriverWait(self.driver, 10)
            
            # Look for various possible selectors for search results
            selectors_to_try = [
                "a[href*='best-colleges']",
                "a[href*='premium.usnews.com']",
                ".gs-title a",
                ".gsc-thumbnail-inside a",
                "a[href*='usnews.com'][href*='university']",
                "a[href*='usnews.com'][href*='college']"
            ]
            
            for selector in selectors_to_try:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if links:
                        print(f"Found {len(links)} links using selector: {selector}")
                        for link in links:
                            href = link.get_attribute('href')
                            if href and ('best-colleges' in href or 'premium.usnews.com' in href):
                                university_links.append(href)
                        break
                except NoSuchElementException:
                    continue
            
            # If no links found with specific selectors, try all links
            if not university_links:
                print("Trying to find all links on the page...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and ('best-colleges' in href or 'premium.usnews.com' in href):
                        university_links.append(href)
                        
        except TimeoutException:
            print("Timeout waiting for search results to load")
            
        return university_links
    
    def extract_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract university ID from a US News university URL.
        
        Args:
            url: University page URL
            
        Returns:
            University ID if found, None otherwise
        """
        # Pattern to match university ID in URLs
        # Examples:
        # https://premium.usnews.com/best-colleges/harvard-university-2155/
        # https://www.usnews.com/best-colleges/harvard-university-2155
        patterns = [
            r'/best-colleges/[^/]+-(\d+)/?',
            r'/best-colleges/[^/]+-university-(\d+)/?',
            r'/best-colleges/[^/]+-college-(\d+)/?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_university_id(self, university_name: str) -> Optional[str]:
        """
        Main method to extract university ID by name.
        
        Args:
            university_name: Name of the university to search for
            
        Returns:
            University ID if found, None otherwise
        """
        try:
            # Set up the driver
            self.setup_driver()
            
            # Navigate to search page
            search_url = self.build_search_url(university_name)
            print(f"🔍 Searching for '{university_name}'...")
            print(f"Navigating to: {search_url}")
            self.driver.get(search_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Extract university links
            university_links = self.extract_university_links()
            
            if not university_links:
                print("❌ No university links found in search results")
                return None
            
            print(f"📋 Found {len(university_links)} potential university links:")
            for i, link in enumerate(university_links, 1):
                print(f"{i}. {link}")
                
            # Try to extract ID from each link
            for link in university_links:
                university_id = self.extract_id_from_url(link)
                if university_id:
                    print(f"\n✅ Found university ID: {university_id}")
                    print(f"📄 From URL: {link}")
                    return university_id
            
            print("❌ No university ID found in any of the links")
            return None
            
        except Exception as e:
            print(f"❌ Error during ID extraction: {str(e)}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()


# This module is designed to be imported and used by main_scraper.py
# For testing individual functionality, use main_scraper.py
