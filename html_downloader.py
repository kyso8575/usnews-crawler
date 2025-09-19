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
from typing import Optional, List, Dict
from selenium_base import SeleniumBase


class HTMLDownloader(SeleniumBase):
    """Downloads HTML content from US News university pages."""
    
    def __init__(self, headless: bool = True, truncate_at_widget: bool = True, universities_json: str = "universities.json", use_existing_chrome: bool = False, enable_api_collection: bool = False):
        """
        Initialize the HTML downloader with Chrome WebDriver.
        
        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            truncate_at_widget: If True, cut HTML at the blueshift recommendations widget if present
            universities_json: Path to the JSON file containing university information
            use_existing_chrome: Whether to connect to existing Chrome browser (default: False)
            enable_api_collection: Whether to enable API response collection (default: False)
        """
        # API 수집이 필요한 경우에만 네트워크 모니터링 활성화
        super().__init__(headless=headless, use_existing_chrome=use_existing_chrome, enable_network_monitoring=enable_api_collection)
        self.truncate_at_widget = truncate_at_widget
        self.downloads_dir = "downloads"
        self.universities_json = universities_json
        self.universities = []
        self.enable_api_collection = enable_api_collection
        # Supported page types
        self.page_types = ["", "overall-rankings", "applying", "paying", "academics", "student-life", "campus-info"]
        
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
            page_type: Type of page ("", overall-rankings, applying, paying, academics, student-life, campus-info)
            
        Returns:
            Full URL for the requested page
        """
        # All pages use premium.usnews.com as the base URL
        base_url = "https://premium.usnews.com"
        
        # For empty page_type (main page), don't add the slash and page_type
        if page_type == "":
            return f"{base_url}{link}"
        else:
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
        if page_type == "":
            filename = "main.html"
        else:
            filename = f"{page_type.replace('-', '_')}.html"
        
        return university_dir, filename
    
    def download_university_page(self, university_name: str, page_type: str, university_info: Optional[Dict] = None) -> Optional[str]:
        """
        Download HTML content from a specific university page.
        
        Args:
            university_name: Name of the university (will be searched in universities.json)
            page_type: Type of page (applying, overall-rankings, paying, academics)
            university_info: Pre-fetched university info to avoid redundant lookups
            
        Returns:
            Path to the saved HTML file if successful, None otherwise
        """
        if page_type not in self.page_types:
            print(f"❌ Unsupported page type: {page_type}")
            print(f"Supported types: {', '.join(self.page_types)}")
            return None
        
        # Use provided university info or find it
        if university_info is None:
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
            
            # applying 페이지이고 API 수집이 활성화된 경우에만 모니터링 패턴 추가
            if page_type == "applying" and self.enable_api_collection:
                self.add_monitoring_pattern("/best-colleges/compass/api/admissions-calculator?school_id=")
                print("📡 API 응답 모니터링 시작...")
            
            # Construct the page URL using the link from JSON
            page_url = self.construct_url_from_link(university_link, page_type)
            
            page_display_name = "main" if page_type == "" else page_type
            print(f"📥 {page_display_name} 페이지 다운로드 중...")
            
            # 재시도 로직: 최대 2번 시도 (첫 시도 + 1번 재시도)
            max_retries = 1
            retry_count = 0
            
            while retry_count <= max_retries:
                if not self.navigate_to(page_url, wait_time=10):
                    return None
                
                # Check HTTP response status first
                if self.is_error_response():
                    error_type = self.get_error_type()
                    
                    # 영구적 에러 (404, 403 등)인 경우 즉시 건너뛰기
                    if self.is_permanent_error():
                        print(f"⚠️ {page_display_name} 페이지 건너뜀 - {error_type}")
                        return None
                    
                    # 일시적 에러인 경우 재시도
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"⚠️ {page_display_name} 페이지 에러 ({error_type}) - 1분 후 재시도 ({retry_count}/{max_retries})")
                        time.sleep(60)  # 1분 대기
                        
                        # 드라이버 재시작으로 깨끗한 상태에서 재시도
                        self.close()
                        continue
                    else:
                        print(f"❌ {page_display_name} 페이지 재시도 실패 - {error_type}")
                        return None
                else:
                    # 에러가 없으면 정상 처리
                    break
            
            # Get page source after confirming it's not an error
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
            
            # applying 페이지이고 API 수집이 활성화된 경우에만 API 응답 저장
            if page_type == "applying" and self.enable_api_collection:
                api_filename = filename.replace('.html', '_api_responses.txt')
                api_file_path = os.path.join(university_dir, api_filename)
                
                # API 응답 수집 및 저장
                print(f"📡 API 응답 수집 중... (7초 대기)")
                time.sleep(7)  # API 호출이 완료될 때까지 충분히 대기
                
                if self.save_api_responses_to_file("/best-colleges/compass/api/admissions-calculator?school_id=", api_file_path):
                    print(f"✅ API 응답 저장됨: {api_filename}")
                else:
                    if self.use_existing_chrome:
                        print(f"⚠️ 기존 Chrome에서는 API 응답 수집이 제한됩니다. HTML은 정상 저장됨.")
                    else:
                        print(f"⚠️ API 응답을 찾을 수 없습니다. (페이지에 calculator가 없을 수 있음)")
            
            # 개별 페이지에서는 캐시 정리하지 않음 (학교 단위로 정리)
            
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
        
        try:
            print(f"📚 Downloading all pages for {university_info['name']} (ID: {university_info['id']})")
            print("=" * 60)
            
            for i, page_type in enumerate(self.page_types, 1):
                page_display_name = "main" if page_type == "" else page_type
                print(f"\n📖 [{i}/{len(self.page_types)}] Downloading {page_display_name} page...")
                print("-" * 40)
                
                # 각 페이지마다 새로운 드라이버 시작
                self.setup_driver()
                
                # applying 페이지이고 API 수집이 활성화된 경우에만 모니터링 패턴 추가
                if page_type == "applying" and self.enable_api_collection:
                    self.add_monitoring_pattern("/best-colleges/compass/api/admissions-calculator?school_id=")
                
                file_path = self.download_university_page(university_name, page_type, university_info)
                if file_path:
                    downloaded_files.append(file_path)
                else:
                    page_display_name = "main" if page_type == "" else page_type
                    print(f"⏭️ {page_display_name} 페이지 건너뜀 (페이지가 존재하지 않거나 오류 발생)")
                
                # 페이지 다운로드 후 드라이버 종료
                self.close()
                
                # Delay between downloads to be respectful to the server
                if i < len(self.page_types):
                    print("⏳ Waiting 10 seconds before next download...")
                    time.sleep(10)
            
            print(f"\n🎉 Download Summary:")
            print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(self.page_types)} pages")
            
            # 학교 전체 다운로드 완료 후 최종 캐시 정리
            print(f"🧹 {university_info['name']} 학교 다운로드 완료 - 최종 캐시 정리 중...")
            if self.driver:
                self.clear_cache_and_data()
            
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
    
