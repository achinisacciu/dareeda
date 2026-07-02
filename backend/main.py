from contextlib import asynccontextmanager

from api.routes import analysis, health, reports
from core.config import _init_dirs, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ponytail: init dirs all'avvio, non a import-time
    _init_dirs()
    yield


app = FastAPI(
    title="DAREEDA API",
    description="Dati puri. Flussi solidi. Nessun database.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registriamo solo i router sopravvissuti
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
