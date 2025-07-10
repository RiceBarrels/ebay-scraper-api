# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemadapter import ItemAdapter


class EbaySearchItem(scrapy.Item):
    """Item for eBay search results and listing data"""
    
    # Basic Product Information
    product_title = scrapy.Field()
    product_url = scrapy.Field()
    product_id = scrapy.Field()
    listing_id = scrapy.Field()
    
    # Pricing Information
    current_price = scrapy.Field()
    current_price_value = scrapy.Field()
    currency = scrapy.Field()
    original_price = scrapy.Field()
    discount_percentage = scrapy.Field()
    price_type = scrapy.Field()  # auction, buy_it_now, best_offer
    
    # Auction/Bidding Information
    bid_count = scrapy.Field()
    time_left = scrapy.Field()
    end_time = scrapy.Field()
    buy_it_now_price = scrapy.Field()
    reserve_met = scrapy.Field()
    
    # Product Details
    condition = scrapy.Field()
    condition_description = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    
    # Images and Media
    main_image = scrapy.Field()
    thumbnail_image = scrapy.Field()
    image_count = scrapy.Field()
    
    # Seller Information
    seller_name = scrapy.Field()
    seller_id = scrapy.Field()
    seller_feedback_score = scrapy.Field()
    seller_feedback_percentage = scrapy.Field()
    seller_location = scrapy.Field()
    seller_verified = scrapy.Field()
    top_rated_seller = scrapy.Field()
    
    # Shipping Information
    shipping_cost = scrapy.Field()
    shipping_type = scrapy.Field()  # free, calculated, flat_rate
    ships_from = scrapy.Field()
    ships_to = scrapy.Field()
    handling_time = scrapy.Field()
    fast_n_free = scrapy.Field()
    
    # Product Specifics
    quantity_available = scrapy.Field()
    items_sold = scrapy.Field()
    watchers = scrapy.Field()
    listing_type = scrapy.Field()  # auction, fixed_price, classified
    listing_format = scrapy.Field()
    
    # Search Context
    search_query = scrapy.Field()
    search_position = scrapy.Field()
    search_page = scrapy.Field()
    search_sort = scrapy.Field()
    
    # Additional Features
    returns_accepted = scrapy.Field()
    return_period = scrapy.Field()
    authenticity_guarantee = scrapy.Field()
    ebay_plus = scrapy.Field()
    sponsored = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    scraper_version = scrapy.Field()


class EbayProductItem(scrapy.Item):
    """Item for detailed eBay product information"""
    
    # Basic Product Information
    product_id = scrapy.Field()
    listing_id = scrapy.Field()
    product_title = scrapy.Field()
    product_url = scrapy.Field()
    
    # Detailed Description
    description_full = scrapy.Field()
    description_html = scrapy.Field()
    short_description = scrapy.Field()
    
    # Pricing Details
    current_price = scrapy.Field()
    current_price_value = scrapy.Field()
    currency = scrapy.Field()
    original_price = scrapy.Field()
    savings_amount = scrapy.Field()
    savings_percentage = scrapy.Field()
    price_history = scrapy.Field()
    
    # Auction Information
    auction_type = scrapy.Field()
    bid_count = scrapy.Field()
    bid_history = scrapy.Field()
    time_left = scrapy.Field()
    end_time = scrapy.Field()
    start_time = scrapy.Field()
    reserve_price = scrapy.Field()
    reserve_met = scrapy.Field()
    buy_it_now_price = scrapy.Field()
    
    # Product Specifications
    condition = scrapy.Field()
    condition_details = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    mpn = scrapy.Field()  # Manufacturer Part Number
    upc = scrapy.Field()
    ean = scrapy.Field()
    isbn = scrapy.Field()
    color = scrapy.Field()
    size = scrapy.Field()
    
    # Category Information
    primary_category = scrapy.Field()
    secondary_category = scrapy.Field()
    category_path = scrapy.Field()
    category_id = scrapy.Field()
    
    # Item Specifics
    item_specifics = scrapy.Field()  # Dict of all specific attributes
    product_identifiers = scrapy.Field()
    compatibility = scrapy.Field()
    
    # Images and Media
    main_image = scrapy.Field()
    all_images = scrapy.Field()
    image_urls = scrapy.Field()
    gallery_images = scrapy.Field()
    
    # Seller Details
    seller_name = scrapy.Field()
    seller_id = scrapy.Field()
    seller_feedback_score = scrapy.Field()
    seller_feedback_percentage = scrapy.Field()
    seller_member_since = scrapy.Field()
    seller_location = scrapy.Field()
    seller_business_type = scrapy.Field()
    seller_verified = scrapy.Field()
    top_rated_seller = scrapy.Field()
    seller_other_items_count = scrapy.Field()
    
    # Shipping Information
    shipping_options = scrapy.Field()
    shipping_costs = scrapy.Field()
    handling_time = scrapy.Field()
    ships_from = scrapy.Field()
    ships_to_locations = scrapy.Field()
    international_shipping = scrapy.Field()
    expedited_shipping = scrapy.Field()
    
    # Return Policy
    returns_accepted = scrapy.Field()
    return_period = scrapy.Field()
    return_policy_details = scrapy.Field()
    return_shipping_paid_by = scrapy.Field()
    restocking_fee = scrapy.Field()
    
    # Payment Information
    payment_methods = scrapy.Field()
    paypal_accepted = scrapy.Field()
    credit_cards_accepted = scrapy.Field()
    financing_available = scrapy.Field()
    
    # Quantity and Availability
    quantity_available = scrapy.Field()
    quantity_sold = scrapy.Field()
    items_sold_recently = scrapy.Field()
    watchers_count = scrapy.Field()
    views_count = scrapy.Field()
    
    # Listing Information
    listing_type = scrapy.Field()
    listing_format = scrapy.Field()
    listing_start_time = scrapy.Field()
    listing_end_time = scrapy.Field()
    listing_duration = scrapy.Field()
    
    # Special Features
    ebay_plus = scrapy.Field()
    fast_n_free = scrapy.Field()
    authenticity_guarantee = scrapy.Field()
    global_shipping = scrapy.Field()
    no_reserve = scrapy.Field()
    sponsored_listing = scrapy.Field()
    
    # Reviews and Ratings
    item_rating = scrapy.Field()
    review_count = scrapy.Field()
    review_summary = scrapy.Field()
    
    # Similar Items
    similar_items = scrapy.Field()
    related_categories = scrapy.Field()
    suggested_items = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    scraper_version = scrapy.Field()


class EbaySellerItem(scrapy.Item):
    """Item for eBay seller information and statistics"""
    
    # Basic Seller Information
    seller_id = scrapy.Field()
    seller_name = scrapy.Field()
    seller_url = scrapy.Field()
    username = scrapy.Field()
    
    # Profile Information
    profile_image = scrapy.Field()
    business_name = scrapy.Field()
    business_type = scrapy.Field()
    member_since = scrapy.Field()
    location = scrapy.Field()
    
    # Feedback and Ratings
    feedback_score = scrapy.Field()
    feedback_percentage = scrapy.Field()
    positive_feedback = scrapy.Field()
    neutral_feedback = scrapy.Field()
    negative_feedback = scrapy.Field()
    feedback_count_12_months = scrapy.Field()
    
    # Seller Performance
    top_rated_seller = scrapy.Field()
    fast_n_free_seller = scrapy.Field()
    ebay_plus_seller = scrapy.Field()
    powerseller = scrapy.Field()
    verified_seller = scrapy.Field()
    
    # Business Information
    business_address = scrapy.Field()
    vat_id = scrapy.Field()
    return_policy = scrapy.Field()
    shipping_policy = scrapy.Field()
    
    # Store Information
    ebay_store = scrapy.Field()
    store_name = scrapy.Field()
    store_url = scrapy.Field()
    store_categories = scrapy.Field()
    
    # Activity Statistics
    items_for_sale = scrapy.Field()
    total_items_sold = scrapy.Field()
    followers_count = scrapy.Field()
    
    # Contact Information
    contact_info = scrapy.Field()
    website_url = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    scraper_version = scrapy.Field()


class EbayCategoryItem(scrapy.Item):
    """Item for eBay category information"""
    
    category_id = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    parent_category = scrapy.Field()
    subcategories = scrapy.Field()
    category_path = scrapy.Field()
    item_count = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field() 