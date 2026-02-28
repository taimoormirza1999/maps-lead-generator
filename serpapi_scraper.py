"""
Google Maps Scraper using SerpAPI (More Reliable)
SerpAPI handles Google's anti-bot measures and provides clean JSON data

Get your API key at: https://serpapi.com (free tier: 100 searches/month)
"""

import csv
from datetime import datetime
from serpapi import GoogleSearch


def scrape_with_serpapi(query: str, api_key: str, location: str = "Riyadh, Saudi Arabia"):
    """
    Scrape Google Maps results using SerpAPI

    Args:
        query: Search query
        api_key: Your SerpAPI key
        location: Location for search
    """

    params = {
        "engine": "google_maps",
        "q": query,
        "ll": "@24.7136,46.6753,12z",  # Riyadh coordinates
        "type": "search",
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    businesses = []

    if "local_results" in results:
        for place in results["local_results"]:
            business = {
                'Name': place.get('title', ''),
                'Email': '',
                'Phone': place.get('phone', ''),
                'Location': place.get('address', ''),
                'Last Contacted': '',
                'Status': '',
                'Social Media': '',
                'Joined': '',
                'Address': place.get('address', ''),
                'Rating': place.get('rating', ''),
                'Reviews': place.get('reviews', ''),
                'Category': place.get('type', ''),
                'Website': place.get('website', ''),
                'Hours': place.get('hours', ''),
                'Place ID': place.get('place_id', '')
            }
            businesses.append(business)
            print(f"  Found: {business['Name']} - {business['Phone']}")

    return businesses


def save_to_csv(businesses: list, output_file: str = None):
    """Save businesses to CSV file"""
    if output_file is None:
        output_file = f"real_estate_agencies_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

    if businesses:
        fieldnames = ['Name', 'Email', 'Phone', 'Location', 'Last Contacted', 'Status',
                      'Social Media', 'Joined', 'Address', 'Rating', 'Reviews',
                      'Category', 'Website', 'Hours', 'Place ID']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(businesses)

        print(f"\nSaved {len(businesses)} businesses to: {output_file}")
    return output_file


def main():
    # ===== CONFIGURATION =====
    API_KEY = "YOUR_SERPAPI_KEY_HERE"  # Get from https://serpapi.com
    QUERY = "Real estate agency Riyadh 13762 Saudi Arabia"

    if API_KEY == "YOUR_SERPAPI_KEY_HERE":
        print("=" * 50)
        print("Please set your SerpAPI key!")
        print("1. Get free API key at: https://serpapi.com")
        print("2. Replace 'YOUR_SERPAPI_KEY_HERE' with your key")
        print("=" * 50)
        return

    print(f"Searching for: {QUERY}")
    businesses = scrape_with_serpapi(QUERY, API_KEY)
    save_to_csv(businesses)


if __name__ == "__main__":
    main()
