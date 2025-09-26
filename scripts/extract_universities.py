#!/usr/bin/env python3
"""
ranking.html에서 universities.json 추출 스크립트

US News ranking.html 파일에서 대학교 정보를 추출하여 universities.json을 생성합니다.
"""

import re
import json
import argparse
import html
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class University:
    name: str
    link: str
    id: str


class UniversityExtractor:
    def __init__(self, ranking_file: str = "data/ranking.html"):
        self.ranking_file = Path(ranking_file)
        self.universities: List[University] = []

    def extract_universities(self) -> List[University]:
        """ranking.html에서 대학교 정보 추출"""
        if not self.ranking_file.exists():
            print(f"파일이 존재하지 않습니다: {self.ranking_file}")
            return []

        try:
            content = self.ranking_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            return []

        universities = []
        
        # 대학교 정보를 추출하는 패턴들
        # 1. name 속성과 href 속성을 가진 div 요소에서 추출
        name_pattern = r'name="([^"]+)"'
        href_pattern = r'href="(/best-colleges/[^"]+)"'
        
        # 2. 정규식으로 대학교 정보 추출
        # div 요소에서 name과 href를 함께 찾기
        div_pattern = r'<div[^>]*name="([^"]+)"[^>]*>.*?<a[^>]*href="(/best-colleges/[^"]+)"'
        
        matches = re.findall(div_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for name, href in matches:
            # href에서 ID 추출 (예: /best-colleges/princeton-university-2627 -> 2627)
            id_match = re.search(r'-(\d+)(?:\?|$)', href)
            university_id = id_match.group(1) if id_match else ""
            
            # href에서 쿼리 파라미터 제거
            clean_href = href.split('?')[0]
            
            university = University(
                name=html.unescape(name),  # HTML 엔티티 디코딩
                link=clean_href,
                id=university_id
            )
            universities.append(university)
        
        # 중복 제거 (name 기준)
        seen_names = set()
        unique_universities = []
        for uni in universities:
            if uni.name not in seen_names:
                seen_names.add(uni.name)
                unique_universities.append(uni)
        
        self.universities = unique_universities
        return unique_universities

    def save_json(self, output_file: str = "data/universities.json") -> None:
        """JSON 파일로 저장"""
        if not self.universities:
            print("저장할 대학교 정보가 없습니다.")
            return

        # JSON 형태로 변환
        json_data = []
        for uni in self.universities:
            json_data.append({
                "name": uni.name,
                "link": uni.link
            })

        # 출력 디렉토리 생성
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"총 {len(json_data)}개 대학교 정보를 {output_file}에 저장했습니다.")

    def print_summary(self) -> None:
        """추출 결과 요약 출력"""
        if not self.universities:
            print("추출된 대학교 정보가 없습니다.")
            return

        print(f"\n추출된 대학교 수: {len(self.universities)}")
        print("\n처음 10개 대학교:")
        for i, uni in enumerate(self.universities[:10], 1):
            print(f"{i:2d}. {uni.name} (ID: {uni.id})")
        
        if len(self.universities) > 10:
            print(f"... 및 {len(self.universities) - 10}개 더")


def parse_args():
    parser = argparse.ArgumentParser(description='ranking.html에서 universities.json 추출')
    parser.add_argument('--input', type=str, default='data/ranking.html', help='입력 HTML 파일 경로')
    parser.add_argument('--output', type=str, default='data/universities.json', help='출력 JSON 파일 경로')
    parser.add_argument('--verbose', action='store_true', help='상세 정보 출력')
    return parser.parse_args()


def main():
    args = parse_args()
    print("US News 대학교 정보 추출기")
    print("="*40)
    
    extractor = UniversityExtractor(args.input)
    universities = extractor.extract_universities()
    
    if not universities:
        print("대학교 정보를 추출할 수 없습니다.")
        return
    
    if args.verbose:
        extractor.print_summary()
    
    extractor.save_json(args.output)
    print("완료!")


if __name__ == "__main__":
    main()
