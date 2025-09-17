# Project Brief: US News University ID Scraper

## Overview
A Selenium-based web scraper that extracts university IDs from US News education search results.

## Core Requirements
1. Use Selenium to navigate US News search pages
2. Search for universities (example: Harvard)
3. Extract university IDs from the search results
4. Target URL pattern: `https://premium.usnews.com/best-colleges/{university-name}-{ID}/`
5. Extract the numeric ID (e.g., "2155" from Harvard's URL)

## Example Workflow
1. Navigate to: `https://www.usnews.com/search/education?q=harvard#gsc.tab=0&gsc.q=harvard&gsc.page=1`
2. Find search results that link to university pages
3. Extract IDs from URLs like: `https://premium.usnews.com/best-colleges/harvard-university-2155/`
4. Return the extracted ID (2155)

## Success Criteria
- Successfully navigate US News search pages
- Parse search results to find university links
- Extract university IDs reliably
- Handle different university names/searches
