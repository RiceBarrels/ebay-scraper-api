import scrapy
import json
import re
from urllib.parse import urlencode, urlparse, parse_qs, urljoin
from ebay_scraper.items import EbaySearchItem
from datetime import datetime
import logging


class EbaySearchSpider(scrapy.Spider):
    name = 'ebay_search'
    allowed_domains = ['ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.ca', 'ebay.com.au', 'proxy.scrapeops.io']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
    }
    
    def __init__(self, query=None, max_results=50, site='US', condition=None, 
                 min_price=None, max_price=None, sort='BestMatch', *args, **kwargs):
        super(EbaySearchSpider, self).__init__(*args, **kwargs)
        
        self.search_query = query or 'laptop computer'
        self.max_results = int(max_results)
        self.site = site.upper()
        self.condition = condition
        self.min_price = min_price
        self.max_price = max_price
        self.sort = sort
        self.results_count = 0
        self.current_page = 1
        
        # eBay site URLs
        self.site_urls = {
            'US': 'https://www.ebay.com',
            'UK': 'https://www.ebay.co.uk',
            'DE': 'https://www.ebay.de',
            'CA': 'https://www.ebay.ca',
            'AU': 'https://www.ebay.com.au',
            'FR': 'https://www.ebay.fr',
            'IT': 'https://www.ebay.it',
            'ES': 'https://www.ebay.es',
        }
        
        self.base_url = self.site_urls.get(self.site, self.site_urls['US'])
        
        self.logger.info(f"Starting eBay search for: '{self.search_query}' on {self.site}")
        self.logger.info(f"Max results to scrape: {self.max_results}")
    
    def start_requests(self):
        """Generate initial search requests"""
        search_params = {
            '_nkw': self.search_query,  # Search query
            '_sop': self._get_sort_value(self.sort),  # Sort option
        }
        
        # Add condition filter
        if self.condition:
            search_params['LH_ItemCondition'] = self._get_condition_value(self.condition)
        
        # Add price range
        if self.min_price:
            search_params['_udlo'] = self.min_price
        if self.max_price:
            search_params['_udhi'] = self.max_price
        
        # Add other useful parameters
        search_params.update({
            '_from': 'R40',  # Results per page
            '_sacat': '0',   # All categories
            'rt': 'nc',      # No cache
            '_dcat': '1',    # Include description in search
        })
        
        search_url = f"{self.base_url}/sch/i.html?{urlencode(search_params)}"
        
        yield scrapy.Request(
            url=search_url,
            callback=self.parse_search_results,
            meta={
                'search_query': self.search_query,
                'page': 1,
                'search_params': search_params
            },
            headers=self._get_headers()
        )
    
    def _get_headers(self):
        """Get appropriate headers for eBay requests"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_sort_value(self, sort):
        """Convert sort option to eBay sort value"""
        sort_mapping = {
            'BestMatch': '12',
            'PricePlusShippingLowest': '15',
            'PricePlusShippingHighest': '16',
            'EndTimeSoonest': '1',
            'StartTimeNewest': '10',
            'DistanceNearest': '21',
        }
        return sort_mapping.get(sort, '12')
    
    def _get_condition_value(self, condition):
        """Convert condition to eBay condition value"""
        condition_mapping = {
            'new': '1000',
            'open_box': '1500',
            'used': '3000',
            'refurbished': '2000',
            'for_parts': '7000',
        }
        return condition_mapping.get(condition.lower(), '')
    
    def parse_search_results(self, response):
        """Parse eBay search results page"""
        self.logger.info(f"Parsing search results from: {response.url}")
        
        # Extract search result items
        item_containers = response.css('.s-item')
        
        if not item_containers:
            self.logger.warning("No search result items found")
            return
        
        for container in item_containers:
            if self.results_count >= self.max_results:
                return
            
            # Skip sponsored/ad items if desired
            if container.css('.s-item__subtitle:contains("Sponsored")'):
                continue
            
            try:
                item_data = self.extract_search_item_data(container, response.meta)
                if item_data:
                    self.results_count += 1
                    yield item_data
            except Exception as e:
                self.logger.error(f"Error extracting search item: {e}")
                continue
        
        # Check for next page
        if self.results_count < self.max_results:
            next_page_url = self.get_next_page_url(response)
            if next_page_url:
                self.current_page += 1
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_search_results,
                    meta={
                        'search_query': response.meta['search_query'],
                        'page': self.current_page,
                        'search_params': response.meta['search_params']
                    },
                    headers=self._get_headers()
                )
    
    def extract_search_item_data(self, container, meta):
        """Extract data from a single search result item"""
        try:
            item = EbaySearchItem()
            
            # Product title and URL
            title_link = container.css('h3.s-item__title a')
            if not title_link:
                title_link = container.css('.s-item__link')
            
            if title_link:
                item['product_title'] = title_link.css('::text').get('')
                item['product_url'] = title_link.css('::attr(href)').get('')
                
                # Extract item ID from URL
                if item['product_url']:
                    item['product_id'] = self._extract_item_id(item['product_url'])
                    item['listing_id'] = item['product_id']
            else:
                return None
            
            # Skip if no title or URL
            if not item['product_title'] or not item['product_url']:
                return None

            # Skip placeholder or invalid items (item_id must be all digits and at least 9 digits)
            if not item['product_id'] or not item['product_id'].isdigit() or len(item['product_id']) < 9:
                return None
            
            # Clean title
            item['product_title'] = self._clean_title(item['product_title'])
            
            # Current price
            price_element = container.css('.s-item__price .notranslate')
            if price_element:
                price_text = price_element.css('::text').get('')
                item['current_price'] = price_text.strip()
            else:
                # Alternative price selectors
                price_alt = container.css('.s-item__price::text').get('')
                item['current_price'] = price_alt.strip() if price_alt else ''
            
            # Shipping cost
            shipping_element = container.css('.s-item__shipping')
            if shipping_element:
                shipping_text = shipping_element.css('::text').get('')
                item['shipping_cost'] = shipping_text.strip() if shipping_text else ''
            else:
                item['shipping_cost'] = ''
            
            # Seller information
            seller_element = container.css('.s-item__seller-info-text')
            if seller_element:
                seller_text = seller_element.css('::text').get('')
                if seller_text:
                    item['seller_name'] = seller_text.strip()
            else:
                item['seller_name'] = ''
            
            # Location
            location_element = container.css('.s-item__location')
            if location_element:
                location_text = location_element.css('::text').get('')
                item['seller_location'] = location_text.strip() if location_text else ''
            else:
                item['seller_location'] = ''
            
            # Condition
            condition_element = container.css('.SECONDARY_INFO')
            if condition_element:
                condition_text = condition_element.css('::text').get('')
                item['condition'] = condition_text.strip() if condition_text else ''
            else:
                item['condition'] = ''
            
            # Main image
            image_element = container.css('.s-item__image img')
            if image_element:
                item['main_image'] = image_element.css('::attr(src)').get('')
                item['thumbnail_image'] = item['main_image']
            else:
                item['main_image'] = ''
                item['thumbnail_image'] = ''
            
            # Auction/bid information
            bid_element = container.css('.s-item__bidding')
            if bid_element:
                bid_text = bid_element.css('::text').get('')
                if bid_text and 'bid' in bid_text.lower():
                    item['bid_count'] = self._extract_bid_count(bid_text)
                    item['price_type'] = 'auction'
                else:
                    item['bid_count'] = ''
                    item['price_type'] = 'buy_it_now'
            else:
                item['bid_count'] = ''
                item['price_type'] = 'buy_it_now'
            
            # Time left (for auctions)
            time_element = container.css('.s-item__time-left')
            if time_element:
                time_text = time_element.css('::text').get('')
                item['time_left'] = time_text.strip() if time_text else ''
            else:
                item['time_left'] = ''
            
            # Buy It Now price (for auctions)
            buy_now_element = container.css('.s-item__purchase-options-with-icon')
            if buy_now_element:
                buy_now_text = buy_now_element.css('::text').get('')
                if 'Buy It Now' in buy_now_text:
                    item['buy_it_now_price'] = self._extract_price_from_text(buy_now_text)
                else:
                    item['buy_it_now_price'] = ''
            else:
                item['buy_it_now_price'] = ''
            
            # Watchers count
            watchers_element = container.css('.s-item__watchheart-count')
            if watchers_element:
                watchers_text = watchers_element.css('::text').get('')
                item['watchers'] = self._extract_number(watchers_text) if watchers_text else ''
            else:
                item['watchers'] = ''
            
            # Items sold information
            sold_element = container.css('.s-item__quantitySold')
            if sold_element:
                sold_text = sold_element.css('::text').get('')
                item['items_sold'] = self._extract_number(sold_text) if sold_text else ''
            else:
                item['items_sold'] = ''
            
            # Special features
            item['fast_n_free'] = bool(container.css('.s-item__fast-n-free'))
            item['top_rated_seller'] = bool(container.css('.s-item__etrs'))
            item['returns_accepted'] = bool(container.css('.s-item__returns'))
            item['authenticity_guarantee'] = bool(container.css('.s-item__authenticity'))
            
            # Search context
            item['search_query'] = meta['search_query']
            item['search_position'] = self.results_count + 1
            item['search_page'] = meta['page']
            item['search_sort'] = self.sort
            
            # Additional fields with defaults
            item['original_price'] = ''
            item['discount_percentage'] = ''
            item['brand'] = ''
            item['model'] = ''
            item['category'] = ''
            item['subcategory'] = ''
            item['seller_id'] = ''
            item['seller_feedback_score'] = ''
            item['seller_feedback_percentage'] = ''
            item['seller_verified'] = False
            item['quantity_available'] = ''
            item['listing_type'] = item['price_type']
            item['listing_format'] = ''
            item['ebay_plus'] = bool(container.css('.s-item__etrs'))
            item['sponsored'] = bool(container.css('.s-item__subtitle:contains("Sponsored")'))
            item['reserve_met'] = ''
            item['end_time'] = ''
            item['ships_from'] = ''
            item['ships_to'] = ''
            item['handling_time'] = ''
            item['shipping_type'] = ''
            item['return_period'] = ''
            item['image_count'] = 1 if item['main_image'] else 0
            
            self.logger.info(f"Extracted item: {item['product_title'][:50]}... - ${item['current_price']}")
            return item
            
        except Exception as e:
            self.logger.error(f"Error extracting search item data: {e}")
            return None
    
    def _clean_title(self, title):
        """Clean product title"""
        if not title:
            return ''
        
        # Remove 'New Listing' prefix
        title = re.sub(r'^New Listing\s*', '', title, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _extract_item_id(self, url):
        """Extract eBay item ID from URL"""
        try:
            patterns = [
                r'/itm/(\d+)',
                r'/itm/[^/]+/(\d+)',
                r'item=(\d+)',
                r'ItemID=(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return ''
        except:
            return ''
    
    def _extract_bid_count(self, text):
        """Extract number of bids from text"""
        try:
            match = re.search(r'(\d+)\s*bid', text, re.IGNORECASE)
            return match.group(1) if match else ''
        except:
            return ''
    
    def _extract_price_from_text(self, text):
        """Extract price from text"""
        try:
            # Look for price patterns like $123.45
            price_match = re.search(r'[\$£€¥]\s*([0-9,]+\.?\d*)', text)
            return price_match.group(0) if price_match else ''
        except:
            return ''
    
    def _extract_number(self, text):
        """Extract number from text"""
        try:
            match = re.search(r'(\d+)', text)
            return match.group(1) if match else ''
        except:
            return ''
    
    def get_next_page_url(self, response):
        """Get URL for next page of results"""
        try:
            # Look for pagination next button
            next_link = response.css('.pagination__next::attr(href)').get()
            if next_link:
                return urljoin(response.url, next_link)
            
            # Alternative pagination selector
            next_link_alt = response.css('a.pager-next::attr(href)').get()
            if next_link_alt:
                return urljoin(response.url, next_link_alt)
            
            # Build next page URL manually
            current_params = response.meta.get('search_params', {})
            current_params['_pgn'] = self.current_page + 1
            
            base_url = f"{self.base_url}/sch/i.html"
            next_url = f"{base_url}?{urlencode(current_params)}"
            
            # Verify there are more results by checking result count
            result_count_text = response.css('.srp-controls__count-heading::text').get('')
            if result_count_text and 'of' in result_count_text:
                try:
                    # Extract total results and current position
                    match = re.search(r'(\d+[\d,]*)\s*-\s*(\d+[\d,]*)\s*of\s*(\d+[\d,]*)', result_count_text)
                    if match:
                        current_end = int(match.group(2).replace(',', ''))
                        total_results = int(match.group(3).replace(',', ''))
                        
                        if current_end < total_results:
                            return next_url
                except:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting next page URL: {e}")
            return None 