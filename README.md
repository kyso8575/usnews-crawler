# 🎓 US News University Scraper

미국 대학교 정보를 US News에서 자동으로 스크래핑하는 도구입니다.

## 📋 기능

- 436개 미국 대학교 정보 자동 수집
- 7가지 페이지 타입 지원: main, overall-rankings, applying, paying, academics, student-life, campus-info
- 기존 Chrome 브라우저 연결 지원
- 자동 타임아웃으로 빠른 수집
- 대학교별 폴더 자동 생성
- **🆕 Admissions Calculator API 모니터링**: 네트워크 응답 실시간 감지 및 저장

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (이미 설치됨)
pip install -r requirements.txt
```

### 2. 기본 사용법 (헤드리스 모드)

```bash
# 개별 대학교 스크래핑 (백그라운드에서 실행)
python main_scraper.py princeton
python main_scraper.py harvard
python main_scraper.py mit

# 모든 대학교 일괄 스크래핑 (436개 대학교)
python main_scraper.py --all

# 사용 가능한 대학교 목록 보기
python main_scraper.py --list

# 도움말
python main_scraper.py --help
```

**참고**: 모든 스크래핑은 헤드리스 모드(백그라운드)에서 실행되어 브라우저 창이 뜨지 않습니다.

### 3. 🆕 Admissions Calculator API 모니터링

US News의 Admissions Calculator API 응답을 실시간으로 감지하고 저장할 수 있습니다.

```bash
# 대화형 API 모니터링 (추천)
python admissions_calculator_monitor.py

# 또는 테스트 스크립트 실행
python test_api_monitor.py
```

**사용법**:
1. 브라우저가 열리면 대학 페이지로 이동
2. Admissions Calculator 섹션에서 성적 입력/계산 버튼 클릭
3. API 응답이 자동으로 `api_responses/` 폴더에 저장됨

**타겟 API**: `https://www.usnews.com/best-colleges/compass/api/admissions-calculator?school_id=...`

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
│   └── campus_info.html
├── Harvard_University/
│   ├── main.html
│   ├── overall_rankings.html
│   ├── applying.html
│   ├── paying.html
│   ├── academics.html
│   ├── student_life.html
│   └── campus_info.html
└── ...

api_responses/
├── princeton_university_2155.txt
├── harvard_university_2155.txt
├── admissions_api_20240918_143022.txt
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
# 436개 모든 대학교 스크래핑
python main_scraper.py --all

# ⚠️ 주의사항:
# - 매우 오래 걸립니다 (수 시간~수 일)
# - Ctrl+C로 언제든 중단 가능
# - 진행률과 통계를 실시간으로 표시
# - 실패한 대학교는 자동으로 건너뜀
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

### API 모니터링 사용

```bash
# 1. 대화형 모니터링 실행
python admissions_calculator_monitor.py

# 출력 예시:
# 🎓 대학 이름을 입력하세요: Princeton University
# 🆔 대학 ID를 입력하세요: 2155
# 🌐 대학 페이지로 이동: https://www.usnews.com/best-colleges/princeton-university-2155
# 📡 API 모니터링 시작: best-colleges/compass/api/admissions-calculator
# ⏳ API 호출 대기 중... (최대 60초)
# ✅ 1개의 API 응답 감지!
# 🎉 API 응답이 성공적으로 저장되었습니다: api_responses/princeton_university_2155.txt

# 2. 프로그래밍 방식 사용
python -c "
from admissions_calculator_monitor import AdmissionsCalculatorMonitor
monitor = AdmissionsCalculatorMonitor(headless=False)
saved_file = monitor.monitor_university_api('Princeton University', '2155')
print(f'저장됨: {saved_file}')
"
```

## ⚙️ 설정 옵션

### HTMLDownloader 클래스 옵션

```python
from html_downloader import HTMLDownloader

# 기본 사용 (헤드리스 모드)
downloader = HTMLDownloader(headless=True)

# 기존 Chrome 사용 (개발/디버깅용)
downloader = HTMLDownloader(headless=False, use_existing_chrome=True)

# 위젯 제거 비활성화
downloader = HTMLDownloader(headless=True, truncate_at_widget=False)
```

## 🔧 고급 사용법

### 개별 페이지 다운로드

```python
from html_downloader import HTMLDownloader

downloader = HTMLDownloader(headless=True)
downloader.setup_driver()

# 특정 페이지만 다운로드
file_path = downloader.download_university_page("princeton", "applying")
print(f"저장됨: {file_path}")

downloader.close()
```

### 대학교 정보 조회

```python
from html_downloader import HTMLDownloader

downloader = HTMLDownloader(headless=True)

# 대학교 검색
university_info = downloader.find_university_by_name("princeton")
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
Target University: princeton

📥 Downloading HTML Content from All Pages
--------------------------------------------------
✅ Loaded 436 universities from universities.json

📚 Downloading all pages for Princeton University (ID: 2627)
============================================================

📖 [1/4] Downloading applying page...
----------------------------------------
📥 applying 페이지 다운로드 중...
✅ 페이지 로딩 완료
✅ 저장됨: applying.html (345,009자)

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

## 🔄 업데이트

새로운 대학교 정보를 업데이트하려면:

```bash
# ranking.html 파일 업데이트 후
python university_ranking_parser.py
```

## 📋 요구사항

- Python 3.13+
- Chrome 브라우저
- 필요한 패키지: `requirements.txt` 참조

## 📞 문의

문제가 발생하거나 새로운 기능이 필요하시면 이슈를 생성해주세요.
