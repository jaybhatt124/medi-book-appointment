from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.get("", response_model=List[schemas.ClinicOut])
def list_clinics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Clinic).all()


@router.get("/{clinic_id}", response_model=schemas.ClinicOut)
def get_clinic(
    clinic_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic
