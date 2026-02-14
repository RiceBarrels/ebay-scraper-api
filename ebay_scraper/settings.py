# Scrapy settings for ebay_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'ebay_scraper'

SPIDER_MODULES = ['ebay_scraper.spiders']
NEWSPIDER_MODULE = 'ebay_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# ScrapeOps Settings
SCRAPEOPS_API_KEY = 'Your-API-Key'  # Get your ScrapeOps API key from https://scrapeops.io/app/register/main/
SCRAPEOPS_PROXY_ENABLED = False
SCRAPEOPS_RENDER_JS = True
SCRAPEOPS_WAIT = 3000
SCRAPEOPS_BYPASS = 'generic_level_2'

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    'ebay_scraper.middlewares.EbayScraperSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': None,
    'ebay_scraper.middlewares.EbayScraperDownloaderMiddleware': 543,
    'ebay_scraper.middlewares.UserAgentRotationMiddleware': 400,
    'ebay_scraper.middlewares.EbayLocationMiddleware': 350,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'ebay_scraper.pipelines.EbayDataValidationPipeline': 200,
    'ebay_scraper.pipelines.EbayDataCleaningPipeline': 300,
}

# Enable AutoThrottle extension and configure the options
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 10
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [301, 302, 303, 306, 307, 308, 404, 410]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Custom eBay Settings
EBAY_BASE_URL = 'https://www.ebay.com'
EBAY_SEARCH_URL = 'https://www.ebay.com/sch/i.html'
EBAY_ITEM_URL = 'https://www.ebay.com/itm'
EBAY_STORES_URL = 'https://stores.ebay.com'
EBAY_CATEGORIES_URL = 'https://www.ebay.com/sch/allcategories'

# eBay Global Sites
EBAY_SITES = {
    'US': 'https://www.ebay.com',
    'UK': 'https://www.ebay.co.uk',
    'DE': 'https://www.ebay.de',
    'CA': 'https://www.ebay.ca',
    'AU': 'https://www.ebay.com.au',
    'FR': 'https://www.ebay.fr',
    'IT': 'https://www.ebay.it',
    'ES': 'https://www.ebay.es',
}

# Currency Settings
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'CAD': 'C$',
    'AUD': 'A$',
    'JPY': '¥',
}

# Request and Response Settings
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Concurrent Settings
CONCURRENT_REQUESTS = 16
REACTOR_THREADPOOL_MAXSIZE = 20

# Memory and Performance
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s: %(message)s'

# Data Export Settings
FEEDS = {
    'data/ebay_search_results.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['product_id', 'listing_id', 'product_title', 'product_url', 'current_price', 'main_image', 'condition', 'seller_name', 'seller_location', 'shipping_cost', 'price_type', 'listing_type', 'search_query', 'search_position', 'search_page', 'search_sort', 'scraped_at', 'scraper_version'],
    },
    'data/ebay_products.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['product_id', 'listing_id', 'product_title', 'product_url', 'current_price', 'main_image', 'condition', 'seller_name', 'seller_location', 'shipping_costs', 'auction_type', 'listing_type', 'scraped_at', 'scraper_version'],
    },
    'data/ebay_data.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
        'fields': None,
    },
}

# Request Fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# User Agents List for Rotation
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
]

# eBay Search Parameters
EBAY_SEARCH_PARAMS = {
    'sort': {
        'best_match': 'BestMatch',
        'price_low': 'PricePlusShippingLowest',
        'price_high': 'PricePlusShippingHighest',
        'distance': 'DistanceNearest',
        'time_ending': 'EndTimeSoonest',
        'time_newly': 'StartTimeNewest',
    },
    'condition': {
        'new': '1000',
        'open_box': '1500',
        'used': '3000',
        'very_good': '4000',
        'good': '5000',
        'acceptable': '6000',
        'for_parts': '7000',
    },
    'listing_type': {
        'all': '',
        'auction': 'Auction',
        'buy_it_now': 'FixedPrice',
        'classified': 'Classified',
    },
}

# Price Range Settings
PRICE_RANGES = {
    'under_25': {'min': 0, 'max': 25},
    '25_to_50': {'min': 25, 'max': 50},
    '50_to_100': {'min': 50, 'max': 100},
    '100_to_200': {'min': 100, 'max': 200},
    'over_200': {'min': 200, 'max': None},
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# eBay Specific Headers
EBAY_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'https://www.ebay.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Default Location Settings
DEFAULT_LOCATION = {
    'country': 'US',
    'zip_code': '90210',
    'currency': 'USD',
} 