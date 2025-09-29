"""
Selenium Configuration and Constants

이 모듈은 Selenium 관련 설정과 상수들을 관리합니다.
"""

import logging
from dataclasses import dataclass
from typing import List

# ===================== Module-level Constants =====================
# Defaults (constructor compatibility)
DEFAULT_IMPLICIT_WAIT = 5

# Error detection constants (URL/status based only)
NETWORK_ERROR_URL_INDICATORS = [
    "chrome-error://",
    "chrome://network-error/",
]

PERMANENT_STATUS_CODES = [404, 410]
RETRY_POSSIBLE_CODES = [408, 429]

# Common popup close selectors
CLOSE_SELECTORS = [
    # 일반적인 닫기 버튼
    'button[aria-label="Close"]',
    'button[title="Close"]',
    'button.close',
    '.close-button',
    '.modal-close',
    '.popup-close',
    '[data-dismiss="modal"]',
    # X 버튼들
    'button:contains("×")',
    'button:contains("✕")',
    'span.close',
    '.fa-times',
    '.fa-close',
    # US News 특정 팝업들
    '.sailthru-overlay-close',
    '.newsletter-signup-close',
    '.subscription-modal-close',
    '.ad-close',
    '.banner-close',
    # 쿠키 동의 관련
    'button:contains("Accept")',
    'button:contains("OK")',
    'button:contains("Got it")',
    'button:contains("Continue")',
    '.cookie-consent button',
    # 구독/로그인 관련 팝업
    '.subscription-overlay .close',
    '.login-modal .close',
    '.paywall-close',
]


@dataclass
class SeleniumConfig:
    """Holds timeouts and behavior flags for SeleniumBase."""
    implicit_wait: int = DEFAULT_IMPLICIT_WAIT
    page_load_timeout: int = 20
    response_slow_threshold: int = 10
    startup_healthcheck_timeout: int = 10
    pre_nav_healthcheck_timeout: int = 30
    healthcheck_on_startup: bool = True
    healthcheck_before_navigation: bool = False
    origin_nav_timeout: int = 30  # 세션 캡처시 사이트 방문 타임아웃
    post_render_wait_seconds: int = 4
    navigate_retry_count: int = 1
    retry_backoff_seconds: int = 60
    debugger_address: str = "127.0.0.1:9222"
    restart_pause_seconds: int = 2
    # Login check
    login_check_url: str = "https://premium.usnews.com/best-colleges"
    login_check_timeout_seconds: int = 10


def setup_basic_logging(level: int = logging.INFO) -> None:
    """Initialize basic logging to stdout if not already configured."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format='%(message)s')
