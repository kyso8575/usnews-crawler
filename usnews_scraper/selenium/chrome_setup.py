"""
Chrome Setup Module

Chrome 옵션 설정과 WebDriver 초기화를 담당합니다.
"""

import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .config import SeleniumConfig

logger = logging.getLogger("usnews_scraper.selenium.chrome_setup")


class ChromeSetup:
    """Chrome WebDriver 설정과 초기화를 담당하는 클래스"""
    
    def __init__(self, config: SeleniumConfig):
        self.config = config
        
    def setup_chrome_options(self, headless: bool = True, use_existing_chrome: bool = False) -> Options:
        """
        Chrome 옵션을 설정합니다.
        
        Args:
            headless: 헤드리스 모드로 실행할지 여부
            use_existing_chrome: 기존 Chrome에 연결할지 여부
            
        Returns:
            설정된 Chrome 옵션
        """
        chrome_options = Options()
        
        if use_existing_chrome:
            # 기존 Chrome에 연결하기 위한 설정
            chrome_options.add_experimental_option("debuggerAddress", self.config.debugger_address)
            logger.info("🔗 기존 Chrome 브라우저에 연결합니다...")
        else:
            if headless:
                chrome_options.add_argument("--headless")
            
            # 기본 옵션들 (필수 및 경량화 위주)
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-images")  # 이미지 로딩 비활성화(보조)
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 이미지 완전 비활성화(주)
            chrome_options.add_argument("--no-proxy-server")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--disable-dns-prefetch")

            # HTTP2/QUIC 관련 오류 완화 (HTTP2 프로토콜 에러 방지)
            chrome_options.add_argument("--disable-http2")
            chrome_options.add_argument("--disable-quic")

            # User Agent 설정
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )

            # 브라우저 환경 설정(이미지, 알림 등) - 이미지/알림 차단
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.geolocation": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # 페이지 로드 전략: eager (DOMContentLoaded 까지 대기)
            chrome_options.page_load_strategy = 'eager'

            # 인증서 관련 이슈 완화
            chrome_options.set_capability("acceptInsecureCerts", True)
        
        return chrome_options
    
    def create_driver(self, chrome_options: Options) -> Optional[webdriver.Chrome]:
        """
        Chrome WebDriver를 생성합니다.
        
        Args:
            chrome_options: 설정된 Chrome 옵션
            
        Returns:
            Chrome WebDriver 인스턴스 또는 None
        """
        # 단순화된 드라이버 생성 전략 루프
        last_error: Optional[Exception] = None
        strategies = [
            ("system", lambda: webdriver.Chrome(options=chrome_options)),
            ("webdriver_manager", lambda: webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)),
            ("homebrew", lambda: webdriver.Chrome(service=Service("/opt/homebrew/bin/chromedriver"), options=chrome_options)),
        ]
        
        for name, builder in strategies:
            try:
                driver = builder()
                if name == "webdriver_manager":
                    logger.info("✅ 자동 다운로드된 ChromeDriver 사용")
                elif name == "homebrew":
                    logger.info("✅ Homebrew ChromeDriver 사용")
                return driver
            except Exception as e:
                last_error = e
                continue
        
        if last_error:
            logger.error(f"❌ ChromeDriver 초기화 실패: {last_error}")
        
        return None
    
    def setup_driver(self, headless: bool = True, use_existing_chrome: bool = False) -> tuple[Optional[webdriver.Chrome], Optional[WebDriverWait]]:
        """
        Chrome WebDriver를 설정하고 시작합니다.
        
        Args:
            headless: 헤드리스 모드로 실행할지 여부
            use_existing_chrome: 기존 Chrome에 연결할지 여부
            
        Returns:
            (driver, wait) 튜플
        """
        try:
            chrome_options = self.setup_chrome_options(headless=headless, use_existing_chrome=use_existing_chrome)
            driver = self.create_driver(chrome_options)
            
            if not driver:
                return None, None
            
            driver.implicitly_wait(self.config.implicit_wait)
            wait = WebDriverWait(driver, self.config.implicit_wait)
            
            return driver, wait
            
        except Exception as e:
            logger.error(f"❌ WebDriver 설정 중 오류 발생: {str(e)}")
            return None, None
