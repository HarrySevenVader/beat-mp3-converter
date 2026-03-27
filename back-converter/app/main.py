from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import configure_logging, get_settings, metrics_service, request_logging_middleware
from app.routes.convert import router as convert_router

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def add_request_observability(request, call_next):
    return await request_logging_middleware(request, call_next)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "X-Request-Id"],
)

app.include_router(convert_router)


@app.get("/api/system/metrics")
def read_metrics():
    return {
        "service": settings.app_name,
        **metrics_service.snapshot(),
    }


@app.get("/api/system/health")
def read_health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/")
def read_root():
    return {"Servidor funcionando🚀"}