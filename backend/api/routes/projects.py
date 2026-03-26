import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload, load_only
from api.models.database import get_db
from api.models.orm import Project, Dataset
from api.models.schemas import ProjectCreate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return (
        db.query(Project)
        .options(
            load_only(Project.id, Project.name, Project.description, Project.created_at),
            selectinload(Project.datasets).load_only(
                Dataset.id,
                Dataset.project_id,
                Dataset.filename,
                Dataset.file_format,
                Dataset.n_rows,
                Dataset.n_cols,
                Dataset.memory_mb,
                Dataset.sampled,
                Dataset.sample_n,
                Dataset.created_at,
            ),
        )
        .order_by(Project.created_at.desc())
        .all()
    )

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(id=str(uuid.uuid4()), name=body.name, description=body.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = (
        db.query(Project)
        .options(
            load_only(Project.id, Project.name, Project.description, Project.created_at),
            selectinload(Project.datasets).load_only(
                Dataset.id,
                Dataset.project_id,
                Dataset.filename,
                Dataset.file_format,
                Dataset.n_rows,
                Dataset.n_cols,
                Dataset.memory_mb,
                Dataset.sampled,
                Dataset.sample_n,
                Dataset.created_at,
            ),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Progetto non trovato")
    return p

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Progetto non trovato")
        
    import shutil
    from core.config import settings
    proj_dir = settings.data_dir / project_id
    if proj_dir.exists():
        shutil.rmtree(proj_dir, ignore_errors=True)
        
    db.delete(p)
    db.commit()
