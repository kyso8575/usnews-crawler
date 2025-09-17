"""
Main Scraper

This is the main entry point that uses the separated modules:
- UniversityIDExtractor: Extracts university IDs from search results
- HTMLDownloader: Downloads HTML content from university pages
"""

import sys
from university_id_extractor import UniversityIDExtractor
from html_downloader import HTMLDownloader


def main():
    """Main function to run the complete scraping workflow."""
    if len(sys.argv) != 2:
        print("Usage: python main_scraper.py <university_name>")
        print("Example: python main_scraper.py harvard")
        sys.exit(1)
    
    university_name = sys.argv[1]
    
    print("🎓 US News University Scraper")
    print("=" * 50)
    print(f"Target University: {university_name}")
    print()
    
    # Step 1: Extract University ID
    print("📋 STEP 1: Extracting University ID")
    print("-" * 30)
    
    extractor = UniversityIDExtractor(headless=False)  # Set to False for debugging
    university_id = extractor.extract_university_id(university_name)
    
    if not university_id:
        print("❌ Could not extract university ID. Exiting.")
        return
    
    print(f"\n🎯 University ID successfully extracted: {university_id}")
    
    # Step 2: Download HTML Content from All Pages
    print(f"\n📥 STEP 2: Downloading HTML Content from All Pages")
    print("-" * 50)
    
    downloader = HTMLDownloader(headless=False)  # Set to False for debugging
    downloaded_files = downloader.download_all_pages(university_name, university_id)
    
    if not downloaded_files:
        print("❌ Could not download any HTML content. Exiting.")
        return
    
    print(f"\n✅ COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"🎓 University: {university_name}")
    print(f"🆔 ID: {university_id}")
    print(f"📁 Downloaded {len(downloaded_files)} pages:")
    for i, file_path in enumerate(downloaded_files, 1):
        print(f"   {i}. {file_path}")
    print()
    print("🎉 Complete university data extraction and download completed successfully!")


if __name__ == "__main__":
    main()
