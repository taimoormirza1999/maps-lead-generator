#!/bin/bash

echo "=========================================="
echo "Google Maps Real Estate Scraper"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo ""
echo "Choose scraping method:"
echo "1) Playwright (Simple, direct browser automation)"
echo "2) Scrapy + Playwright (Full Scrapy framework)"
echo "3) SerpAPI (Most reliable, requires API key)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Running Playwright scraper..."
        python google_maps_scraper.py
        ;;
    2)
        echo "Running Scrapy spider..."
        cd scrapy_project
        mkdir -p output
        scrapy crawl google_maps
        cd ..
        ;;
    3)
        echo "Running SerpAPI scraper..."
        python serpapi_scraper.py
        ;;
    *)
        echo "Invalid choice. Running Playwright scraper by default..."
        python google_maps_scraper.py
        ;;
esac

echo ""
echo "Done! Check for CSV output files."
