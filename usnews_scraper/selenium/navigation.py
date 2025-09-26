"""
Navigation Module

URL 네비게이션과 에러 처리를 담당합니다.
"""

import time
import logging
from typing import Optional, Dict
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException

from .config import SeleniumConfig, NETWORK_ERROR_URL_INDICATORS, PERMANENT_STATUS_CODES, RETRY_POSSIBLE_CODES

logger = logging.getLogger("usnews_scraper.selenium.navigation")


class NavigationManager:
    """URL 네비게이션과 에러 처리를 담당하는 클래스"""
    
    def __init__(self, config: SeleniumConfig):
        self.config = config
    
    def navigate_to(self, driver: webdriver.Chrome, url: str, wait_time: int = 3, do_precheck: Optional[bool] = None, health_checker=None, driver_container=None) -> bool:
        """
        지정된 URL로 이동합니다.
        
        Args:
            driver: Chrome WebDriver 인스턴스
            url: 이동할 URL
            wait_time: 페이지 로드 후 대기 시간 (기본값: 3초)
            do_precheck: 사전 응답성 체크 여부
            health_checker: 헬스체크 매니저 인스턴스
            
        Returns:
            성공 여부
        """
        try:
            if not driver:
                logger.error("❌ WebDriver가 없습니다.")
                return False

            # navigate 전 사전 응답성 체크는 옵션으로 수행
            final_precheck = self.config.healthcheck_before_navigation if do_precheck is None else do_precheck
            if final_precheck and health_checker:
                if not health_checker.ensure_responsive_or_restart(timeout_seconds=self.config.pre_nav_healthcheck_timeout):
                    logger.warning("❌ Chrome 상태 불량 - 재시작 실패")
                    return False
                
            # 적절한 타임아웃 설정 (추천 위젯 로딩 전에 중단)
            driver.set_page_load_timeout(self.config.page_load_timeout)
            
            attempts = 0
            while True:
                try:
                    driver.get(url)
                    logger.info("✅ 페이지 로딩 완료")
                    time.sleep(self.config.post_render_wait_seconds)
                    break
                except (TimeoutException, WebDriverException) as e:
                    attempts += 1
                    logger.warning(f"⚠️ 네비게이션 예외({attempts}/{self.config.navigate_retry_count + 1}): {e}")
                    if attempts > self.config.navigate_retry_count:
                        return False
                    if health_checker and driver_container and not health_checker.restart_chrome(driver_container):
                        return False
                    try:
                        driver.set_page_load_timeout(self.config.page_load_timeout)
                    except Exception:
                        pass
                    time.sleep(self.config.retry_backoff_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ URL 이동 중 오류: {str(e)}")
            return False
    
    def get_page_source(self, driver: webdriver.Chrome) -> Optional[str]:
        """
        현재 페이지의 HTML 소스를 가져옵니다.
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns:
            HTML 소스 또는 None
        """
        try:
            if not driver:
                return None
            
            # 타임아웃을 위한 시그널 처리
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("페이지 소스 가져오기 타임아웃")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(20)  # 20초 타임아웃
            
            try:
                page_source = driver.page_source
                return page_source
            finally:
                signal.alarm(0)  # 타임아웃 해제
                
        except TimeoutError:
            logger.warning("⚠️ 페이지 소스 가져오기 타임아웃 (20초)")
            return None
        except Exception as e:
            logger.warning(f"❌ 페이지 소스 가져오기 중 오류: {str(e)}")
            return None
    
    def get_response_status_code(self, driver: webdriver.Chrome) -> Optional[int]:
        """
        현재 페이지의 HTTP 응답 상태 코드를 가져옵니다.
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns:
            HTTP 상태 코드 또는 None
        """
        try:
            if not driver:
                return None
            # JavaScript를 사용하여 응답 상태 코드 가져오기
            status_code = driver.execute_script("""
                var req = new XMLHttpRequest();
                req.open('GET', window.location.href, false);
                req.send();
                return req.status;
            """)
            return status_code
        except Exception:
            # 첫 번째 방법이 실패하면 Performance API 사용
            try:
                status_code = driver.execute_script("""
                    var perfEntries = performance.getEntriesByType('navigation');
                    if (perfEntries.length > 0) {
                        return perfEntries[0].responseStatus || 200;
                    }
                    return 200;
                """)
                return status_code
            except Exception as e:
                logger.warning(f"⚠️ 상태 코드 확인 실패: {str(e)}")
                return None

    def get_error_info(self, driver: webdriver.Chrome) -> Dict[str, Optional[str]]:
        """
        상태코드와 해석된 에러 타입을 함께 반환합니다.
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns: 
            {"status": int|None, "type": str|None}
        """
        try:
            if not driver:
                return {"status": None, "type": "네트워크 에러 (드라이버 없음)"}
            status_code = self.get_response_status_code(driver)
            current_url = driver.current_url
            
            # Akamai CDN 에러 확인 (URL과 HTML 내용 모두 확인)
            if "errors.edgesuite.net" in current_url:
                return {"status": status_code, "type": "Akamai CDN 에러 (스킵)"}
            
            # HTML 내용에서 Akamai CDN 에러 확인
            try:
                page_source = driver.page_source
                if "errors.edgesuite.net" in page_source or "Reference #" in page_source:
                    return {"status": status_code, "type": "Akamai CDN 에러 (스킵)"}
            except Exception:
                pass
            
            # 네트워크 에러 확인 (상태코드 없음 또는 0)
            if status_code is None or status_code == 0:
                if any(indicator in current_url for indicator in NETWORK_ERROR_URL_INDICATORS):
                    return {"status": status_code, "type": "네트워크 연결 실패"}
                return {"status": status_code, "type": "네트워크 에러 (연결 문제)"}
            # HTTP 상태 코드별 분류
            if status_code == 404:
                return {"status": status_code, "type": "페이지 없음 (404)"}
            elif status_code == 403:
                return {"status": status_code, "type": "접근 권한 없음 (403)"}
            elif status_code == 401:
                return {"status": status_code, "type": "인증 필요 (401)"}
            elif status_code == 500:
                return {"status": status_code, "type": "서버 내부 에러 (500)"}
            elif status_code == 502:
                return {"status": status_code, "type": "게이트웨이 에러 (502)"}
            elif status_code == 503:
                return {"status": status_code, "type": "서비스 이용 불가 (503)"}
            elif 400 <= status_code < 500:
                return {"status": status_code, "type": f"클라이언트 에러 ({status_code})"}
            elif status_code >= 500:
                return {"status": status_code, "type": f"서버 에러 ({status_code})"}
            # 정상 응답
            return {"status": status_code, "type": None}
        except Exception as e:
            logger.warning(f"⚠️ 에러 정보 확인 실패: {str(e)}")
            return {"status": None, "type": "에러 타입 확인 실패"}

    def is_error_response(self, driver: webdriver.Chrome) -> bool:
        """
        현재 페이지가 에러 응답인지 확인합니다 (래퍼).
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns:
            에러 응답 여부
        """
        info = self.get_error_info(driver)
        status_code = info.get("status")
        if status_code is None:
            return info.get("type") is not None
        return status_code == 0 or (isinstance(status_code, int) and status_code >= 400)

    def get_error_type(self, driver: webdriver.Chrome) -> Optional[str]:
        """
        에러 타입 문자열을 반환합니다 (래퍼). 정상 응답이면 None.
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns:
            에러 타입 문자열 또는 None
        """
        info = self.get_error_info(driver)
        return info.get("type")

    def is_permanent_error(self, driver: webdriver.Chrome) -> bool:
        """
        영구적인 에러인지 확인합니다 (래퍼).
        
        Args:
            driver: Chrome WebDriver 인스턴스
            
        Returns:
            영구적 에러 여부
        """
        info = self.get_error_info(driver)
        error_type = info.get("type")
        status_code = info.get("status")
        
        # Akamai CDN 에러는 영구 에러로 처리 (즉시 스킵)
        if error_type and "Akamai CDN 에러" in error_type:
            return True
            
        try:
            if status_code in PERMANENT_STATUS_CODES:
                return True
            if isinstance(status_code, int) and 400 <= status_code < 500:
                return status_code not in RETRY_POSSIBLE_CODES
            return False
        except Exception:
            return False
