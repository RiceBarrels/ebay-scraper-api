# eBay Scrapy Scraper 🛒

A powerful and comprehensive eBay scraper built with Scrapy framework that efficiently extracts product listings, detailed product information, and seller data from eBay marketplaces worldwide. This professional-grade scraper is designed for e-commerce researchers, price comparison services, market analysts, and developers who need reliable eBay data extraction capabilities.

## ✨ Key Features

- **🔍 eBay Search Scraper**: Extract product listings, prices, seller info, and auction details
- **📦 eBay Product Scraper**: Gather detailed product information, specifications, and seller details
- **🛡️ Anti-Bot Protection**: Advanced middleware with user-agent rotation and security bypass
- **💰 Price Intelligence**: Smart price normalization and savings calculation
- **📊 Multi-Format Export**: CSV and JSON export with comprehensive data validation
- **🌍 Global eBay Support**: Works with eBay US, UK, DE, CA, AU, and other regional sites
- **⚡ Performance Optimized**: Concurrent requests with intelligent rate limiting
- **🧹 Data Cleaning**: Automatic normalization of prices, conditions, and seller information

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ScrapeOps/Simple-Python-Scrapy-Scrapers/ebay-scrapy-scraper.git
cd ebay-scrapy-scraper

# Install dependencies
pip install -r requirements.txt

# Install ScrapeOps Proxy (recommended)
pip install scrapeops-scrapy-proxy-sdk
```

### Basic Usage

**Search eBay Products:**
```bash
# Search for products with default query
scrapy crawl ebay_search

# Search with custom query and filters
scrapy crawl ebay_search -a query="iPhone 15" -a max_results=100 -a condition="new"

# Search with price range and sorting
scrapy crawl ebay_search -a query="laptop computer" -a min_price=500 -a max_price=1500 -a sort="PricePlusShippingLowest"

# Search on specific eBay site
scrapy crawl ebay_search -a query="vintage watch" -a site="UK" -a max_results=50
```

**Scrape Detailed Product Information:**
```bash
# Scrape products by URLs
scrapy crawl ebay_product -a product_urls="https://www.ebay.com/itm/123456789,https://www.ebay.com/itm/987654321"

# Scrape products by item IDs
scrapy crawl ebay_product -a item_ids="123456789,987654321,555666777"

# Mix URLs and IDs
scrapy crawl ebay_product -a product_urls="https://www.ebay.com/itm/123456789" -a item_ids="987654321"
```

## 📋 Scraped Data Fields

### eBay Search Results (40+ Fields)
- **Product Info**: Title, URL, ID, condition, brand, model, category
- **Pricing**: Current price, original price, savings, currency, shipping cost
- **Auction Data**: Bid count, time left, Buy It Now price, auction type
- **Seller Info**: Name, feedback score, location, top-rated status
- **Metadata**: Search query, position, page, watchers, items sold
- **Features**: Fast N' Free, returns accepted, authenticity guarantee

### eBay Product Details (80+ Fields)
- **Comprehensive Info**: Full description, specifications, item specifics
- **Pricing Details**: Current/original prices, savings calculations, price history
- **Images**: Main image, all product images, gallery thumbnails
- **Seller Details**: Complete seller profile, feedback history, business type
- **Shipping**: Multiple shipping options, costs, handling time, locations
- **Policies**: Return policy, payment methods, authenticity guarantees
- **Technical**: Product identifiers (UPC, EAN, MPN), compatibility info

## 🎯 Use Cases & Applications

### 🔬 Market Research & Analytics
- **Price Monitoring**: Track product prices across different sellers and time periods
- **Competitive Analysis**: Monitor competitor pricing strategies and inventory levels
- **Market Trends**: Analyze product demand, seasonal variations, and category performance
- **Product Research**: Identify trending products and market opportunities

### 💼 Business Intelligence
- **Inventory Management**: Monitor stock levels and availability across sellers
- **Pricing Strategy**: Optimize pricing based on competitor analysis and market data
- **Supplier Discovery**: Find new suppliers and evaluate seller performance
- **Brand Monitoring**: Track brand presence and pricing across the marketplace

### 🛠️ E-commerce Solutions
- **Price Comparison**: Build price comparison websites and tools
- **Product Catalogs**: Create comprehensive product databases with rich metadata
- **Dropshipping Research**: Identify profitable products and reliable suppliers
- **Marketplace Integration**: Sync eBay data with other platforms and systems

### 📈 Investment & Trading
- **Collectibles Valuation**: Track prices of collectibles, vintage items, and rare products
- **Arbitrage Opportunities**: Identify price differences across regions and sellers
- **Market Analysis**: Analyze trading volumes and price movements for investment decisions

## ⚙️ Configuration Options

### Search Parameters
```python
# Search Configuration
SEARCH_CONFIG = {
    'query': 'your search term',
    'max_results': 200,
    'site': 'US',  # US, UK, DE, CA, AU, FR, IT, ES
    'condition': 'new',  # new, used, open_box, refurbished, for_parts
    'min_price': 50,
    'max_price': 500,
    'sort': 'BestMatch'  # BestMatch, PricePlusShippingLowest, PricePlusShippingHighest
}
```

### Site-Specific Settings
```python
# Multi-Site Support
EBAY_SITES = {
    'US': 'https://www.ebay.com',      # United States
    'UK': 'https://www.ebay.co.uk',    # United Kingdom  
    'DE': 'https://www.ebay.de',       # Germany
    'CA': 'https://www.ebay.ca',       # Canada
    'AU': 'https://www.ebay.com.au',   # Australia
    'FR': 'https://www.ebay.fr',       # France
    'IT': 'https://www.ebay.it',       # Italy
    'ES': 'https://www.ebay.es',       # Spain
}
```

### Data Export Settings
```python
# Export Configuration
FEEDS = {
    'data/ebay_search_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'fields': ['product_title', 'current_price', 'seller_name', 'condition']
    },
    'data/ebay_products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'indent': 2
    }
}
```

## ScrapeOps Proxy

This eBay spider uses ScrapeOps Proxy as the proxy solution. ScrapeOps has a free plan that allows you to make up to 1,000 requests per which makes it ideal for the development phase, but can be easily scaled up to millions of pages per month if needs be.

**Get your ScrapeOps API key from https://scrapeops.io/app/register/main/**

To use the ScrapeOps Proxy you need to first install the proxy middleware:
```bash
pip install scrapeops-scrapy-proxy-sdk
```

Then activate the ScrapeOps Proxy by adding your API key to the `SCRAPEOPS_API_KEY` in the `settings.py` file:
```python
SCRAPEOPS_API_KEY = 'YOUR_API_KEY'
SCRAPEOPS_PROXY_ENABLED = True
DOWNLOADER_MIDDLEWARES = {
    'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
}
```

## 📊 eBay Website Analyzer

Before using this scraper, we recommend checking out the comprehensive **eBay Website Analyzer** which provides detailed insights about:

- **Scraping Difficulty**: Current anti-bot measures and detection methods
- **Legal Considerations**: Terms of service compliance and legal requirements
- **Technical Challenges**: Rate limiting, CAPTCHA, and security measures
- **Best Practices**: Recommended approaches for successful scraping
- **Proxy Requirements**: When and how to use proxies effectively

🔗 **View the eBay Website Analyzer**: [https://scrapeops.io/websites/ebay](https://scrapeops.io/websites/ebay)

📖 **Original Scraping Guide**: [https://scrapeops.io/websites/ebay/how-to-scrape-ebay](https://scrapeops.io/websites/ebay/how-to-scrape-ebay)

## 🔧 Advanced Features

### Smart Price Intelligence
- **Multi-Currency Support**: Automatic currency detection and conversion
- **Price Normalization**: Standardized price formats and calculations
- **Savings Detection**: Automatic calculation of discounts and savings percentages
- **Historical Tracking**: Track price changes over time (with custom implementation)

### Robust Data Processing
- **Condition Standardization**: Normalize product conditions across different formats
- **Seller Classification**: Categorize sellers by performance and reliability metrics
- **Deal Detection**: Identify good deals based on multiple quality indicators
- **Data Enrichment**: Add computed fields like price ranges and seller tiers

### Anti-Detection Measures
- **Dynamic Headers**: Rotate user agents and headers to avoid detection
- **Request Throttling**: Intelligent delays and retry mechanisms
- **Security Bypass**: Handle eBay security challenges and redirects
- **Session Management**: Maintain persistent sessions for better success rates

## 📊 Data Analysis Examples

### Python Price Analysis
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load scraped data
search_data = pd.read_csv('data/ebay_search_results.csv')
product_data = pd.read_csv('data/ebay_products.csv')

# Price distribution analysis
search_data['current_price_value'] = pd.to_numeric(search_data['current_price_value'], errors='coerce')
search_data['current_price_value'].hist(bins=50)
plt.title('eBay Price Distribution')
plt.xlabel('Price ($)')
plt.ylabel('Number of Listings')
plt.show()

# Top sellers analysis
top_sellers = search_data.groupby('seller_name').agg({
    'product_title': 'count',
    'current_price_value': 'mean'
}).sort_values('product_title', ascending=False).head(10)

print("Top 10 Sellers by Number of Listings:")
print(top_sellers)

# Deal identification
deals = search_data[
    (search_data['savings_percentage'] > 20) & 
    (search_data['seller_feedback_percentage'] > 98) &
    (search_data['shipping_cost'] == 'Free')
]
print(f"\nFound {len(deals)} potential deals")
```

### Market Intelligence Queries
```sql
-- Average prices by condition
SELECT 
    condition,
    COUNT(*) as listing_count,
    AVG(current_price_value) as avg_price,
    MIN(current_price_value) as min_price,
    MAX(current_price_value) as max_price
FROM ebay_search_results 
WHERE current_price_value > 0
GROUP BY condition
ORDER BY avg_price DESC;

-- Top performing sellers
SELECT 
    seller_name,
    COUNT(*) as total_listings,
    AVG(seller_feedback_percentage) as avg_feedback,
    AVG(current_price_value) as avg_price
FROM ebay_search_results 
WHERE seller_feedback_percentage > 95
GROUP BY seller_name
HAVING total_listings >= 5
ORDER BY total_listings DESC;

-- Price trends by search query
SELECT 
    search_query,
    COUNT(*) as listings,
    AVG(current_price_value) as avg_price,
    STDDEV(current_price_value) as price_variance
FROM ebay_search_results 
GROUP BY search_query
ORDER BY listings DESC;
```

## 🛡️ Ethical Scraping Guidelines

### Responsible Usage
- **Rate Limiting**: Respect eBay's servers with appropriate delays between requests
- **Terms of Service**: Ensure compliance with eBay's Terms of Service and robots.txt
- **Data Privacy**: Handle scraped data responsibly and in compliance with privacy laws
- **Commercial Use**: Understand the legal implications of using scraped data commercially

### Best Practices
- **Monitor Performance**: Track request success rates and response times
- **Error Handling**: Implement robust error handling and retry logic
- **Data Storage**: Use secure and compliant data storage methods
- **Regular Updates**: Keep scraper updated with eBay's website changes

## 🚨 Troubleshooting

### Common Issues

**Security Challenges**
```bash
# Enable debug logging
scrapy crawl ebay_search -L DEBUG

# Check for security redirects
grep "sec.ebay.com\|signin.ebay.com" scrapy.log
```

**Rate Limiting**
```python
# Increase delays in settings.py
DOWNLOAD_DELAY = 5
RANDOMIZE_DOWNLOAD_DELAY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_MAX_DELAY = 15
```

**Data Quality Issues**
```python
# Enable comprehensive data processing
ITEM_PIPELINES = {
    'ebay_scraper.pipelines.EbayDataValidationPipeline': 200,
    'ebay_scraper.pipelines.EbayDataCleaningPipeline': 300,
    'ebay_scraper.pipelines.EbayPriceNormalizationPipeline': 400,
}
```

### Debug Commands
```bash
# Test search functionality
scrapy shell "https://www.ebay.com/sch/i.html?_nkw=test"

# Test product page parsing
scrapy shell "https://www.ebay.com/itm/123456789"

# Check middleware functionality
scrapy crawl ebay_search -s LOG_LEVEL=DEBUG -a query="test" -a max_results=5
```

## 📈 Performance Metrics

### Benchmark Results
- **Search Speed**: ~100 listings/minute with rate limiting
- **Product Speed**: ~30 detailed products/minute including all data
- **Data Accuracy**: >95% successful field extraction
- **Memory Usage**: <300MB for 1000+ product dataset
- **Success Rate**: >90% even with anti-bot measures

### Scalability Options
- **Small Scale**: 1-500 products - Perfect for price monitoring
- **Medium Scale**: 500-10,000 products - Market research and analysis
- **Large Scale**: 10,000+ products - Enterprise data collection and business intelligence

## 🌍 Global eBay Support

### Supported Marketplaces
- **🇺🇸 eBay US** - ebay.com (USD)
- **🇬🇧 eBay UK** - ebay.co.uk (GBP)
- **🇩🇪 eBay Germany** - ebay.de (EUR)
- **🇨🇦 eBay Canada** - ebay.ca (CAD)
- **🇦🇺 eBay Australia** - ebay.com.au (AUD)
- **🇫🇷 eBay France** - ebay.fr (EUR)
- **🇮🇹 eBay Italy** - ebay.it (EUR)
- **🇪🇸 eBay Spain** - ebay.es (EUR)

### Currency Handling
Automatic currency detection and normalization for all supported regions with proper symbol mapping and conversion support.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/ScrapeOps/Simple-Python-Scrapy-Scrapers/ebay-scrapy-scraper.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Users are responsible for complying with eBay's Terms of Service and applicable laws. The authors are not responsible for any misuse of this software.

## 🔗 Related Projects

- **Amazon Scrapy Scraper** - For Amazon marketplace data
- **Shopify Store Scraper** - For Shopify-based stores
- **AliExpress Scraper** - For AliExpress product data

---
