# Abbiamo rimosso 'datasets' e 'projects'
from api.routes import analysis, health, reports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DAREEDA API",
    description="Dati puri. Flussi solidi. Nessun database.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registriamo solo i router sopravvissuti
app.include_router(health.router,   prefix="/api/health",   tags=["health"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router,  prefix="/api/reports",  tags=["reports"])
