# DEPRECATED: This script was used to initially parse ranking.html
# The data has been extracted to universities.json
# This file is kept for reference only
#!/usr/bin/env python3
"""
University Ranking Parser

HTML 파일에서 대학교 이름과 링크를 추출하여 JSON 파일로 저장하는 스크립트
"""

import json
import re
from bs4 import BeautifulSoup
from pathlib import Path


class UniversityRankingParser:
    """대학교 랭킹 HTML을 파싱하여 대학교 정보를 추출하는 클래스"""
    
    def __init__(self, html_file_path: str):
        """
        HTML 파일 경로로 파서 초기화
        
        Args:
            html_file_path: ranking.html 파일의 경로
        """
        self.html_file_path = Path(html_file_path)
        self.universities = []
    
    def parse_html(self) -> list:
        """
        HTML 파일을 파싱하여 대학교 정보 추출
        
        Returns:
            list: 대학교 정보가 담긴 딕셔너리 리스트
                 [{"name": "Princeton University", "link": "/best-colleges/princeton-university-2627"}, ...]
        """
        try:
            # HTML 파일 읽기
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Beautiful Soup로 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 대학교 리스트 아이템 찾기
            university_items = soup.find_all('li', class_='item-list__ListItemStyled-sc-18yjqdy-1')
            
            print(f"Found {len(university_items)} university items")
            
            for item in university_items:
                university_info = self._extract_university_info(item)
                if university_info:
                    self.universities.append(university_info)
            
            print(f"Successfully parsed {len(self.universities)} universities")
            return self.universities
            
        except FileNotFoundError:
            print(f"Error: HTML file not found at {self.html_file_path}")
            return []
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return []
    
    def _extract_university_info(self, item) -> dict:
        """
        개별 대학교 아이템에서 이름과 링크 추출
        
        Args:
            item: BeautifulSoup element (li 태그)
            
        Returns:
            dict: {"name": "University Name", "link": "/best-colleges/university-name-id"}
        """
        try:
            # 방법 1: name 속성에서 대학교 이름 찾기
            card_container = item.find('div', attrs={'name': True})
            if card_container:
                university_name = card_container.get('name')
            else:
                # 방법 2: h3 태그에서 대학교 이름 찾기
                h3_tag = item.find('h3')
                if h3_tag:
                    university_name = h3_tag.get_text().strip()
                else:
                    return None
            
            # 대학교 링크 찾기 - /best-colleges/로 시작하는 href
            link_element = item.find('a', href=re.compile(r'^/best-colleges/'))
            if not link_element:
                return None
            
            university_link = link_element.get('href')
            
            # URL에서 쿼리 파라미터 제거 (예: ?photo-strip)
            university_link = university_link.split('?')[0]
            
            return {
                "name": university_name,
                "link": university_link
            }
            
        except Exception as e:
            print(f"Error extracting university info: {e}")
            return None
    
    def save_to_json(self, output_file: str = "universities.json") -> bool:
        """
        추출된 대학교 정보를 JSON 파일로 저장
        
        Args:
            output_file: 저장할 JSON 파일명
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            output_path = Path(output_file)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(self.universities, file, indent=2, ensure_ascii=False)
            
            print(f"Successfully saved {len(self.universities)} universities to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False
    
    def print_universities(self):
        """추출된 대학교 정보를 콘솔에 출력"""
        if not self.universities:
            print("No universities found")
            return
        
        print(f"\n=== Extracted Universities ({len(self.universities)}) ===")
        for i, university in enumerate(self.universities, 1):
            print(f"{i:2d}. {university['name']}")
            print(f"    Link: {university['link']}")


def main():
    """메인 함수"""
    # HTML 파일 경로
    html_file = "ranking.html"
    
    # 파서 생성 및 실행
    parser = UniversityRankingParser(html_file)
    
    # HTML 파싱
    universities = parser.parse_html()
    
    if universities:
        # 결과 출력
        parser.print_universities()
        
        # JSON 파일로 저장
        parser.save_to_json("universities.json")
        
        print(f"\n✅ Successfully processed {len(universities)} universities")
        print("📁 Data saved to universities.json")
    else:
        print("❌ No universities found or error occurred")


if __name__ == "__main__":
    main()
