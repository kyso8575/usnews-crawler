"""
Main Scraper

This is the main entry point that uses the HTMLDownloader module:
- HTMLDownloader: Downloads HTML content from university pages using universities.json
"""

import sys
from html_downloader import HTMLDownloader


def show_help():
    """Show help information and available universities."""
    print("🎓 US News University Scraper")
    print("=" * 50)
    print("Usage:")
    print("  python main_scraper.py <university_name>")
    print("  python main_scraper.py --list")
    print("  python main_scraper.py --help")
    print()
    print("Examples:")
    print("  python main_scraper.py harvard")
    print("  python main_scraper.py 'Princeton University'")
    print("  python main_scraper.py mit")
    print()
    print("Options:")
    print("  --list    Show all available universities")
    print("  --help    Show this help message")


def list_universities():
    """List all available universities from the JSON file."""
    try:
        downloader = HTMLDownloader()
        universities = downloader.list_all_universities()
        
        print("📚 Available Universities:")
        print("=" * 50)
        for i, university in enumerate(universities, 1):
            print(f"{i:3d}. {university}")
        print(f"\nTotal: {len(universities)} universities")
        
    except Exception as e:
        print(f"❌ Error loading universities: {e}")


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
    
    university_name = arg
    
    print("🎓 US News University Scraper")
    print("=" * 50)
    print(f"Target University: {university_name}")
    print()
    
    # Download HTML Content from All Pages
    print(f"📥 Downloading HTML Content from All Pages")
    print("-" * 50)
    
    downloader = HTMLDownloader(headless=False)  # Show browser for monitoring
    downloaded_files = downloader.download_all_pages(university_name)
    
    if not downloaded_files:
        print("❌ Could not download any HTML content.")
        print("\n💡 Tips:")
        print("- Check if the university name is correct")
        print("- Use 'python main_scraper.py --list' to see available universities")
        print("- Try using partial names (e.g., 'harvard' instead of 'Harvard University')")
        return
    
    print(f"\n✅ COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"🎓 University: {university_name}")
    print(f"📁 Downloaded {len(downloaded_files)} pages:")
    for i, file_path in enumerate(downloaded_files, 1):
        print(f"   {i}. {file_path}")
    print()
    print("🎉 Complete university data download completed successfully!")


if __name__ == "__main__":
    main()
