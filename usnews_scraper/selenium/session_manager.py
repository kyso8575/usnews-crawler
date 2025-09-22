"""
Session Manager Module

로그인 세션 캡처와 적용을 담당합니다.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .config import SeleniumConfig

logger = logging.getLogger("usnews_scraper.selenium.session_manager")


class SessionManager:
    """세션 캡처와 적용을 담당하는 클래스"""
    
    def __init__(self, config: SeleniumConfig):
        self.config = config
        # 로그인 세션 보존을 위한 상태 저장소
        self.session_cookies: List[Dict[str, Any]] = []
        self.local_storage_items: Dict[str, str] = {}
        self.session_storage_items: Dict[str, str] = {}
    
    def _create_temp_driver_connected_to_existing(self) -> Optional[webdriver.Chrome]:
        """디버그 포트로 실행 중인 기존 Chrome에 연결하는 임시 드라이버를 생성합니다."""
        try:
            logger.info(f"🔗 Chrome 연결 시도: {self.config.debugger_address}")
            opts = Options()
            opts.add_experimental_option("debuggerAddress", self.config.debugger_address)
            temp_driver = webdriver.Chrome(options=opts)
            logger.info("✅ Chrome 연결 성공")
            return temp_driver
        except Exception as e:
            logger.warning(f"❌ 기존 Chrome 연결 실패: {str(e)}")
            logger.warning(f"💡 Chrome이 다음 명령으로 실행되어야 합니다:")
            logger.warning(f"   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev_session")
            return None
    
    def capture_session_from_existing(self, origins: List[str]) -> bool:
        """
        실행 중인 Chrome(로그인 유지)에서 쿠키 및 스토리지(local/session)를 수집합니다.
        
        Args:
            origins: 세션을 적용할 오리진 목록 (예: ["https://www.usnews.com", "https://premium.usnews.com"])
            
        Returns:
            캡처 성공 여부
        """
        logger.info(f"🔍 세션 캡처 시작: {origins}")
        
        # 기존 연결 확인
        temp_driver = self._create_temp_driver_connected_to_existing()
        if temp_driver is None:
            logger.warning("❌ 기존 Chrome 연결 실패")
            return False
        
        logger.info("✅ 기존 Chrome 연결 성공")
        
        try:
            # 오리진 방문 타임아웃 1회 설정
            try:
                temp_driver.set_page_load_timeout(self.config.origin_nav_timeout)
            except Exception:
                pass

            collected_cookies: List[Dict[str, Any]] = []
            collected_local: Dict[str, str] = {}
            collected_session: Dict[str, str] = {}

            local_js = (
                "var x={}; for (var i=0;i<localStorage.length;i++){var k=localStorage.key(i); x[k]=localStorage.getItem(k);} return x;"
            )
            session_js = (
                "var x={}; for (var i=0;i<sessionStorage.length;i++){var k=sessionStorage.key(i); x[k]=sessionStorage.getItem(k);} return x;"
            )

            for origin in origins:
                try:
                    logger.info(f"🌐 {origin} 방문 중...")
                    temp_driver.get(origin)
                    time.sleep(1)
                    # 쿠키 수집
                    try:
                        cookies = temp_driver.get_cookies()
                        if cookies:
                            collected_cookies.extend(cookies)
                            logger.info(f"🍪 {origin}에서 쿠키 {len(cookies)}개 수집")
                        else:
                            logger.info(f"🍪 {origin}에서 쿠키 없음")
                    except Exception as e:
                        logger.warning(f"❌ {origin} 쿠키 수집 실패: {e}")
                    # localStorage 수집
                    try:
                        local_items = temp_driver.execute_script(local_js)
                        if isinstance(local_items, dict) and local_items:
                            collected_local.update(local_items)
                            logger.info(f"💾 {origin}에서 localStorage {len(local_items)}개 수집")
                        else:
                            logger.info(f"💾 {origin}에서 localStorage 없음")
                    except Exception as e:
                        logger.warning(f"❌ {origin} localStorage 수집 실패: {e}")
                    # sessionStorage 수집
                    try:
                        session_items = temp_driver.execute_script(session_js)
                        if isinstance(session_items, dict) and session_items:
                            collected_session.update(session_items)
                            logger.info(f"🗂️ {origin}에서 sessionStorage {len(session_items)}개 수집")
                        else:
                            logger.info(f"🗂️ {origin}에서 sessionStorage 없음")
                    except Exception as e:
                        logger.warning(f"❌ {origin} sessionStorage 수집 실패: {e}")
                except Exception as e:
                    logger.warning(f"❌ {origin} 방문 실패: {e}")
                    continue

            self.session_cookies = collected_cookies
            self.local_storage_items = collected_local
            self.session_storage_items = collected_session
            logger.info(
                f"🔐 세션 캡처: 쿠키 {len(self.session_cookies)}개, localStorage {len(self.local_storage_items)}개, sessionStorage {len(self.session_storage_items)}개"
            )
            # 무언가라도 수집되었는지 기준으로 반환
            return bool(self.session_cookies or self.local_storage_items or self.session_storage_items)
        finally:
            # 기존 Chrome을 종료하지 않도록 조심스럽게 연결만 해제
            try:
                temp_driver.quit()
            except Exception:
                pass
    
    def apply_session_to_current_driver(self, driver: webdriver.Chrome, origins: List[str]) -> bool:
        """
        현재 드라이버에 캡처된 세션(쿠키/스토리지)을 적용합니다.
        요청에 쿠키가 포함되도록 각 오리진으로 먼저 이동 후 설정합니다.
        
        Args:
            driver: 세션을 적용할 WebDriver 인스턴스
            origins: 세션을 적용할 오리진 목록
            
        Returns:
            적용 성공 여부
        """
        if not driver:
            return False
        if not self.session_cookies and not self.local_storage_items and not self.session_storage_items:
            return False
        # 중복 오리진 제거(순서 보존)
        unique_origins = list(dict.fromkeys(origins))
        applied_any = False
        original_timeout = self.config.page_load_timeout
        try:
            # Temporarily reduce page load timeout for quick origin hops
            try:
                driver.set_page_load_timeout(self.config.origin_nav_timeout)
            except Exception:
                pass

            # 도메인별 쿠키 그룹핑(간단 필터만 사용)
            cookies_list = self.session_cookies or []

            for origin in unique_origins:
                try:
                    driver.get(origin)
                    time.sleep(1)

                    # localStorage 적용
                    if self.local_storage_items:
                        for k, v in self.local_storage_items.items():
                            try:
                                driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", k, v)
                                applied_any = True
                            except Exception:
                                continue

                    # sessionStorage 적용
                    if self.session_storage_items:
                        for k, v in self.session_storage_items.items():
                            try:
                                driver.execute_script("window.sessionStorage.setItem(arguments[0], arguments[1]);", k, v)
                                applied_any = True
                            except Exception:
                                continue

                    # 쿠키 적용 (도메인 매칭)
                    if cookies_list:
                        origin_host = urlparse(origin).hostname or ""
                        for c in cookies_list:
                            try:
                                cookie_domain = (c.get("domain") or origin_host).lstrip(".")
                                if origin_host.endswith(cookie_domain):
                                    cookie_to_add = {
                                        "name": c.get("name"),
                                        "value": c.get("value"),
                                        "path": c.get("path", "/"),
                                        "domain": c.get("domain", None),
                                        "secure": c.get("secure", False),
                                        "httpOnly": c.get("httpOnly", False),
                                    }
                                    if "expiry" in c:
                                        cookie_to_add["expiry"] = c["expiry"]
                                    if cookie_to_add.get("domain") is None:
                                        cookie_to_add.pop("domain", None)
                                    driver.add_cookie(cookie_to_add)
                                    applied_any = True
                            except Exception:
                                continue
                except Exception:
                    continue
            return applied_any
        except Exception as e:
            logger.warning(f"⚠️ 세션 적용 실패: {str(e)}")
            return False
        finally:
            # Restore page load timeout
            try:
                driver.set_page_load_timeout(original_timeout)
            except Exception:
                pass
    
    def clear_cache_and_data(self, driver: webdriver.Chrome) -> bool:
        """브라우저 캐시와 데이터를 지웁니다.
        
        Args:
            driver: 캐시를 지울 WebDriver 인스턴스
            
        Returns:
            성공 여부
        """
        try:
            if not driver:
                return False
            
            logger.info("🧹 브라우저 캐시 정리 중...")
            
            # 쿠키 지우기
            try:
                driver.delete_all_cookies()
                logger.info("  ✅ 쿠키 지우기 완료")
            except Exception:
                pass
            
            # 로컬 스토리지 지우기
            try:
                driver.execute_script("window.localStorage.clear();")
                logger.info("  ✅ 로컬 스토리지 지우기 완료")
            except Exception:
                pass
            
            # 세션 스토리지 지우기
            try:
                driver.execute_script("window.sessionStorage.clear();")
                logger.info("  ✅ 세션 스토리지 지우기 완료")
            except Exception:
                pass
            
            # Chrome DevTools를 통한 캐시 지우기 (가능한 경우)
            try:
                driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                logger.info("  ✅ 네트워크 캐시 지우기 완료")
            except Exception:
                pass
            
            logger.info("✅ 캐시 정리 완료")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 캐시 정리 중 오류: {str(e)}")
            return False
