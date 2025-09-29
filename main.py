#!/usr/bin/env python3
"""
Main Entry Point for University HTML Downloader

CLI tool for downloading HTML files from US News university pages.
Supports downloading different page types with modular architecture.
"""

import sys
import json
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from usnews_scraper.html_downloader import HTMLDownloader, DownloaderConfig
from usnews_scraper.selenium_base import setup_basic_logging


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger(__name__).setLevel(logging.INFO)


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
    downloader = HTMLDownloader(headless=True, downloader_config=config)
    
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
    downloader = HTMLDownloader(headless=True, downloader_config=config)
    
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


def list_universities():
    """List all available universities."""
    universities = load_universities()
    if not universities:
        print("No universities found")
        return
    
    print(f"Available universities ({len(universities)}):")
    for i, university in enumerate(universities, 1):
        print(f"{i:4d}. {university}")


def main():
    """Main CLI entry point."""
    setup_logging()
    setup_basic_logging()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py <university_name>     # Download HTML for specific university")
        print("  python main.py --all                 # Download HTML for all universities")
        print("  python main.py --list                # List all available universities")
        print("  python main.py --help                # Show this help")
        return
    
    command = sys.argv[1].lower()
    
    if command == "--help":
        print("US News University HTML Downloader")
        print("=" * 50)
        print("Commands:")
        print("  <university_name>  Download HTML for specific university")
        print("  --all             Download HTML for all universities")
        print("  --list            List all available universities")
        print("  --help            Show this help")
        print("")
        print("Examples:")
        print("  python main.py 'Princeton University'")
        print("  python main.py 'Harvard University'")
        print("  python main.py --all")
        print("  python main.py --list")
        
    elif command == "--list":
        list_universities()
        
    elif command == "--all":
        download_all_html()
        
    else:
        # Treat as university name
        university_name = " ".join(sys.argv[1:])
        download_html(university_name)


if __name__ == "__main__":
    main()