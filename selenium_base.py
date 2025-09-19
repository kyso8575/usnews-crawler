"""
Selenium Base Module

이 모듈은 Selenium WebDriver의 공통 설정과 기능들을 제공합니다.
다른 모듈들에서 이를 상속받아 사용할 수 있습니다.
네트워크 모니터링 기능도 포함되어 있습니다.
"""

import time
import json
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumBase:
    """Selenium WebDriver의 기본 설정과 공통 기능을 제공하는 베이스 클래스"""
    
    def __init__(self, headless: bool = True, implicit_wait: int = 10, use_existing_chrome: bool = False, 
                 enable_network_monitoring: bool = False):
        """
        Selenium 베이스 클래스 초기화
        
        Args:
            headless: 헤드리스 모드로 실행할지 여부 (기본값: True)
            implicit_wait: 암시적 대기 시간 (기본값: 10초)
            use_existing_chrome: 기존 실행 중인 Chrome을 사용할지 여부 (기본값: False)
            enable_network_monitoring: 네트워크 모니터링 활성화 여부 (기본값: False)
        """
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.use_existing_chrome = use_existing_chrome
        self.enable_network_monitoring = enable_network_monitoring
        self.driver = None
        self.wait = None
        
        # 네트워크 모니터링 관련 속성들
        self.network_responses: List[Dict[str, Any]] = []
        self.monitoring_patterns: List[str] = []
        self.network_enabled = False
        
    def setup_chrome_options(self) -> Options:
        """
        Chrome 옵션을 설정합니다.
        
        Returns:
            설정된 Chrome 옵션
        """
        chrome_options = Options()
        
        if self.use_existing_chrome:
            # 기존 Chrome에 연결하기 위한 설정
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            print("🔗 기존 Chrome 브라우저에 연결합니다...")
        else:
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
            
            # macOS 관련 경고 억제
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            
            # User Agent 설정
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            # 네트워크 모니터링을 위한 설정
            if self.enable_network_monitoring:
                chrome_options.add_experimental_option("useAutomationExtension", False)
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_argument("--enable-logging")
                chrome_options.add_argument("--log-level=0")
                chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
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
            
            # 네트워크 모니터링 활성화
            if self.enable_network_monitoring:
                self._enable_network_monitoring()
            
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
            self.driver.set_page_load_timeout(15)
            
            try:
                self.driver.get(url)
                print(f"✅ 페이지 로딩 완료")
                time.sleep(4)  # 페이지 완전 렌더링 대기
            except Exception:
                print(f"⚠️ 타임아웃으로 로딩 중단 (메인 콘텐츠 확보)")
                time.sleep(wait_time + 4)  # 타임아웃 후 추가 대기
            
            return True
            
        except Exception as e:
            print(f"❌ URL 이동 중 오류: {str(e)}")
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
    
    def get_response_status_code(self) -> Optional[int]:
        """
        현재 페이지의 HTTP 응답 상태 코드를 가져옵니다.
        
        Returns:
            HTTP 상태 코드 또는 None
        """
        try:
            # JavaScript를 사용하여 응답 상태 코드 가져오기
            status_code = self.driver.execute_script("""
                var req = new XMLHttpRequest();
                req.open('GET', window.location.href, false);
                req.send();
                return req.status;
            """)
            return status_code
        except Exception:
            # 첫 번째 방법이 실패하면 Performance API 사용
            try:
                status_code = self.driver.execute_script("""
                    var perfEntries = performance.getEntriesByType('navigation');
                    if (perfEntries.length > 0) {
                        return perfEntries[0].responseStatus || 200;
                    }
                    return 200;
                """)
                return status_code
            except Exception as e:
                print(f"⚠️ 상태 코드 확인 실패: {str(e)}")
                return None
    
    def is_error_response(self) -> bool:
        """
        현재 페이지가 에러 응답인지 확인합니다.
        
        Returns:
            에러 응답 여부 (True/False)
        """
        try:
            status_code = self.get_response_status_code()
            
            if status_code is None:
                # 상태 코드를 가져올 수 없으면 URL 확인
                current_url = self.driver.current_url
                error_indicators = ["chrome-error://", "chrome://network-error/"]
                return any(indicator in current_url for indicator in error_indicators)
            
            # 4xx, 5xx 에러 또는 0 (네트워크 실패)
            return status_code == 0 or status_code >= 400
            
        except Exception as e:
            print(f"⚠️ 에러 응답 확인 실패: {str(e)}")
            return False
    
    def get_error_type(self) -> str:
        """
        에러 타입을 구체적으로 분류합니다.
        
        Returns:
            에러 타입 문자열 또는 None (정상 페이지)
        """
        try:
            status_code = self.get_response_status_code()
            current_url = self.driver.current_url
            
            # Chrome 네트워크 에러 확인
            if status_code is None or status_code == 0:
                if "chrome-error://" in current_url or "chrome://network-error/" in current_url:
                    return "네트워크 연결 실패"
                else:
                    return "네트워크 에러 (연결 문제)"
            
            # HTTP 상태 코드별 분류
            if status_code == 404:
                return "페이지 없음 (404)"
            elif status_code == 403:
                return "접근 권한 없음 (403)"
            elif status_code == 401:
                return "인증 필요 (401)"
            elif status_code == 500:
                return "서버 내부 에러 (500)"
            elif status_code == 502:
                return "게이트웨이 에러 (502)"
            elif status_code == 503:
                return "서비스 이용 불가 (503)"
            elif 400 <= status_code < 500:
                return f"클라이언트 에러 ({status_code})"
            elif status_code >= 500:
                return f"서버 에러 ({status_code})"
            else:
                return None  # 정상 응답
                
        except Exception as e:
            print(f"⚠️ 에러 타입 확인 실패: {str(e)}")
            return "에러 타입 확인 실패"
    
    def is_permanent_error(self) -> bool:
        """
        영구적인 에러인지 (재시도 불필요) 확인합니다.
        
        Returns:
            영구적 에러 여부 (True: 재시도 불필요, False: 재시도 가능)
        """
        try:
            status_code = self.get_response_status_code()
            
            # 404, 403, 401 등은 재시도해도 소용없는 영구적 에러
            permanent_status_codes = [404, 403, 401, 410]  # 410 = Gone
            
            if status_code in permanent_status_codes:
                return True
            
            # 4xx 중에서도 클라이언트 에러는 대부분 영구적
            if 400 <= status_code < 500:
                # 408 (Timeout), 429 (Too Many Requests)는 재시도 가능
                retry_possible_codes = [408, 429]
                return status_code not in retry_possible_codes
            
            # 5xx 서버 에러나 네트워크 에러는 재시도 가능
            return False
            
        except Exception as e:
            print(f"⚠️ 영구 에러 확인 실패: {str(e)}")
            return False  # 확실하지 않으면 재시도 시도
    
    
    def clear_cache_and_data(self):
        """브라우저 캐시와 데이터를 지웁니다."""
        try:
            if not self.driver:
                return False
            
            print("🧹 브라우저 캐시 정리 중...")
            
            # 쿠키 지우기
            try:
                self.driver.delete_all_cookies()
                print("  ✅ 쿠키 지우기 완료")
            except Exception:
                pass
            
            # 로컬 스토리지 지우기
            try:
                self.driver.execute_script("window.localStorage.clear();")
                print("  ✅ 로컬 스토리지 지우기 완료")
            except Exception:
                pass
            
            # 세션 스토리지 지우기
            try:
                self.driver.execute_script("window.sessionStorage.clear();")
                print("  ✅ 세션 스토리지 지우기 완료")
            except Exception:
                pass
            
            # Chrome DevTools를 통한 캐시 지우기 (가능한 경우)
            try:
                self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                print("  ✅ 네트워크 캐시 지우기 완료")
            except Exception:
                pass
            
            print("✅ 캐시 정리 완료")
            return True
            
        except Exception as e:
            print(f"⚠️ 캐시 정리 중 오류: {str(e)}")
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
                
    # ========== 네트워크 모니터링 관련 메서드들 ==========
    
    def _enable_network_monitoring(self):
        """
        Chrome DevTools Protocol을 통한 네트워크 모니터링을 활성화합니다.
        """
        try:
            # Network 도메인 활성화
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.network_enabled = True
            print("✅ 네트워크 모니터링이 활성화되었습니다.")
        except Exception as e:
            if self.use_existing_chrome:
                print("⚠️ 기존 Chrome에서는 네트워크 모니터링이 제한될 수 있습니다.")
            else:
                print(f"❌ 네트워크 모니터링 활성화 실패: {str(e)}")
            self.network_enabled = False
    
    def add_monitoring_pattern(self, pattern: str):
        """
        모니터링할 URL 패턴을 추가합니다.
        
        Args:
            pattern: 모니터링할 URL 패턴 (예: "admissions-calculator")
        """
        if pattern not in self.monitoring_patterns:
            self.monitoring_patterns.append(pattern)
            print(f"📡 모니터링 패턴 추가: {pattern}")
    
    def get_network_responses(self, url_pattern: str = None) -> List[Dict[str, Any]]:
        """
        수집된 네트워크 응답을 가져옵니다.
        
        Args:
            url_pattern: 필터링할 URL 패턴 (선택사항)
            
        Returns:
            네트워크 응답 리스트
        """
        if not self.network_enabled:
            return []
        
        try:
            # Performance 로그에서 네트워크 이벤트 가져오기
            logs = self.driver.get_log('performance')
            responses = []
            
            for log in logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    response_data = message['message']['params']
                    response_url = response_data['response']['url']
                    
                    # URL 패턴 필터링
                    if url_pattern and url_pattern not in response_url:
                        continue
                    
                    # 응답 상태가 성공인 경우만
                    if response_data['response']['status'] >= 200 and response_data['response']['status'] < 300:
                        response_info = {
                            'url': response_url,
                            'status': response_data['response']['status'],
                            'headers': response_data['response']['headers'],
                            'request_id': response_data['requestId'],
                            'timestamp': log['timestamp']
                        }
                        responses.append(response_info)
            
            return responses
            
        except Exception as e:
            if self.use_existing_chrome and "log type 'performance' not found" in str(e):
                print("⚠️ 기존 Chrome에서는 performance 로그에 접근할 수 없습니다.")
            else:
                print(f"❌ 네트워크 응답 가져오기 실패: {str(e)}")
            return []
    
    def get_response_body(self, request_id: str) -> Optional[str]:
        """
        특정 요청 ID의 응답 본문을 가져옵니다.
        
        Args:
            request_id: 응답 본문을 가져올 요청 ID
            
        Returns:
            응답 본문 또는 None
        """
        if not self.network_enabled:
            return None
        
        try:
            response = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
            return response.get('body', None)
        except Exception as e:
            print(f"❌ 응답 본문 가져오기 실패 (ID: {request_id}): {str(e)}")
            return None
    
    def save_api_responses_to_file(self, url_pattern: str, filename: str) -> bool:
        """
        특정 URL 패턴의 첫 번째 성공한 API 응답을 텍스트 파일로 저장합니다.
        
        Args:
            url_pattern: 필터링할 URL 패턴
            filename: 저장할 파일명
            
        Returns:
            성공 여부
        """
        try:
            responses = self.get_network_responses(url_pattern)
            
            if not responses:
                print(f"⚠️ '{url_pattern}' 패턴과 일치하는 응답이 없습니다.")
                return False
            
            # 첫 번째 성공한 응답만 처리
            first_response = responses[0]
            body = self.get_response_body(first_response['request_id'])
            
            if not body:
                print(f"⚠️ 첫 번째 응답의 본문을 가져올 수 없습니다.")
                return False
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== API 응답 수집 결과 ===\n")
                f.write(f"패턴: {url_pattern}\n")
                f.write(f"수집 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"선택된 응답: 첫 번째 성공 응답 (총 {len(responses)}개 중)\n\n")
                
                f.write(f"--- API 응답 ---\n")
                f.write(f"URL: {first_response['url']}\n")
                f.write(f"상태: {first_response['status']}\n")
                f.write(f"요청 ID: {first_response['request_id']}\n\n")
                
                f.write("응답 본문:\n")
                f.write(body)
                f.write("\n")
            
            print(f"✅ 첫 번째 API 응답이 '{filename}'에 저장되었습니다. (총 {len(responses)}개 응답 중 선택)")
            return True
            
        except Exception as e:
            print(f"❌ 파일 저장 실패: {str(e)}")
            return False
    
