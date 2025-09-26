#!/usr/bin/env python3
"""
Extract all Princeton University page data using all available parsers
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from parser.campus_info_parser import CampusInfoParser
from parser.student_life_parser import StudentLifeParser
from parser.academics_parser import AcademicsParser
from parser.applying_parser import ApplyingParser
from parser.cost_parser import CostParser
from parser.overall_rankings import OverallRankingsParser


def extract_all_princeton_data():
    """Extract data from all Princeton University pages."""
    
    princeton_dir = project_root / "downloads" / "Princeton_University"
    output_dir = project_root / "data" / "extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize all parsers
    parsers = {
        'campus_info': CampusInfoParser(),
        'student_life': StudentLifeParser(),
        'academics': AcademicsParser(),
        'applying': ApplyingParser(),
        'cost': CostParser(),
        'overall_rankings': OverallRankingsParser()
    }
    
    # Page mappings
    pages = {
        'campus_info': 'campus_info.html',
        'student_life': 'student_life.html',
        'academics': 'academics.html',
        'applying': 'applying.html',
        'paying': 'paying.html',  # cost parser for paying page
        'overall_rankings': 'overall_rankings.html'
    }
    
    results = {}
    
    for page_type, html_file in pages.items():
        html_path = princeton_dir / html_file
        
        if not html_path.exists():
            print(f"❌ HTML file not found: {html_path}")
            continue
        
        print(f"📄 Processing {page_type}...")
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"   HTML content length: {len(html_content)} characters")
        
        # Parse based on page type
        if page_type == 'paying':
            # Use cost parser for paying page
            parser = parsers['cost']
            parsed_data = parser.parse(html_content, "Princeton University")
        else:
            parser = parsers[page_type]
            parsed_data = parser.parse(html_content, "Princeton University")
        
        if parsed_data:
            print(f"   ✅ Successfully parsed {page_type} data")
            
            # Convert to dictionary
            data_dict = parsed_data.to_dict()
            
            # Save to JSON file
            output_file = output_dir / f"Princeton_University_{page_type}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Data saved to: {output_file}")
            
            # Show summary
            if page_type == 'paying':
                data_key = 'paying'
            elif page_type == 'overall_rankings':
                data_key = 'rankings'
            else:
                data_key = page_type
            
            if data_key in data_dict:
                field_count = len(data_dict[data_key])
                print(f"   📊 Extracted {field_count} fields")
                
                # Show some sample data
                sample_data = data_dict[data_key]
                if isinstance(sample_data, dict):
                    sample_keys = list(sample_data.keys())[:3]
                    for key in sample_keys:
                        value = sample_data[key]
                        if isinstance(value, list):
                            print(f"      - {key}: [{len(value)} items]")
                        else:
                            print(f"      - {key}: {str(value)[:50]}...")
            
            results[page_type] = {
                'success': True,
                'file': str(output_file),
                'field_count': field_count if 'field_count' in locals() else 0
            }
        else:
            print(f"   ❌ Failed to parse {page_type} data")
            results[page_type] = {'success': False}
    
    # Summary
    print(f"\n🎉 Extraction complete!")
    print(f"📁 Output directory: {output_dir}")
    
    successful = [k for k, v in results.items() if v.get('success', False)]
    failed = [k for k, v in results.items() if not v.get('success', False)]
    
    print(f"✅ Successful: {len(successful)} pages")
    for page in successful:
        field_count = results[page].get('field_count', 0)
        print(f"   - {page}: {field_count} fields")
    
    if failed:
        print(f"❌ Failed: {len(failed)} pages")
        for page in failed:
            print(f"   - {page}")


if __name__ == "__main__":
    extract_all_princeton_data()
