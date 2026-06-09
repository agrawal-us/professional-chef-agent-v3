import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware


def make_envelope(
    data: dict | None,
    request_id: str,
    start_time: float,
    success: bool = True,
    error: dict | None = None,
) -> dict:
    return {
        "success": success,
        "data": data,
        "error": error,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": int((time.monotonic() - start_time) * 1000),
        },
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting Professional Chef Agent API")
    print(f"  Environment : {settings.environment}")
    print(f"  Version     : {settings.api_version}")
    print(f"  LLM provider: {settings.llm_provider}")
    yield
    print("Shutting down Professional Chef Agent API")


app = FastAPI(
    title="Professional Chef Agent API",
    version=settings.api_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)  # outermost — wraps CORS so all responses get X-Request-ID


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    rid = getattr(request.state, "request_id", "unknown")
    st = getattr(request.state, "start_time", time.monotonic())
    return JSONResponse(
        status_code=404,
        content=make_envelope(
            data=None,
            request_id=rid,
            start_time=st,
            success=False,
            error={
                "code": "NOT_FOUND",
                "message": f"Route {request.url.path} not found",
                "details": None,
            },
        ),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    rid = getattr(request.state, "request_id", "unknown")
    st = getattr(request.state, "start_time", time.monotonic())
    return JSONResponse(
        status_code=500,
        content=make_envelope(
            data=None,
            request_id=rid,
            start_time=st,
            success=False,
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
            },
        ),
    )


@app.get("/api/v1/health")
async def health(request: Request):
    rid = getattr(request.state, "request_id", "unknown")
    st = getattr(request.state, "start_time", time.monotonic())
    return make_envelope(
        data={
            "status": "healthy",
            "version": settings.api_version,
            "dependencies": {
                "postgres": {"status": "ok"},
                "redis": {"status": "ok"},
                "llm": {"status": "ok"},
                "openai": {"status": "ok"},
            },
        },
        request_id=rid,
        start_time=st,
    )


@app.get("/")
async def root(request: Request):
    rid = getattr(request.state, "request_id", "unknown")
    st = getattr(request.state, "start_time", time.monotonic())
    return make_envelope(
        data={
            "message": "Professional Chef Agent API",
            "version": settings.api_version,
            "environment": settings.environment,
            "docs": "/docs",
            "health": "/api/v1/health",
        },
        request_id=rid,
        start_time=st,
    )
