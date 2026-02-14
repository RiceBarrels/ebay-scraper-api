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

app = FastAPI(
    title="eBay Scraper API",
    description="API for scraping eBay search results",
    version="1.0.0"
)

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
        "endpoints": {
            "/search": "Synchronous search (waits for results)",
            "/search/async": "Async search (returns job_id)",
            "/jobs/{job_id}": "Check async job status"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
