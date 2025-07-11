from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timedelta
from typing import Optional
import string, random
import uvicorn
from logger_util import Log  # ✅ import your reusable logging function

app = FastAPI()

# In-memory storage
urls_db = {}      # shortcode: {original_url, created_at, expiry}
clicks_db = {}    # shortcode: list of clicks

# =================== Logger Middleware ===================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    Log("backend", "info", "middleware", f"{request.method} {request.url}")
    response = await call_next(request)
    return response

# =================== Helper Functions ===================
def generate_shortcode(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in urls_db:
            return code

# =================== Pydantic Models ===================
class ShortenRequest(BaseModel):
    url: HttpUrl
    validity: Optional[int] = 30  # default 30 minutes
    shortcode: Optional[str] = None

class ShortenResponse(BaseModel):
    shortLink: str
    expiry: str

# =================== Routes ===================
@app.post("/shorturls", response_model=ShortenResponse, status_code=201)
async def create_short_url(data: ShortenRequest):
    shortcode = data.shortcode or generate_shortcode()

    if shortcode in urls_db:
        Log("backend", "error", "handler", "Shortcode already exists")
        raise HTTPException(status_code=400, detail="Shortcode already exists")

    try:
        expiry_time = datetime.utcnow() + timedelta(minutes=int(data.validity))
        urls_db[shortcode] = {
            "original_url": data.url,
            "created_at": datetime.utcnow(),
            "expiry": expiry_time
        }
        clicks_db[shortcode] = []
    except Exception as e:
        Log("backend", "fatal", "handler", f"Unexpected error during URL creation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    Log("backend", "info", "handler", f"Created short URL for: {data.url}")
    return ShortenResponse(
        shortLink=f"http://localhost:8000/{shortcode}",
        expiry=expiry_time.isoformat()
    )

@app.get("/shorturls/{shortcode}")
async def get_url_stats(shortcode: str):
    if shortcode not in urls_db:
        Log("backend", "error", "handler", f"Shortcode not found: {shortcode}")
        raise HTTPException(status_code=404, detail="Shortcode not found")

    url_info = urls_db[shortcode]
    click_data = clicks_db.get(shortcode, [])

    Log("backend", "info", "handler", f"Fetched stats for shortcode: {shortcode}")
    return {
        "original_url": url_info["original_url"],
        "created_at": url_info["created_at"].isoformat(),
        "expiry": url_info["expiry"].isoformat(),
        "total_clicks": len(click_data),
        "clicks": click_data
    }

@app.get("/{shortcode}")
async def redirect_to_original(shortcode: str, request: Request):
    if shortcode not in urls_db:
        Log("backend", "error", "handler", f"Shortcode not found during redirect: {shortcode}")
        raise HTTPException(status_code=404, detail="Shortcode not found")

    url_info = urls_db[shortcode]
    if datetime.utcnow() > url_info["expiry"]:
        Log("backend", "error", "handler", f"Attempt to access expired short URL: {shortcode}")
        raise HTTPException(status_code=410, detail="Short URL has expired")

    # Log redirection
    Log("backend", "info", "handler", f"Redirecting to {url_info['original_url']} for {shortcode}")

    clicks_db[shortcode].append({
        "timestamp": datetime.utcnow().isoformat(),
        "referrer": request.headers.get("referer"),
        "geo": request.client.host
    })

    return RedirectResponse(url=url_info["original_url"])

