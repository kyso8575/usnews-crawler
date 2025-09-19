#!/usr/bin/env python3
"""
API Response Collector

이 스크립트는 applying 페이지에서 admissions-calculator API 응답만 수집합니다.
HTML 다운로드와는 별개로 동작하며, 새로운 Chrome 인스턴스를 사용합니다.
"""

import sys
import os
from html_downloader import HTMLDownloader


def print_header(title: str, width: int = 50):
    """Print a formatted header."""
    print(title)
    print("=" * width)


def show_help():
    """Show help information."""
    print_header("📊 API Response Collector")
    print("Usage:")
    print("  python api_collector.py <university_name>")
    print("  python api_collector.py --help")
    print()
    print("Examples:")
    print("  python api_collector.py harvard")
    print("  python api_collector.py 'Princeton University'")
    print("  python api_collector.py mit")
    print()
    print("Description:")
    print("  - applying 페이지에서 admissions-calculator API 응답만 수집")
    print("  - 새로운 Chrome 인스턴스 사용 (네트워크 모니터링 지원)")
    print("  - HTML 파일이 이미 존재해도 API 응답만 추가로 저장")


def collect_api_response(university_name: str):
    """
    특정 대학의 applying 페이지에서 API 응답을 수집합니다.
    
    Args:
        university_name: 대학교 이름
    """
    downloader = None
    try:
        print_header("📊 API Response Collector")
        print(f"Target University: {university_name}")
        print()
        
        # 새로운 Chrome 인스턴스로 API 응답 수집
        print("🔍 새로운 Chrome 인스턴스로 API 응답 수집 시작...")
        downloader = HTMLDownloader(headless=True, use_existing_chrome=False, enable_api_collection=True)
        
        # applying 페이지에서 API 응답 수집
        print(f"📡 {university_name}의 applying 페이지에서 API 응답 수집 중...")
        result = downloader.download_university_page(university_name, "applying")
        
        if result:
            # API 응답 파일 경로 생성
            api_file = result.replace('.html', '_api_responses.txt')
            
            if os.path.exists(api_file):
                file_size = os.path.getsize(api_file)
                print(f"\n✅ API 응답 수집 성공!")
                print(f"📁 HTML 파일: {result}")
                print(f"📊 API 응답 파일: {api_file}")
                print(f"📏 API 응답 크기: {file_size:,} bytes")
                
                # API 응답 내용 미리보기
                try:
                    with open(api_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'school_id=' in content and '"data":' in content:
                        # school_id 추출
                        import re
                        school_id_match = re.search(r'school_id=(\d+)', content)
                        if school_id_match:
                            school_id = school_id_match.group(1)
                            print(f"🎯 확인된 school_id: {school_id}")
                        
                        print("✅ API 데이터 검증 완료!")
                    else:
                        print("⚠️ API 응답 형식을 확인할 수 없습니다.")
                        
                except Exception as e:
                    print(f"⚠️ API 응답 파일 읽기 실패: {e}")
            else:
                print("❌ API 응답 파일이 생성되지 않았습니다.")
                
        else:
            print("❌ applying 페이지 다운로드 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API 응답 수집 중 오류 발생: {str(e)}")
        return False
        
    finally:
        if downloader:
            downloader.close()
            print("\n🔒 Chrome 브라우저 종료")


def main():
    """Main function."""
    if len(sys.argv) != 2:
        show_help()
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg in ["--help", "-h"]:
        show_help()
        return
    
    university_name = arg
    
    success = collect_api_response(university_name)
    
    if success:
        print_header("\n🎉 API 응답 수집 완료!")
        print("💡 이제 downloads/ 폴더에서 API 응답 파일을 확인하세요.")
    else:
        print_header("\n❌ API 응답 수집 실패")
        print("💡 Tips:")
        print("- 대학교 이름이 정확한지 확인하세요")
        print("- 'python main_scraper.py --list'로 사용 가능한 대학 목록 확인")
        print("- applying 페이지가 존재하는지 확인하세요")


if __name__ == "__main__":
    main()
