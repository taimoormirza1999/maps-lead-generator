"""
Google Maps Real Estate Agency Scraper
Supports: Direct URL or Search Query
Pass --with-emails to also extract emails from each business website (slower).
"""

import asyncio
import csv
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright

_EMAIL_RE = re.compile(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b')
_JUNK = ['noreply', 'no-reply', 'example', 'yoursite', 'sentry', 'jquery', '@2x', 'schema.org']
_JUNK_DOMAINS = {'example.com', 'test.com', 'sentry.io', 'wix.com', 'schema.org', 'w3.org'}

async def _extract_email(context, url: str) -> str:
    page = None
    try:
        page = await context.new_page()
        await page.goto(url, wait_until='domcontentloaded', timeout=12000)
        for el in await page.locator('a[href^="mailto:"]').all():
            href = (await el.get_attribute('href') or '').replace('mailto:', '').split('?')[0].strip()
            if '@' in href and href.split('@')[-1].lower() not in _JUNK_DOMAINS and not any(j in href.lower() for j in _JUNK):
                return href.lower()
        try:
            text = await page.inner_text('body')
            valid = [e.lower() for e in _EMAIL_RE.findall(text)
                     if e.split('@')[-1].lower() not in _JUNK_DOMAINS and not any(j in e.lower() for j in _JUNK)]
            if valid:
                return valid[0]
        except Exception:
            pass
        try:
            await page.goto(url.rstrip('/') + '/contact', wait_until='domcontentloaded', timeout=8000)
            for el in await page.locator('a[href^="mailto:"]').all():
                href = (await el.get_attribute('href') or '').replace('mailto:', '').split('?')[0].strip()
                if '@' in href and href.split('@')[-1].lower() not in _JUNK_DOMAINS and not any(j in href.lower() for j in _JUNK):
                    return href.lower()
            text = await page.inner_text('body')
            valid = [e.lower() for e in _EMAIL_RE.findall(text)
                     if e.split('@')[-1].lower() not in _JUNK_DOMAINS and not any(j in e.lower() for j in _JUNK)]
            if valid:
                return valid[0]
        except Exception:
            pass
        return ''
    except Exception:
        return ''
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass


async def scrape_google_maps(url_or_query: str, output_file: str = None, extract_emails: bool = False, headless: bool = False):
    """
    Scrape business listings from Google Maps

    Args:
        url_or_query: Either a full Google URL or a search query
        output_file: Output CSV filename (auto-generated if not provided)
    """

    if output_file is None:
        # Generate a clean filename from the query
        if url_or_query.startswith('http'):
            safe_name = "scraped"
        else:
            safe_name = url_or_query.lower().replace(' ', '-').replace(',', '')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
            safe_name = safe_name.strip('-')[:60]  # max 60 chars
        output_file = f"{safe_name}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

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
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            locale='en-US'
        )
        page = await context.new_page()

        print(f"Opening: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(5)

        # Scroll to load ALL results (keeps scrolling until no new results)
        print("Loading all results...")
        try:
            results_panel = page.locator('div[role="feed"]')
            prev_count = 0
            stuck_count = 0
            max_scrolls = 50
            for scroll_num in range(max_scrolls):
                await results_panel.evaluate('el => el.scrollTop = el.scrollHeight')
                await asyncio.sleep(2)
                current_count = await page.locator('a.hfpxzc').count()
                print(f"  Scroll {scroll_num + 1}: {current_count} results loaded")
                if current_count == prev_count:
                    stuck_count += 1
                    if stuck_count >= 3:  # 3 scrolls with no new results = end
                        break
                else:
                    stuck_count = 0
                prev_count = current_count
        except Exception as e:
            print(f"  Scroll error: {e}")

        # Get all business links
        links = await page.locator('a.hfpxzc').all()
        print(f"Found {len(links)} businesses total")

        for i, link in enumerate(links):  # Process ALL results
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

                # Extract email from website (only if --with-emails flag passed)
                if extract_emails and business.get('Website'):
                    try:
                        business['Email'] = await _extract_email(context, business['Website'])
                    except Exception:
                        pass

                if business['Name']:
                    businesses.append(business)
                    email_str = f" | {business['Email']}" if business.get('Email') else ''
                    print(f"  [{i+1}] {business['Name'][:40]} | {business['Phone'] or 'No phone'}{email_str}")

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
    with_emails = '--with-emails' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--with-emails']

    if args:
        url_or_query = ' '.join(args)
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

    asyncio.run(scrape_google_maps(url_or_query, extract_emails=with_emails))


if __name__ == "__main__":
    main()
