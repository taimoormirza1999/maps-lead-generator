# Scrapy settings for realestate_scraper project

BOT_NAME = "realestate_scraper"

SPIDER_MODULES = ["realestate_scraper.spiders"]
NEWSPIDER_MODULE = "realestate_scraper.spiders"

# Crawl responsibly by identifying yourself
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 1

# Configure a delay for requests
DOWNLOAD_DELAY = 3

# Disable cookies
COOKIES_ENABLED = True

# Enable Playwright for JavaScript rendering
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # Set True for production
    "timeout": 60000,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000

# Output settings
FEEDS = {
    'output/%(name)s_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['Name', 'Email', 'Phone', 'Location', 'Last_Contacted',
                   'Status', 'Social_Media', 'Joined', 'Address', 'Rating',
                   'Reviews', 'Category', 'Website'],
    },
}

# Enable logging
LOG_LEVEL = 'INFO'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
