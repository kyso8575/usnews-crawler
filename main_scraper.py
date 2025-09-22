"""
Main Scraper

This is the main entry point that uses the HTMLDownloader module:
- HTMLDownloader: Downloads HTML content from university pages using universities.json
"""

import sys
import json
import logging
from usnews_scraper.html_downloader import HTMLDownloader, DownloaderConfig
from usnews_scraper.selenium_base import setup_basic_logging


logger = logging.getLogger("usnews_scraper.main_scraper")

def print_header(title: str, width: int = 50):
    """Print a formatted header."""
    logger.info(title)
    logger.info("=" * width)


def load_universities_list():
    """Load university names from JSON file."""
    try:
        with open("data/universities.json", 'r', encoding='utf-8') as f:
            universities_data = json.load(f)
        return [uni['name'] for uni in universities_data]
    except Exception as e:
        logger.error(f"❌ Error loading universities: {e}")
        return []


def show_help():
    """Show help information and available universities."""
    print_header("🎓 US News University Scraper")
    logger.info("Usage:")
    logger.info("  python main_scraper.py <university_name>")
    logger.info("  python main_scraper.py --list")
    logger.info("  python main_scraper.py --all")
    logger.info("  python main_scraper.py --help")
    logger.info("")
    logger.info("Examples:")
    logger.info("  python main_scraper.py 'Princeton University'")
    logger.info("  python main_scraper.py --all")
    logger.info("")
    logger.info("Options:")
    logger.info("  --list    Show all available universities")
    # Dynamically show current count from JSON
    try:
        total = len(load_universities_list())
    except Exception:
        total = "unknown"
    logger.info(f"  --all     Download all universities ({total} universities)")
    logger.info("  --help    Show this help message")


def list_universities():
    """List all available universities from the JSON file."""
    universities = load_universities_list()
    if not universities:
        return
    
    print_header("📚 Available Universities")
    for i, university in enumerate(universities, 1):
        logger.info(f"{i:3d}. {university}")
    logger.info(f"\nTotal: {len(universities)} universities")


def download_all_universities():
    """Download all universities from the JSON file."""
    try:
        # Use context manager to ensure clean driver shutdown
        # 기존 Chrome에서 로그인 세션을 복사해서 새 Chrome에서 사용
        config = DownloaderConfig(preserve_login_from_existing=True)
        downloader = HTMLDownloader(headless=False, use_existing_chrome=False, universities_json="data/universities.json", downloader_config=config)
        universities = downloader.list_all_universities()
        
        print_header("🎓 US News University Scraper - BULK DOWNLOAD", 60)
        logger.info(f"📊 Total Universities: {len(universities)}")
        logger.info("⚠️  This will take a very long time!")
        logger.info("💡 You can stop anytime with Ctrl+C")
        logger.info("")
        
        # 자동으로 bulk download 시작 (확인 생략)
        logger.info("🚀 Starting bulk download automatically...")
        logger.info("")
        
        success_count = 0
        failed_count = 0
        
        for i, university_name in enumerate(universities, 1):
                logger.info(f"\n🏫 [{i}/{len(universities)}] Processing: {university_name}")
                logger.info("=" * 80)
                
                try:
                    downloaded_files = downloader.download_all_pages(university_name)
                    if downloaded_files:
                        success_count += 1
                        logger.info(f"✅ {university_name}: {len(downloaded_files)} pages downloaded")
                    else:
                        failed_count += 1
                        logger.info(f"❌ {university_name}: No pages downloaded")
                        
                except KeyboardInterrupt:
                    logger.info(f"\n\n⏹️  Bulk download interrupted by user")
                    logger.info(f"📊 Progress: {i-1}/{len(universities)} universities processed")
                    break
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ {university_name}: Error - {str(e)}")
                
                # Progress summary every 10 universities
                if i % 10 == 0:
                    logger.info(f"\n📈 Progress Update: {i}/{len(universities)} universities processed")
                    logger.info(f"✅ Success: {success_count} | ❌ Failed: {failed_count}")
        
        print_header("\n🎉 BULK DOWNLOAD SUMMARY:")
        logger.info(f"📊 Total Processed: {success_count + failed_count}")
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {failed_count}")
        logger.info(f"📁 Check downloads/ directory for all files")
        
    except Exception as e:
        logger.error(f"❌ Error during bulk download: {e}")


def main():
    """Main function to run the complete scraping workflow."""
    if len(sys.argv) != 2:
        show_help()
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg in ["--help", "-h"]:
        show_help()
        return
    elif arg in ["--list", "-l"]:
        list_universities()
        return
    elif arg in ["--all", "-a"]:
        download_all_universities()
        return
    
    university_name = arg
    
    print_header("🎓 US News University Scraper")
    logger.info(f"Target University: {university_name}")
    logger.info("")
    
    print_header("📥 Downloading HTML Content from All Pages")
    
    # 기존 Chrome에서 로그인 세션을 복사해서 새 Chrome에서 사용
    config = DownloaderConfig(preserve_login_from_existing=True)
    downloader = HTMLDownloader(headless=True, use_existing_chrome=False, universities_json="data/universities.json", downloader_config=config)
    downloaded_files = downloader.download_all_pages(university_name)
    
    if not downloaded_files:
        logger.info("❌ Could not download any HTML content.")
        logger.info("\n💡 Tips:")
        logger.info("- Check if the university name is correct")
        logger.info("- Use 'python main_scraper.py --list' to see available universities")
        logger.info("- Try using partial names (e.g., 'harvard' instead of 'Harvard University')")
        return
    
    print_header("\n✅ COMPLETED SUCCESSFULLY!")
    logger.info(f"🎓 University: {university_name}")
    logger.info(f"📁 Downloaded {len(downloaded_files)} pages:")
    for i, file_path in enumerate(downloaded_files, 1):
        logger.info(f"   {i}. {file_path}")
    logger.info("")
    logger.info("🎉 Complete university data download completed successfully!")


if __name__ == "__main__":
    # Initialize basic logging to stdout for CLI consistency (shared helper)
    setup_basic_logging(logging.INFO)
    main()
