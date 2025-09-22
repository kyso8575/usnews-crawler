"""
Health Check Module

Chrome 응답성 체크, 팝업 닫기, 재시작 기능을 담당합니다.
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By

from .config import SeleniumConfig, CLOSE_SELECTORS

logger = logging.getLogger("usnews_scraper.selenium.health_check")


class HealthChecker:
    """Chrome 상태 관리와 헬스체크를 담당하는 클래스"""
    
    def __init__(self, config: SeleniumConfig):
        self.config = config
        self.chrome_setup = None  # 순환 import 방지용, 나중에 설정
    
    def set_chrome_setup(self, chrome_setup):
        """Chrome 설정 매니저를 설정합니다. (순환 import 방지)"""
        self.chrome_setup = chrome_setup
    
    def ensure_responsive_or_restart(self, driver_container, timeout_seconds: int = 30) -> bool:
        """
        브라우저 응답성을 점검하고 필요 시 재시작합니다.
        
        Args:
            driver_container: driver 속성을 가진 객체 (SeleniumBase 인스턴스)
            timeout_seconds: 타임아웃 (초)
            
        Returns: 
            True(normal) / False(restart failed)
        """
        try:
            logger.info("🔄 Chrome 응답성 확인 중...")
            if not driver_container.driver:
                logger.warning("❌ 드라이버가 없음 - 새로 시작합니다.")
                return self.restart_chrome(driver_container)
            # 간단한 JavaScript 실행으로 응답성 테스트
            start_time = time.time()
            try:
                result = driver_container.driver.execute_script("return document.readyState;")
            except Exception as e:
                logger.warning(f"❌ Chrome 응답 불가 ({e}) - 재시작합니다.")
                return self.restart_chrome(driver_container)
            response_time = time.time() - start_time
            if response_time > self.config.response_slow_threshold:
                logger.warning(f"⚠️ Chrome 응답 속도 느림 ({response_time:.2f}s > {self.config.response_slow_threshold}s) - 재시작")
                return self.restart_chrome(driver_container)
            if result != "complete":
                logger.warning(f"⚠️ 페이지 로딩 미완료 상태({result}) - 재시작")
                return self.restart_chrome(driver_container)
            logger.info("✅ Chrome 정상 동작 중")
            return True
        except Exception as e:
            logger.warning(f"❌ Chrome 상태 확인 실패: {e} - 재시작")
            return self.restart_chrome(driver_container)
    
    def close_popups_and_modals(self, driver: webdriver.Chrome) -> None:
        """
        페이지에 떠있는 팝업, 모달창, 광고 등을 자동으로 닫습니다.
        
        Args:
            driver: Chrome WebDriver 인스턴스
        """
        try:
            # 일반적인 닫기 버튼 선택자들
            close_selectors = CLOSE_SELECTORS
            
            closed_count = 0
            
            for selector in close_selectors:
                try:
                    # CSS 선택자로 찾기
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                closed_count += 1
                                time.sleep(0.5)  # 팝업이 사라질 시간
                                break
                            except Exception:
                                # 클릭 실패해도 계속 진행
                                pass
                except Exception:
                    # 선택자가 없어도 계속 진행
                    pass
            
            # ESC 키로 모달 닫기 시도
            try:
                from selenium.webdriver.common.keys import Keys
                body = driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except Exception:
                pass
            
            if closed_count > 0:
                logger.info(f"🗂️ {closed_count}개의 팝업/모달을 닫았습니다.")
                
        except Exception as e:
            logger.warning(f"⚠️ 팝업 닫기 중 오류 (무시하고 계속): {str(e)}")
    
    def restart_chrome(self, driver_container) -> bool:
        """Chrome을 완전히 재시작합니다.
        
        Args:
            driver_container: driver와 wait 속성을 가진 객체 (SeleniumBase 인스턴스)
            
        Returns:
            재시작 성공 여부
        """
        try:
            logger.info("🔄 Chrome 재시작 중...")
            
            # 기존 드라이버 종료
            if driver_container.driver:
                try:
                    driver_container.driver.quit()
                except Exception:
                    pass
                driver_container.driver = None
                driver_container.wait = None
            
            # 잠깐 대기
            time.sleep(self.config.restart_pause_seconds)
            
            # 새 드라이버 시작 (chrome_setup이 설정되어 있어야 함)
            if self.chrome_setup:
                headless = getattr(driver_container, 'headless', True)
                use_existing_chrome = getattr(driver_container, 'use_existing_chrome', False)
                
                driver, wait = self.chrome_setup.setup_driver(
                    headless=headless, 
                    use_existing_chrome=use_existing_chrome
                )
                
                if driver:
                    driver_container.driver = driver
                    driver_container.wait = wait
                    
                    # 시작 시 1회만 응답성 헬스체크
                    if self.config.healthcheck_on_startup:
                        self.ensure_responsive_or_restart(driver_container, timeout_seconds=self.config.startup_healthcheck_timeout)
                    
                    logger.info("✅ Chrome 재시작 완료")
                    return True
                else:
                    logger.warning("❌ Chrome 재시작 실패")
                    return False
            else:
                logger.error("❌ Chrome 설정 매니저가 없어서 재시작할 수 없습니다.")
                return False
                
        except Exception as e:
            logger.warning(f"❌ Chrome 재시작 중 오류: {str(e)}")
            return False
