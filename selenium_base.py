"""
Selenium Base Module

이 모듈은 Selenium WebDriver의 공통 설정과 기능들을 제공합니다.
다른 모듈들에서 이를 상속받아 사용할 수 있습니다.
"""

import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumBase:
    """Selenium WebDriver의 기본 설정과 공통 기능을 제공하는 베이스 클래스"""
    
    def __init__(self, headless: bool = True, implicit_wait: int = 10):
        """
        Selenium 베이스 클래스 초기화
        
        Args:
            headless: 헤드리스 모드로 실행할지 여부 (기본값: True)
            implicit_wait: 암시적 대기 시간 (기본값: 10초)
        """
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver = None
        self.wait = None
        
    def setup_chrome_options(self) -> Options:
        """
        Chrome 옵션을 설정합니다.
        
        Returns:
            설정된 Chrome 옵션
        """
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # 기본 옵션들
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 네트워크 관련 옵션들
        chrome_options.add_argument("--disable-http2")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-extensions")
        
        # User Agent 설정
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        return chrome_options
    
    def setup_driver(self):
        """
        Chrome WebDriver를 설정하고 시작합니다.
        """
        try:
            chrome_options = self.setup_chrome_options()
            
            # 시스템에 설치된 ChromeDriver 사용 시도
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception:
                # 시스템 ChromeDriver가 없으면 자동 다운로드 시도
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✅ 자동 다운로드된 ChromeDriver 사용")
                except Exception as e:
                    print(f"❌ ChromeDriver 자동 다운로드 실패: {str(e)}")
                    # 마지막 시도: Homebrew ChromeDriver 경로
                    try:
                        service = Service("/opt/homebrew/bin/chromedriver")
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        print("✅ Homebrew ChromeDriver 사용")
                    except Exception as e2:
                        print(f"❌ Homebrew ChromeDriver 실패: {str(e2)}")
                        raise e
            
            self.driver.implicitly_wait(self.implicit_wait)
            self.wait = WebDriverWait(self.driver, self.implicit_wait)
            
            
        except Exception as e:
            print(f"❌ WebDriver 설정 중 오류 발생: {str(e)}")
            raise
    
    def navigate_to(self, url: str, wait_time: int = 3) -> bool:
        """
        지정된 URL로 이동합니다.
        
        Args:
            url: 이동할 URL
            wait_time: 페이지 로드 후 대기 시간 (기본값: 3초)
            
        Returns:
            성공 여부
        """
        try:
            if not self.driver:
                self.setup_driver()
                
            # 적절한 타임아웃 설정 (추천 위젯 로딩 전에 중단)
            self.driver.set_page_load_timeout(10)
            
            try:
                self.driver.get(url)
                print(f"✅ 페이지 로딩 완료")
                time.sleep(0.5)
            except Exception:
                print(f"⚠️ 타임아웃으로 로딩 중단 (메인 콘텐츠 확보)")
                time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            print(f"❌ URL 이동 중 오류: {str(e)}")
            return False
    
    def find_element_safe(self, by: By, value: str, timeout: int = 10) -> Optional[any]:
        """
        안전하게 요소를 찾습니다.
        
        Args:
            by: 요소를 찾을 방법 (By.ID, By.CLASS_NAME 등)
            value: 찾을 값
            timeout: 타임아웃 시간 (기본값: 10초)
            
        Returns:
            찾은 요소 또는 None
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(f"⚠️ 요소를 찾을 수 없음: {by}='{value}'")
            return None
        except Exception as e:
            print(f"❌ 요소 찾기 중 오류: {str(e)}")
            return None
    
    def find_elements_safe(self, by: By, value: str) -> List[any]:
        """
        안전하게 여러 요소를 찾습니다.
        
        Args:
            by: 요소를 찾을 방법
            value: 찾을 값
            
        Returns:
            찾은 요소들의 리스트
        """
        try:
            elements = self.driver.find_elements(by, value)
            return elements
        except Exception as e:
            print(f"❌ 요소들 찾기 중 오류: {str(e)}")
            return []
    
    def click_element_safe(self, element) -> bool:
        """
        안전하게 요소를 클릭합니다.
        
        Args:
            element: 클릭할 요소
            
        Returns:
            성공 여부
        """
        try:
            element.click()
            return True
        except ElementNotInteractableException:
            print("⚠️ 요소가 클릭 가능하지 않음")
            return False
        except Exception as e:
            print(f"❌ 클릭 중 오류: {str(e)}")
            return False
    
    def send_keys_safe(self, element, text: str) -> bool:
        """
        안전하게 텍스트를 입력합니다.
        
        Args:
            element: 입력할 요소
            text: 입력할 텍스트
            
        Returns:
            성공 여부
        """
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            print(f"❌ 텍스트 입력 중 오류: {str(e)}")
            return False
    
    def wait_for_page_load(self, timeout: int = 15) -> bool:
        """
        페이지가 로드될 때까지 기다립니다.
        
        Args:
            timeout: 타임아웃 시간 (기본값: 15초)
            
        Returns:
            성공 여부
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✅ 페이지 로드 완료")
            return True
        except TimeoutException:
            print("⚠️ 페이지 로드 타임아웃")
            return False
        except Exception as e:
            print(f"❌ 페이지 로드 대기 중 오류: {str(e)}")
            return False
    
    def get_page_source(self) -> Optional[str]:
        """
        현재 페이지의 HTML 소스를 가져옵니다.
        
        Returns:
            HTML 소스 또는 None
        """
        try:
            return self.driver.page_source
        except Exception as e:
            print(f"❌ 페이지 소스 가져오기 중 오류: {str(e)}")
            return None
    
    def get_current_url(self) -> Optional[str]:
        """
        현재 URL을 가져옵니다.
        
        Returns:
            현재 URL 또는 None
        """
        try:
            return self.driver.current_url
        except Exception as e:
            print(f"❌ 현재 URL 가져오기 중 오류: {str(e)}")
            return None
    
    def get_page_title(self) -> Optional[str]:
        """
        현재 페이지의 제목을 가져옵니다.
        
        Returns:
            페이지 제목 또는 None
        """
        try:
            return self.driver.title
        except Exception as e:
            print(f"❌ 페이지 제목 가져오기 중 오류: {str(e)}")
            return None
    
    def take_screenshot(self, filename: str) -> bool:
        """
        스크린샷을 찍습니다.
        
        Args:
            filename: 저장할 파일명
            
        Returns:
            성공 여부
        """
        try:
            self.driver.save_screenshot(filename)
            print(f"📸 스크린샷 저장됨: {filename}")
            return True
        except Exception as e:
            print(f"❌ 스크린샷 저장 중 오류: {str(e)}")
            return False
    
    def close(self):
        """WebDriver를 종료합니다."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"❌ WebDriver 종료 중 오류: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        """Context manager 진입"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()


# 편의를 위한 함수들
def create_selenium_instance(headless: bool = True) -> SeleniumBase:
    """
    Selenium 인스턴스를 생성합니다.
    
    Args:
        headless: 헤드리스 모드 여부
        
    Returns:
        SeleniumBase 인스턴스
    """
    return SeleniumBase(headless=headless)


# Context manager 사용 예시:
# with create_selenium_instance(headless=False) as selenium:
#     selenium.navigate_to("https://example.com")
#     element = selenium.find_element_safe(By.ID, "some-id")
#     if element:
#         selenium.click_element_safe(element)
