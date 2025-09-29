# 🎓 US News University HTML Downloader

미국 대학교 정보를 US News에서 자동으로 HTML 파일로 다운로드하는 도구입니다.

## 📋 기능

- **1,827개 미국 대학교** HTML 자동 다운로드
- **7가지 페이지 타입** 지원: main, overall-rankings, applying, paying, academics, student-life, campus-info
- **🔐 로그인 세션 캡처**: 기존 Chrome에서 로그인 상태를 복사하여 새 브라우저에서 사용
- **모듈화된 아키텍처**: selenium 기능을 6개 모듈로 분리하여 유지보수성 향상
- **30초 딜레이**: 서버 부하 방지를 위한 안전한 다운로드 간격
- **대학교별 폴더** 자동 생성
- **중복 콘텐츠 감지**: SHA256 해시로 동일한 내용 중복 저장 방지

- **Admissions Calculator JSON 캡처 (NEW)**: 기존 로그인 세션을 이용해 `admissions-calculator` API 응답 JSON 저장

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (이미 설치됨)
pip install -r requirements.txt
```

### 2. 기본 사용법

```bash
# 개별 대학교 HTML 다운로드 (세션 캡처 모드)
python main.py "Princeton University"
python main.py "Harvard University"
python main.py "MIT"

# 모든 대학교 일괄 HTML 다운로드 (1,827개 대학교)
python main.py --all

# 사용 가능한 대학교 목록 보기
python main.py --list

# 도움말
python main.py --help
```

**🔐 로그인 세션 캡처**: 기존 Chrome에서 로그인 상태를 자동으로 복사하여 새 브라우저에서 사용합니다.

### 3. 🔐 로그인 세션 캡처 설정

프리미엄 콘텐츠에 접근하려면 로그인된 Chrome 브라우저가 필요합니다:

```bash
# 1. Chrome을 디버그 모드로 실행
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev_session

# 2. 브라우저에서 US News에 로그인
# https://www.usnews.com 에서 로그인

# 3. 스크래퍼 실행 (자동으로 세션 캡처)
python main.py "Princeton University"
```

**세션 캡처 로그 예시**:
```
🔍 세션 캡처 시작: ['https://www.usnews.com', 'https://premium.usnews.com']
✅ Chrome 연결 성공
🍪 https://www.usnews.com에서 쿠키 84개 수집
💾 https://www.usnews.com에서 localStorage 90개 수집
🗂️ https://www.usnews.com에서 sessionStorage 3개 수집
🔐 세션 캡처: 쿠키 168개, localStorage 89개, sessionStorage 3개
🔐 기존 Chrome의 로그인 세션을 캡처했습니다.
```

### 4. 📊 Admissions Calculator JSON 캡처 (API)

기존 Chrome 로그인 세션을 활용해 학교별 `admissions-calculator` API 응답 JSON을 저장합니다.

1) Chrome을 디버그 모드로 실행하고 로그인 상태를 유지하세요:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_dev_session
```

2) 단일 학교 수집:

```bash
# 이름으로 (부분 매칭 가능)
venv/bin/python scripts/fetch_admissions_calculator.py --name "Princeton University"

# 링크로 (예: universities.json의 link 값)
venv/bin/python scripts/fetch_admissions_calculator.py --link "/best-colleges/princeton-university-2627"

# school_id 직접 지정
venv/bin/python scripts/fetch_admissions_calculator.py --school-id 2627 --name "Princeton University"
```

3) 일괄 수집 (전체):

```bash
# 전체에서 앞의 N개만, 항목 간 지연, 타임아웃 조정
venv/bin/python scripts/fetch_admissions_calculator.py --all --limit 100 --delay 0.5 --wait 20

# 기존 파일 덮어쓰기
venv/bin/python scripts/fetch_admissions_calculator.py --all --overwrite --wait 20
```

4) 출력 위치:

```
downloads/<University>/admissions_calculator.json
```

5) 참고 사항:
- 반드시 디버그 모드 Chrome에 로그인되어 있어야 합니다.
- 타임아웃이 짧으면 캡처에 실패할 수 있으니 `--wait` 값을 늘려보세요.
- 이미 파일이 있으면 기본적으로 스킵합니다. 덮어쓰려면 `--overwrite` 사용.

## 📁 출력 구조

```
downloads/
├── Princeton_University/
│   ├── main.html
│   ├── overall_rankings.html
│   ├── applying.html
│   ├── paying.html
│   ├── academics.html
│   ├── student_life.html
│   ├── campus_info.html
│   └── admissions_calculator.json  # API 응답(JSON)
├── Harvard_University/
│   ├── main.html
│   ├── overall_rankings.html
│   ├── applying.html
│   ├── paying.html
│   ├── academics.html
│   ├── student_life.html
│   └── campus_info.html
└── ...

```

## 📖 사용 예시

### 개별 대학교 스크래핑

```bash
# Princeton University 스크래핑
python main_scraper.py princeton

# Harvard University 스크래핑  
python main_scraper.py harvard

# MIT 스크래핑
python main_scraper.py mit
```

### 일괄 스크래핑 (모든 대학교)

```bash
# 1,827개 모든 대학교 스크래핑
python main_scraper.py --all

# ⚠️ 주의사항:
# - 매우 오래 걸립니다 (수 시간~수 일)
# - Ctrl+C로 언제든 중단 가능
# - 진행률과 통계를 실시간으로 표시
# - 실패한 대학교는 자동으로 건너뜀
# - 이미 다운로드된 대학교는 자동으로 스킵
```

### 대학교 이름 검색

```bash
# 사용 가능한 모든 대학교 목록 보기
python main_scraper.py --list

# 출력 예시:
# 1. Princeton University
# 2. Massachusetts Institute of Technology
# 3. Harvard University
# ...
```

### 부분 이름으로 검색

대학교 이름의 일부만 입력해도 자동으로 찾아줍니다:

```bash
python main_scraper.py stanford    # Stanford University
python main_scraper.py "new york"  # New York University
python main_scraper.py texas       # The University of Texas--Austin (첫 번째 매칭)
```

### 중복 콘텐츠 감지

스크래퍼는 SHA256 해시를 사용하여 동일한 콘텐츠의 중복 저장을 방지합니다:

```bash
# 이미 다운로드된 대학교는 자동으로 스킵
⏭️ Princeton University 이미 완전히 다운로드됨 - 스킵
📁 기존 파일: 7개 (완료)
```

## ⚙️ 설정 옵션

### HTMLDownloader 클래스 옵션

```python
from usnews_scraper.html_downloader import HTMLDownloader, DownloaderConfig

# 기본 사용 (세션 캡처 모드)
config = DownloaderConfig(preserve_login_from_existing=True)
downloader = HTMLDownloader(
    headless=True, 
    use_existing_chrome=False,
    downloader_config=config
)

# 기존 Chrome 직접 사용 (개발/디버깅용)
downloader = HTMLDownloader(headless=False, use_existing_chrome=True)

# 위젯 제거 비활성화
config = DownloaderConfig(truncate_at_widget=False)
downloader = HTMLDownloader(downloader_config=config)
```

## 🔧 고급 사용법

### 개별 페이지 다운로드

```python
from usnews_scraper.html_downloader import HTMLDownloader, DownloaderConfig

config = DownloaderConfig(preserve_login_from_existing=True)
downloader = HTMLDownloader(
    headless=True, 
    use_existing_chrome=False,
    downloader_config=config
)

# 특정 페이지만 다운로드
file_path = downloader.download_university_page("Princeton University", "applying")
print(f"저장됨: {file_path}")

downloader.close()
```

### 대학교 정보 조회

```python
from usnews_scraper.html_downloader import HTMLDownloader

downloader = HTMLDownloader(headless=True)

# 대학교 검색
university_info = downloader.find_university_by_name("Princeton University")
print(university_info)
# {'name': 'Princeton University', 'link': '/best-colleges/princeton-university-2627', 'id': '2627'}

# 모든 대학교 목록
universities = downloader.list_all_universities()
print(f"총 {len(universities)}개 대학교")
```

## 📝 로그 출력

실행 중 다음과 같은 로그가 출력됩니다:

```
🎓 US News University Scraper
==================================================
Target University: Princeton University

📥 Downloading HTML Content from All Pages
==================================================
✅ Loaded 1827 universities from data/universities.json
🔍 세션 캡처 시작: ['https://www.usnews.com', 'https://premium.usnews.com']
🔗 Chrome 연결 시도: 127.0.0.1:9222
✅ Chrome 연결 성공
🍪 https://www.usnews.com에서 쿠키 84개 수집
💾 https://www.usnews.com에서 localStorage 90개 수집
🗂️ https://www.usnews.com에서 sessionStorage 3개 수집
🔐 세션 캡처: 쿠키 168개, localStorage 89개, sessionStorage 3개
🔐 기존 Chrome의 로그인 세션을 캡처했습니다.

📚 Downloading all pages for Princeton University
============================================================
🔄 Chrome 응답성 확인 중...
✅ Chrome 정상 동작 중
🔐 로그인 세션 적용 시도 중... (1/3)
🔐 로그인 세션 적용 완료 (학교 단위)

📖 [1/7] Downloading main page...
----------------------------------------
📥 main 페이지 다운로드 중...
✅ 페이지 로딩 완료
✅ 저장됨: main.html (412,745자)
⏳ Waiting 10 seconds before next download...
...
```

## 🛠️ 문제 해결

### Chrome 연결 오류

```
❌ URL 이동 중 오류: Message: chrome not reachable
```

**해결법**: Chrome이 디버그 모드로 실행되었는지 확인하세요.

### 대학교를 찾을 수 없음

```
❌ University 'unknown' not found in the universities list
```

**해결법**: 
- `python main_scraper.py --list`로 정확한 이름 확인
- 부분 이름으로 검색해보세요 (예: "harvard" 대신 "harv")

### 페이지 로딩 타임아웃

```
⚠️ 타임아웃으로 로딩 중단 (메인 콘텐츠 확보)
```

이는 정상적인 동작입니다. 메인 콘텐츠는 확보되며, 추천 위젯 로딩을 방지합니다.

## 📊 지원하는 페이지 타입

1. **main**: 대학교 메인 페이지 (개요 정보)
2. **overall-rankings**: 전체 랭킹 정보
3. **applying**: 입학 정보 (지원 요건, 시험 점수 등)
4. **paying**: 학비 및 재정 지원 정보
5. **academics**: 학과 및 학업 정보
6. **student-life**: 학생 생활 정보 (기숙사, 클럽 등)
7. **campus-info**: 캠퍼스 정보 (위치, 시설 등)

## 🏗️ 아키텍처

### 모듈화된 구조

```
scraper/
├── usnews_scraper/         # HTML 다운로더 패키지
│   ├── selenium/           # Selenium 모듈들
│   │   ├── __init__.py     # 통합 모듈
│   │   ├── config.py       # 설정과 상수
│   │   ├── chrome_setup.py # Chrome 설정
│   │   ├── navigation.py   # 네비게이션/에러 처리
│   │   ├── session_manager.py # 세션 관리
│   │   └── health_check.py # 상태 체크
│   ├── html_downloader.py # 메인 HTML 다운로더
│   └── selenium_base.py    # 통합 베이스 클래스
├── data/
│   └── universities.json   # 대학교 목록 데이터
├── downloads/              # 다운로드된 HTML 파일들
├── main.py                 # 메인 실행 파일
└── requirements.txt       # 의존성 패키지
```

### 주요 특징

- **HTML 전용**: HTML 파일 다운로드에 특화된 간단한 구조
- **모듈화**: 기능별 독립적인 모듈로 분리
- **유지보수성**: 각 기능을 개별적으로 수정 가능
- **안전한 다운로드**: 30초 딜레이로 서버 부하 방지

## 📋 요구사항

- Python 3.13+
- Chrome 브라우저
- 필요한 패키지: `requirements.txt` 참조

## 📞 문의

문제가 발생하거나 새로운 기능이 필요하시면 이슈를 생성해주세요.
