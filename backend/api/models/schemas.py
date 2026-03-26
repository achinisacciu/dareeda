from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    datasets: list['DatasetResponse'] = []
    class Config:
        from_attributes = True

class DatasetResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_format: str
    n_rows: int
    n_cols: int
    memory_mb: float
    sampled: bool
    sample_n: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

class AnalysisStatusResponse(BaseModel):
    id: str
    status: str
    progress_pct: int
    current_module: Optional[str]
    error_message: Optional[str]

class ReportJobResponse(BaseModel):
    id: str
    analysis_id: str
    status: str
    pdf_path: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
