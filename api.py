from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import json
import os
import uuid
import asyncio
from datetime import datetime
import requests

app = FastAPI(
    title="eBay Scraper API",
    description="API for scraping eBay search results",
    version="1.0.0"
)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Store for async job results
jobs = {}

class ScrapeRequest(BaseModel):
    query: str
    max_results: int = 20
    site: str = "US"
    condition: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort: str = "BestMatch"

class JobStatus(BaseModel):
    job_id: str
    status: str
    results: Optional[List[dict]] = None
    error: Optional[str] = None
    created_at: str

def run_scraper(job_id: str, params: ScrapeRequest):
    """Run the scraper in background"""
    try:
        output_file = f"/tmp/scrape_{job_id}.json"

        cmd = [
            "scrapy", "crawl", "ebay_search",
            "-a", f"query={params.query}",
            "-a", f"max_results={params.max_results}",
            "-a", f"site={params.site}",
            "-a", f"sort={params.sort}",
            "-o", output_file,
            "-L", "ERROR"
        ]

        if params.condition:
            cmd.extend(["-a", f"condition={params.condition}"])
        if params.min_price:
            cmd.extend(["-a", f"min_price={params.min_price}"])
        if params.max_price:
            cmd.extend(["-a", f"max_price={params.max_price}"])

        # Run scrapy
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300
        )

        # Read results
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                data = json.load(f)
            os.remove(output_file)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["results"] = data
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = result.stderr or "No results found"

    except subprocess.TimeoutExpired:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "Scraping timeout (5 min limit)"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/")
async def root():
    return {
        "message": "eBay Scraper API",
        "docs": "/docs",
        "proxy_configured": bool(SCRAPER_API_KEY),
        "endpoints": {
            "/search/lite": "Lightweight search (recommended)",
            "/search": "Scrapy-based search",
            "/search/async": "Async search (returns job_id)",
            "/jobs/{job_id}": "Check async job status",
            "/test": "Test eBay connection",
            "/debug": "Debug eBay response"
        }
    }

@app.get("/search")
async def search_sync(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(20, ge=1, le=100, description="Max results to return"),
    site: str = Query("US", description="eBay site (US, UK, DE, CA, AU)"),
    condition: Optional[str] = Query(None, description="Condition filter (new, used, refurbished)"),
    sort: str = Query("BestMatch", description="Sort order")
):
    """
    Synchronous search - waits for scraping to complete.
    Good for small requests (< 20 items).
    """
    job_id = str(uuid.uuid4())[:8]
    output_file = f"/tmp/scrape_{job_id}.json"

    cmd = [
        "scrapy", "crawl", "ebay_search",
        "-a", f"query={query}",
        "-a", f"max_results={max_results}",
        "-a", f"site={site}",
        "-a", f"sort={sort}",
        "-o", output_file,
        "-L", "ERROR"
    ]

    if condition:
        cmd.extend(["-a", f"condition={condition}"])

    try:
        subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=120
        )

        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                data = json.load(f)
            os.remove(output_file)
            return {
                "success": True,
                "query": query,
                "count": len(data),
                "results": data
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "No results found"}
            )

    except subprocess.TimeoutExpired:
        return JSONResponse(
            status_code=408,
            content={"success": False, "error": "Request timeout"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/search/async")
async def search_async(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Async search - returns immediately with a job_id.
    Use /jobs/{job_id} to check status and get results.
    Good for large requests.
    """
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "results": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "params": request.dict()
    }

    background_tasks.add_task(run_scraper, job_id, request)

    return {
        "job_id": job_id,
        "status": "running",
        "check_url": f"/jobs/{job_id}"
    }

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Check status of an async scraping job"""
    if job_id not in jobs:
        return JSONResponse(
            status_code=404,
            content={"error": "Job not found"}
        )

    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "results_count": len(job["results"]) if job["results"] else 0,
        "results": job["results"],
        "error": job["error"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Get API key from environment variable
SCRAPER_API_KEY = os.environ.get('SCRAPER_API_KEY', '')

@app.get("/search/lite")
async def search_lite(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(20, ge=1, le=50, description="Max results")
):
    """
    Lightweight search using requests (no Scrapy).
    Uses ScraperAPI proxy if SCRAPER_API_KEY is set.
    """
    import re
    from bs4 import BeautifulSoup

    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&_sop=12&LH_BIN=1"

    # Use ScraperAPI if key is available
    if SCRAPER_API_KEY:
        url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={ebay_url}"
        headers = {}
    else:
        url = ebay_url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to fetch eBay: {str(e)}", "using_proxy": bool(SCRAPER_API_KEY)}
        )

    soup = BeautifulSoup(response.text, 'lxml')
    results = []

    # Find items using s-card (new structure)
    cards = soup.select('.s-card')

    for card in cards[:max_results]:
        try:
            # Get link and extract item ID
            link_elem = card.select_one('.s-card__link')
            if not link_elem:
                continue

            href = link_elem.get('href', '')
            item_id_match = re.search(r'/itm/(\d+)', href)
            if not item_id_match:
                continue

            item_id = item_id_match.group(1)

            # Get title
            title_elem = card.select_one('.s-card__title span')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Skip ads / placeholder items
            if not title or title.lower() in ('shop on ebay', ''):
                continue
            if item_id == '123456':
                continue

            # Get price
            price_elem = card.select_one('.s-card__price')
            price = price_elem.get_text(strip=True) if price_elem else ''

            # Skip auction/bid items
            full_text = card.get_text(separator=' ', strip=True).lower()
            if 'bid' in full_text and 'buy it now' not in full_text:
                continue

            # Extract numeric price
            price_num = None
            price_match = re.search(r'[\$£€]([0-9,]+\.?\d*)', price)
            if price_match:
                price_num = float(price_match.group(1).replace(',', ''))

            # Get condition
            condition_elem = card.select_one('.s-card__subtitle span')
            condition = condition_elem.get_text(strip=True) if condition_elem else ''

            # Get image
            img_elem = card.select_one('img')
            image = img_elem.get('src', '') if img_elem else ''

            if title and item_id:
                results.append({
                    'product_id': item_id,
                    'title': title,
                    'price': price,
                    'price_num': price_num,
                    'condition': condition,
                    'url': f'https://www.ebay.com/itm/{item_id}',
                    'image': image
                })

        except Exception:
            continue

    return {
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    }

@app.get("/test")
async def test_ebay_connection():
    """Test if we can connect to eBay"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        resp = requests.get("https://www.ebay.com", headers=headers, timeout=10)
        return {
            "status": "ok",
            "ebay_status_code": resp.status_code,
            "can_connect": resp.status_code == 200
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "can_connect": False
        }

@app.get("/debug")
async def debug_ebay(query: str = "iphone"):
    """Debug eBay response"""
    import re
    from bs4 import BeautifulSoup

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    url = f"https://www.ebay.com/sch/i.html?_nkw={query}"

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(resp.text, 'lxml')

        # Check what we got
        title = soup.title.string if soup.title else "No title"

        # Count different elements
        s_cards = len(soup.select('.s-card'))
        s_items = len(soup.select('.s-item'))
        all_links = len(soup.select('a[href*="/itm/"]'))

        # Get sample of classes
        all_classes = set()
        for elem in soup.select('[class]')[:100]:
            for c in elem.get('class', []):
                if 's-' in c or 'srp' in c:
                    all_classes.add(c)

        return {
            "status_code": resp.status_code,
            "page_title": title,
            "s_cards_found": s_cards,
            "s_items_found": s_items,
            "item_links_found": all_links,
            "sample_classes": list(all_classes)[:20],
            "is_blocked": "captcha" in resp.text.lower() or "robot" in resp.text.lower()
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
