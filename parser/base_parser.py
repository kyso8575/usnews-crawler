"""
Base Parser with Key Management System

이 모듈은 모든 파서의 기본 클래스를 제공하며,
자동으로 새로운 키를 감지하고 설명을 추가하는 기능을 포함합니다.
"""

import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from scripts.key_manager import KeyManager


class BaseParser:
    """모든 파서의 기본 클래스 - 키 관리 시스템 포함"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.key_manager = KeyManager()
    
    def parse(self, html_content: str, university_name: str, page_type: str, data_model_class, data_field_name: str = None):
        """
        공통 파싱 로직을 수행합니다.
        
        Args:
            html_content: HTML 내용
            university_name: 대학교 이름
            page_type: 페이지 타입
            data_model_class: 데이터 모델 클래스
            data_field_name: 데이터 필드 이름 (기본값: page_type)
            
        Returns:
            파싱된 데이터 객체 또는 None
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 페이지별 데이터 추출 메서드 호출
            extract_method_name = f"_extract_all_{page_type}_data"
            if hasattr(self, extract_method_name):
                extracted_data = getattr(self, extract_method_name)(soup)
            else:
                self.logger.error(f"Extract method {extract_method_name} not found")
                return None
            
            # 평면 구조 변환 (필요한 경우)
            if hasattr(self, "_convert_to_flat_structure"):
                extracted_data = self._convert_to_flat_structure(extracted_data)
            
            # Process extracted data and detect new keys
            extracted_data = self._process_extracted_data(
                extracted_data, university_name, page_type
            )
            
            # Log key statistics
            self._log_key_statistics(extracted_data, page_type)
            
            # 데이터 모델 생성
            field_name = data_field_name or page_type
            data_obj = data_model_class(
                university_name=university_name,
                **{field_name: extracted_data}
            )
            
            self.logger.info(f"Successfully parsed {page_type} data for {university_name}")
            return data_obj
            
        except Exception as e:
            self.logger.error(f"Error parsing {page_type} data for {university_name}: {e}")
            return None
    
    def _process_extracted_data(self, data: Dict[str, Any], university_name: str, page_type: str) -> Dict[str, Any]:
        """
        추출된 데이터를 처리하고 새로운 키를 감지합니다.
        
        Args:
            data: 추출된 데이터
            university_name: 대학교 이름
            page_type: 페이지 타입 (campus_info, student_life, etc.)
            
        Returns:
            처리된 데이터
        """
        try:
            # 새로운 키 감지
            new_keys = self._detect_new_keys(data, university_name, page_type)
            
            if new_keys:
                self.logger.info(f"🔍 {page_type}: {len(new_keys)}개의 새로운 키 발견")
                for key in new_keys:
                    self.logger.info(f"   - {key}")
                
                # 키 설명 추출 (HTML에서 라벨 정보 가져오기)
                key_descriptions = self._extract_key_descriptions(data, page_type)
                
                # 새로운 키를 키 설명 시스템에 추가
                self._add_new_keys_to_system(new_keys, university_name, page_type, key_descriptions)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error processing extracted data: {e}")
            return data
    
    def _detect_new_keys(self, data: Dict[str, Any], university_name: str, page_type: str) -> list:
        """새로운 키를 감지합니다."""
        try:
            # 현재 페이지 타입의 알려진 키들 가져오기
            known_keys = self.key_manager.get_known_keys(page_type)
            
            # 실제 데이터의 키들
            actual_keys = set(data.keys())
            
            # 새로운 키들 찾기
            new_keys = list(actual_keys - known_keys)
            
            return new_keys
            
        except Exception as e:
            self.logger.error(f"Error detecting new keys: {e}")
            return []
    
    def _add_new_keys_to_system(self, new_keys: list, university_name: str, page_type: str, key_descriptions: Dict[str, str] = None):
        """새로운 키들을 키 설명 시스템에 추가합니다."""
        try:
            # 각 페이지별로 키 추가
            for key in new_keys:
                if key not in self.key_manager.descriptions["pages"][page_type]["keys"]:
                    # 키 설명이 제공된 경우 사용, 아니면 기본값
                    description = key_descriptions.get(key, "TODO: Add description") if key_descriptions else "TODO: Add description"
                    
                    self.key_manager.descriptions["pages"][page_type]["keys"][key] = description
            
            # 페이지별 키 수 업데이트
            self.key_manager.descriptions["pages"][page_type]["total_keys"] = len(
                self.key_manager.descriptions["pages"][page_type]["keys"]
            )
            
            # 전체 키 수 업데이트
            total_keys = 0
            for page_data in self.key_manager.descriptions["pages"].values():
                total_keys += page_data["total_keys"]
            self.key_manager.descriptions["metadata"]["total_keys"] = total_keys
            
            # 대학교 목록 업데이트
            if university_name not in self.key_manager.descriptions["metadata"]["universities_processed"]:
                self.key_manager.descriptions["metadata"]["universities_processed"].append(university_name)
            
            self.key_manager.save_descriptions()
            
            self.logger.info(f"✅ {len(new_keys)}개의 새로운 키가 {page_type} 페이지에 추가되었습니다.")
            
        except Exception as e:
            self.logger.error(f"Error adding new keys to system: {e}")
    
    def _log_key_statistics(self, data: Dict[str, Any], page_type: str):
        """키 통계를 로깅합니다."""
        total_keys = len(data)
        known_keys = len(self.key_manager.get_known_keys(page_type))
        new_keys = total_keys - known_keys
        
        self.logger.info(f"📊 {page_type} 키 통계:")
        self.logger.info(f"   - 총 키: {total_keys}개")
        self.logger.info(f"   - 알려진 키: {known_keys}개")
        self.logger.info(f"   - 새로운 키: {new_keys}개")
    
    def _sanitize_key(self, text: str) -> str:
        """텍스트를 유효한 딕셔너리 키로 변환합니다."""
        # Convert to lowercase, replace spaces and special chars with underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '_', text.lower())
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key
    
    def _extract_text_from_element(self, element, default: str = "") -> str:
        """요소에서 텍스트를 안전하게 추출합니다."""
        if element:
            return element.get_text(strip=True)
        return default
    
    def _extract_list_from_elements(self, elements) -> list:
        """요소 리스트에서 텍스트 리스트를 추출합니다."""
        items = []
        for element in elements:
            text = self._extract_text_from_element(element)
            if text:
                items.append(text)
        return items
    
    def _extract_data_by_test_id(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """data-test-id 속성을 가진 요소들에서 데이터를 추출합니다."""
        data = {}
        elements_with_test_id = soup.find_all(attrs={'data-test-id': True})
        
        for elem in elements_with_test_id:
            test_id = elem.get('data-test-id')
            if test_id:
                text_content = self._extract_text_from_element(elem)
                if text_content:
                    data[test_id] = text_content
        
        return data
    
    def _extract_datarow_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """DataRow 구조에서 데이터를 추출합니다."""
        datarow_data = {}
        
        # data-test-id가 있는 요소들 먼저 처리
        datarow_data.update(self._extract_data_by_test_id(soup))
        
        # DataRow 컨테이너들 처리
        datarow_containers = soup.find_all('div', class_=lambda x: x and 'DataRow__Row' in x)
        
        for container in datarow_containers:
            # 라벨과 값 찾기
            label_elem = container.find('p', class_=lambda x: x and 'fZPEMD' in x)
            value_elem = container.find('p', class_=lambda x: x and 'iKkzvP' in x)
            
            if label_elem and value_elem:
                label = self._extract_text_from_element(label_elem)
                value = self._extract_text_from_element(value_elem)
                if label and value:
                    key = self._sanitize_key(label)
                    datarow_data[key] = value
        
        return datarow_data
    
    def _extract_list_data(self, soup: BeautifulSoup, list_class_pattern: str = None) -> Dict[str, Any]:
        """리스트 데이터를 추출합니다."""
        list_data = {}
        
        # TruncatedList 찾기
        truncated_lists = soup.find_all('div', class_=lambda x: x and 'TruncatedList' in x)
        
        for truncated_list in truncated_lists:
            # 섹션 제목 찾기
            section_title = self._find_section_title(truncated_list)
            
            # 리스트 아이템들 추출
            list_items = truncated_list.find_all('li')
            if list_items:
                items = self._extract_list_from_elements(list_items)
                if items and section_title:
                    key = f"{self._sanitize_key(section_title)}_list"
                    list_data[key] = items
        
        return list_data
    
    def _extract_key_descriptions(self, data: Dict[str, Any], page_type: str) -> Dict[str, str]:
        """키에 대한 설명을 추출합니다."""
        descriptions = {}
        
        # 각 키에 대해 설명 생성
        for key in data.keys():
            # 키 이름을 기반으로 설명 생성
            description = self._generate_description_from_key(key)
            descriptions[key] = description
        
        return descriptions
    
    def _generate_description_from_key(self, key: str) -> str:
        """키 이름을 기반으로 설명을 생성합니다."""
        # 언더스코어를 공백으로 변환하고 첫 글자를 대문자로
        description = key.replace('_', ' ').title()
        
        # 특별한 패턴들 처리
        if key.startswith('env_'):
            description = description.replace('Env ', 'Environment ')
        elif key.startswith('reg_'):
            description = description.replace('Reg ', 'Regulation ')
        elif key.startswith('v_'):
            description = description.replace('V ', 'Value ')
        elif key.startswith('fn_'):
            description = description.replace('Fn ', 'Financial ')
        elif key.startswith('stu_'):
            description = description.replace('Stu ', 'Student ')
        elif key.startswith('dis_'):
            description = description.replace('Dis ', 'Disability ')
        elif key.startswith('ld_'):
            description = description.replace('Ld ', 'Learning Disability ')
        elif key.startswith('asd_'):
            description = description.replace('Asd ', 'Autism Spectrum Disorder ')
        elif key.startswith('adhd_'):
            description = description.replace('Adhd ', 'ADHD ')
        elif key.startswith('pro_'):
            description = description.replace('Pro ', 'Program ')
        elif key.startswith('g_'):
            description = description.replace('G ', 'General ')
        elif key.startswith('payscale_'):
            description = description.replace('Payscale ', 'PayScale ')
        
        # 특별한 키들에 대한 설명
        special_descriptions = {
            'CAMPUS_CARRY_POLICY': 'Firearm campus carry policy',
            'GUIDNCECMPSACSBLTY': 'Guidance campus accessibility',
            'total_all_students': 'Total number of all students',
            'total_undergrads': 'Total number of undergraduate students',
            'total_grads_and_pros': 'Total number of graduate and professional students',
            'application_deadline': 'Application deadline date',
            'application_fee': 'Application fee amount',
            'acceptance_rate': 'Acceptance rate percentage',
            'national_universities': 'National Universities ranking',
            'best_value_schools': 'Best Value Schools ranking',
            'best_undergraduate_engineering_programs': 'Best Undergraduate Engineering Programs ranking'
        }
        
        if key in special_descriptions:
            return special_descriptions[key]
        
        return description
