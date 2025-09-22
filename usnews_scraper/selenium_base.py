"""
Selenium Base Module (Refactored)

이 모듈은 Selenium WebDriver의 공통 설정과 기능들을 제공합니다.
분리된 모듈들을 조합하여 기존 API를 유지합니다.
"""

import logging
from typing import Optional, List, Dict, Any

from .selenium import (
    SeleniumConfig, setup_basic_logging,
    ChromeSetup, NavigationManager, SessionManager, HealthChecker
)

logger = logging.getLogger("usnews_scraper.selenium_base")

# Backward compatibility exports
from .selenium.config import DEFAULT_IMPLICIT_WAIT, CLOSE_SELECTORS

class SeleniumBase:
    """Selenium WebDriver의 기본 설정과 공통 기능을 제공하는 베이스 클래스 (리팩토링됨)"""
    
    def __init__(self, headless: bool = True, implicit_wait: int = DEFAULT_IMPLICIT_WAIT, 
                 use_existing_chrome: bool = False, enable_network_monitoring: bool = False, 
                 config: Optional[SeleniumConfig] = None):
        """
        Selenium 베이스 클래스 초기화
        
        Args:
            headless: 헤드리스 모드로 실행할지 여부 (기본값: True)
            implicit_wait: 암시적 대기 시간 (기본값: 5초)
            use_existing_chrome: 기존 실행 중인 Chrome을 사용할지 여부 (기본값: False)
            enable_network_monitoring: 네트워크 모니터링 활성화 여부 (기본값: False, 무시됨)
            config: 선택적 SeleniumConfig 인스턴스
        """
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.use_existing_chrome = use_existing_chrome
        # Network monitoring removed; parameter kept for backward compatibility (ignored)
        self.enable_network_monitoring = False
        self.driver = None
        self.wait = None
        
        # Config
        self.config: SeleniumConfig = config or SeleniumConfig(implicit_wait=self.implicit_wait)
        
        # 분리된 매니저들 초기화
        self.chrome_setup = ChromeSetup(self.config)
        self.navigation_manager = NavigationManager(self.config)
        self.session_manager = SessionManager(self.config)
        self.health_checker = HealthChecker(self.config)
        
        # 순환 참조 설정
        self.health_checker.set_chrome_setup(self.chrome_setup)
    
    # ========== Chrome 설정 및 드라이버 관리 ==========
    def setup_chrome_options(self):
        """Chrome 옵션을 설정합니다. (하위 호환성)"""
        return self.chrome_setup.setup_chrome_options(
            headless=self.headless, 
            use_existing_chrome=self.use_existing_chrome
        )
    
    def setup_driver(self):
        """Chrome WebDriver를 설정하고 시작합니다."""
        self.driver, self.wait = self.chrome_setup.setup_driver(
            headless=self.headless,
            use_existing_chrome=self.use_existing_chrome
        )
        
        if not self.driver:
            raise RuntimeError("ChromeDriver 초기화 실패")
        
        # 시작 시 1회만 응답성 헬스체크
        if self.config.healthcheck_on_startup:
            self.health_checker.ensure_responsive_or_restart(self, timeout_seconds=self.config.startup_healthcheck_timeout)
    
    # ========== 네비게이션 및 에러 처리 ==========
    def navigate_to(self, url: str, wait_time: int = 3, do_precheck: Optional[bool] = None) -> bool:
        """지정된 URL로 이동합니다."""
        if not self.driver:
            self.setup_driver()
            
        return self.navigation_manager.navigate_to(
            driver=self.driver,
            url=url,
            wait_time=wait_time,
            do_precheck=do_precheck,
            health_checker=self.health_checker
        )
    
    def get_page_source(self) -> Optional[str]:
        """현재 페이지의 HTML 소스를 가져옵니다."""
        return self.navigation_manager.get_page_source(self.driver)
    
    def get_response_status_code(self) -> Optional[int]:
        """현재 페이지의 HTTP 응답 상태 코드를 가져옵니다."""
        return self.navigation_manager.get_response_status_code(self.driver)
    
    def get_error_info(self) -> Dict[str, Optional[str]]:
        """상태코드와 해석된 에러 타입을 함께 반환합니다."""
        return self.navigation_manager.get_error_info(self.driver)
    
    def is_error_response(self) -> bool:
        """현재 페이지가 에러 응답인지 확인합니다."""
        return self.navigation_manager.is_error_response(self.driver)
    
    def get_error_type(self) -> Optional[str]:
        """에러 타입 문자열을 반환합니다."""
        return self.navigation_manager.get_error_type(self.driver)
    
    def is_permanent_error(self) -> bool:
        """영구적인 에러인지 확인합니다."""
        return self.navigation_manager.is_permanent_error(self.driver)
    
    # ========== 세션 관리 ==========
    def capture_session_from_existing(self, origins: List[str]) -> bool:
        """실행 중인 Chrome에서 쿠키 및 스토리지를 수집합니다."""
        return self.session_manager.capture_session_from_existing(origins)
    
    def apply_session_to_current_driver(self, origins: List[str]) -> bool:
        """현재 드라이버에 캡처된 세션을 적용합니다."""
        return self.session_manager.apply_session_to_current_driver(self.driver, origins)
    
    def clear_cache_and_data(self) -> bool:
        """브라우저 캐시와 데이터를 지웁니다."""
        return self.session_manager.clear_cache_and_data(self.driver)
    
    # ========== 헬스체크 및 유지보수 ==========
    def ensure_responsive_or_restart(self, timeout_seconds: int = 30) -> bool:
        """브라우저 응답성을 점검하고 필요 시 재시작합니다."""
        return self.health_checker.ensure_responsive_or_restart(self, timeout_seconds)
    
    def close_popups_and_modals(self):
        """페이지에 떠있는 팝업, 모달창, 광고 등을 자동으로 닫습니다."""
        if self.driver:
            self.health_checker.close_popups_and_modals(self.driver)
    
    def _restart_chrome(self) -> bool:
        """Chrome을 완전히 재시작합니다. (하위 호환성)"""
        return self.health_checker.restart_chrome(self)
    
    # ========== 세션 상태 접근 (하위 호환성) ==========
    @property
    def session_cookies(self) -> List[Dict[str, Any]]:
        """캡처된 세션 쿠키 목록"""
        return self.session_manager.session_cookies
    
    @session_cookies.setter
    def session_cookies(self, value: List[Dict[str, Any]]):
        """세션 쿠키 설정"""
        self.session_manager.session_cookies = value
    
    @property
    def local_storage_items(self) -> Dict[str, str]:
        """캡처된 localStorage 아이템들"""
        return self.session_manager.local_storage_items
    
    @local_storage_items.setter
    def local_storage_items(self, value: Dict[str, str]):
        """localStorage 아이템 설정"""
        self.session_manager.local_storage_items = value
    
    @property
    def session_storage_items(self) -> Dict[str, str]:
        """캡처된 sessionStorage 아이템들"""
        return self.session_manager.session_storage_items
    
    @session_storage_items.setter
    def session_storage_items(self, value: Dict[str, str]):
        """sessionStorage 아이템 설정"""
        self.session_manager.session_storage_items = value
    
    # ========== 정리 ==========
    def close(self):
        """WebDriver를 종료합니다."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"❌ WebDriver 종료 중 오류: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
