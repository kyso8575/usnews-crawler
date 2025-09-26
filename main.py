#!/usr/bin/env python3
"""
Main Entry Point for University Data Extraction

CLI tool for extracting structured data from university HTML files.
Supports parsing different page types with modular architecture.
"""

import sys
import json
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from parser.overall_rankings import OverallRankingsParser
from parser.cost_parser import CostParser
from parser.applying_parser import ApplyingParser
from parser.academics_parser import AcademicsParser
from parser.student_life_parser import StudentLifeParser
from models.overall_rankings_data import OverallRankingsData
from models.cost_data import CostData
from models.applying_data import ApplyingData
from models.academics_data import AcademicsData
from models.student_life_data import StudentLifeData
from usnews_scraper.html_downloader import HTMLDownloader, DownloaderConfig
from usnews_scraper.selenium_base import setup_basic_logging


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('extraction.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger(__name__).setLevel(logging.INFO)
    logging.getLogger("parser.overall_rankings").setLevel(logging.INFO)


def load_universities() -> List[str]:
    """Load university names from JSON file."""
    try:
        with open("data/universities.json", 'r', encoding='utf-8') as f:
            universities_data = json.load(f)
        return [uni['name'] for uni in universities_data]
    except Exception as e:
        logging.error(f"Error loading universities: {e}")
        return []


def download_html(university_name: str):
    """Download HTML for a single university."""
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading HTML for {university_name}")
    
    config = DownloaderConfig(preserve_login_from_existing=True)
    downloader = HTMLDownloader(headless=False, downloader_config=config)
    
    try:
        result = downloader.download_all_pages(university_name)
        if result:
            logger.info(f"✅ Successfully downloaded HTML for {university_name}")
        else:
            logger.error(f"❌ Failed to download HTML for {university_name}")
    except Exception as e:
        logger.error(f"❌ Error downloading {university_name}: {e}")


def download_all_html():
    """Download HTML for all universities with progress tracking."""
    logger = logging.getLogger(__name__)
    universities = load_universities()
    
    if not universities:
        logger.error("No universities found to download")
        return
    
    logger.info(f"🚀 Starting download for {len(universities)} universities")
    logger.info("=" * 80)
    
    config = DownloaderConfig(preserve_login_from_existing=True)
    downloader = HTMLDownloader(headless=False, downloader_config=config)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, university in enumerate(universities, 1):
        try:
            # 진행 상황 로그 추가
            logger.info(f"\n🎓 [{i}/{len(universities)}] Processing: {university}")
            logger.info(f"📊 Progress: {i}/{len(universities)} ({i/len(universities)*100:.1f}%)")
            logger.info("-" * 60)
            
            result = downloader.download_all_pages(university)
            
            if result:
                success_count += 1
                logger.info(f"✅ Successfully downloaded {university} ({len(result)} pages)")
            else:
                skipped_count += 1
                logger.info(f"⏭️ Skipped {university} (already downloaded or no pages available)")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Error downloading {university}: {e}")
        
        # 전체 진행 상황 요약 (매 10개마다)
        if i % 10 == 0 or i == len(universities):
            logger.info(f"\n📈 Progress Summary:")
            logger.info(f"   Completed: {i}/{len(universities)} ({i/len(universities)*100:.1f}%)")
            logger.info(f"   Success: {success_count}")
            logger.info(f"   Skipped: {skipped_count}")
            logger.info(f"   Failed: {failed_count}")
            logger.info("=" * 60)
    
    # 최종 결과
    logger.info(f"\n🎉 Download Complete!")
    logger.info(f"📊 Final Results:")
    logger.info(f"   Total universities: {len(universities)}")
    logger.info(f"   Successfully downloaded: {success_count}")
    logger.info(f"   Skipped (already downloaded): {skipped_count}")
    logger.info(f"   Failed: {failed_count}")
    if success_count + failed_count > 0:
        logger.info(f"   Success rate: {success_count/(success_count+failed_count)*100:.1f}%")


def get_available_universities() -> List[str]:
    """Get list of universities that have downloaded HTML files."""
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        return []
    
    universities = []
    for uni_dir in downloads_dir.iterdir():
        if uni_dir.is_dir():
            # Check if overall_rankings.html exists
            rankings_file = uni_dir / "overall_rankings.html"
            if rankings_file.exists():
                universities.append(uni_dir.name.replace("_", " "))
    
    return sorted(universities)


def get_available_universities_with_cost() -> List[str]:
    """Get list of universities that have downloaded paying.html files."""
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        return []
    
    universities = []
    for uni_dir in downloads_dir.iterdir():
        if uni_dir.is_dir():
            # Check if paying.html exists
            paying_file = uni_dir / "paying.html"
            if paying_file.exists():
                universities.append(uni_dir.name.replace("_", " "))
    
    return sorted(universities)


def get_available_universities_with_academics() -> List[str]:
    """Get list of universities that have downloaded academics.html files."""
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        return []
    
    universities = []
    for uni_dir in downloads_dir.iterdir():
        if uni_dir.is_dir():
            # Check if academics.html exists
            academics_file = uni_dir / "academics.html"
            if academics_file.exists():
                universities.append(uni_dir.name.replace("_", " "))
    
    return sorted(universities)


def get_available_universities_with_applying() -> List[str]:
    """Get list of universities that have downloaded applying.html files."""
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        return []
    
    universities = []
    for uni_dir in downloads_dir.iterdir():
        if uni_dir.is_dir():
            # Check if applying.html exists
            applying_file = uni_dir / "applying.html"
            if applying_file.exists():
                universities.append(uni_dir.name.replace("_", " "))
    
    return sorted(universities)


def get_available_universities_with_student_life() -> List[str]:
    """Get list of universities that have downloaded student_life.html files."""
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        return []
    
    universities = []
    for uni_dir in downloads_dir.iterdir():
        if uni_dir.is_dir():
            # Check if student_life.html exists
            student_life_file = uni_dir / "student_life.html"
            if student_life_file.exists():
                universities.append(uni_dir.name.replace("_", " "))
    
    return sorted(universities)


def parse_overall_rankings(university_name: str) -> Optional[OverallRankingsData]:
    """Parse overall rankings for a single university."""
    logger = logging.getLogger(__name__)
    
    # Convert university name to directory format
    uni_dir_name = university_name.replace(" ", "_")
    html_file = Path(f"downloads/{uni_dir_name}/overall_rankings.html")
    
    if not html_file.exists():
        logger.error(f"HTML file not found: {html_file}")
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = OverallRankingsParser()
        rankings_data = parser.parse(html_content, university_name)
        
        if rankings_data:
            logger.info(f"✅ Successfully parsed rankings for {university_name}")
            return rankings_data
        else:
            logger.error(f"❌ Failed to parse rankings for {university_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error parsing {university_name}: {e}")
        return None


def parse_all_overall_rankings():
    """Parse overall rankings for all available universities."""
    logger = logging.getLogger(__name__)
    universities = get_available_universities()
    
    if not universities:
        logger.error("No universities with HTML files found")
        return
    
    logger.info(f"Parsing overall rankings for {len(universities)} universities")
    
    all_data = {
        'universities': {},
        'summary': {
            'total_universities': len(universities),
            'parsed_universities': 0,
            'failed_universities': 0
        }
    }
    
    for university in universities:
        try:
            logger.info(f"Parsing {university}...")
            rankings_data = parse_overall_rankings(university)
            
            if rankings_data:
                all_data['universities'][university] = rankings_data.to_dict()
                all_data['summary']['parsed_universities'] += 1
                logger.info(f"✅ Successfully parsed {university}")
            else:
                all_data['summary']['failed_universities'] += 1
                logger.warning(f"⚠️ Failed to parse {university}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing {university}: {e}")
            all_data['summary']['failed_universities'] += 1
    
    # Save combined data
    os.makedirs("data/extracted", exist_ok=True)
    output_file = "data/extracted/overall_rankings_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Parsing complete!")
    logger.info(f"Total universities: {all_data['summary']['total_universities']}")
    logger.info(f"Successfully parsed: {all_data['summary']['parsed_universities']}")
    logger.info(f"Failed: {all_data['summary']['failed_universities']}")
    logger.info(f"Combined data saved to {output_file}")


def parse_cost_data(university_name: str) -> Optional[CostData]:
    """Parse cost/paying data for a single university."""
    logger = logging.getLogger(__name__)
    
    # Convert university name to directory format
    uni_dir_name = university_name.replace(" ", "_")
    html_file = Path(f"downloads/{uni_dir_name}/paying.html")
    
    if not html_file.exists():
        logger.error(f"Paying HTML file not found: {html_file}")
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = CostParser()
        cost_data = parser.parse(html_content, university_name)
        
        if cost_data:
            logger.info(f"✅ Successfully parsed cost data for {university_name}")
            return cost_data
        else:
            logger.error(f"❌ Failed to parse cost data for {university_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error parsing cost data for {university_name}: {e}")
        return None


def parse_all_cost_data():
    """Parse cost/paying data for all available universities."""
    logger = logging.getLogger(__name__)
    universities = get_available_universities_with_cost()
    
    if not universities:
        logger.error("No universities with paying HTML files found")
        return
    
    logger.info(f"Parsing cost data for {len(universities)} universities")
    
    all_data = {
        'universities': {},
        'summary': {
            'total_universities': len(universities),
            'parsed_universities': 0,
            'failed_universities': 0
        }
    }
    
    for university in universities:
        try:
            logger.info(f"Parsing cost data for {university}...")
            cost_data = parse_cost_data(university)
            
            if cost_data:
                all_data['universities'][university] = cost_data.to_dict()
                all_data['summary']['parsed_universities'] += 1
                logger.info(f"✅ Successfully parsed cost data for {university}")
            else:
                all_data['summary']['failed_universities'] += 1
                logger.warning(f"⚠️ Failed to parse cost data for {university}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing cost data for {university}: {e}")
            all_data['summary']['failed_universities'] += 1
    
    # Save combined data
    os.makedirs("data/extracted", exist_ok=True)
    output_file = "data/extracted/cost_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Cost data parsing complete!")
    logger.info(f"Total universities: {all_data['summary']['total_universities']}")
    logger.info(f"Successfully parsed: {all_data['summary']['parsed_universities']}")
    logger.info(f"Failed: {all_data['summary']['failed_universities']}")
    logger.info(f"Combined data saved to {output_file}")


def parse_academics_data(university_name: str) -> Optional[AcademicsData]:
    """Parse academics data for a single university."""
    logger = logging.getLogger(__name__)
    
    # Convert university name to directory format
    uni_dir_name = university_name.replace(" ", "_")
    html_file = Path(f"downloads/{uni_dir_name}/academics.html")
    
    if not html_file.exists():
        logger.error(f"Academics HTML file not found: {html_file}")
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = AcademicsParser()
        academics_data = parser.parse(html_content, university_name)
        
        if academics_data:
            logger.info(f"✅ Successfully parsed academics data for {university_name}")
            return academics_data
        else:
            logger.error(f"❌ Failed to parse academics data for {university_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error parsing academics data for {university_name}: {e}")
        return None


def parse_applying_data(university_name: str) -> Optional[ApplyingData]:
    """Parse applying/admissions data for a single university."""
    logger = logging.getLogger(__name__)
    
    # Convert university name to directory format
    uni_dir_name = university_name.replace(" ", "_")
    html_file = Path(f"downloads/{uni_dir_name}/applying.html")
    
    if not html_file.exists():
        logger.error(f"Applying HTML file not found: {html_file}")
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = ApplyingParser()
        applying_data = parser.parse(html_content, university_name)
        
        if applying_data:
            logger.info(f"✅ Successfully parsed applying data for {university_name}")
            return applying_data
        else:
            logger.error(f"❌ Failed to parse applying data for {university_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error parsing applying data for {university_name}: {e}")
        return None


def parse_all_academics_data():
    """Parse academics data for all available universities."""
    logger = logging.getLogger(__name__)
    universities = get_available_universities_with_academics()
    
    if not universities:
        logger.error("No universities with academics HTML files found")
        return
    
    logger.info(f"Parsing academics data for {len(universities)} universities")
    
    all_data = {
        'universities': {},
        'summary': {
            'total_universities': len(universities),
            'parsed_universities': 0,
            'failed_universities': 0
        }
    }
    
    for university in universities:
        try:
            logger.info(f"Parsing academics data for {university}...")
            academics_data = parse_academics_data(university)
            
            if academics_data:
                all_data['universities'][university] = academics_data.to_dict()
                all_data['summary']['parsed_universities'] += 1
                logger.info(f"✅ Successfully parsed academics data for {university}")
            else:
                all_data['summary']['failed_universities'] += 1
                logger.warning(f"⚠️ Failed to parse academics data for {university}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing academics data for {university}: {e}")
            all_data['summary']['failed_universities'] += 1
    
    # Save combined data
    os.makedirs("data/extracted", exist_ok=True)
    output_file = "data/extracted/academics_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Academics data parsing complete!")
    logger.info(f"Total universities: {all_data['summary']['total_universities']}")
    logger.info(f"Successfully parsed: {all_data['summary']['parsed_universities']}")
    logger.info(f"Failed: {all_data['summary']['failed_universities']}")
    logger.info(f"Combined data saved to {output_file}")


def parse_all_applying_data():
    """Parse applying/admissions data for all available universities."""
    logger = logging.getLogger(__name__)
    universities = get_available_universities_with_applying()
    
    if not universities:
        logger.error("No universities with applying HTML files found")
        return
    
    logger.info(f"Parsing applying data for {len(universities)} universities")
    
    all_data = {
        'universities': {},
        'summary': {
            'total_universities': len(universities),
            'parsed_universities': 0,
            'failed_universities': 0
        }
    }
    
    for university in universities:
        try:
            logger.info(f"Parsing applying data for {university}...")
            applying_data = parse_applying_data(university)
            
            if applying_data:
                all_data['universities'][university] = applying_data.to_dict()
                all_data['summary']['parsed_universities'] += 1
                logger.info(f"✅ Successfully parsed applying data for {university}")
            else:
                all_data['summary']['failed_universities'] += 1
                logger.warning(f"⚠️ Failed to parse applying data for {university}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing applying data for {university}: {e}")
            all_data['summary']['failed_universities'] += 1
    
    # Save combined data
    os.makedirs("data/extracted", exist_ok=True)
    output_file = "data/extracted/applying_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Applying data parsing complete!")
    logger.info(f"Total universities: {all_data['summary']['total_universities']}")
    logger.info(f"Successfully parsed: {all_data['summary']['parsed_universities']}")
    logger.info(f"Failed: {all_data['summary']['failed_universities']}")
    logger.info(f"Combined data saved to {output_file}")


def parse_student_life_data(university_name: str) -> Optional[StudentLifeData]:
    """Parse student life data for a single university."""
    logger = logging.getLogger(__name__)
    
    # Convert university name to directory format
    uni_dir_name = university_name.replace(" ", "_")
    html_file = Path(f"downloads/{uni_dir_name}/student_life.html")
    
    if not html_file.exists():
        logger.error(f"Student life HTML file not found: {html_file}")
        return None
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = StudentLifeParser()
        student_life_data = parser.parse(html_content, university_name)
        
        if student_life_data:
            logger.info(f"✅ Successfully parsed student life data for {university_name}")
            return student_life_data
        else:
            logger.error(f"❌ Failed to parse student life data for {university_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error parsing student life data for {university_name}: {e}")
        return None


def parse_all_student_life_data():
    """Parse student life data for all available universities."""
    logger = logging.getLogger(__name__)
    universities = get_available_universities_with_student_life()
    
    if not universities:
        logger.error("No universities with student life HTML files found")
        return
    
    logger.info(f"Parsing student life data for {len(universities)} universities")
    
    all_data = {
        'universities': {},
        'summary': {
            'total_universities': len(universities),
            'parsed_universities': 0,
            'failed_universities': 0
        }
    }
    
    for university in universities:
        try:
            logger.info(f"Parsing student life data for {university}...")
            student_life_data = parse_student_life_data(university)
            
            if student_life_data:
                all_data['universities'][university] = student_life_data.to_dict()
                all_data['summary']['parsed_universities'] += 1
                logger.info(f"✅ Successfully parsed student life data for {university}")
            else:
                all_data['summary']['failed_universities'] += 1
                logger.warning(f"⚠️ Failed to parse student life data for {university}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing student life data for {university}: {e}")
            all_data['summary']['failed_universities'] += 1
    
    # Save combined data
    os.makedirs("data/extracted", exist_ok=True)
    output_file = "data/extracted/student_life_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Student life data parsing complete!")
    logger.info(f"Total universities: {all_data['summary']['total_universities']}")
    logger.info(f"Successfully parsed: {all_data['summary']['parsed_universities']}")
    logger.info(f"Failed: {all_data['summary']['failed_universities']}")
    logger.info(f"Combined data saved to {output_file}")


def show_help():
    """Show help information."""
    print("🎓 University Data Extraction Tool")
    print("=" * 40)
    print("Usage:")
    print("  python main.py download <university_name>      # Download HTML")
    print("  python main.py download-all                     # Download HTML for all universities")
    print("  python main.py parse-rankings <university_name>  # Parse overall rankings")
    print("  python main.py parse-all-rankings               # Parse all overall rankings")
    print("  python main.py parse-cost <university_name>     # Parse cost/paying data")
    print("  python main.py parse-all-cost                   # Parse all cost/paying data")
    print("  python main.py parse-applying <university_name> # Parse applying/admissions data")
    print("  python main.py parse-all-applying               # Parse all applying/admissions data")
    print("  python main.py parse-academics <university_name> # Parse academics data")
    print("  python main.py parse-all-academics              # Parse all academics data")
    print("  python main.py parse-student-life <university_name> # Parse student life data")
    print("  python main.py parse-all-student-life          # Parse all student life data")
    print("  python main.py list                             # Show available universities")
    print("  python main.py list-cost                        # Show universities with cost data")
    print("  python main.py list-applying                    # Show universities with applying data")
    print("  python main.py list-academics                   # Show universities with academics data")
    print("  python main.py list-student-life                # Show universities with student life data")
    print("  python main.py help                             # Show this help")
    print()
    print("Examples:")
    print("  python main.py download 'Harvard University'")
    print("  python main.py download-all")
    print("  python main.py parse-rankings 'Harvard University'")
    print("  python main.py parse-all-rankings")
    print("  python main.py parse-cost 'Harvard University'")
    print("  python main.py parse-all-cost")
    print("  python main.py parse-applying 'Harvard University'")
    print("  python main.py parse-all-applying")
    print("  python main.py parse-academics 'Harvard University'")
    print("  python main.py parse-all-academics")


def show_universities():
    """Show available universities with HTML files."""
    universities = get_available_universities()
    
    if not universities:
        print("No universities with HTML files found in downloads/ directory")
        return
    
    print(f"📚 Available Universities ({len(universities)} total):")
    print("=" * 50)
    
    for i, university in enumerate(universities, 1):
        print(f"{i:2d}. {university}")


def show_universities_with_cost():
    """Show available universities with cost/paying HTML files."""
    universities = get_available_universities_with_cost()
    
    if not universities:
        print("No universities with cost/paying HTML files found in downloads/ directory")
        return
    
    print(f"💰 Universities with Cost Data ({len(universities)} total):")
    print("=" * 50)
    
    for i, university in enumerate(universities, 1):
        print(f"{i:2d}. {university}")


def show_universities_with_academics():
    """Show available universities with academics HTML files."""
    universities = get_available_universities_with_academics()
    
    if not universities:
        print("No universities with academics HTML files found in downloads/ directory")
        return
    
    print(f"🎓 Universities with Academics Data ({len(universities)} total):")
    print("=" * 50)
    
    for i, university in enumerate(universities, 1):
        print(f"{i:2d}. {university}")


def show_universities_with_applying():
    """Show available universities with applying/admissions HTML files."""
    universities = get_available_universities_with_applying()
    
    if not universities:
        print("No universities with applying/admissions HTML files found in downloads/ directory")
        return
    
    print(f"📝 Universities with Applying Data ({len(universities)} total):")
    print("=" * 50)
    
    for i, university in enumerate(universities, 1):
        print(f"{i:2d}. {university}")


def show_universities_with_student_life():
    """Show available universities with student life HTML files."""
    universities = get_available_universities_with_student_life()
    
    if not universities:
        print("No universities with student life HTML files found in downloads/ directory")
        return
    
    print(f"🎭 Universities with Student Life Data ({len(universities)} total):")
    print("=" * 50)
    
    for i, university in enumerate(universities, 1):
        print(f"{i:2d}. {university}")


def main():
    """Main function."""
    setup_logging()
    setup_basic_logging()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        show_help()
    elif command == "list":
        show_universities()
    elif command == "list-cost":
        show_universities_with_cost()
    elif command == "list-applying":
        show_universities_with_applying()
    elif command == "list-academics":
        show_universities_with_academics()
    elif command == "download":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py download <university_name>")
            return
        university_name = sys.argv[2]
        download_html(university_name)
    elif command == "download-all":
        download_all_html()
    elif command == "parse-rankings":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py parse-rankings <university_name>")
            return
        university_name = sys.argv[2]
        rankings_data = parse_overall_rankings(university_name)
        if rankings_data:
            # Save individual file
            os.makedirs("data/extracted", exist_ok=True)
            output_file = f"data/extracted/{university_name.replace(' ', '_')}_rankings.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rankings_data.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Rankings data saved to {output_file}")
    elif command == "parse-all-rankings":
        parse_all_overall_rankings()
    elif command == "parse-cost":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py parse-cost <university_name>")
            return
        university_name = sys.argv[2]
        cost_data = parse_cost_data(university_name)
        if cost_data:
            # Save individual file
            os.makedirs("data/extracted", exist_ok=True)
            output_file = f"data/extracted/{university_name.replace(' ', '_')}_cost.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cost_data.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Cost data saved to {output_file}")
    elif command == "parse-all-cost":
        parse_all_cost_data()
    elif command == "parse-applying":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py parse-applying <university_name>")
            return
        university_name = sys.argv[2]
        applying_data = parse_applying_data(university_name)
        if applying_data:
            # Save individual file
            os.makedirs("data/extracted", exist_ok=True)
            output_file = f"data/extracted/{university_name.replace(' ', '_')}_applying.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(applying_data.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Applying data saved to {output_file}")
    elif command == "parse-all-applying":
        parse_all_applying_data()
    elif command == "parse-academics":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py parse-academics <university_name>")
            return
        university_name = sys.argv[2]
        academics_data = parse_academics_data(university_name)
        if academics_data:
            # Save individual file
            os.makedirs("data/extracted", exist_ok=True)
            output_file = f"data/extracted/{university_name.replace(' ', '_')}_academics.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(academics_data.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Academics data saved to {output_file}")
    elif command == "parse-all-academics":
        parse_all_academics_data()
    elif command == "parse-student-life":
        if len(sys.argv) < 3:
            print("❌ Please provide university name")
            print("Usage: python main.py parse-student-life <university_name>")
            return
        university_name = sys.argv[2]
        student_life_data = parse_student_life_data(university_name)
        if student_life_data:
            # Save individual file
            os.makedirs("data/extracted", exist_ok=True)
            output_file = f"data/extracted/{university_name.replace(' ', '_')}_student_life.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(student_life_data.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Student life data saved to {output_file}")
    elif command == "parse-all-student-life":
        parse_all_student_life_data()
    elif command == "list-student-life":
        show_universities_with_student_life()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()