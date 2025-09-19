"""
Main Scraper

This is the main entry point that uses the HTMLDownloader module:
- HTMLDownloader: Downloads HTML content from university pages using universities.json
"""

import sys
import json
from html_downloader import HTMLDownloader


def print_header(title: str, width: int = 50):
    """Print a formatted header."""
    print(title)
    print("=" * width)


def load_universities_list():
    """Load university names from JSON file."""
    try:
        with open("universities.json", 'r', encoding='utf-8') as f:
            universities_data = json.load(f)
        return [uni['name'] for uni in universities_data]
    except Exception as e:
        print(f"❌ Error loading universities: {e}")
        return []


def show_help():
    """Show help information and available universities."""
    print_header("🎓 US News University Scraper")
    print("Usage:")
    print("  python main_scraper.py <university_name>")
    print("  python main_scraper.py --list")
    print("  python main_scraper.py --all")
    print("  python main_scraper.py --help")
    print()
    print("Examples:")
    print("  python main_scraper.py harvard")
    print("  python main_scraper.py 'Princeton University'")
    print("  python main_scraper.py mit")
    print("  python main_scraper.py --all")
    print()
    print("Options:")
    print("  --list    Show all available universities")
    print("  --all     Download all universities (436 universities)")
    print("  --help    Show this help message")


def list_universities():
    """List all available universities from the JSON file."""
    universities = load_universities_list()
    if not universities:
        return
    
    print_header("📚 Available Universities")
    for i, university in enumerate(universities, 1):
        print(f"{i:3d}. {university}")
    print(f"\nTotal: {len(universities)} universities")


def download_all_universities():
    """Download all universities from the JSON file."""
    try:
        downloader = HTMLDownloader(headless=True, use_existing_chrome=True)
        universities = downloader.list_all_universities()
        
        print_header("🎓 US News University Scraper - BULK DOWNLOAD", 60)
        print(f"📊 Total Universities: {len(universities)}")
        print("⚠️  This will take a very long time!")
        print("💡 You can stop anytime with Ctrl+C")
        print()
        
        # 자동으로 bulk download 시작 (확인 생략)
        print("🚀 Starting bulk download automatically...")
        print()
        
        success_count = 0
        failed_count = 0
        
        for i, university_name in enumerate(universities, 1):
            print(f"\n🏫 [{i}/{len(universities)}] Processing: {university_name}")
            print("=" * 80)
            
            try:
                downloaded_files = downloader.download_all_pages(university_name)
                if downloaded_files:
                    success_count += 1
                    print(f"✅ {university_name}: {len(downloaded_files)} pages downloaded")
                else:
                    failed_count += 1
                    print(f"❌ {university_name}: No pages downloaded")
                    
            except KeyboardInterrupt:
                print(f"\n\n⏹️  Bulk download interrupted by user")
                print(f"📊 Progress: {i-1}/{len(universities)} universities processed")
                break
            except Exception as e:
                failed_count += 1
                print(f"❌ {university_name}: Error - {str(e)}")
            
            # Progress summary every 10 universities
            if i % 10 == 0:
                print(f"\n📈 Progress Update: {i}/{len(universities)} universities processed")
                print(f"✅ Success: {success_count} | ❌ Failed: {failed_count}")
        
        print_header("\n🎉 BULK DOWNLOAD SUMMARY:")
        print(f"📊 Total Processed: {success_count + failed_count}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📁 Check downloads/ directory for all files")
        
    except Exception as e:
        print(f"❌ Error during bulk download: {e}")


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
    print(f"Target University: {university_name}")
    print()
    
    print_header("📥 Downloading HTML Content from All Pages")
    
    downloader = HTMLDownloader(headless=True, use_existing_chrome=True)  # Run in headless mode with existing Chrome
    downloaded_files = downloader.download_all_pages(university_name)
    
    if not downloaded_files:
        print("❌ Could not download any HTML content.")
        print("\n💡 Tips:")
        print("- Check if the university name is correct")
        print("- Use 'python main_scraper.py --list' to see available universities")
        print("- Try using partial names (e.g., 'harvard' instead of 'Harvard University')")
        return
    
    print_header("\n✅ COMPLETED SUCCESSFULLY!")
    print(f"🎓 University: {university_name}")
    print(f"📁 Downloaded {len(downloaded_files)} pages:")
    for i, file_path in enumerate(downloaded_files, 1):
        print(f"   {i}. {file_path}")
    print()
    print("🎉 Complete university data download completed successfully!")


if __name__ == "__main__":
    main()
