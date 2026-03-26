from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import datasets, analysis, projects, reports, health
from api.models.database import init_db

app = FastAPI(
    title="DAREEDA API",
    description="Dati puri. Flussi solidi.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(health.router,    prefix="/api/health",    tags=["health"])
app.include_router(projects.router,  prefix="/api/projects",  tags=["projects"])
app.include_router(datasets.router,  prefix="/api/datasets",  tags=["datasets"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["analysis"])
app.include_router(reports.router,   prefix="/api/reports",   tags=["reports"])
