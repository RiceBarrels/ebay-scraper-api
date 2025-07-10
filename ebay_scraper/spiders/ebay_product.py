import scrapy
import json
import re
from urllib.parse import urljoin, urlparse, parse_qs
from ebay_scraper.items import EbayProductItem
from datetime import datetime
import logging


class EbayProductSpider(scrapy.Spider):
    name = 'ebay_product'
    allowed_domains = ['ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.ca', 'ebay.com.au', 'proxy.scrapeops.io']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
    }
    
    def __init__(self, product_urls=None, item_ids=None, *args, **kwargs):
        super(EbayProductSpider, self).__init__(*args, **kwargs)
        
        self.product_urls = []
        
        # Parse product URLs from argument
        if product_urls:
            urls = product_urls.split(',')
            for url in urls:
                url = url.strip()
                if url.startswith('http'):
                    self.product_urls.append(url)
                else:
                    # Assume it's an item ID or partial URL
                    if url.isdigit():
                        # It's an item ID
                        full_url = f'https://www.ebay.com/itm/{url}'
                        self.product_urls.append(full_url)
        
        # Parse item IDs from argument
        if item_ids:
            ids = item_ids.split(',')
            for item_id in ids:
                item_id = item_id.strip()
                if item_id.isdigit():
                    full_url = f'https://www.ebay.com/itm/{item_id}'
                    self.product_urls.append(full_url)
        
        # Default product URLs if none provided
        if not self.product_urls:
            self.product_urls = [
                'https://www.ebay.com/itm/123456789',  # Example - will need actual URLs
            ]
        
        self.logger.info(f"Starting product scraping for {len(self.product_urls)} products")
        for url in self.product_urls:
            self.logger.info(f"Product URL: {url}")
    
    def start_requests(self):
        """Generate initial product requests"""
        for product_url in self.product_urls:
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product,
                meta={'product_url': product_url},
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
    
    def parse_product(self, response):
        """Parse eBay product page"""
        self.logger.info(f"Parsing product: {response.url}")
        
        # Check if page is valid
        if response.status == 404 or 'this listing has ended' in response.text.lower():
            self.logger.warning(f"Product not found or ended: {response.url}")
            return
        
        try:
            # Extract structured data from page
            product_data = self.extract_product_data(response)
            if product_data:
                yield product_data
        except Exception as e:
            self.logger.error(f"Error parsing product {response.url}: {e}")
    
    def extract_product_data(self, response):
        """Extract detailed product data from eBay product page"""
        try:
            item = EbayProductItem()
            
            # Basic product information
            item['product_url'] = response.url
            item['product_id'] = self._extract_item_id(response.url)
            item['listing_id'] = item['product_id']
            
            # Product title (updated selectors)
            title_element = response.css('h1.x-item-title__mainTitle span::text').get()
            if not title_element:
                title_element = response.css('h1 span::text').get()
            if not title_element:
                title_element = response.css('h1::text').get()
            if not title_element:
                title_element = response.css('title::text').get()
            item['product_title'] = title_element.strip() if title_element else ''

            # Price information (updated selectors for new eBay layout)
            price_element = response.css('.x-price-primary .ux-textspans::text').get()
            if not price_element:
                price_element = response.css('.x-price-primary span::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__price .ux-textspans::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__price span::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__price::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__mainPrice::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__value::text').get()
            if not price_element:
                price_element = response.css('.x-price-approx__amount::text').get()
            if not price_element:
                price_element = response.css('.notranslate::text').get()
            if not price_element:
                price_element = response.css('#prcIsum::text').get()
            item['current_price'] = price_element.strip() if price_element else ''

            # Original price (if on sale)
            original_price = response.css('.originalPrice .notranslate::text').get()
            item['original_price'] = original_price.strip() if original_price else ''
            
            # Condition
            condition_element = response.css('div.x-item-condition-value span::text').get()
            if not condition_element:
                condition_element = response.css('span.condText::text').get()
            if not condition_element:
                condition_element = response.css('div[itemprop="itemCondition"]::text').get()
            item['condition'] = condition_element.strip() if condition_element else ''
            
            # Condition details
            condition_details = response.css('.conditionDetails::text').get()
            item['condition_details'] = condition_details.strip() if condition_details else ''
            
            # Brand and model
            item['brand'] = self._extract_item_specific(response, 'Brand')
            item['model'] = self._extract_item_specific(response, 'Model')
            item['mpn'] = self._extract_item_specific(response, 'MPN')
            item['upc'] = self._extract_item_specific(response, 'UPC')
            item['ean'] = self._extract_item_specific(response, 'EAN')
            
            # Description
            description_element = response.css('#desc_div')
            if description_element:
                # Get text content, preserving some structure
                description_text = ' '.join(description_element.css('::text').getall())
                item['description_full'] = self._clean_text(description_text)
                item['description_html'] = description_element.get()
            else:
                item['description_full'] = ''
                item['description_html'] = ''
            
            # Short description from item specifics
            short_desc = response.css('.u-flL.w2kTitleBidPrice::text').get()
            item['short_description'] = short_desc.strip() if short_desc else ''
            
            # Images
            main_image = response.css('img#icImg::attr(src)').get()
            if not main_image:
                main_image = response.css('img[alt*="main"]::attr(src)').get()
            if not main_image:
                main_image = response.css('img::attr(src)').get()
            item['main_image'] = main_image if main_image else ''
            
            # All images
            all_images = response.css('#pic img::attr(src)').getall()
            if not all_images:
                all_images = response.css('.pic img::attr(src)').getall()
            item['all_images'] = all_images
            item['image_urls'] = all_images
            
            # Seller information
            seller_element = response.css('span.mbg-nw::text').get()
            if not seller_element:
                seller_element = response.css('span.x-seller-username span::text').get()
            if not seller_element:
                seller_element = response.css('div.x-seller-info__name span::text').get()
            item['seller_name'] = seller_element.strip() if seller_element else ''
            
            # Seller feedback
            feedback_element = response.css('.mbg-l a::text').get()
            if feedback_element and '(' in feedback_element:
                item['seller_feedback_score'] = re.search(r'\((\d+)\)', feedback_element)
                item['seller_feedback_score'] = item['seller_feedback_score'].group(1) if item['seller_feedback_score'] else ''
                
                # Feedback percentage
                percentage_match = re.search(r'(\d+\.?\d*)%', feedback_element)
                item['seller_feedback_percentage'] = percentage_match.group(1) if percentage_match else ''
            else:
                item['seller_feedback_score'] = ''
                item['seller_feedback_percentage'] = ''
            
            # Seller location
            location_element = response.css('.u-flL.itemprop::text').get()
            item['seller_location'] = location_element.strip() if location_element else ''
            
            # Quantity available
            quantity_element = response.css('#qtySubTxt::text').get()
            if quantity_element:
                quantity_match = re.search(r'(\d+)', quantity_element)
                item['quantity_available'] = quantity_match.group(1) if quantity_match else ''
            else:
                item['quantity_available'] = ''
            
            # Items sold
            sold_element = response.css('.notranslate.vi-acc-del-range::text').get()
            if sold_element and 'sold' in sold_element.lower():
                sold_match = re.search(r'(\d+)', sold_element)
                item['quantity_sold'] = sold_match.group(1) if sold_match else ''
            else:
                item['quantity_sold'] = ''
            
            # Watchers
            watchers_element = response.css('.watchers::text').get()
            if watchers_element:
                watchers_match = re.search(r'(\d+)', watchers_element)
                item['watchers_count'] = watchers_match.group(1) if watchers_match else ''
            else:
                item['watchers_count'] = ''
            
            # Auction information
            auction_element = response.css('.notranslate.vi-price .u-flL')
            if auction_element and 'bid' in auction_element.css('::text').get('').lower():
                item['auction_type'] = 'auction'
                bid_text = auction_element.css('::text').get('')
                bid_match = re.search(r'(\d+)', bid_text)
                item['bid_count'] = bid_match.group(1) if bid_match else ''
                
                # Time left
                time_left_element = response.css('.timeMs::text').get()
                item['time_left'] = time_left_element.strip() if time_left_element else ''
            else:
                item['auction_type'] = 'fixed_price'
                item['bid_count'] = ''
                item['time_left'] = ''
            
            # Shipping information
            shipping_cost = response.css('#fshippingCost .notranslate::text').get()
            if not shipping_cost:
                shipping_cost = response.css('.vi-price .ship-cost::text').get()
            
            if shipping_cost:
                if 'free' in shipping_cost.lower():
                    item['shipping_costs'] = 'Free'
                else:
                    item['shipping_costs'] = shipping_cost.strip()
            else:
                item['shipping_costs'] = ''
            
            # Handling time
            handling_element = response.css('.vi-acc-del-range::text').get()
            item['handling_time'] = handling_element.strip() if handling_element else ''
            
            # Ships from
            ships_from = response.css('.ux-labels-values__values-content::text').get()
            item['ships_from'] = ships_from.strip() if ships_from else ''
            
            # Return policy
            returns_element = response.css('.u-flL.condText a::text').get()
            if returns_element and 'return' in returns_element.lower():
                item['returns_accepted'] = True
                
                # Return period
                period_match = re.search(r'(\d+)\s*day', returns_element, re.IGNORECASE)
                item['return_period'] = period_match.group(1) if period_match else ''
            else:
                item['returns_accepted'] = False
                item['return_period'] = ''
            
            # Item specifics
            item_specifics = {}
            specific_rows = response.css('.u-flL.uxLabelsValues tr')
            for row in specific_rows:
                label = row.css('td:first-child::text').get()
                value = row.css('td:last-child::text').get()
                if label and value:
                    item_specifics[label.strip().rstrip(':')] = value.strip()
            
            item['item_specifics'] = json.dumps(item_specifics) if item_specifics else ''
            
            # Category information
            breadcrumb_elements = response.css('.seo-breadcrumb-text::text').getall()
            if breadcrumb_elements:
                item['category_path'] = ' > '.join([elem.strip() for elem in breadcrumb_elements])
                item['primary_category'] = breadcrumb_elements[-1].strip() if breadcrumb_elements else ''
            else:
                item['category_path'] = ''
                item['primary_category'] = ''
            
            # Special features
            item['ebay_plus'] = bool(response.css('.ebayplus'))
            item['fast_n_free'] = bool(response.css('.fast-n-free'))
            item['authenticity_guarantee'] = bool(response.css('.authenticity-guarantee'))
            item['top_rated_seller'] = bool(response.css('.top-rated'))
            
            # Payment methods
            payment_methods = response.css('.payDet .paymentMethods::text').getall()
            item['payment_methods'] = ', '.join(payment_methods) if payment_methods else ''
            
            # Additional fields with defaults
            item['savings_amount'] = ''
            item['savings_percentage'] = ''
            item['currency'] = 'USD'  # Default, could be extracted from price
            item['listing_type'] = item['auction_type']
            item['listing_format'] = item['auction_type']
            item['listing_duration'] = ''
            item['start_time'] = ''
            item['end_time'] = ''
            item['reserve_price'] = ''
            item['reserve_met'] = False
            item['no_reserve'] = True
            item['buy_it_now_price'] = ''
            item['sponsored_listing'] = False
            item['seller_verified'] = False
            item['seller_business_type'] = ''
            item['seller_member_since'] = ''
            item['seller_other_items_count'] = ''
            item['credit_cards_accepted'] = True
            item['paypal_accepted'] = True
            item['financing_available'] = False
            item['expedited_shipping'] = False
            item['global_shipping'] = False
            item['international_shipping'] = False
            item['restocking_fee'] = ''
            item['return_shipping_paid_by'] = ''
            item['return_policy_details'] = ''
            item['ships_to_locations'] = ''
            item['compatibility'] = ''
            item['color'] = ''
            item['size'] = ''
            item['isbn'] = ''
            item['product_identifiers'] = ''
            item['price_history'] = ''
            item['bid_history'] = ''
            item['suggested_items'] = ''
            item['similar_items'] = ''
            item['related_categories'] = ''
            item['secondary_category'] = ''
            item['category_id'] = ''
            item['views_count'] = ''
            item['review_count'] = ''
            item['review_summary'] = ''
            item['item_rating'] = ''
            item['gallery_images'] = []
            
            self.logger.info(f"Extracted product: {item.get('product_title', 'Unknown')} - {item.get('current_price', 'N/A')}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error extracting product data: {e}")
            return None
    
    def _extract_item_id(self, url):
        """Extract item ID from eBay URL"""
        try:
            # Parse URL to get item ID
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            # Look for item ID in path
            for part in path_parts:
                if part.isdigit() and len(part) >= 10:  # eBay item IDs are typically 10+ digits
                    return part
            
            # If not found in path, check query parameters
            query_params = parse_qs(parsed_url.query)
            if 'item' in query_params:
                return query_params['item'][0]
            
            return ''
        except Exception as e:
            self.logger.error(f"Error extracting item ID from URL {url}: {e}")
            return ''
    
    def _extract_item_specific(self, response, label):
        """Extract specific item detail by label"""
        try:
            # Look for the label in item specifics
            specific_rows = response.css('.u-flL.uxLabelsValues tr')
            for row in specific_rows:
                row_label = row.css('td:first-child::text').get()
                if row_label and label.lower() in row_label.lower():
                    value = row.css('td:last-child::text').get()
                    return value.strip() if value else ''
            return ''
        except Exception as e:
            self.logger.error(f"Error extracting item specific {label}: {e}")
            return ''
    
    def _clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ''
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned 