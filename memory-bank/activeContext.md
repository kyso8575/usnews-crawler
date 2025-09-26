# Active Context

## Current Focus
Successfully implemented campus-info data extraction with structured parsing using data-test-id attributes.

## Current Project Structure
```
scraper/
├── usnews_scraper/                 # Python package (core modules)
│   ├── __init__.py
│   ├── html_downloader.py          # HTML download orchestration
│   └── selenium_base.py            # Selenium common utilities
├── models/                         # Data models for different page types
│   ├── campus_info_data.py         # Campus info data structure
│   ├── student_life_data.py        # Student life data structure
│   ├── cost_data.py                # Cost/paying data structure
│   ├── academics_data.py           # Academics data structure
│   └── overall_rankings.py         # Overall rankings data structure
├── parser/                         # HTML parsers for different page types
│   ├── campus_info_parser.py       # Campus info HTML parser
│   ├── student_life_parser.py      # Student life HTML parser
│   ├── cost_parser.py              # Cost/paying HTML parser
│   ├── academics_parser.py          # Academics HTML parser
│   └── overall_rankings.py         # Overall rankings HTML parser
├── data/
│   ├── universities.json           # University list dataset
│   └── extracted/                  # Extracted structured data
│       ├── Princeton_University_student_life.json
│       └── Princeton_University_campus_info.json
├── downloads/                      # Saved HTML by university
├── main.py                         # Main entrypoint
├── requirements.txt                # Dependencies
└── memory-bank/                    # Project documentation
```

## Recently Completed
1. ✅ Created campus-info data model (`models/campus_info_data.py`)
2. ✅ Created campus-info parser (`parser/campus_info_parser.py`)
3. ✅ Implemented data-test-id based extraction for structured data
4. ✅ Successfully tested with Princeton University campus-info data
5. ✅ Extracted comprehensive campus information including:
   - Campus size (3,500 acres)
   - Alcohol policy (Yes)
   - Firearm policy (Banned)
   - Learning disability services
   - Salary information ($87,815 median starting salary)
   - Accessibility information

## Next Steps
1. ⏳ Integrate campus-info parser into main scraping workflow
2. ⏳ Test with other universities' campus-info pages
3. ⏳ Add more data-test-id mappings as needed

## Current Capabilities
- **University listing (--list)**: ✅ Working
- **Search navigation & HTML download**: ✅ Working via `HTMLDownloader`
- **Student life data extraction**: ✅ Working
- **Campus info data extraction**: ✅ Working (NEW)

## Key Technical Details
- **Target URL Pattern**: `https://premium.usnews.com/best-colleges/{university-name}-{id}/campus-info`
- **Data Extraction**: Uses data-test-id attributes for structured data
- **Parser Pattern**: Label-value pairs with DataRow class structure
- **Browser**: Chrome with automatic driver management

## Development Notes
- Campus-info parser successfully extracts structured data using data-test-id attributes
- Data is organized into meaningful categories (campus size, policies, services)
- Parser handles both simple values and complex label-value structures
- Ready for integration into main scraping workflow