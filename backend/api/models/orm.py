import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.models.database import Base

def new_id() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id:          Mapped[str]           = mapped_column(String, primary_key=True, default=new_id)
    name:        Mapped[str]           = mapped_column(String(255), nullable=False)
    description: Mapped[str | None]    = mapped_column(Text, nullable=True)
    created_at:  Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:  Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datasets: Mapped[list["Dataset"]] = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id:                  Mapped[str]        = mapped_column(String, primary_key=True, default=new_id)
    project_id:          Mapped[str]        = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    filename:            Mapped[str]        = mapped_column(String(255), nullable=False)
    filepath:            Mapped[str]        = mapped_column(String(512), nullable=False)
    file_format:         Mapped[str]        = mapped_column(String(10), nullable=False)
    n_rows:              Mapped[int]        = mapped_column(Integer, default=0)
    n_cols:              Mapped[int]        = mapped_column(Integer, default=0)
    memory_mb:           Mapped[float]      = mapped_column(Float, default=0.0)
    sampled:             Mapped[bool]       = mapped_column(Boolean, default=False)
    sample_n:            Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Misure suggerite serializzate come JSON (lista di dict con status pending/accepted/rejected)
    suggested_features:  Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:          Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)

    project:       Mapped["Project"]            = relationship("Project", back_populates="datasets")
    analysis_runs: Mapped[list["AnalysisRun"]]  = relationship("AnalysisRun", back_populates="dataset", cascade="all, delete-orphan")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id:             Mapped[str]             = mapped_column(String, primary_key=True, default=new_id)
    dataset_id:     Mapped[str]             = mapped_column(String, ForeignKey("datasets.id"), nullable=False)
    status:         Mapped[str]             = mapped_column(String(20), default="pending")
    progress_pct:   Mapped[int]             = mapped_column(Integer, default=0)
    current_module: Mapped[str | None]      = mapped_column(String(100), nullable=True)
    result_path:    Mapped[str | None]      = mapped_column(String(512), nullable=True)
    error_message:  Mapped[str | None]      = mapped_column(Text, nullable=True)
    started_at:     Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at:   Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    dataset:      Mapped["Dataset"]           = relationship("Dataset", back_populates="analysis_runs")
    report_jobs:  Mapped[list["ReportJob"]]   = relationship("ReportJob", back_populates="analysis_run", cascade="all, delete-orphan")


class ReportJob(Base):
    __tablename__ = "report_jobs"

    id:           Mapped[str]        = mapped_column(String, primary_key=True, default=new_id)
    analysis_id:  Mapped[str]        = mapped_column(String, ForeignKey("analysis_runs.id"), nullable=False)
    status:       Mapped[str]        = mapped_column(String(20), default="pending")
    pdf_path:     Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at:   Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)

    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="report_jobs")
