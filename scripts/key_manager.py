"""
Key Manager Script

이 스크립트는 새로운 대학교 데이터를 처리할 때 
기존에 없던 새로운 키를 감지하고 설명을 추가하는 시스템입니다.
"""

import json
import os
from typing import Dict, List, Set, Any
from datetime import datetime


class KeyManager:
    def __init__(self, descriptions_file: str = "data/key_descriptions.json"):
        self.descriptions_file = descriptions_file
        self.load_descriptions()
    
    def load_descriptions(self):
        """키 설명 파일을 로드합니다."""
        if os.path.exists(self.descriptions_file):
            with open(self.descriptions_file, 'r', encoding='utf-8') as f:
                self.descriptions = json.load(f)
        else:
            self.descriptions = self._create_empty_descriptions()
    
    def save_descriptions(self):
        """키 설명 파일을 저장합니다."""
        self.descriptions["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(self.descriptions_file, 'w', encoding='utf-8') as f:
            json.dump(self.descriptions, f, ensure_ascii=False, indent=2)
    
    def _create_empty_descriptions(self) -> Dict:
        """빈 설명 구조를 생성합니다."""
        return {
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "description": "University data key descriptions and mappings",
                "total_keys": 0,
                "universities_processed": []
            },
            "pages": {
                "campus_info": {"description": "Campus information", "total_keys": 0, "keys": {}},
                "student_life": {"description": "Student life information", "total_keys": 0, "keys": {}},
                "academics": {"description": "Academic information", "total_keys": 0, "keys": {}},
                "applying": {"description": "Application information", "total_keys": 0, "keys": {}},
                "paying": {"description": "Financial information", "total_keys": 0, "keys": {}},
                "overall_rankings": {"description": "University rankings", "total_keys": 0, "keys": {}}
            },
            "unknown_keys": {
                "description": "Keys found in new universities that don't exist in the description database",
                "keys": {}
            }
        }
    
    def get_known_keys(self, page_type: str) -> Set[str]:
        """특정 페이지 타입의 알려진 키들을 반환합니다."""
        if page_type in self.descriptions["pages"]:
            return set(self.descriptions["pages"][page_type]["keys"].keys())
        return set()
    
    def find_new_keys(self, university_data: Dict[str, Any], university_name: str) -> Dict[str, List[str]]:
        """새로운 키들을 찾습니다."""
        new_keys = {}
        
        for page_type, page_data in university_data.items():
            if page_type in ["university_name", "currency", "source"]:
                continue
                
            # overall_rankings 페이지의 경우 rankings 키 하위 데이터 확인
            if page_type == "overall_rankings" and isinstance(page_data, dict) and "rankings" in page_data:
                actual_keys = set(page_data["rankings"].keys())
                page_type = "overall_rankings"
            elif isinstance(page_data, dict):
                actual_keys = set(page_data.keys())
            else:
                continue
            
            known_keys = self.get_known_keys(page_type)
            unknown_keys = actual_keys - known_keys
            
            if unknown_keys:
                new_keys[page_type] = list(unknown_keys)
                print(f"🔍 {page_type}: {len(unknown_keys)}개의 새로운 키 발견")
                for key in unknown_keys:
                    print(f"   - {key}")
        
        return new_keys
    
    def add_unknown_keys(self, new_keys: Dict[str, List[str]], university_name: str):
        """알려지지 않은 키들을 unknown_keys 섹션에 추가합니다."""
        for page_type, keys in new_keys.items():
            for key in keys:
                key_id = f"{page_type}_{key}"
                if key_id not in self.descriptions["unknown_keys"]["keys"]:
                    self.descriptions["unknown_keys"]["keys"][key_id] = {
                        "key": key,
                        "page_type": page_type,
                        "first_seen_in": university_name,
                        "description": "TODO: Add description",
                        "data_type": "unknown",
                        "example": "TODO: Add example",
                        "needs_review": True
                    }
        
        # 메타데이터 업데이트
        if university_name not in self.descriptions["metadata"]["universities_processed"]:
            self.descriptions["metadata"]["universities_processed"].append(university_name)
    
    def process_university_data(self, data_dir: str, university_name: str) -> Dict[str, Any]:
        """대학교 데이터를 처리하고 새로운 키를 찾습니다."""
        print(f"\\n🏫 Processing {university_name}...")
        
        # 대학교 데이터 파일들 찾기
        university_files = [f for f in os.listdir(data_dir) 
                          if f.startswith(university_name.replace(' ', '_')) and f.endswith('.json')]
        
        if not university_files:
            print(f"❌ No data files found for {university_name}")
            return {}
        
        # 모든 페이지 데이터 로드
        university_data = {}
        for file in university_files:
            page_type = file.replace(f"{university_name.replace(' ', '_')}_", "").replace('.json', '')
            file_path = os.path.join(data_dir, file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if page_type == "overall_rankings":
                    university_data[page_type] = {"rankings": data.get("rankings", {})}
                else:
                    university_data[page_type] = data.get(page_type, {})
        
        # 새로운 키 찾기
        new_keys = self.find_new_keys(university_data, university_name)
        
        if new_keys:
            print(f"\\n📝 총 {sum(len(keys) for keys in new_keys.values())}개의 새로운 키 발견!")
            self.add_unknown_keys(new_keys, university_name)
            self.save_descriptions()
            print("✅ 새로운 키들이 key_descriptions.json에 추가되었습니다.")
        else:
            print("✅ 새로운 키가 발견되지 않았습니다.")
        
        return new_keys
    
    def show_unknown_keys(self):
        """검토가 필요한 알려지지 않은 키들을 표시합니다."""
        unknown_keys = self.descriptions["unknown_keys"]["keys"]
        needs_review = [k for k, v in unknown_keys.items() if v.get("needs_review", False)]
        
        if needs_review:
            print(f"\\n📋 검토가 필요한 키들 ({len(needs_review)}개):")
            for key_id in needs_review:
                key_info = unknown_keys[key_id]
                print(f"   - {key_info['page_type']}: {key_info['key']}")
                print(f"     첫 발견: {key_info['first_seen_in']}")
                print(f"     설명 필요: {key_info['description']}")
        else:
            print("\\n✅ 검토가 필요한 키가 없습니다.")


if __name__ == "__main__":
    # 사용 예시
    key_manager = KeyManager()
    
    # 프린스턴 대학교 데이터 처리
    new_keys = key_manager.process_university_data("data/extracted", "Princeton University")
    
    # 알려지지 않은 키들 표시
    key_manager.show_unknown_keys()
