from api.models.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session


def get_session(db: Session = Depends(get_db)):
    return db
