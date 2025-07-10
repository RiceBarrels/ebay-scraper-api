# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
from itemadapter import is_item, ItemAdapter
import random
import time
import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs
import json


class EbayScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class EbayScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        
        # Add eBay-specific headers
        request.headers.setdefault('Referer', 'https://www.ebay.com/')
        request.headers.setdefault('Origin', 'https://www.ebay.com')
        
        # Add random delay
        if hasattr(spider, 'custom_delay'):
            time.sleep(random.uniform(0.5, spider.custom_delay))
        
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        
        # Handle eBay security challenges and redirects
        if 'sec.ebay.com' in response.url or 'signin.ebay.com' in response.url:
            spider.logger.warning(f"Security challenge detected: {response.url}")
            # Return original request for retry with different parameters
            retry_request = request.copy()
            retry_request.headers['User-Agent'] = self._get_random_user_agent(spider)
            return retry_request
        
        if response.status == 429:
            spider.logger.warning(f"Rate limited on {response.url}")
            # Return request for retry with increased delay
            retry_request = request.copy()
            retry_request.dont_filter = True
            retry_request.priority = request.priority + 1
            retry_request.meta['download_delay'] = random.uniform(5, 10)
            return retry_request
        
        # Handle blocked by country/region
        if response.status == 403 and 'blocked' in response.text.lower():
            spider.logger.warning(f"Blocked by region/country: {response.url}")
        
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        spider.logger.error(f"Download exception for {request.url}: {exception}")
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
    
    def _get_random_user_agent(self, spider):
        """Get random user agent from settings"""
        user_agents = getattr(spider.settings, 'USER_AGENT_LIST', [])
        if user_agents:
            return random.choice(user_agents)
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


class UserAgentRotationMiddleware:
    """Middleware to rotate User-Agent headers"""
    
    def __init__(self, user_agent_list):
        self.user_agent_list = user_agent_list

    @classmethod
    def from_crawler(cls, crawler):
        user_agent_list = crawler.settings.get('USER_AGENT_LIST', [])
        return cls(user_agent_list=user_agent_list)

    def process_request(self, request, spider):
        if self.user_agent_list:
            ua = random.choice(self.user_agent_list)
            request.headers['User-Agent'] = ua
        return None


class EbayLocationMiddleware:
    """Middleware to handle eBay location-specific settings"""
    
    def __init__(self, default_location):
        self.default_location = default_location
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        default_location = crawler.settings.get('DEFAULT_LOCATION', {'country': 'US'})
        return cls(default_location=default_location)
    
    def process_request(self, request, spider):
        # Add location-specific parameters to eBay requests
        if 'ebay.com' in request.url:
            # Add country/region specific headers
            country = getattr(spider, 'country', self.default_location.get('country', 'US'))
            
            if country == 'US':
                request.headers['Accept-Language'] = 'en-US,en;q=0.9'
            elif country == 'UK':
                request.headers['Accept-Language'] = 'en-GB,en;q=0.9'
            elif country == 'DE':
                request.headers['Accept-Language'] = 'de-DE,de;q=0.9,en;q=0.8'
            elif country == 'FR':
                request.headers['Accept-Language'] = 'fr-FR,fr;q=0.9,en;q=0.8'
            
            # Add location cookies if needed
            if hasattr(spider, 'location_preferences'):
                location_prefs = spider.location_preferences
                if 'zip_code' in location_prefs:
                    request.cookies['zip'] = location_prefs['zip_code']
        
        return None


class EbayDataExtractionMiddleware:
    """Middleware to pre-process eBay responses and extract embedded data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, request, response, spider):
        if 'ebay.com' in response.url:
            # Extract embedded JSON data from eBay pages
            extracted_data = self._extract_ebay_data(response)
            if extracted_data:
                # Store extracted data in response meta for spider access
                response.meta['ebay_data'] = extracted_data
        
        return response
    
    def _extract_ebay_data(self, response):
        """Extract embedded JSON data from eBay pages"""
        try:
            content = response.text
            
            # Look for different eBay data patterns
            patterns = [
                r'raptor\.model = ({.*?});',
                r'window\.__PRELOADED_STATE__ = ({.*?});',
                r'window\.MSKU = ({.*?});',
                r'var _cfg = ({.*?});',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting eBay data: {e}")
            return None


class EbayRetryMiddleware:
    """Custom retry middleware for eBay-specific errors"""
    
    def __init__(self, retry_times=3):
        self.retry_times = retry_times
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        retry_times = crawler.settings.getint('RETRY_TIMES', 3)
        return cls(retry_times=retry_times)
    
    def process_response(self, request, response, spider):
        if response.status in [429, 503, 502, 500, 403]:
            retry_times = request.meta.get('retry_times', 0) + 1
            
            if retry_times <= self.retry_times:
                self.logger.warning(
                    f"Retrying {request.url} (retry {retry_times}/{self.retry_times}) - Status: {response.status}"
                )
                
                # Increase delay for retries
                delay = min(2 ** retry_times, 60)  # Exponential backoff, max 60s
                time.sleep(delay)
                
                retry_request = request.copy()
                retry_request.meta['retry_times'] = retry_times
                retry_request.dont_filter = True
                
                # Change user agent on retry
                user_agents = spider.settings.get('USER_AGENT_LIST', [])
                if user_agents:
                    retry_request.headers['User-Agent'] = random.choice(user_agents)
                
                return retry_request
            else:
                self.logger.error(f"Max retries exceeded for {request.url}")
        
        return response


class EbayCaptchaDetectionMiddleware:
    """Middleware to detect and handle CAPTCHA challenges"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, request, response, spider):
        # Check for CAPTCHA indicators
        if self._has_captcha(response):
            self.logger.warning(f"CAPTCHA detected on {response.url}")
            # You could integrate with CAPTCHA solving services here
            # For now, we'll just log and continue
        
        return response
    
    def _has_captcha(self, response):
        """Check if response contains CAPTCHA challenge"""
        content = response.text.lower()
        captcha_indicators = [
            'captcha',
            'security challenge',
            'verify you are human',
            'robot verification',
            'please complete the security check'
        ]
        return any(indicator in content for indicator in captcha_indicators)


class EbaySecurityBypassMiddleware:
    """Middleware to handle eBay security measures"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, request, response, spider):
        # Handle security redirects
        if self._is_security_page(response):
            return self._handle_security_page(request, response, spider)
        
        # Handle bot detection
        if self._is_bot_detection(response):
            return self._handle_bot_detection(request, response, spider)
        
        return response
    
    def _is_security_page(self, response):
        """Check if response is a security challenge page"""
        return (
            'sec.ebay.com' in response.url or
            'security check' in response.text.lower() or
            'verify your identity' in response.text.lower()
        )
    
    def _is_bot_detection(self, response):
        """Check if response indicates bot detection"""
        content = response.text.lower()
        bot_indicators = [
            'automated traffic',
            'suspicious activity',
            'bot detection',
            'unusual browsing behavior'
        ]
        return any(indicator in content for indicator in bot_indicators)
    
    def _handle_security_page(self, request, response, spider):
        """Handle security challenge pages"""
        self.logger.info(f"Handling security page: {response.url}")
        
        # Try to extract the continue URL or redirect
        # This is a simplified implementation
        return response
    
    def _handle_bot_detection(self, request, response, spider):
        """Handle bot detection pages"""
        self.logger.info(f"Bot detection on: {response.url}")
        
        # Increase delay and change user agent
        retry_request = request.copy()
        retry_request.meta['download_delay'] = random.uniform(10, 20)
        
        user_agents = spider.settings.get('USER_AGENT_LIST', [])
        if user_agents:
            retry_request.headers['User-Agent'] = random.choice(user_agents)
        
        return retry_request


class EbayPriceExtractionMiddleware:
    """Middleware to help with price extraction and normalization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, request, response, spider):
        if 'ebay.com' in response.url:
            # Extract price-related data
            price_data = self._extract_price_data(response)
            if price_data:
                response.meta['price_data'] = price_data
        
        return response
    
    def _extract_price_data(self, response):
        """Extract price-related information from eBay pages"""
        try:
            # Look for structured data with prices
            price_patterns = [
                r'"price":\s*"([^"]+)"',
                r'"amount":\s*"([^"]+)"',
                r'"value":\s*([0-9.]+)',
            ]
            
            prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, response.text)
                prices.extend(matches)
            
            return {'extracted_prices': prices} if prices else None
        except Exception as e:
            self.logger.error(f"Error extracting price data: {e}")
            return None 