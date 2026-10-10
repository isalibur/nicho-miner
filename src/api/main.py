from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from src.db import init_db, get_niches, get_anomalies, get_keywords

app = FastAPI(title="Minerador de Nichos API", version="2.0")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN", "dev-token-12345")
security = HTTPBearer(auto_error=False)

rate_limit_store = {}

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30


async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[client_ip].append(now)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await rate_limit(request)
    response = await call_next(request)
    return response


@app.get("/niches")
async def niches(token: str = Depends(verify_token)):
    return JSONResponse(content=get_niches())


@app.get("/anomalies")
async def anomalies(token: str = Depends(verify_token)):
    return JSONResponse(content=get_anomalies())


@app.get("/keywords")
async def keywords(token: str = Depends(verify_token)):
    return JSONResponse(content=get_keywords())
