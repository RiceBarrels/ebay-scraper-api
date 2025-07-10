# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import csv
import json
import re
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import os
from price_parser import Price


class EbayDataValidationPipeline:
    """Pipeline to validate eBay scraped data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Required fields validation
        required_fields = {
            'EbaySearchItem': ['product_title', 'product_url', 'current_price'],
            'EbayProductItem': ['product_title', 'product_url'],  # Made current_price optional
            'EbaySellerItem': ['seller_name', 'seller_id'],
            'EbayCategoryItem': ['category_name', 'category_id']
        }
        
        item_type = type(item).__name__
        if item_type in required_fields:
            for field in required_fields[item_type]:
                if not adapter.get(field):
                    raise DropItem(f"Missing required field '{field}' in {item_type}")
        
        # URL validation
        if adapter.get('product_url') and not self._is_valid_ebay_url(adapter['product_url']):
            raise DropItem(f"Invalid eBay URL: {adapter.get('product_url')}")
        
        # Price validation
        if adapter.get('current_price') and not self._is_valid_price(adapter['current_price']):
            self.logger.warning(f"Invalid price format: {adapter.get('current_price')}")
        
        self.logger.debug(f"Validated {item_type}: {adapter.get('product_title', 'Unknown')}")
        return item
    
    def _is_valid_ebay_url(self, url):
        """Validate if URL is a valid eBay URL"""
        if not url:
            return False
        
        ebay_domains = ['ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.ca', 'ebay.com.au', 'ebay.fr']
        try:
            parsed = urlparse(url)
            return any(domain in parsed.netloc for domain in ebay_domains)
        except:
            return False
    
    def _is_valid_price(self, price_str):
        """Validate if price string is in a valid format"""
        if not price_str:
            return False
        
        try:
            # Try to parse price using price-parser
            price = Price.fromstring(price_str)
            return price.amount is not None
        except:
            return False


class EbayDataCleaningPipeline:
    """Pipeline to clean and normalize eBay data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean title and description
        if adapter.get('product_title'):
            adapter['product_title'] = self._clean_text(adapter['product_title'])
        
        if adapter.get('description_full'):
            adapter['description_full'] = self._clean_text(adapter['description_full'])
        
        if adapter.get('short_description'):
            adapter['short_description'] = self._clean_text(adapter['short_description'])
        
        # Clean seller name
        if adapter.get('seller_name'):
            adapter['seller_name'] = self._clean_text(adapter['seller_name'])
        
        # Clean condition
        if adapter.get('condition'):
            adapter['condition'] = self._normalize_condition(adapter['condition'])
        
        # Extract item ID from URL
        if adapter.get('product_url') and not adapter.get('product_id'):
            adapter['product_id'] = self._extract_item_id(adapter['product_url'])
        
        # Clean shipping information
        if adapter.get('shipping_cost'):
            adapter['shipping_cost'] = self._clean_shipping_cost(adapter['shipping_cost'])
        
        # Clean location
        if adapter.get('seller_location'):
            adapter['seller_location'] = self._clean_location(adapter['seller_location'])
        
        # Add scraped timestamp
        adapter['scraped_at'] = datetime.now().isoformat()
        adapter['scraper_version'] = '1.0.0'
        
        return item
    
    def _clean_text(self, text):
        """Clean text by removing extra whitespace and special characters"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove or replace special characters
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
        
        return text
    
    def _normalize_condition(self, condition):
        """Normalize condition values"""
        if not condition:
            return ''
        
        condition_lower = condition.lower().strip()
        
        condition_mapping = {
            'new': 'New',
            'brand new': 'New',
            'new with tags': 'New',
            'new without tags': 'New',
            'new other': 'New (Other)',
            'open box': 'Open Box',
            'manufacturer refurbished': 'Refurbished',
            'seller refurbished': 'Refurbished',
            'used': 'Used',
            'pre-owned': 'Used',
            'very good': 'Used - Very Good',
            'good': 'Used - Good',
            'acceptable': 'Used - Acceptable',
            'for parts or not working': 'For Parts',
            'for parts': 'For Parts',
            'not working': 'For Parts'
        }
        
        for key, value in condition_mapping.items():
            if key in condition_lower:
                return value
        
        return condition.title()
    
    def _extract_item_id(self, url):
        """Extract eBay item ID from URL"""
        if not url:
            return ''
        
        try:
            # eBay item URLs typically contain the item ID
            # Format: https://www.ebay.com/itm/ITEM_ID or /itm/title/ITEM_ID
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
    
    def _clean_shipping_cost(self, shipping_cost):
        """Clean and normalize shipping cost"""
        if not shipping_cost:
            return ''
        
        shipping_lower = shipping_cost.lower().strip()
        
        if any(word in shipping_lower for word in ['free', 'no cost', 'no charge']):
            return 'Free'
        elif 'calculated' in shipping_lower:
            return 'Calculated'
        elif 'local pickup' in shipping_lower:
            return 'Local Pickup'
        else:
            return shipping_cost.strip()
    
    def _clean_location(self, location):
        """Clean seller location"""
        if not location:
            return ''
        
        # Remove extra whitespace and common location prefixes
        location = location.strip()
        location = re.sub(r'^(from|ships from|located in)\s*', '', location, flags=re.IGNORECASE)
        
        return location


class EbayPriceNormalizationPipeline:
    """Pipeline to normalize and parse eBay prices"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Normalize current price
        if adapter.get('current_price'):
            price_info = self._parse_price(adapter['current_price'])
            adapter['current_price_value'] = price_info['amount']
            adapter['currency'] = price_info['currency']
        
        # Normalize original price
        if adapter.get('original_price'):
            original_price_info = self._parse_price(adapter['original_price'])
            adapter['original_price_value'] = original_price_info['amount']
        
        # Calculate savings
        if (adapter.get('current_price_value') and adapter.get('original_price_value') and
            adapter['current_price_value'] < adapter['original_price_value']):
            
            current = float(adapter['current_price_value'])
            original = float(adapter['original_price_value'])
            
            adapter['savings_amount'] = round(original - current, 2)
            adapter['savings_percentage'] = round(((original - current) / original) * 100, 1)
        
        # Normalize shipping cost
        if adapter.get('shipping_cost') and adapter['shipping_cost'] not in ['Free', 'Calculated', 'Local Pickup']:
            shipping_info = self._parse_price(adapter['shipping_cost'])
            adapter['shipping_cost_value'] = shipping_info['amount']
        
        return item
    
    def _parse_price(self, price_str):
        """Parse price string and extract amount and currency"""
        try:
            price = Price.fromstring(str(price_str))
            return {
                'amount': float(price.amount) if price.amount else 0.0,
                'currency': price.currency or 'USD'
            }
        except Exception as e:
            self.logger.warning(f"Could not parse price '{price_str}': {e}")
            return {'amount': 0.0, 'currency': 'USD'}


class EbayDataEnrichmentPipeline:
    """Pipeline to enrich eBay data with additional information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Categorize listing type
        if adapter.get('price_type'):
            adapter['listing_category'] = self._categorize_listing(adapter['price_type'])
        
        # Add seller tier based on feedback
        if adapter.get('seller_feedback_score'):
            adapter['seller_tier'] = self._categorize_seller(adapter['seller_feedback_score'])
        
        # Add price range category
        if adapter.get('current_price_value'):
            adapter['price_range'] = self._categorize_price(adapter['current_price_value'])
        
        # Extract brand from title if not available
        if not adapter.get('brand') and adapter.get('product_title'):
            adapter['brand'] = self._extract_brand(adapter['product_title'])
        
        # Add deal indicators
        adapter['is_deal'] = self._is_good_deal(adapter)
        
        # Add URL components
        if adapter.get('product_url'):
            parsed_url = urlparse(adapter['product_url'])
            adapter['ebay_site'] = parsed_url.netloc
        
        return item
    
    def _categorize_listing(self, price_type):
        """Categorize listing based on price type"""
        if not price_type:
            return 'unknown'
        
        price_type_lower = price_type.lower()
        
        if 'auction' in price_type_lower:
            return 'auction'
        elif 'buy' in price_type_lower and 'now' in price_type_lower:
            return 'fixed_price'
        elif 'offer' in price_type_lower:
            return 'best_offer'
        else:
            return 'other'
    
    def _categorize_seller(self, feedback_score):
        """Categorize seller based on feedback score"""
        try:
            score = int(feedback_score) if feedback_score else 0
            
            if score >= 10000:
                return 'power_seller'
            elif score >= 1000:
                return 'experienced'
            elif score >= 100:
                return 'established'
            elif score >= 10:
                return 'newcomer'
            else:
                return 'new'
        except:
            return 'unknown'
    
    def _categorize_price(self, price_value):
        """Categorize price into ranges"""
        try:
            price = float(price_value) if price_value else 0
            
            if price < 10:
                return 'under_10'
            elif price < 25:
                return '10_to_25'
            elif price < 50:
                return '25_to_50'
            elif price < 100:
                return '50_to_100'
            elif price < 250:
                return '100_to_250'
            elif price < 500:
                return '250_to_500'
            else:
                return 'over_500'
        except:
            return 'unknown'
    
    def _extract_brand(self, title):
        """Extract brand from product title"""
        if not title:
            return ''
        
        # Common brand patterns (this is a simplified list)
        brands = [
            'Apple', 'Samsung', 'Nike', 'Adidas', 'Sony', 'Canon', 'Nikon',
            'Dell', 'HP', 'Lenovo', 'Microsoft', 'Google', 'Amazon',
            'Coach', 'Gucci', 'Louis Vuitton', 'Prada', 'Rolex'
        ]
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        return ''
    
    def _is_good_deal(self, adapter):
        """Determine if item is a good deal based on various factors"""
        indicators = []
        
        # Check if there are savings
        if adapter.get('savings_percentage') and float(adapter['savings_percentage']) > 20:
            indicators.append('high_discount')
        
        # Check for free shipping
        if adapter.get('shipping_cost') == 'Free':
            indicators.append('free_shipping')
        
        # Check seller rating
        if adapter.get('seller_feedback_percentage'):
            try:
                rating = float(adapter['seller_feedback_percentage'])
                if rating >= 98:
                    indicators.append('top_seller')
            except:
                pass
        
        return len(indicators) >= 2  # Consider it a deal if 2+ indicators


class EbayDuplicatesPipeline:
    """Pipeline to filter out duplicate items"""
    
    def __init__(self):
        self.ids_seen = set()
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Create unique identifier based on item type
        item_type = type(item).__name__
        
        if item_type == 'EbaySearchItem':
            unique_id = adapter.get('product_id') or adapter.get('listing_id') or adapter.get('product_url')
        elif item_type == 'EbayProductItem':
            unique_id = adapter.get('product_id') or adapter.get('listing_id')
        elif item_type == 'EbaySellerItem':
            unique_id = adapter.get('seller_id')
        elif item_type == 'EbayCategoryItem':
            unique_id = adapter.get('category_id')
        else:
            unique_id = str(item)
        
        if unique_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {unique_id}")
        else:
            self.ids_seen.add(unique_id)
            return item


class EbayCSVExportPipeline:
    """Pipeline to export eBay data to CSV files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.files = {}
        self.writers = {}
    
    def open_spider(self, spider):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize CSV files for different item types
        self.files['search'] = open('data/ebay_search_results.csv', 'w', newline='', encoding='utf-8')
        self.files['product'] = open('data/ebay_products.csv', 'w', newline='', encoding='utf-8')
        self.files['seller'] = open('data/ebay_sellers.csv', 'w', newline='', encoding='utf-8')
        self.files['category'] = open('data/ebay_categories.csv', 'w', newline='', encoding='utf-8')
        
        # CSV headers for each file type
        search_headers = [
            'product_id', 'listing_id', 'product_title', 'product_url', 'current_price',
            'main_image', 'condition', 'seller_name', 'seller_location', 'shipping_costs',
            'auction_type', 'listing_type', 'scraped_at', 'scraper_version'
        ]
        
        product_headers = [
            'product_id', 'listing_id', 'product_title', 'product_url', 'current_price',
            'main_image', 'condition', 'seller_name', 'seller_location', 'shipping_costs',
            'auction_type', 'listing_type', 'scraped_at', 'scraper_version'
        ]
        
        seller_headers = [
            'seller_id', 'seller_name', 'seller_url', 'feedback_score', 'feedback_percentage',
            'member_since', 'location', 'top_rated_seller', 'items_for_sale', 'scraped_at'
        ]
        
        category_headers = [
            'category_id', 'category_name', 'category_url', 'parent_category', 'item_count', 'scraped_at'
        ]
        
        # Create CSV writers
        self.writers['search'] = csv.DictWriter(self.files['search'], fieldnames=search_headers)
        self.writers['product'] = csv.DictWriter(self.files['product'], fieldnames=product_headers)
        self.writers['seller'] = csv.DictWriter(self.files['seller'], fieldnames=seller_headers)
        self.writers['category'] = csv.DictWriter(self.files['category'], fieldnames=category_headers)
        
        # Write headers
        for writer in self.writers.values():
            writer.writeheader()
    
    def close_spider(self, spider):
        for file in self.files.values():
            file.close()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_type = type(item).__name__
        
        try:
            if item_type == 'EbaySearchItem':
                # Only include fields that are in our headers
                search_data = {
                    'product_id': adapter.get('product_id', ''),
                    'listing_id': adapter.get('listing_id', ''),
                    'product_title': adapter.get('product_title', ''),
                    'product_url': adapter.get('product_url', ''),
                    'current_price': adapter.get('current_price', ''),
                    'main_image': adapter.get('main_image', ''),
                    'condition': adapter.get('condition', ''),
                    'seller_name': adapter.get('seller_name', ''),
                    'seller_location': adapter.get('seller_location', ''),
                    'shipping_costs': adapter.get('shipping_costs', ''),
                    'auction_type': adapter.get('auction_type', ''),
                    'listing_type': adapter.get('listing_type', ''),
                    'scraped_at': adapter.get('scraped_at', ''),
                    'scraper_version': adapter.get('scraper_version', '')
                }
                self.writers['search'].writerow(search_data)
            elif item_type == 'EbayProductItem':
                # Only include fields that are in our headers
                product_data = {
                    'product_id': adapter.get('product_id', ''),
                    'listing_id': adapter.get('listing_id', ''),
                    'product_title': adapter.get('product_title', ''),
                    'product_url': adapter.get('product_url', ''),
                    'current_price': adapter.get('current_price', ''),
                    'main_image': adapter.get('main_image', ''),
                    'condition': adapter.get('condition', ''),
                    'seller_name': adapter.get('seller_name', ''),
                    'seller_location': adapter.get('seller_location', ''),
                    'shipping_costs': adapter.get('shipping_costs', ''),
                    'auction_type': adapter.get('auction_type', ''),
                    'listing_type': adapter.get('listing_type', ''),
                    'scraped_at': adapter.get('scraped_at', ''),
                    'scraper_version': adapter.get('scraper_version', '')
                }
                self.writers['product'].writerow(product_data)
            elif item_type == 'EbaySellerItem':
                self.writers['seller'].writerow(dict(adapter))
            elif item_type == 'EbayCategoryItem':
                self.writers['category'].writerow(dict(adapter))
            
            self.logger.debug(f"Exported {item_type} to CSV")
        except Exception as e:
            self.logger.error(f"Error exporting {item_type} to CSV: {e}")
        
        return item


class EbayJSONExportPipeline:
    """Pipeline to export eBay data to JSON files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data = {
            'search': [],
            'product': [],
            'seller': [],
            'category': []
        }
    
    def close_spider(self, spider):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Export each data type to separate JSON files
        for data_type, items in self.data.items():
            if items:
                filename = f'data/ebay_{data_type}_data.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Exported {len(items)} {data_type} items to {filename}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_type = type(item).__name__
        
        try:
            if item_type == 'EbaySearchItem':
                self.data['search'].append(dict(adapter))
            elif item_type == 'EbayProductItem':
                self.data['product'].append(dict(adapter))
            elif item_type == 'EbaySellerItem':
                self.data['seller'].append(dict(adapter))
            elif item_type == 'EbayCategoryItem':
                self.data['category'].append(dict(adapter))
        except Exception as e:
            self.logger.error(f"Error processing {item_type} for JSON export: {e}")
        
        return item 