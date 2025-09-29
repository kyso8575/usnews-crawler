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
import hashlib
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from .selenium_base import SeleniumBase, SeleniumConfig

logger = logging.getLogger("usnews_scraper.html_downloader")


# ===================== Module-level Constants =====================
# Supported page types (align with selenium_base.py constant style)
PAGE_TYPES = [
    "",  # main
    "overall-rankings",
    "applying",
    "paying",
    "academics",
    "student-life",
    "campus-info",
]

# Base URL for premium pages
BASE_URL = "https://premium.usnews.com"

# Common origins for session capture/application
USNEWS_ORIGINS = [
    "https://www.usnews.com",
    "https://premium.usnews.com",
]

# Compiled regex for canonical link extraction
CANONICAL_RE = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)', re.IGNORECASE)


@dataclass
class DownloaderConfig:
    truncate_at_widget: bool = True
    downloads_dir: str = "downloads"
    wait_success_seconds: int = 15
    wait_skip_seconds: int = 15
    page_type_overrides: Optional[Dict[str, Dict[str, int]]] = None
    preserve_login_from_existing: bool = False


class HTMLDownloader(SeleniumBase):
    """Downloads HTML content from US News university pages."""
    
    def __init__(self, universities_json: str = "data/universities.json", headless: bool = True, use_existing_chrome: bool = False, selenium_config: Optional[SeleniumConfig] = None, downloader_config: Optional[DownloaderConfig] = None):
        """
        Initialize the HTML downloader with Chrome WebDriver.
        
        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            truncate_at_widget: If True, cut HTML at the blueshift recommendations widget if present
            universities_json: Path to the JSON file containing university information
            use_existing_chrome: Whether to connect to existing Chrome browser (default: False)
            preserve_login_from_existing: Capture session from existing Chrome and apply to new drivers
            downloads_dir: Output directory for saved HTML files (default: "downloads")
            config: Optional SeleniumConfig to control timeouts and behavior
        """
        dc = downloader_config or DownloaderConfig()
        super().__init__(headless=headless, use_existing_chrome=use_existing_chrome, config=selenium_config)
        self.truncate_at_widget = dc.truncate_at_widget
        self.downloads_dir = dc.downloads_dir
        self.universities_json = universities_json
        self.universities = []
        self.preserve_login_from_existing = dc.preserve_login_from_existing
        # Inter-download wait times
        self.wait_success_seconds = dc.wait_success_seconds
        self.wait_skip_seconds = dc.wait_skip_seconds
        # Per page-type overrides: { page_type: {"timeout": int, "retries": int} }
        self.page_type_overrides: Dict[str, Dict[str, int]] = dc.page_type_overrides or {}
        # Redirect handling
        self.redirect_retry_max = 1
        # Supported page types
        self.page_types = list(PAGE_TYPES)
        # Per-university dedupe store (reset per university in download_all_pages)
        self._current_university_hashes: set[str] = set()
        
        # Load universities from JSON file
        self.load_universities()
        
        # 기존 Chrome 세션에서 로그인 상태 보존이 필요한 경우 세션 캡처
        if self.preserve_login_from_existing and not self.use_existing_chrome:
            try:
                if self.capture_session_from_existing(USNEWS_ORIGINS):
                    logger.info("🔐 기존 Chrome의 로그인 세션을 캡처했습니다.")
                else:
                    logger.warning("⚠️ 기존 Chrome 세션 캡처에 실패했습니다. 로그인 유지 없이 진행합니다.")
            except Exception as e:
                logger.warning(f"⚠️ 세션 캡처 중 오류: {e}")
    
    def load_universities(self):
        """Load university information from JSON file."""
        try:
            with open(self.universities_json, 'r', encoding='utf-8') as f:
                self.universities = json.load(f)
            logger.info(f"✅ Loaded {len(self.universities)} universities from {self.universities_json}")
        except FileNotFoundError:
            logger.error(f"❌ Universities JSON file not found: {self.universities_json}")
            self.universities = []
        except Exception as e:
            logger.error(f"❌ Error loading universities JSON: {e}")
            self.universities = []
    

    
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
                return {
                    'name': university['name'],
                    'link': university['link'],
                }
        
        logger.error(f"❌ University '{university_name}' not found in the universities list")
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
        # Normalize page type to avoid double slashes
        page_type = (page_type or "").strip("/")

        # Validate and normalize link; allow absolute URL or relative path
        if not isinstance(link, str) or not link:
            return BASE_URL
        if "://" in link:
            path = urlparse(link).path
        else:
            path = link

        # Ensure leading slash on path
        if not path.startswith("/"):
            path = "/" + path

        # Compose final URL using module-level BASE_URL
        if page_type == "":
            return f"{BASE_URL}{path}"
        return f"{BASE_URL}{path}/{page_type}"
    
    def create_downloads_directory(self):
        """Create downloads directory if it doesn't exist."""
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def generate_filename_and_path(self, university_name: str, page_type: str) -> Tuple[str, str]:
        """
        Generate filename and directory path for the downloaded HTML file.
        
        Args:
            university_name: Name of the university
            page_type: Type of page (applying, overall-rankings, paying, academics)
            
        Returns:
            Tuple of (directory_path, filename)
        """
        # Create safe directory name
        safe_name = self._slugify_name(university_name)
        
        # Create university directory
        university_dir = os.path.join(self.downloads_dir, safe_name)
        
        # Simple filename based on page type
        if page_type == "":
            filename = "main.html"
        else:
            filename = f"{page_type.replace('-', '_')}.html"
        
        return university_dir, filename

    def _slugify_name(self, name: str) -> str:
        """Normalize university name to a safe directory slug."""
        normalized = name.replace(' ', '_').replace('&', 'and').replace(',', '').replace('.', '')
        normalized = ''.join(c for c in normalized if c.isalnum() or c in '_-')
        return normalized
    
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
            logger.error(f"❌ Unsupported page type: {page_type}")
            logger.info(f"Supported types: {', '.join(self.page_types)}")
            return None
        
        # Use provided university info or find it
        if university_info is None:
            university_info = self.find_university_by_name(university_name)
            if not university_info:
                return None
        
        university_link = university_info['link']
        actual_name = university_info['name']
        
        try:
            # ---- 작은 헬퍼들로 로직 분리 ----
            def _ensure_driver_and_session() -> None:
                if not self.driver:
                    self.setup_driver()
                    if self.preserve_login_from_existing and not self.use_existing_chrome:
                        try:
                            self.apply_session_to_current_driver(USNEWS_ORIGINS)
                        except Exception:
                            pass

            def _navigate_with_timeout_override(url: str, timeout_override: Optional[int], wait_seconds: int) -> bool:
                original_timeout_local = None
                if timeout_override is not None:
                    original_timeout_local = self.config.page_load_timeout
                    self.config.page_load_timeout = int(timeout_override)
                try:
                    return self.navigate_to(url, wait_time=wait_seconds)
                finally:
                    if original_timeout_local is not None:
                        self.config.page_load_timeout = original_timeout_local

            def _redirected_to_main(current_url_value: str, html_text: str, expected_page_type: str) -> bool:
                # 경로 세그먼트 기준으로 좀 더 엄격히 확인
                from urllib.parse import urlparse as _urlparse
                if not expected_page_type:
                    return False
                def _ends_with_segment(full_url: str, segment: str) -> bool:
                    segs = [s for s in _urlparse(full_url).path.split('/') if s]
                    return len(segs) > 0 and segs[-1] == segment
                if current_url_value and not _ends_with_segment(current_url_value, expected_page_type):
                    return True
                canonical_match_local = CANONICAL_RE.search(html_text)
                if canonical_match_local:
                    canonical_href_local = canonical_match_local.group(1)
                    if not _ends_with_segment(canonical_href_local, expected_page_type):
                        return True
                return False

            def _save_html(html_text: str, uni_name: str, ptype: str, display_name: str) -> Optional[str]:
                try:
                    logger.info(f"💾 {display_name} 파일 저장 중...")
                    self.create_downloads_directory()
                    university_dir_local, filename_local = self.generate_filename_and_path(uni_name, ptype)
                    os.makedirs(university_dir_local, exist_ok=True)
                    file_path_local = os.path.join(university_dir_local, filename_local)
                    
                    # 해시 계산 (중복 검사용)
                    try:
                        content_hash_local = hashlib.sha256(html_text.encode('utf-8')).hexdigest()
                    except Exception as e:
                        logger.warning(f"⚠️ 해시 계산 실패: {e}")
                        content_hash_local = None
                    
                    # 중복 검사
                    if content_hash_local and content_hash_local in self._current_university_hashes:
                        logger.info(f"⏭️ {display_name} 중복 콘텐츠 감지 - 저장 건너뜀")
                        return None
                    
                    # 파일 저장
                    with open(file_path_local, 'w', encoding='utf-8') as f:
                        f.write(html_text)
                    
                    # 해시 저장
                    if content_hash_local:
                        self._current_university_hashes.add(content_hash_local)
                    
                    logger.info(f"✅ 저장 완료: {filename_local} ({len(html_text):,}자)")
                    return file_path_local
                    
                except Exception as e:
                    logger.error(f"❌ {display_name} 파일 저장 실패: {str(e)}")
                    return None

            # ---- 본 로직 ----
            _ensure_driver_and_session()

            page_url = self.construct_url_from_link(university_link, page_type)
            page_display_name = "main" if page_type == "" else page_type
            logger.info(f"📥 {page_display_name} 페이지 다운로드 중...")

            override = self.page_type_overrides.get(page_type, {})
            max_retries = int(override.get("retries", 3))
            retry_count = 0
            redirect_retry_left = 1
            nav_wait_seconds = getattr(self.config, 'post_render_wait_seconds', 10)

            while retry_count <= max_retries:
                timeout_override = int(override["timeout"]) if "timeout" in override else None
                nav_ok = _navigate_with_timeout_override(page_url, timeout_override, nav_wait_seconds)
                if not nav_ok:
                    return None

                if self.is_error_response():
                    error_type = self.get_error_type()
                    if self.is_permanent_error():
                        logger.warning(f"⚠️ {page_display_name} 페이지 건너뜀 - {error_type}")
                        return None
                    if retry_count < max_retries:
                        retry_count += 1
                        backoff = getattr(self.config, 'retry_backoff_seconds', 60)
                        logger.warning(f"⚠️ {page_display_name} 페이지 에러 ({error_type}) - {backoff}초 후 재시도 ({retry_count}/{max_retries})")
                        time.sleep(backoff)
                        logger.info("🔄 드라이버 재시작 중...")
                        self._restart_chrome()
                        continue
                    logger.error(f"❌ {page_display_name} 페이지 재시도 실패 - {error_type}")
                    return None
                break

            # HTML 콘텐츠 가져오기 (타임아웃 및 재시도 로직 추가)
            html_content = None
            content_retry_count = 0
            max_content_retries = 2
            content_timeout = 30  # 30초 타임아웃
            
            while content_retry_count <= max_content_retries:
                try:
                    current_url = self.driver.current_url if self.driver else ""
                    logger.info(f"📄 HTML 콘텐츠 추출 중... (시도 {content_retry_count + 1}/{max_content_retries + 1})")
                    
                    # 타임아웃을 위한 시그널 처리
                    import signal
                    def timeout_handler(signum, frame):
                        raise TimeoutError("HTML 콘텐츠 추출 타임아웃")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(content_timeout)
                    
                    try:
                        html_content = self.get_page_source()
                    finally:
                        signal.alarm(0)  # 타임아웃 해제
                    
                    if not html_content:
                        logger.error("❌ HTML 콘텐츠가 비어있습니다")
                        if content_retry_count < max_content_retries:
                            content_retry_count += 1
                            logger.warning(f"⚠️ HTML 콘텐츠 추출 재시도 ({content_retry_count}/{max_content_retries})")
                            time.sleep(5)
                            continue
                        return None
                    
                    if len(html_content) < 1000:
                        logger.warning(f"⚠️ HTML 콘텐츠가 너무 짧습니다 ({len(html_content)}자)")
                    
                    logger.info(f"✅ HTML 콘텐츠 추출 성공 ({len(html_content):,}자)")
                    break  # 성공 시 루프 탈출
                    
                except TimeoutError:
                    logger.warning(f"⚠️ HTML 콘텐츠 추출 타임아웃 ({content_timeout}초)")
                    if content_retry_count < max_content_retries:
                        content_retry_count += 1
                        logger.warning(f"⚠️ HTML 콘텐츠 추출 재시도 ({content_retry_count}/{max_content_retries})")
                        time.sleep(5)
                        continue
                    else:
                        logger.error(f"❌ HTML 콘텐츠 추출 최종 실패 - 타임아웃")
                        return None
                        
                except Exception as e:
                    logger.error(f"❌ HTML 콘텐츠 추출 실패: {str(e)}")
                    if content_retry_count < max_content_retries:
                        content_retry_count += 1
                        logger.warning(f"⚠️ HTML 콘텐츠 추출 재시도 ({content_retry_count}/{max_content_retries})")
                        time.sleep(5)
                        continue
                    else:
                        return None
            
            if html_content is None:
                logger.error("❌ HTML 콘텐츠 추출 최종 실패")
                return None

            if page_type != "":
                if _redirected_to_main(current_url, html_content, page_type):
                    if redirect_retry_left > 0:
                        logger.info(f"🔁 Redirect detected for '{page_display_name}' - attempting session reapply and retry (1/1)")
                        try:
                            if self.preserve_login_from_existing and not self.use_existing_chrome:
                                self.apply_session_to_current_driver(USNEWS_ORIGINS)
                            if not self.navigate_to(page_url, wait_time=nav_wait_seconds, do_precheck=True):
                                return None
                            try:
                                current_url = self.driver.current_url if self.driver else ""
                                logger.info("📄 리다이렉트 후 HTML 콘텐츠 재추출 중...")
                                html_content = self.get_page_source()
                                if not html_content:
                                    logger.error("❌ 리다이렉트 후 HTML 콘텐츠가 비어있습니다")
                                    return None
                                logger.info(f"✅ 리다이렉트 후 HTML 콘텐츠 추출 성공 ({len(html_content):,}자)")
                            except Exception as e:
                                logger.error(f"❌ 리다이렉트 후 HTML 콘텐츠 추출 실패: {str(e)}")
                                return None
                        finally:
                            redirect_retry_left -= 1
                    if _redirected_to_main(current_url, html_content, page_type):
                        logger.info(f"⏭️ Skipping save for '{page_type}' - redirected to main page (avoiding duplicate).")
                        return None

            # 로그인 상태 확인
            is_logged_in = self._check_login_status(html_content)
            if not is_logged_in:
                logger.warning(f"⚠️ {page_display_name} 페이지가 로그인되지 않은 상태로 다운로드됨")
                logger.info("🔄 Chrome 재시작 및 로그인 재시도 중...")
                
                # Chrome 재시작 및 로그인 재시도
                if self._restart_chrome_and_relogin():
                    # 재로그인 후 페이지 다시 다운로드 시도
                    logger.info(f"🔄 {page_display_name} 페이지 재다운로드 시도...")
                    nav_ok = _navigate_with_timeout_override(page_url, timeout_override, nav_wait_seconds)
                    if nav_ok:
                        try:
                            html_content = self.get_page_source()
                            if html_content:
                                # 재로그인 후 로그인 상태 재확인
                                is_logged_in_retry = self._check_login_status(html_content)
                                if is_logged_in_retry:
                                    logger.info(f"✅ {page_display_name} 페이지 재로그인 성공")
                                else:
                                    logger.warning(f"⚠️ {page_display_name} 페이지 재로그인 후에도 비로그인 상태")
                            else:
                                logger.error(f"❌ {page_display_name} 페이지 재다운로드 실패 - HTML 콘텐츠 없음")
                        except Exception as e:
                            logger.error(f"❌ {page_display_name} 페이지 재다운로드 실패: {e}")
                    else:
                        logger.error(f"❌ {page_display_name} 페이지 재다운로드 실패 - 네비게이션 실패")
                else:
                    logger.error(f"❌ Chrome 재시작 및 로그인 재시도 실패")
            else:
                logger.info(f"✅ {page_display_name} 페이지 로그인 상태 확인됨")

            # 위젯 제거 처리
            try:
                if self.truncate_at_widget:
                    logger.info("✂️ 추천 위젯 제거 확인 중...")
                    cut_index = self._find_widget_cut_index(html_content)
                    if cut_index is not None and cut_index > 0:
                        original_length = len(html_content)
                        html_content = html_content[:cut_index] + "\n<!-- Truncated before recommendations widget -->\n"
                        logger.info(f"✂️ 추천 위젯 제거됨 ({original_length:,}자 → {len(html_content):,}자)")
                    else:
                        logger.info("✅ 추천 위젯 없음 - 원본 콘텐츠 유지")
            except Exception as e:
                logger.warning(f"⚠️ 위젯 제거 중 오류 (원본 유지): {str(e)}")

            # 파일 저장
            return _save_html(html_content, actual_name, page_type, page_display_name)

        except Exception as e:
            logger.error(f"❌ Error downloading {page_type} page: {str(e)}")
            backoff = getattr(self.config, 'retry_backoff_seconds', 60)
            logger.info(f"⏰ 에러 발생으로 인한 {backoff}초 대기...")
            time.sleep(backoff)
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
            # ---- 작은 헬퍼들 ----
            def _apply_login_session_with_timeout(timeout_seconds: int) -> bool:
                """기존 크롬 세션을 현재 드라이버에 적용 (타임아웃 지원)."""
                try:
                    import signal
                    def timeout_handler(signum, frame):
                        raise TimeoutError("로그인 세션 적용 타임아웃")
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(max(1, int(timeout_seconds)))
                    self.apply_session_to_current_driver(USNEWS_ORIGINS)
                    signal.alarm(0)
                    return True
                except TimeoutError:
                    try:
                        import signal as _s
                        _s.alarm(0)
                    except Exception:
                        pass
                    logger.warning("⚠️ 로그인 세션 적용 타임아웃")
                    return False
                except Exception as e:
                    try:
                        import signal as _s
                        _s.alarm(0)
                    except Exception:
                        pass
                    logger.warning(f"⚠️ 로그인 세션 적용 실패: {e}")
                    return False

            def _apply_login_session_with_retries(max_attempts: int = 3) -> bool:
                """재시도와 드라이버 재시작을 포함하여 세션 적용을 시도."""
                attempts = 0
                login_timeout = int(getattr(self.config, 'origin_nav_timeout', 30))
                restart_pause = float(getattr(self.config, 'restart_pause_seconds', 2))
                while attempts < max_attempts:
                    attempts += 1
                    logger.info(f"🔐 로그인 세션 적용 시도 중... ({attempts}/{max_attempts})")
                    ok = _apply_login_session_with_timeout(login_timeout)
                    if ok:
                        logger.info("🔐 로그인 세션 적용 완료 (학교 단위)")
                        return True
                    if attempts < max_attempts:
                        logger.info("🔄 드라이버 재시작 후 로그인 재시도...")
                        try:
                            self.close()
                            time.sleep(restart_pause)
                            self.setup_driver()
                            logger.info(f"✅ 드라이버 재시작 완료 - 로그인 재시도 {attempts + 1}/{max_attempts}")
                        except Exception as restart_e:
                            logger.error(f"❌ 드라이버 재시작 실패: {restart_e}")
                            break
                logger.error(f"❌ {max_attempts}회 시도 후 로그인 실패 - 로그인 없이 계속 진행")
                try:
                    self.close()
                    self.setup_driver()
                    logger.info("🔄 드라이버 최종 재시작 완료")
                except Exception:
                    logger.error("❌ 최종 드라이버 재시작 실패")
                return False

            # 대학교 폴더 존재 여부 확인
            university_dir, _ = self.generate_filename_and_path(university_info['name'], "")
            if os.path.exists(university_dir):
                existing_files = [f for f in os.listdir(university_dir) if f.endswith('.html')]
                expected_pages = len(self.page_types)
                
                if len(existing_files) >= expected_pages:
                    logger.info(f"⏭️ {university_info['name']} 이미 완전히 다운로드됨 - 스킵")
                    logger.info(f"📁 기존 파일: {len(existing_files)}개 (완료)")
                    return [os.path.join(university_dir, f) for f in existing_files]
                elif len(existing_files) > 0:
                    logger.info(f"⚠️ {university_info['name']} 부분적으로만 다운로드됨 ({len(existing_files)}/{expected_pages}개)")
                    logger.info(f"🔄 나머지 페이지 다운로드를 계속합니다...")
                    # 부분 다운로드인 경우 계속 진행
            
            logger.info(f"📚 Downloading all pages for {university_info['name']}")
            logger.info("=" * 60)
            
            # 학교 단위로 드라이버 1회만 생성하여 모든 페이지 처리 (속도 향상)
            self.setup_driver()
            if self.preserve_login_from_existing and not self.use_existing_chrome:
                _apply_login_session_with_retries(max_attempts=3)

            # Reset per-university dedupe store
            self._current_university_hashes = set()

            for i, page_type in enumerate(self.page_types, 1):
                page_display_name = "main" if page_type == "" else page_type
                logger.info(f"\n📖 [{i}/{len(self.page_types)}] Downloading {page_display_name} page...")
                logger.info("-" * 40)
                
                # API 수집 로직 제거됨
                
                file_path = self.download_university_page(university_name, page_type, university_info)
                if file_path:
                    downloaded_files.append(file_path)
                else:
                    logger.info(f"⏭️ {page_display_name} 페이지 건너뜀 (페이지가 존재하지 않거나 오류 발생)")
                    
                    # 메인 페이지에서 에러가 나면 해당 대학교 전체 스킵
                    if page_type == "":
                        logger.warning(f"⚠️ {university_info['name']} 메인 페이지 에러 - 해당 대학교 전체 스킵")
                        break

                # Delay between downloads (shorter if skipped)
                if i < len(self.page_types):
                    wait_seconds = self.wait_success_seconds if file_path else self.wait_skip_seconds
                    logger.info(f"⏳ Waiting {wait_seconds} seconds before next download...")
                    time.sleep(wait_seconds)
            
            logger.info(f"\n🎉 Download Summary:")
            logger.info(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(self.page_types)} pages")
            
            # 학교 전체 다운로드 완료 후 최종 캐시 정리
            logger.info(f"🧹 {university_info['name']} 학교 다운로드 완료 - 최종 캐시 정리 중...")
            if self.driver:
                self.clear_cache_and_data()
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Error during batch download: {str(e)}")
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

    def _check_login_status(self, html_content: str) -> bool:
        """
        Check if the downloaded page indicates a logged-in state.
        
        Args:
            html_content: HTML content to check
            
        Returns:
            True if logged in, False if not logged in
        """
        # Canonical URL 기준으로 우선 판단
        canonical_match = CANONICAL_RE.search(html_content)
        if canonical_match:
            canonical_url = canonical_match.group(1)
            if 'premium.usnews.com' in canonical_url:
                return True  # Premium host = logged in
            elif 'www.usnews.com' in canonical_url:
                return False  # www host = not logged in
        
        # Sign out/Log out markers
        sign_out_patterns = [r'\bSign out\b', r'\bLog out\b']
        for pattern in sign_out_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                return True
        
        # Sign in/Log in markers
        sign_in_patterns = [r'\bSign in\b', r'\bLog in\b']
        for pattern in sign_in_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                return False
        
        # Default to not logged in if unclear
        return False

    def _restart_chrome_and_relogin(self) -> bool:
        """
        Restart Chrome and attempt to re-login by copying session from existing Chrome.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("🔄 Chrome 재시작 및 로그인 재시도 중...")
            
            # 현재 드라이버 종료
            if self.driver:
                self.close()
            
            # 잠시 대기
            time.sleep(2)
            
            # 새 드라이버 시작
            self.setup_driver()
            
            # 기존 Chrome 세션 복사 시도
            if self.preserve_login_from_existing and not self.use_existing_chrome:
                try:
                    self.apply_session_to_current_driver(USNEWS_ORIGINS)
                    logger.info("✅ Chrome 재시작 및 로그인 세션 복사 완료")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ 로그인 세션 복사 실패: {e}")
                    return False
            else:
                logger.info("✅ Chrome 재시작 완료 (세션 복사 없음)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Chrome 재시작 실패: {e}")
            return False
    
    
    
