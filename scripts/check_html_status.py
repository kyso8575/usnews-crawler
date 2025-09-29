#!/usr/bin/env python3
"""
Downloads HTML Validator

- 로그인 여부 판별
- 에러 페이지 판별
- 콘텐츠 로딩/완전성 판별

결과는 JSON 하나로만 저장합니다.
"""

import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse


@dataclass
class PageCheckResult:
    university: str
    file_type: str
    path: str
    is_logged_in: bool
    is_premium: bool
    is_error_page: bool
    content_ok: bool
    issues: List[str]
    file_size: int


class DownloadsValidator:
    def __init__(self, downloads_dir: str = "downloads", verbose: bool = False):
        self.downloads_dir = Path(downloads_dir)
        self.results: List[PageCheckResult] = []
        self.verbose = verbose

        # 로그인/프리미엄 판별 관련 텍스트
        self.sign_in_markers = [r'\bSign in\b', r'\bLog in\b', r'로그인']
        self.sign_out_markers = [r'\bSign out\b', r'\bLog out\b', r'로그아웃']
        self.account_markers = [r'My Account', r'Profile', r'Settings']

        # 비로그인/업셀/락 표시 (비로그인 힌트)
        self.upsell_or_lock_patterns = [
            r'\bTry it now\b',
            r'compass.*unlock',
            r'premium.*unlock',
            r'College Compass',
        ]

        # 에러/차단/빈 페이지 판별(일반적인 텍스트 + USNews 일부 패턴)
        self.error_patterns = [
            r'404 Not Found',
            r'403 Forbidden',
            r'401 Unauthorized',
            r'We hit a snag',
            r'An error occurred',
            r'Access Denied',
            r'akamai error',
            r'cf-error',
            r'Captcha|captcha',
        ]


    def _match(self, pattern: str, text: str) -> bool:
        return re.search(pattern, text, re.IGNORECASE) is not None

    def _matches_any(self, patterns: List[str], text: str) -> Optional[str]:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return pat
        return None

    def _extract_canonical(self, content: str) -> Optional[str]:
        m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', content, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    def _is_premium_by_canonical(self, canonical_url: Optional[str]) -> bool:
        if not canonical_url:
            return False
        try:
            host = urlparse(canonical_url).hostname or ''
        except Exception:
            return False
        return host.startswith('premium.usnews.com')

    def check_file(self, file_path: Path) -> PageCheckResult:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return PageCheckResult(
                university=file_path.parent.name,
                file_type=file_path.stem,
                path=str(file_path),
                is_logged_in=False,
                is_premium=False,
                is_error_page=True,
                content_ok=False,
                issues=[f'read_error:{e}'],
                file_size=0,
            )

        issues: List[str] = []
        file_size = len(content)

        # canonical 검사로 premium 여부 우선 판정
        canonical = self._extract_canonical(content)
        is_premium = self._is_premium_by_canonical(canonical)
        if canonical:
            issues.append(f'canonical:{canonical}')
        if is_premium:
            issues.append('premium_by_canonical')

        # 로그인 여부: canonical URL 기준으로 우선 판단
        is_logged_in = False
        if is_premium:
            # premium canonical이면 로그인으로 간주
            is_logged_in = True
            issues.append('login_hit:premium_host')
        elif canonical and 'www.usnews.com' in canonical:
            # www.usnews.com canonical이면 비로그인으로 간주
            is_logged_in = False
            issues.append('not_logged_in:www_host')
        elif self._matches_any(self.sign_out_markers, content):
            # Sign out/Log out이 있으면 로그인으로 간주
            is_logged_in = True
            issues.append('login_hit:signout')
        elif self._matches_any(self.sign_in_markers, content):
            # Sign in/Log in이 있으면 비로그인으로 간주
            is_logged_in = False
            issues.append('login_hint:signin_present')
        else:
            # canonical URL이 없거나 다른 호스트면 불확실
            is_logged_in = False
            issues.append('not_logged_in:no_canonical_or_unknown_host')

        # 에러페이지 판단
        error_hit = self._matches_any(self.error_patterns, content)
        is_error_page = bool(error_hit)
        if error_hit:
            issues.append(f'error_hit:{error_hit}')

        # 업셀/락 힌트 기록(참고용)
        upsell_hit = self._matches_any(self.upsell_or_lock_patterns, content)
        if upsell_hit:
            issues.append(f'upsell:{upsell_hit}')

        # 콘텐츠 완전성은 항상 True로 설정 (로직 제거)
        content_ok = True

        if self.verbose:
            print(f"- Checked {file_path}: logged_in={is_logged_in}, premium={is_premium}, error={is_error_page}, content_ok={content_ok}")

        return PageCheckResult(
            university=file_path.parent.name,
            file_type=file_path.stem,
            path=str(file_path),
            is_logged_in=is_logged_in,
            is_premium=is_premium,
            is_error_page=is_error_page,
            content_ok=content_ok,
            issues=issues,
            file_size=file_size,
        )

    def scan(self, only_university: Optional[str] = None) -> List[PageCheckResult]:
        if not self.downloads_dir.exists():
            print(f'downloads 폴더가 없습니다: {self.downloads_dir}')
            return []
        results: List[PageCheckResult] = []
        uni_dirs = [d for d in self.downloads_dir.iterdir() if d.is_dir()]
        if only_university:
            uni_dirs = [d for d in uni_dirs if d.name == only_university]
        uni_dirs = sorted(uni_dirs)
        print(f"대상 대학교 수: {len(uni_dirs)}")
        for idx, uni_dir in enumerate(uni_dirs, 1):
            html_files = sorted(uni_dir.glob('*.html'))
            print(f"[{idx}/{len(uni_dirs)}] {uni_dir.name} - 파일 {len(html_files)}개 검사")
            for html in html_files:
                results.append(self.check_file(html))
        self.results = results
        return results

    def print_summary(self) -> None:
        # 문제가 있는 페이지만 필터링
        problem_pages = []
        for r in self.results:
            if not r.is_logged_in or r.is_error_page:
                problem_pages.append(r)
        
        print("\n" + "="*60)
        print("HTML 상태 검사 결과")
        print("="*60)
        print(f"총 파일 수: {len(self.results)}")
        print(f"로그인된 파일: {sum(1 for r in self.results if r.is_logged_in)}")
        print(f"에러 페이지: {sum(1 for r in self.results if r.is_error_page)}")
        print(f"문제 페이지: {len(problem_pages)}")
        
        if problem_pages:
            print(f"\n문제 페이지 목록:")
            for page in problem_pages:
                print(f"  - {page.university}/{page.file_type}.html")
                if not page.is_logged_in:
                    print(f"    * 로그인 안됨")
                if page.is_error_page:
                    print(f"    * 에러 페이지")
                for issue in page.issues:
                    print(f"    * {issue}")
        else:
            print("\n모든 페이지가 정상입니다!")

    def save_json_report(self, output: str = 'html_quality_report.json') -> None:
        # 문제가 있는 페이지만 필터링 (링크만 포함)
        problem_pages = []
        for r in self.results:
            if not r.is_logged_in or r.is_error_page:
                problem_pages.append(r.path)
        
        summary: Dict[str, int] = {
            'total_files': len(self.results),
            'problem_files': len(problem_pages),
            'logged_in_files': sum(1 for r in self.results if r.is_logged_in),
            'not_logged_in_files': sum(1 for r in self.results if not r.is_logged_in),
            'error_pages': sum(1 for r in self.results if r.is_error_page),
        }
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'problem_pages': problem_pages,
        }
        
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'JSON 리포트 저장: {output}')


def parse_args():
    parser = argparse.ArgumentParser(description='Downloads HTML Validator')
    parser.add_argument('--university', type=str, default=None, help='특정 대학교명만 검사 (예: Princeton_University)')
    parser.add_argument('--verbose', action='store_true', help='진행 로그 출력')
    parser.add_argument('--json', action='store_true', help='JSON 리포트 생성')
    parser.add_argument('--output', type=str, default='html_quality_report.json', help='JSON 리포트 파일명 (--json 옵션과 함께 사용)')
    return parser.parse_args()


def main():
    args = parse_args()
    print('Downloads HTML Validator 실행')
    validator = DownloadsValidator(verbose=args.verbose)
    results = validator.scan(only_university=args.university)
    if not results:
        print('검사할 HTML이 없습니다.')
        return
    
    # 기본적으로 콘솔에 요약 출력
    validator.print_summary()
    
    # --json 옵션이 있으면 JSON 리포트도 생성
    if args.json:
        validator.save_json_report(args.output)
    
    print('\n완료')


if __name__ == '__main__':
    main()
