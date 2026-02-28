# Google Maps Business Scraper

A Python scraper that extracts business information from Google Maps search results and exports to CSV.

## Features

- Scrape business listings from Google Maps
- Accept either a **search query** or **Google URL**
- Auto-converts Google Search URLs to Maps URLs
- Exports to CSV (compatible with Excel/Google Sheets)

## Output Fields

| Field | Description |
|-------|-------------|
| Name | Business name |
| Phone | Phone number |
| Address | Full address |
| Location | Location (same as address) |
| Rating | Google rating |
| Website | Business website |
| Email | Email (if available) |
| Social Media | Social media links |

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install browser for Playwright
playwright install chromium
```

## Usage

### Interactive Mode
```bash
python google_maps_scraper.py
```
Then enter your search query or URL when prompted.

### With Search Query
```bash
python google_maps_scraper.py "Real estate agency Riyadh Saudi Arabia"
```

### With Google URL
```bash
python google_maps_scraper.py "https://www.google.com/search?q=Real+estate+agency+Riyadh&udm=1"
```

## Output

The scraper creates a CSV file with timestamp:
```
real_estate_agencies_2026-02-02_215147.csv
```

## Project Structure

```
scrapper/
├── google_maps_scraper.py   # Main scraper (Playwright)
├── serpapi_scraper.py       # Alternative using SerpAPI
├── requirements.txt         # Dependencies
├── run_scraper.sh          # Easy run script
└── scrapy_project/         # Scrapy version
    └── realestate_scraper/
        └── spiders/
            └── google_maps_spider.py
```

## Requirements

- Python 3.8+
- Playwright
- Chromium browser (auto-installed)

## Notes

- The scraper runs with browser visible (`headless=False`) by default
- Set `headless=True` in the script for background operation
- Google may show CAPTCHAs after many requests
- For production use, consider using SerpAPI (see `serpapi_scraper.py`)

## License

MIT
