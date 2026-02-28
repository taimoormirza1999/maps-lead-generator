"""
Google Maps Real Estate Spider
Uses Scrapy with Playwright for JavaScript rendering
"""

import re
import scrapy
from scrapy_playwright.page import PageMethod
from realestate_scraper.items import RealEstateItem


class GoogleMapsSpider(scrapy.Spider):
    name = "google_maps"
    allowed_domains = ["google.com"]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]
        else:
            self.start_urls = [
                "https://www.google.com/search?q=Real+estate+agency+Riyadh+13762,+Saudi+Arabia&udm=1"
            ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.Nv2PK", timeout=30000),
                        PageMethod("wait_for_timeout", 3000),  # Wait for dynamic content
                    ],
                },
                callback=self.parse,
                errback=self.errback_handler,
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # Scroll to load more results
        self.logger.info("Scrolling to load all results...")
        feed = await page.query_selector('div[role="feed"]')
        if feed:
            for _ in range(5):
                await feed.evaluate('el => el.scrollTop = el.scrollHeight')
                await page.wait_for_timeout(1500)

        # Get all business cards
        business_cards = await page.query_selector_all('div.Nv2PK')
        self.logger.info(f"Found {len(business_cards)} business listings")

        for i, card in enumerate(business_cards):
            try:
                item = RealEstateItem()

                # Click on card to open details
                link = await card.query_selector('a.hfpxzc')
                if link:
                    await link.click()
                    await page.wait_for_timeout(2000)

                # Extract name
                name_el = await page.query_selector('h1.DUwDvf')
                if name_el:
                    item['Name'] = await name_el.inner_text()

                # Extract rating
                rating_el = await page.query_selector('div.F7nice span[aria-hidden="true"]')
                if rating_el:
                    item['Rating'] = await rating_el.inner_text()

                # Extract reviews count
                reviews_el = await page.query_selector('div.F7nice span[aria-label*="reviews"]')
                if reviews_el:
                    label = await reviews_el.get_attribute('aria-label')
                    if label:
                        match = re.search(r'(\d+)', label)
                        if match:
                            item['Reviews'] = match.group(1)

                # Extract category
                category_el = await page.query_selector('button.DkEaL')
                if category_el:
                    item['Category'] = await category_el.inner_text()

                # Extract address
                address_el = await page.query_selector('button[data-item-id="address"] div.fontBodyMedium')
                if address_el:
                    address = await address_el.inner_text()
                    item['Address'] = address
                    item['Location'] = address

                # Extract phone
                phone_el = await page.query_selector('button[data-item-id*="phone"] div.fontBodyMedium')
                if phone_el:
                    phone = await phone_el.inner_text()
                    item['Phone'] = "'" + phone if phone.startswith('+') else phone

                # Extract website
                website_el = await page.query_selector('a[data-item-id="authority"]')
                if website_el:
                    item['Website'] = await website_el.get_attribute('href')

                # Look for social media links
                social_links = []
                all_links = await page.query_selector_all('a[href*="facebook.com"], a[href*="instagram.com"], a[href*="linkedin.com"], a[href*="twitter.com"]')
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and href not in social_links:
                        social_links.append(href)
                item['Social_Media'] = ', '.join(social_links)

                # Initialize empty fields
                item['Email'] = ''
                item['Last_Contacted'] = ''
                item['Status'] = ''
                item['Joined'] = ''

                if item.get('Name'):
                    self.logger.info(f"  [{i+1}] {item['Name']} - {item.get('Phone', 'N/A')}")
                    yield item

            except Exception as e:
                self.logger.error(f"Error extracting business {i+1}: {str(e)}")
                continue

        await page.close()

    async def errback_handler(self, failure):
        self.logger.error(f"Request failed: {failure}")
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
