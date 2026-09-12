import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app import models  # noqa: F401  (ensures all models are registered on Base.metadata)
from app.config import get_settings
from app.database import Base, engine
from app.routers import audit, auth, dashboard, expenses, notifications, reports, security, settlements, trips
from app.security.rate_limit import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("splitsmart")

settings = get_settings()

if settings.is_production and settings.SECRET_KEY == "dev-only-insecure-secret-change-me":
    raise RuntimeError("SECRET_KEY must be set to a strong random value in production (see .env.example)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SplitSmart API",
    description="Secure group expense management with a cryptographically chained audit ledger.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Too many requests. Please try again later."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


@app.get("/api/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(expenses.router)
app.include_router(settlements.router)
app.include_router(audit.router)
app.include_router(security.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
