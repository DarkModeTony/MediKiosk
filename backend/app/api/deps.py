import os
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Hospital, Patient, Encounter, Document
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def is_auth_enforced() -> bool:
    return os.getenv("AUTH_ENFORCE", "false").lower() in ("true", "1", "yes")

def get_or_create_default_hospital(db: Session) -> Hospital:
    hospital = db.query(Hospital).first()
    if not hospital:
        hospital = Hospital(name="Default General Hospital")
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
    return hospital

def get_or_create_default_doctor(db: Session) -> User:
    hospital = get_or_create_default_hospital(db)
    user = db.query(User).filter(User.role == "DOCTOR").first()
    if not user:
        user = User(
            hospital_id=hospital.id,
            role="DOCTOR",
            username="default_doctor",
            password_hash="mock_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    x_test_hospital_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate the current user via JWT token.
    If AUTH_ENFORCE is disabled and no token is passed, falls back to a default hospital user
    for backward compatibility with unauthenticated tests/demo mode.
    """
    jwt_token = token
    if not jwt_token and authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ")[1]

    if jwt_token:
        payload = decode_access_token(jwt_token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # No token provided
    if is_auth_enforced():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Optional header override for multi-tenant testing without token
    if x_test_hospital_id:
        try:
            hosp_uuid = uuid.UUID(x_test_hospital_id)
            user = db.query(User).filter(User.hospital_id == hosp_uuid).first()
            if user:
                return user
            # Create a test doctor for this hospital
            user = User(
                hospital_id=hosp_uuid,
                role="DOCTOR",
                username=f"doctor_{x_test_hospital_id[:8]}",
                password_hash="test",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except ValueError:
            pass

    return get_or_create_default_doctor(db)

def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the authenticated user is a physician/doctor or admin."""
    role = (current_user.role or "").upper()
    if role not in ("DOCTOR", "PHYSICIAN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Physician access required for clinical operations"
        )
    return current_user

def verify_patient_access(patient_id: str, current_user: User, db: Session) -> Patient:
    """Verify that patient exists and belongs to the user's hospital."""
    try:
        pat_uuid = uuid.UUID(patient_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient = db.query(Patient).filter(Patient.id == pat_uuid).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if patient.hospital_id and current_user.hospital_id and patient.hospital_id != current_user.hospital_id:
        # Cross-hospital access is denied
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient

def verify_encounter_access(encounter_id: str, current_user: User, db: Session) -> Encounter:
    """Verify that encounter exists and belongs to the user's hospital."""
    try:
        enc_uuid = uuid.UUID(encounter_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    encounter = db.query(Encounter).filter(Encounter.id == enc_uuid).first()
    if not encounter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    if encounter.patient_id:
        patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
        if patient and patient.hospital_id and current_user.hospital_id and patient.hospital_id != current_user.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encounter not found"
            )
    return encounter

def verify_document_access(document_id: str, current_user: User, db: Session) -> Document:
    """Verify that document exists and its encounter belongs to the user's hospital."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.encounter_id:
        verify_encounter_access(str(doc.encounter_id), current_user, db)
    return doc
