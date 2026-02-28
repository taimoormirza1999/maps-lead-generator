"""
Google Maps Real Estate Agency Scraper
Supports: Direct URL or Search Query
"""

import asyncio
import csv
import sys
from datetime import datetime
from playwright.async_api import async_playwright


async def scrape_google_maps(url_or_query: str, output_file: str = None):
    """
    Scrape business listings from Google Maps

    Args:
        url_or_query: Either a full Google URL or a search query
        output_file: Output CSV filename (auto-generated if not provided)
    """

    if output_file is None:
        output_file = f"real_estate_agencies_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

    # Detect if input is URL or search query
    if url_or_query.startswith('http'):
        url = url_or_query
        # Convert Google Search URL to Maps URL if needed
        if 'google.com/search' in url and 'udm=1' in url:
            # Extract query from search URL
            import re
            match = re.search(r'[?&]q=([^&]+)', url)
            if match:
                query = match.group(1).replace('+', ' ')
                url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    else:
        # It's a search query
        url = f"https://www.google.com/maps/search/{url_or_query.replace(' ', '+')}"

    businesses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            locale='en-US'
        )
        page = await context.new_page()

        print(f"Opening: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(5)

        # Scroll to load more results
        print("Loading results...")
        try:
            results_panel = page.locator('div[role="feed"]')
            for _ in range(3):
                await results_panel.evaluate('el => el.scrollTop = el.scrollHeight')
                await asyncio.sleep(2)
        except:
            pass

        # Get all business links
        links = await page.locator('a.hfpxzc').all()
        print(f"Found {len(links)} businesses")

        for i, link in enumerate(links[:20]):  # Limit to 20
            try:
                business = {
                    'Name': '', 'Email': '', 'Phone': '', 'Social Media': '', 'Website': ''
                }

                # Get name from aria-label
                name = await link.get_attribute('aria-label')
                if name:
                    business['Name'] = name

                # Click to open details
                await link.click()
                await asyncio.sleep(2)

                # Extract phone
                try:
                    phone_btn = page.locator('button[data-item-id*="phone"]').first
                    if await phone_btn.count() > 0:
                        business['Phone'] = await phone_btn.locator('div.fontBodyMedium').inner_text()
                except:
                    pass

                # Extract website
                try:
                    web_link = page.locator('a[data-item-id="authority"]').first
                    if await web_link.count() > 0:
                        business['Website'] = await web_link.get_attribute('href')
                except:
                    pass

                if business['Name']:
                    businesses.append(business)
                    print(f"  [{i+1}] {business['Name'][:40]} | {business['Phone'] or 'No phone'}")

            except Exception as e:
                print(f"  Error on item {i+1}: {str(e)[:50]}")
                continue

        await browser.close()

    # Save to CSV
    if businesses:
        fieldnames = ['Name', 'Email', 'Phone', 'Social Media', 'Website']

        # Clean data - ensure phone is string with quotes for Excel
        for b in businesses:
            if b.get('Phone'):
                b['Phone'] = "'" + str(b['Phone'])  # Prefix with ' to force text in Excel

        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(businesses)

        print(f"\n{'='*50}")
        print(f"Saved {len(businesses)} businesses to: {output_file}")
        print(f"{'='*50}")
    else:
        print("No businesses found")

    return businesses, output_file


def main():
    print("=" * 50)
    print("Google Maps Scraper")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) > 1:
        url_or_query = ' '.join(sys.argv[1:])
    else:
        print("\nEnter a Google URL or search query:")
        print("Examples:")
        print("  - Real estate agency Riyadh Saudi Arabia")
        print("  - https://www.google.com/search?q=...&udm=1")
        print("  - https://www.google.com/maps/search/...")
        print()
        url_or_query = input("URL or Query: ").strip()

    if not url_or_query:
        url_or_query = "Real estate agency Riyadh Saudi Arabia"
        print(f"Using default: {url_or_query}")

    asyncio.run(scrape_google_maps(url_or_query))


if __name__ == "__main__":
    main()
